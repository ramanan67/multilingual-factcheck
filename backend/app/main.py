"""
FastAPI Main Application Entry Point.
Initializes FastAPI, CORS middleware, API routers, and serves the static frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os

from backend.app.api.routes import router
from backend.app.config import settings
from backend.app.utils.database import init_db
from backend.app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    init_db()
    logger.info(f"{settings.APP_NAME} initialized successfully.")
    yield
    logger.info(f"{settings.APP_NAME} shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multilingual Fake News Detection & News Verification Web Application for English & Tamil.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)

# Mount Frontend Static Directory
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info(f"Mounted static frontend from {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
