import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Bus Tracker"
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    access_token_expire_minutes: int = 60 * 12  # 12 hours for driver sessions
    
    # Database - defaults to SQLite for easy local development
    # For PostgreSQL: set DATABASE_URL=postgresql://user:pass@localhost:5432/bustracker
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./bustracker.db"  # SQLite for local dev, change to PostgreSQL for production
    )
    
    # Frontend URL for generating tracking links
    # In production, set this to your domain: https://yourdomain.com
    # Leave empty to auto-detect from request
    frontend_url: str = os.getenv("FRONTEND_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()

