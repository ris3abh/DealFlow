import os
from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # General settings
    APP_NAME: str = "DealFlow API"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dealflow-secret-key")
    AUTH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dealflow.db")
    
    # Model settings
    DEFAULT_MODEL_PLATFORM: str = "OPENAI"
    DEFAULT_MODEL_TYPE: str = "GPT_4O_MINI"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Client settings
    MAX_CLIENTS: int = 10
    MAX_CONVERSATIONS_PER_CLIENT: int = 1000
    CONVERSATION_TIMEOUT_MINUTES: int = 60  # Inactive conversations timeout
    
    # Performance settings
    WORKER_POOL_SIZE: int = 4
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()