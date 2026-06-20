import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TRAINING_DIR = Path(os.getenv("TRAINING_DIR", r"D:\skripsi\Python\DataCoffe"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "coffee-secret-key")
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    DEFAULT_MODEL_PATH = TRAINING_DIR / "cnn_multimodal_model.h5"
    MODEL_PATH = Path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH if DEFAULT_MODEL_PATH.exists() else BASE_DIR / "models" / "coffee_grading_cnn_model.keras"))
    LABELS_PATH = Path(os.getenv("LABELS_PATH", BASE_DIR / "models" / "labels.txt"))
    SENSOR_CONFIG_PATH = Path(os.getenv("SENSOR_CONFIG_PATH", BASE_DIR / "sensor_config.json"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    IMG_SIZE = int(os.getenv("IMG_SIZE", "224"))
