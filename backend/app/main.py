"""
Luna Social Backend - Main Application Entry Point

A sophisticated backend for a social dining platform featuring:
- AI-powered recommendation engine (Spatial + Social Analysis)
- LangGraph agents for automated bookings
- Real-time simulation system for demos
- SSE streaming for live updates
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import settings
from .core.database import init_db
from .api import api_router

# Configure logging
# Use LOG_LEVEL from settings if available, otherwise default based on DEBUG
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO if not settings.DEBUG else logging.DEBUG)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose DEBUG logs from third-party HTTP libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Luna Social Backend...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Luna Social Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Luna Social Backend API

    A sophisticated backend platform for social dining experiences.

    ### Features:
    - **Recommendation Engine**: AI-powered venue and social recommendations
    - **Booking Agents**: Automated reservation management
    - **Simulation System**: Realistic user behavior simulation for demos
    - **Real-time Streaming**: SSE-based live event feeds

    ### Key Endpoints:
    - `/api/v1/recommendations/{user_id}` - Get personalized recommendations
    - `/api/v1/bookings/{user_id}/create` - Create automated bookings
    - `/api/v1/simulation/start` - Start behavior simulation
    - `/api/v1/admin/streams/subscribe/{channel}` - Subscribe to live events
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
# Parse CORS origins from settings or use defaults
cors_origins_str = getattr(settings, 'CORS_ORIGINS', '') if hasattr(settings, 'CORS_ORIGINS') else ''
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()] if cors_origins_str else []

# Add common development ports
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]

# Combine and deduplicate origins
all_origins = list(set(cors_origins + default_origins))

# When allow_credentials=True, we must use specific origins, not ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,  # Always use specific origins when credentials are enabled
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
