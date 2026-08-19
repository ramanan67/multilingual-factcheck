"""
Extracts checkable claim text from uploaded images and videos.

Strategy:
- Image: run OCR directly on the image (covers screenshots of WhatsApp
  forwards, social media posts, news chyrons, etc).
- Video: sample a handful of evenly-spaced frames and OCR each one,
  merging the results. This catches on-screen text (captions, news
  tickers, subtitles) but NOT spoken audio -- there is no audio
  transcription step. Adding one (e.g. via whisper) is a reasonable
  future extension, but it roughly doubles the dependency footprint
  (ffmpeg + a speech model) and this app is already heavy on ML deps,
  so it's intentionally left out for now rather than silently degrading
  performance on both features.

Every public function raises MediaProcessingError with a message that's
safe to show directly to the user -- callers should catch that one
exception type and turn it into an HTTP 422, not let raw cv2/pytesseract
exceptions leak out.
"""

import io
import tempfile
import os
from typing import List

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
import pytesseract

MAX_VIDEO_FRAMES = 8


class MediaProcessingError(Exception):
    """Raised for any recoverable media-processing failure; the message
    is written to be shown directly to the end user."""


def _run_ocr(image: Image.Image, lang: str = "eng+tam") -> str:
    try:
        return pytesseract.image_to_string(image, lang=lang).strip()
    except pytesseract.TesseractNotFoundError as e:
        raise MediaProcessingError(
            "OCR engine (Tesseract) isn't installed on the server. "
            "See README for setup instructions."
        ) from e
    except pytesseract.TesseractError as e:
        # Common cause: the "tam" (Tamil) language pack isn't installed --
        # fall back to English-only OCR rather than failing outright.
        if "tam" in str(e).lower() or "failed loading language" in str(e).lower():
            try:
                return pytesseract.image_to_string(image, lang="eng").strip()
            except Exception as inner:
                raise MediaProcessingError(f"OCR failed: {inner}") from inner
        raise MediaProcessingError(f"OCR failed: {e}") from e


def extract_text_from_image_bytes(data: bytes) -> str:
    if not data:
        raise MediaProcessingError("Uploaded image file was empty.")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()  # force-read now so corrupt files fail here, not later
    except UnidentifiedImageError as e:
        raise MediaProcessingError(
            "That file doesn't look like a valid image. Supported formats: "
            "JPG, PNG, WEBP, BMP."
        ) from e
    except Exception as e:
        raise MediaProcessingError(f"Couldn't open the image: {e}") from e

    text = _run_ocr(image)
    if not text:
        raise MediaProcessingError(
            "No readable text was found in this image. The claim checker "
            "works from text (headlines, captions, forwarded messages) -- "
            "if the image has no visible text, try typing the claim instead."
        )
    return text


def _sample_frame_indices(total_frames: int, n: int) -> List[int]:
    if total_frames <= n:
        return list(range(total_frames))
    step = total_frames / n
    return [int(i * step) for i in range(n)]


def extract_text_from_video_bytes(data: bytes, filename_hint: str = ".mp4") -> str:
    if not data:
        raise MediaProcessingError("Uploaded video file was empty.")

    suffix = os.path.splitext(filename_hint)[1] or ".mp4"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise MediaProcessingError(
                "Couldn't open that video file. Supported formats: MP4, "
                "MOV, AVI, WEBM."
            )

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise MediaProcessingError(
                "The video appears to have no readable frames (it may be "
                "corrupted or use an unsupported codec)."
            )

        indices = _sample_frame_indices(total_frames, MAX_VIDEO_FRAMES)
        seen_lines: List[str] = []
        seen_set = set()

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(rgb)
            try:
                frame_text = _run_ocr(pil_frame)
            except MediaProcessingError:
                continue  # skip a single bad frame rather than failing the whole video
            for line in frame_text.splitlines():
                line = line.strip()
                if line and line not in seen_set:
                    seen_set.add(line)
                    seen_lines.append(line)

        cap.release()

        merged = "\n".join(seen_lines).strip()
        if not merged:
            raise MediaProcessingError(
                "No readable on-screen text was found across the sampled "
                "video frames. Note: this checks visible text/captions "
                "only, not spoken audio -- if the claim is only spoken, "
                "try typing it instead."
            )
        return merged

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
