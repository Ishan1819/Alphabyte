import joblib

MODEL_PATH = "models/pii_ner_model.pkl"

try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
