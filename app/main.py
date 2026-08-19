from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.routers import claims
from app.services.ingest import ingest_all

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run one ingestion pass at startup, then keep the index fresh
    # on a fixed interval in the background.
    await ingest_all()
    scheduler.add_job(
        ingest_all,
        "interval",
        minutes=settings.RSS_POLL_INTERVAL_MINUTES,
        id="rss_ingest",
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Multilingual Whitelisted Fact-Check API",
    description="Cross-verifies claims (English/Tamil) against 7 trusted outlets.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "whitelist_size": len(settings.WHITELIST),
        "code_version": "2024-media-upload-3",  # bump this string whenever verdict.py logic changes
    }
