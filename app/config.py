from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./pmb.db"
    SQLALCHEMY_ECHO: bool = False
    
    # Application
    APP_NAME: str = "PMB System - Penerimaan Mahasiswa Baru"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()
