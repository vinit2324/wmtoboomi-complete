"""
Application configuration and settings management.
"""
import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    backend_port: int = 7201
    backend_host: str = "localhost"
    
    # MongoDB
    mongodb_url: str
    database_name: str = "wmtoboomi"
    
    # Security
    encryption_key: str
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 524288000  # 500MB
    
    # CORS
    cors_origins: str = "http://localhost:7200"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using Fernet."""
    
    _cipher: Optional[Fernet] = None
    
    @classmethod
    def get_cipher(cls) -> Fernet:
        """Get or create Fernet cipher instance."""
        if cls._cipher is None:
            settings = get_settings()
            key = settings.encryption_key
            
            # If key is placeholder, generate a new one
            if key == "your-fernet-key-here-generate-new-one":
                key = Fernet.generate_key().decode()
                print(f"\n⚠️  WARNING: Using auto-generated encryption key.")
                print(f"   For production, set ENCRYPTION_KEY in .env to: {key}\n")
            
            cls._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        
        return cls._cipher
    
    @classmethod
    def encrypt(cls, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return value
        cipher = cls.get_cipher()
        return cipher.encrypt(value.encode()).decode()
    
    @classmethod
    def decrypt(cls, encrypted_value: str) -> str:
        """Decrypt an encrypted string value."""
        if not encrypted_value:
            return encrypted_value
        cipher = cls.get_cipher()
        return cipher.decrypt(encrypted_value.encode()).decode()


# Initialize upload directory
def init_upload_dir():
    """Create upload directory if it doesn't exist."""
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
