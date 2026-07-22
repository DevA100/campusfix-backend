"""
Application configuration loaded from environment variables.
"""

import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusFix"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads"  # Changed from "app/uploads" to "uploads" for Render

    # CORS - Allow multiple origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://campusfix-frontend.vercel.app",
        "https://*.vercel.app",
        os.getenv("FRONTEND_URL", ""),
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Clean up CORS origins (remove empty strings)
settings.BACKEND_CORS_ORIGINS = [
    origin for origin in settings.BACKEND_CORS_ORIGINS if origin
]
