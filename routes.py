import os
import pytesseract
import nltk
from fastapi import APIRouter, File, UploadFile, HTTPException
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import pos_tag, ne_chunk
import nltk
nltk.download('punkt')
nltk.download('maxent_ne_chunker_tab')
nltk.download('words')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('punkt_tab')


router = APIRouter()

pytesseract.pytesseract.tesseract_cmd = r"F:/Ishan_Data/PII_Detection/tesseract.exe"


def perform_ocr(image: Image):
    return pytesseract.image_to_string(image)

def extract_pii(text: str):
    """Perform Named Entity Recognition (NER) using NLTK to extract PII data"""
    sentences = sent_tokenize(text)
    entities = []

    for sentence in sentences:
        words = word_tokenize(sentence)
        tagged_words = pos_tag(words)
        chunked = ne_chunk(tagged_words)

        for subtree in chunked:
            if hasattr(subtree, "label"):  # Named Entity detected
                entity = " ".join([token for token, pos in subtree.leaves()])
                entities.append({"entity": entity, "label": subtree.label()})

    return entities

@router.get("/")
def home():
    return {"message": "Welcome to the PII Detection API"}


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1].lower()

        if file_ext not in ["jpg", "jpeg", "png", "pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Process PDF
        if file_ext == "pdf":
            images = convert_from_bytes(await file.read())
            text = " ".join([perform_ocr(img) for img in images])
        else:  # Process JPG/PNG
            image = Image.open(BytesIO(await file.read()))
            text = perform_ocr(image)

        pii_data = extract_pii(text)

        return {"extracted_text": text, "pii_data": pii_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))