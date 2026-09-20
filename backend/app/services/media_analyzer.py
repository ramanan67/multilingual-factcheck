"""
Multimodal Media Analyzer for Image and Video Fact-Checking.
Combines Tesseract OCR (with native Tamil & English traineddata) and EasyOCR
to accurately extract text from screenshots, posters, and video keyframes.
"""

import os
import re
import tempfile
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from PIL import Image
import cv2
import pytesseract

from backend.app.utils.text_cleaner import clean_text
from backend.app.utils.logger import logger

# Configure Tesseract binary and tessdata path
TESSERACT_CANDIDATE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]

for p in TESSERACT_CANDIDATE_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        logger.info(f"Configured Tesseract executable at: {p}")
        break

# Configure custom tessdata directory if available
ASSETS_TESSDATA = Path(__file__).resolve().parent.parent / "assets" / "tessdata"
if ASSETS_TESSDATA.exists() and (ASSETS_TESSDATA / "tam.traineddata").exists():
    os.environ["TESSDATA_PREFIX"] = str(ASSETS_TESSDATA)
    logger.info(f"Configured TESSDATA_PREFIX: {ASSETS_TESSDATA}")

# Lazy EasyOCR reader for deep learning fallback
_easyocr_en_reader = None


def get_easyocr_reader():
    """Lazily initializes EasyOCR reader for English as a secondary engine."""
    global _easyocr_en_reader
    if _easyocr_en_reader is None:
        try:
            import easyocr
            _easyocr_en_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            logger.debug(f"EasyOCR init notice: {str(e)}")
            _easyocr_en_reader = False
    return _easyocr_en_reader if _easyocr_en_reader is not False else None


class MediaAnalyzer:
    """Extracts text and news claims from uploaded images and video files."""

    @classmethod
    def preprocess_image(cls, img_np: np.ndarray) -> np.ndarray:
        """Enhances image contrast and sharpness for screenshots and news graphics."""
        try:
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_np

            h, w = gray.shape[:2]
            if w < 700:
                scale = 700.0 / w
                gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            return enhanced
        except Exception:
            return img_np

    @classmethod
    def extract_text_from_image_bytes(cls, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extracts Tamil and English text from image bytes (PNG, JPG, WEBP).
        Uses Tesseract (eng+tam) first, falling back to EasyOCR.
        """
        if not image_bytes:
            return {"text": "", "lines": [], "confidence": 0.0, "success": False, "error": "Empty image"}

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return {"text": "", "lines": [], "confidence": 0.0, "success": False, "error": "Invalid image format"}

            processed = cls.preprocess_image(img)
            pil_img = Image.fromarray(processed)

            lines: List[str] = []
            ocr_engine_used = "tesseract"

            # Method 1: Tesseract with Tamil + English
            try:
                # Check if Tamil model is present
                tess_lang = "eng+tam" if (ASSETS_TESSDATA / "tam.traineddata").exists() else "eng"
                tess_text = pytesseract.image_to_string(pil_img, lang=tess_lang)
                raw_lines = [clean_text(line) for line in tess_text.split("\n") if len(clean_text(line)) > 1]
                if raw_lines:
                    lines = raw_lines
                    ocr_engine_used = f"tesseract ({tess_lang})"
            except Exception as tess_err:
                logger.debug(f"Tesseract OCR attempt note: {str(tess_err)}")

            # Method 2: Fallback to EasyOCR if Tesseract gave no lines
            if not lines:
                reader = get_easyocr_reader()
                if reader:
                    try:
                        results = reader.readtext(processed)
                        for bbox, text, conf in results:
                            cleaned = clean_text(text)
                            if len(cleaned) > 1 and conf > 0.15:
                                lines.append(cleaned)
                        if lines:
                            ocr_engine_used = "easyocr"
                    except Exception as easy_err:
                        logger.debug(f"EasyOCR attempt note: {str(easy_err)}")

            combined_text = "\n".join(lines).strip()
            if not combined_text:
                return {
                    "text": "",
                    "lines": [],
                    "confidence": 0.0,
                    "success": False,
                    "error": "No readable text detected in this image. Please ensure the screenshot or poster contains visible text."
                }

            return {
                "text": combined_text,
                "lines": lines,
                "confidence": 0.88,
                "engine": ocr_engine_used,
                "success": True
            }

        except Exception as e:
            logger.error(f"Image OCR error: {str(e)}")
            return {"text": "", "lines": [], "confidence": 0.0, "success": False, "error": str(e)}

    @classmethod
    def extract_text_from_video_bytes(cls, video_bytes: bytes, filename: str = "video.mp4") -> Dict[str, Any]:
        """
        Samples video keyframes, extracts on-screen text/tickers, and aggregates unique statements.
        """
        if not video_bytes:
            return {"text": "", "lines": [], "keyframes_analyzed": 0, "success": False}

        suffix = Path(filename).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(video_bytes)
            tmp_path = tmp_file.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return {"text": "", "lines": [], "keyframes_analyzed": 0, "success": False, "error": "Could not open video file"}

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = int(fps * 1.5)
            if frame_interval <= 0:
                frame_interval = 30

            unique_lines = []
            seen_texts = set()
            frames_analyzed = 0
            current_frame_idx = 0

            tess_lang = "eng+tam" if (ASSETS_TESSDATA / "tam.traineddata").exists() else "eng"

            while cap.isOpened() and frames_analyzed < 10:
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                frames_analyzed += 1
                processed_frame = cls.preprocess_image(frame)
                pil_frame = Image.fromarray(processed_frame)

                try:
                    text_out = pytesseract.image_to_string(pil_frame, lang=tess_lang)
                    for line in text_out.split("\n"):
                        cleaned = clean_text(line)
                        if len(cleaned) > 2:
                            norm = cleaned.lower().replace(" ", "")
                            if norm not in seen_texts:
                                seen_texts.add(norm)
                                unique_lines.append(cleaned)
                except Exception:
                    pass

                current_frame_idx += frame_interval
                if current_frame_idx >= total_frames:
                    break

            cap.release()

            combined_text = "\n".join(unique_lines).strip()
            if not combined_text:
                return {
                    "text": "",
                    "lines": [],
                    "keyframes_analyzed": frames_analyzed,
                    "success": False,
                    "error": "No readable text tickers or news banners detected in video keyframes."
                }

            return {
                "text": combined_text,
                "lines": unique_lines,
                "keyframes_analyzed": frames_analyzed,
                "success": True
            }

        except Exception as e:
            logger.error(f"Video analysis error: {str(e)}")
            return {"text": "", "lines": [], "keyframes_analyzed": 0, "success": False, "error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
