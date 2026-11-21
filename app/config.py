"""
Configuration Module for AIS Inventory System
Loads environment variables, manages Neon PostgreSQL connection settings,
and configures single-user application parameters.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()


class Settings(BaseSettings):
    """
    Application Settings
    - Supports Neon PostgreSQL connection string (DATABASE_URL)
    - Automatically normalizes legacy 'postgres://' URLs to 'postgresql://'
    - Falls back to local SQLite if DATABASE_URL is not set for local offline use
    - Sets default single-user operator identity for audit stamping
    """
    APP_NAME: str = "AIS Inventory Management & Valuation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Neon PostgreSQL connection string
    # Format: postgresql://[user]:[password]@[neon-hostname]/[database]?sslmode=require
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./ais_inventory.db"  # Reliable fallback for zero-config offline runs
    )
    
    # Single-user operator profile (College AIS Project Default)
    DEFAULT_OPERATOR: str = os.getenv("DEFAULT_OPERATOR", "System Operator")
    
    @property
    def normalized_database_url(self) -> str:
        """
        Normalizes database URLs for SQLAlchemy 2.0 compatibility.
        Cloud providers (Neon/Heroku) often supply 'postgres://', which SQLAlchemy expects as 'postgresql://'.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
