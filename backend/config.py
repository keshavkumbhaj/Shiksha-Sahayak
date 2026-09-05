import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or backend
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration settings."""
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    
    # Storage paths
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(DATA_DIR / "uploads"))
    PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", str(DATA_DIR / "processed"))
    
    # SQLite Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "shiksha_sahayak.db"))
    
    # Upload limits (16 MB maximum file size)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}
    
    # AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
os.makedirs(Path(Config.DATABASE_PATH).parent, exist_ok=True)
