from fastapi import APIRouter, Request, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from io import BytesIO
import re

# Initialize Router
router = APIRouter()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"F:/Ishan_Data/PII_Detection/tesseract.exe"

def perform_ocr(image: Image):
    """Extract text from image using OCR."""
    return pytesseract.image_to_string(image)

def extract_pii(text: str):
    """Extract specific PII (Name and Aadhar number) from text"""
    pii_data = {
        'name': None,
        'aadhar_number': None,
        'address': None
    }

    # Extract Aadhar number
    aadhar_pattern = r'\d{4}\s?\d{4}\s?\d{4}'
    aadhar_matches = re.findall(aadhar_pattern, text)
    if aadhar_matches:
        pii_data['aadhar_number'] = aadhar_matches[0]

    # Extract name
    name_patterns = [
        r'(?:name is|Name:|^)\s*([A-Z][a-zA-Z\s]+)',
        r'([A-Z][a-zA-Z\s]+)(?=\s+Father)',
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, text)
        if name_match:
            pii_data['name'] = name_match.group(1).strip()
            break

    # Extract address
    address_pattern = r'Address:\s*([^\.]+)'
    address_match = re.search(address_pattern, text)
    if address_match:
        pii_data['address'] = address_match.group(1).strip()

    return pii_data

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1].lower()

        if file_ext not in ["jpg", "jpeg", "png", "pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Process PDF or Image
        if file_ext == "pdf":
            images = convert_from_bytes(await file.read())
            text = " ".join([perform_ocr(img) for img in images])
        else:
            image = Image.open(BytesIO(await file.read()))
            text = perform_ocr(image)

        # Extract PII
        pii_data = extract_pii(text)

        # Format results
        formatted_results = {
            "Original Text": text,
            "Detected PII Information": {
                "Name": pii_data['name'] if pii_data['name'] else "Not detected",
                "Aadhar Number": pii_data['aadhar_number'] if pii_data['aadhar_number'] else "Not detected",
                "Address": pii_data['address'] if pii_data['address'] else "Not detected"
            }
        }

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "results": formatted_results
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
