from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database settings
    TIDB_HOST: str = "localhost"
    TIDB_PORT: int = 4000
    TIDB_USER: str = "root"
    TIDB_PASSWORD: str = ""
    TIDB_DATABASE: str = "smartdocflow"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SmartDocFlow"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # Slack settings
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None
    
    # Google Calendar settings
    GOOGLE_CALENDAR_CREDENTIALS: Optional[str] = None
    
    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt", ".png", ".jpg", ".jpeg"]
    
    # Vector search settings
    VECTOR_DIMENSION: int = 768
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
