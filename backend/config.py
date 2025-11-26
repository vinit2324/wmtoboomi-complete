"""Application configuration"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    app_name: str = "webMethods to Boomi Migration Accelerator"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Backend
    backend_host: str = os.getenv("BACKEND_HOST", "localhost")
    backend_port: int = int(os.getenv("BACKEND_PORT", "7201"))
    
    # MongoDB
    mongodb_url: str = os.getenv(
        "MONGODB_URL",
        "mongodb+srv://vinit:Delhi123@vvmdb1.6umwxkw.mongodb.net/wmtoboomi?retryWrites=true&w=majority&appName=VVMDB1"
    )
    database_name: str = os.getenv("DATABASE_NAME", "wmtoboomi")
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:7200",
        "http://127.0.0.1:7200",
    ]
    
    # Upload
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "524288000"))
    
    # Encryption
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "p2haVTjsxyriBCgqBifQ990JIH4dTs9UX711XsAuU8g=")
    
    class Config:
        env_file = ".env"

settings = Settings()
