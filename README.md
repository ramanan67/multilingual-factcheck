# Multilingual Whitelisted Fact-Check Engine

Cross-verifies claims (English + Tamil) against 7 trusted outlets:
The Hindu, Indian Express, Times of India, Hindustan Times, Daily Thanthi,
Polimer News, and Puthiya Thalaimurai.

Architecture: **Option A + B combined** — a background worker keeps a local
vector index of recent headlines from all 7 outlets fresh (Option B), and
each claim is checked against that index using multilingual embeddings +
NLI stance classification (Option A).

## 1. One-time setup

### Get a Google Programmable Search Engine key
1. Go to https://programmablesearchengine.google.com/ and create a new
   search engine.
2. Under "Sites to search," add each of the 7 domains **individually**
   (one per line) — this is more reliable than combining them with `OR` in
   the query string.
3. Get an API key from https://console.cloud.google.com/apis/credentials
   and enable the "Custom Search API."
4. Copy `.env.example` to `.env` and fill in `GOOGLE_CSE_API_KEY` and
   `GOOGLE_CSE_ENGINE_ID`.

```bash
cp .env.example .env
# edit .env with your keys
```

Note: the Google CSE search service isn't wired into the verdict endpoint
yet by default — the verdict engine runs primarily off the local RSS/scrape
index (`app/services/ingest.py`), which is free and doesn't need the CSE
key to function. CSE (`app/services/search.py`) is there as an on-demand
deeper-search option you can call for claims where the local index turns
up nothing — wire it into `verdict.py` if you want that fallback.

## 2. Run with Docker (recommended — easiest deploy)

```bash
docker compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- Dashboard: http://localhost:8501

First startup will download the embedding + NLI models (a few hundred MB)
and run an initial ingestion pass, so it can take a couple of minutes the
first time.

## 3. Run locally without Docker

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install CPU-only torch FIRST. Without --index-url, pip resolves the
# default torch build, which on some platforms depends on separate NVIDIA
# CUDA packages and fails to import without a real GPU + CUDA drivers
# installed. This CPU build works everywhere and is all this project needs.
pip install torch --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt

# Terminal 1 — API
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Dashboard
streamlit run dashboard.py
```

## 4. Using it

- Open the dashboard, paste a claim in English or Tamil, click **Verify**.
- Click **Refresh source index now** to force an immediate re-pull of the
  latest headlines instead of waiting for the 15-minute background cycle.
- Or call the API directly:

```bash
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Central government announces new scheme for farmers"}'
```

## Project layout

```
app/
  core/config.py       -> whitelist + settings
  models/schemas.py    -> request/response models
  services/
    lang.py            -> Tamil/English detection
    search.py          -> Google CSE site-restricted search (optional)
    ingest.py           -> RSS + scraper fallback ingestion
    vectorstore.py      -> Chroma + multilingual-e5 embeddings
    verdict.py           -> NLI stance classification + verdict logic
  routers/claims.py    -> /api/check, /api/ingest/run
  main.py              -> FastAPI app + background scheduler
dashboard.py           -> Streamlit UI
Dockerfile / Dockerfile.dashboard / docker-compose.yml
```

## Python version

This project targets **Python 3.14.4**. Note that Python 3.14 is very
recent, so several ML dependencies (`torch`, `sentence-transformers`,
`transformers`, `chromadb`) are pinned with `>=` floors rather than exact
versions in `requirements.txt` -- this lets `pip` resolve whatever current
release actually ships a `cp314` wheel, since older exact-pinned versions
(e.g. `torch==2.4.1`) predate 3.14 support entirely and will fail to
install. If you hit a dependency resolution error on install, it likely
means one of these packages hasn't shipped a 3.14 wheel yet; in that case,
either wait for an update or fall back to Python 3.12/3.13, which have
broader ML-ecosystem support today.

## Python version

This project targets **Python 3.14.4** (see `.python-version` and the
Dockerfiles). Note the compatibility caveat below before you build.

### Python 3.14 compatibility note (read before building)

