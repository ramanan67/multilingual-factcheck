from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schemas import ClaimRequest, ClaimResponse, MediaClaimResponse
from app.services.verdict import evaluate_claim
from app.services.ingest import ingest_all
from app.services.media import (
    extract_text_from_image_bytes,
    extract_text_from_video_bytes,
    MediaProcessingError,
)

router = APIRouter(prefix="/api", tags=["claims"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
VIDEO_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}


@router.post("/check", response_model=ClaimResponse)
async def check_claim(payload: ClaimRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    return evaluate_claim(payload.text.strip())


@router.post("/check/media", response_model=MediaClaimResponse)
async def check_media_claim(file: UploadFile = File(...)):
    """
    Accepts an image or video, extracts any readable text from it
    (OCR on images; OCR across sampled frames for video), then runs the
    same claim-verification pipeline as /api/check.
    """
    content_type = (file.content_type or "").lower()

    if content_type in IMAGE_CONTENT_TYPES:
        media_type = "image"
    elif content_type in VIDEO_CONTENT_TYPES:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{content_type or 'unknown'}'. "
                "Supported: JPG/PNG/WEBP/BMP images, or MP4/MOV/AVI/WEBM video."
            ),
        )

    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file was empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data) / 1_000_000:.1f} MB). Limit is 25 MB.",
        )

    try:
        if media_type == "image":
            extracted_text = extract_text_from_image_bytes(data)
        else:
            extracted_text = extract_text_from_video_bytes(data, filename_hint=file.filename or ".mp4")
    except MediaProcessingError as e:
        # Message is already written to be user-facing.
        raise HTTPException(status_code=422, detail=str(e))

    result = evaluate_claim(extracted_text)
    return MediaClaimResponse(
        **result.model_dump(),
        extracted_text=extracted_text,
        media_type=media_type,
    )


@router.post("/ingest/run")
async def trigger_ingest():
    """Manually trigger one ingestion pass across all whitelisted outlets.
    Useful for local testing before the scheduler kicks in."""
    count = await ingest_all()
    return {"indexed": count}
