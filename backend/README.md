# News Truth Checker - Backend API

FastAPI backend service for multilingual fake news detection and news verification.

## Running the Backend
```bash
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Running Tests
```bash
python -m pytest tests/ -v
```

See root [README.md](../README.md) for full architecture and source registry documentation.
