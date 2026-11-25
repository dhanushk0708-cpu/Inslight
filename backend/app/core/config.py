import os
from typing import List
from dotenv import load_dotenv

# Robustly load .env from current directory, parent directory, and backend directory
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(_backend_dir), ".env"))
load_dotenv()


class Settings:
    PROJECT_NAME: str = "INSLIGHT"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database: Supports PostgreSQL or SQLite fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/inslight.db"
    )

    # JWT / Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Groq / LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_URL: str = "https://api.groq.com/openai/v1/chat/completions"

    # Storage paths
    DATASET_STORAGE_DIR: str = os.getenv("DATASET_STORAGE_DIR", "./data/datasets")
    REPORT_STORAGE_DIR: str = os.getenv("REPORT_STORAGE_DIR", "./data/reports")

    # Encryption key for tokens at rest
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # Google OAuth / Gmail Integration
    GOOGLE_OAUTH_CREDENTIALS_FILE: str = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE", "google-oauth-credentials.json")
    GMAIL_REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/gmail/callback")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()

# Ensure data directories exist
os.makedirs("data", exist_ok=True)
os.makedirs(settings.DATASET_STORAGE_DIR, exist_ok=True)
os.makedirs(settings.REPORT_STORAGE_DIR, exist_ok=True)
