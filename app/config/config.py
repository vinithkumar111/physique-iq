import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PhysiqueIQ"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "SUPER_SECRET_SECURITY_KEY_FOR_PHYSIQUEIQ_JWT_TOKENS_DO_NOT_USE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for ease of testing
    
    # Database
    # Defaulting to PostgreSQL but falling back to local SQLite database if not specified
    DATABASE_URL: str = "sqlite:///./physiqueiq.db"
    
    # AI (OpenAI / Ollama)
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_HOST: str = "http://localhost:11434"
    AI_MODEL: str = "gpt-4o"  # or llama3
    
    # Vector DB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Upload Directories
    UPLOAD_DIR: str = "uploads"
    PROGRESS_PHOTO_DIR: str = "uploads/progress_photos"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROGRESS_PHOTO_DIR, exist_ok=True)