`torch` and `transformers` fully support 3.14 (PyTorch added this in the
2.10 release). **`chromadb` is the risky one** — as of writing it has open,
unresolved issues on Python 3.14 caused by:
- `pydantic` v1/v2 conflicts inside chromadb's own dependency tree
- `onnxruntime` (a chromadb dependency) not yet shipping 3.14 wheels on
  every platform
- `hnswlib` failing to compile from source on some systems when no
  prebuilt wheel is available

`requirements.txt` pins the highest versions with the best known chance of
working (`pydantic>=2.12.0`, `chromadb>=1.5.9`). If `pip install -r
requirements.txt` or `docker compose up --build` fails on the `chromadb`
step, you have two options:

1. **Fastest fix**: create a separate virtual environment on Python 3.12
   or 3.13 just for local development, and only use 3.14 for parts that
   don't touch chromadb. This is genuinely simpler than fighting an
   immature dependency chain.
2. **Stay on 3.14.4**: check for a newer `chromadb` release
   (`pip index versions chromadb`) — this ecosystem is moving fast and a
   fix may have landed since this was written.

## Relevance filtering (fixed)

Earlier testing surfaced unrelated articles (e.g. an unrelated entertainment
story) scoring nearly as high as genuinely matching ones, all clustered
around 0.79-0.80 similarity. Root causes, now fixed in this version:

1. **e5 embeddings need asymmetric prefixes.** `intfloat/multilingual-e5-base`
   requires `"query: "` on the claim and `"passage: "` on indexed articles.
   Without them, similarity scores compress into an uninformative band
   regardless of actual relevance. Fixed in `vectorstore.py`.
2. **The NLI hypothesis never included the claim.** The old zero-shot call
   used a generic template ("This text supports the claim.") with no claim
   text inserted, so the model was judging headlines in isolation. Fixed in
   `verdict.py` by using the NLI model directly with
   `premise=article, hypothesis=claim`.

The pipeline now runs: retrieve top 20 candidates → similarity floor →
lexical sanity gate (English only, cheap pre-filter) → NLI entailment/
contradiction check against the actual claim → drop anything neutral →
verdict. The API response includes `candidates_considered` and
`filtered_out` so you can see how much was screened out at each claim.

Tune `SIMILARITY_FLOOR` and `NLI_CONFIDENCE_FLOOR` in `.env` if you find
it's still too permissive or too strict for your test set.

## Photo / video claim checking

Beyond typed claims, `/api/check/media` (and the "Upload photo/video" tab in
the dashboard) accepts an image or video and extracts checkable text from
it before running the same verification pipeline:

- **Images**: OCR runs directly on the file (Tesseract, English + Tamil).
  Good for screenshots of forwarded messages, social posts, news chyrons.
- **Video**: 8 frames are sampled evenly across the clip and each is OCR'd;
  results are merged. This catches on-screen text (captions, subtitles,
  news tickers) but **not spoken audio** — there's no speech-to-text step.
  Adding one (e.g. via Whisper) is a reasonable future extension, but it
  roughly doubles the ML dependency footprint, so it's intentionally left
  out for now rather than bolted on half-tested.

Limits: 25 MB per file. Supported images: JPG/PNG/WEBP/BMP. Supported
video: MP4/MOV/AVI/WEBM.

## Python 3.14 compatibility note

