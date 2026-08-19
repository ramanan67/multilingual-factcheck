# NOTE ON PYTHON 3.14: chromadb (this project's vector store) has an open,
# unresolved bug on Python 3.14 caused by its dependency on Pydantic v1's
# compatibility shim (chroma-core/chroma issues #5996, #5983). Until that's
# patched upstream, this image stays on 3.12, which installs and runs
# cleanly. All application code in app/ is written using only
# 3.14-compatible syntax -- once chromadb ships a fix, changing the line
# below to `python:3.14-slim` is the only change needed.
FROM python:3.12-slim

WORKDIR /app

# build-essential: needed to build a couple of ML deps from source on some platforms
# tesseract-ocr + tesseract-ocr-eng + tesseract-ocr-tam: OCR engine + English/Tamil language packs
# libgl1: required by opencv-python-headless at import time even in headless mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-tam \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
