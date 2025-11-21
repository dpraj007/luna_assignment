"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # App settings
    APP_NAME: str = "Luna Social Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./luna_social.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    USE_FAKE_REDIS: bool = True  # Use fakeredis for demo

    # OpenAI (optional - for LLM-powered features)
    OPENAI_API_KEY: Optional[str] = None

    # Simulation settings
    DEFAULT_SIMULATION_SPEED: float = 1.0
    MAX_SIMULATION_SPEED: float = 100.0
    DEFAULT_USER_POOL_SIZE: int = 50

    # Recommendation settings
    RECOMMENDATION_LIMIT: int = 10
    COMPATIBILITY_THRESHOLD: float = 0.5
    MAX_DISTANCE_KM: float = 50.0

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
