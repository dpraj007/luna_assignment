"""
Application configuration settings.

All settings can be overridden via environment variables.
See .env.example for documentation.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # ==========================================================================
    # App Settings
    # ==========================================================================
    APP_NAME: str = "Luna Social Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # Database
    # ==========================================================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./luna_social.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ==========================================================================
    # Redis & Streaming
    # ==========================================================================
    REDIS_URL: str = "redis://localhost:6379"
    USE_FAKE_REDIS: bool = True  # Use in-memory backend for demo
    STREAM_BACKEND: str = "memory"  # memory, redis, or kafka
    EVENT_HISTORY_LIMIT: int = 1000
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = None

    # ==========================================================================
    # OpenAI (optional - for LLM-powered features)
    # ==========================================================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # ==========================================================================
    # Simulation Settings
    # ==========================================================================
    DEFAULT_SIMULATION_SPEED: float = 1.0
    MAX_SIMULATION_SPEED: float = 100.0
    DEFAULT_USER_POOL_SIZE: int = 50
    SIMULATION_TICK_INTERVAL_SECONDS: float = 1.0
    SIMULATION_MAX_ACTIVE_USERS: int = 100
    USE_LANGGRAPH_ORCHESTRATOR: bool = True

    # ==========================================================================
    # Recommendation Settings
    # ==========================================================================
    RECOMMENDATION_LIMIT: int = 10
    COMPATIBILITY_THRESHOLD: float = 0.5
    MAX_DISTANCE_KM: float = 50.0

    # ==========================================================================
    # Preference Evolution
    # ==========================================================================
    PREFERENCE_EVOLUTION_ENABLED: bool = True
    PREFERENCE_LEARNING_RATE: float = 0.1
    PREFERENCE_SOCIAL_INFLUENCE_RATE: float = 0.02

    # ==========================================================================
    # Environment & Weather
    # ==========================================================================
    WEATHER_API_KEY: Optional[str] = None  # OpenWeatherMap API key
    DEFAULT_LOCATION_LAT: float = 40.7128  # NYC
    DEFAULT_LOCATION_LON: float = -74.0060

    # ==========================================================================
    # Frontend & Visualization
    # ==========================================================================
    MAP_PROVIDER: str = "leaflet"  # leaflet or mapbox
    MAPBOX_TOKEN: Optional[str] = None
    ENABLE_ADVANCED_VISUALIZATIONS: bool = True

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    ENABLE_WEBSOCKET: bool = True
    ENABLE_KAFKA: bool = False
    ENABLE_REPLAY: bool = True
    ENABLE_SNAPSHOTS: bool = True
    ENABLE_JOURNEY_TRACKING: bool = True

    # ==========================================================================
    # CORS Settings
    # ==========================================================================
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