You asked for this to run on Python 3.14.4. Here's the honest state of
that: **it can't, yet** — `chromadb` (this project's vector store) has an
open, unresolved upstream bug on 3.14 caused by its dependency on Pydantic
v1's compatibility shim, which breaks under 3.14
([chroma-core/chroma#5996](https://github.com/chroma-core/chroma/issues/5996),
[#5983](https://github.com/chroma-core/chroma/issues/5983)). This isn't
fixable from inside this app — it needs a patch from chromadb.

What's actually in place:
- The Docker images run **Python 3.12**, which installs and runs cleanly
  (verified: full dependency install + live server + real HTTP requests
  against every endpoint, all passing).
- All application code (`app/`) is written using only 3.14-compatible
  syntax — no deprecated stdlib features, nothing that would break on
  3.14. The moment chromadb ships a fix, switching `FROM python:3.12-slim`
  to `FROM python:3.14-slim` in `Dockerfile` and `Dockerfile.dashboard` is
  the only change needed.
- Check the linked issues periodically; once closed, the switch is safe.

## What was actually verified before delivery

- Every `.py` file compiles (`python -m py_compile`) with no syntax errors.
- `requirements.txt` installs cleanly on Python 3.12 (tested in this
  environment) with pinned versions for reproducibility.
- The full FastAPI app imports and registers all routes correctly.
- A live server was started and every endpoint was hit with real HTTP
  requests: `/health`, `/api/check` (valid text, empty text → 400),
  `/api/check/media` (valid image → 200, unsupported file type → 415).
- The OCR module (`app/services/media.py`) was tested against real
  Tesseract with a synthetic image (successful extraction) and three
  error paths (empty file, corrupt/non-image file, image with no text) —
  all produced the correct user-facing error message.
- Video frame extraction was tested against a real synthetically-generated
  video clip with burned-in text — correctly extracted.
- **Not tested in this environment**: the real embedding model
  (`intfloat/multilingual-e5-base`) and NLI model
  (`mDeBERTa-v3-base-mnli-xnli`) actually downloading and running, because
  this sandbox has no network access to huggingface.co and insufficient
  disk space to install the full `torch` stack. The code that calls them
  was verified by stubbing those two libraries with faithful mocks
  (matching real return types/shapes) and confirming the full request
  pipeline — including the vector query and NLI stance logic — completes
  without errors. Test this specific part on your machine after setup by
  submitting a real claim and checking the response looks sane; if
  something's off there, it's the one area I couldn't fully close the
  loop on here.

## Dependency versions (updated to latest, verified)

`requirements.txt` was bumped to the latest versions of every package as of
this update, including two major-version jumps that could plausibly have
broken things: `chromadb` 0.5.5 → 1.5.9 and `transformers` 4.x → 5.15.1
(`sentence-transformers` 3.0.1 → 6.0.0 too). Rather than assuming a major
bump is safe, this was actually checked:

- Installed all 17 dependencies together in a clean environment — no
  version conflicts.
- Ran chromadb 1.5.9's real API (not stubbed) against this project's exact
  usage: `PersistentClient`, custom `EmbeddingFunction`,
  `get_or_create_collection`, `upsert`, `query` with `query_embeddings` —
  all work as called. Fixed one deprecation warning proactively (chromadb
  1.x will require `EmbeddingFunction` subclasses to define `__init__` in
  a future version).
- Confirmed `transformers` 5.15.1 still exposes `AutoTokenizer` /
  `AutoModelForSequenceClassification` with the same interface this code
  calls, and `sentence_transformers` 6.0.0's `.encode()` still accepts
  this code's positional/keyword usage.
- Ran a full live server against the real installed versions of chromadb,
  torch, transformers, and sentence-transformers (only the actual
  `from_pretrained()` network call to Hugging Face was short-circuited,
  since this environment can't reach it) — every endpoint responded
  correctly.
- Re-tested the OCR pipeline against the latest Pillow/pytesseract/opencv
  versions with a real image — still extracts text correctly.

If you bump versions further yourself later, re-run this kind of check
rather than assuming `pip install --upgrade` is safe — chromadb in
particular has shipped breaking changes across major versions before.

## Known limitations to address before production

1. **Tamil outlets without RSS** (Daily Thanthi, Polimer News) use a generic
   homepage-scraper fallback in `ingest.py`. Their markup will change over
   time — inspect and tune the selector per outlet rather than relying on
   the generic one long-term.
2. **NLI runs synchronously on CPU by default.** Fine for demos; for real
   traffic, move `verdict.py`'s NLI calls to a GPU-backed inference server
   or batch them.
3. **`CONSENSUS_THRESHOLD`** (default 2) controls how many independent
   whitelisted outlets must corroborate a claim before it's marked
   "Verified Real." Tune this in `.env`.
4. Consider adding IndicTrans2 (Tamil→English) ahead of NLI if you find the
   multilingual model's cross-lingual stance detection unreliable on your
   test set — pure multilingual embeddings sometimes aren't enough.
