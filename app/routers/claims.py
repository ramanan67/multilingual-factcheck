from fastapi import APIRouter, HTTPException
from app.models.schemas import ClaimRequest, ClaimResponse
from app.services.verdict import evaluate_claim
from app.services.ingest import ingest_all

router = APIRouter(prefix="/api", tags=["claims"])


@router.post("/check", response_model=ClaimResponse)
async def check_claim(payload: ClaimRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    return evaluate_claim(payload.text.strip())


@router.post("/ingest/run")
async def trigger_ingest():
    """Manually trigger one ingestion pass across all whitelisted outlets.
    Useful for local testing before the scheduler kicks in."""
    count = await ingest_all()
    return {"indexed": count}
