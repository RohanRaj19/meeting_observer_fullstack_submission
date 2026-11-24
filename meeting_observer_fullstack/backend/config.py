import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "development-only-change-this")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6.2-sol").strip()
    PORT = int(os.getenv("PORT", "5000"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "15")) * 1024 * 1024

    database_value = os.getenv("DATABASE_PATH", "instance/meeting_observer.db")
    DATABASE_PATH = (BACKEND_DIR / database_value).resolve()
