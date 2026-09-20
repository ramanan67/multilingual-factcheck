# Tamil & Multilingual News Truth Checker
### *செய்தி உண்மை கண்டறியும் தளம்*

> **"Verify the news. See the evidence. Know why."**

A production-oriented, evidence-based **Multilingual Fake News Detection and News Verification Web Application**. The system cross-references news claims, headlines, full articles, and URLs across major English, National, and Tamil Nadu news organizations and official government portals.

---

## 🌟 Key Highlights & Core Principles

1. **Evidence-First Epistemic Rule**:
   $$\text{Absence of an article} \neq \text{Proof that a claim is false}$$
   The application never marks news as FAKE simply because another website did not publish it. It classifies news as `FAKE / FALSE` only when positive contradictory evidence or official debunks are found. If evidence is scarce, it safely concludes `UNVERIFIED`.

2. **Multilingual English & தமிழ் Native Support**:
   - Automatic script detection for English, Tamil (Unicode block `U+0B80`-`U+0BFF`), and mixed claims.
   - Cross-lingual search query generation expanding Tamil to English and English to Tamil.
   - Agglutinative morphology matching and synonym expansion for Tamil and English news terms.

3. **Anti-Syndication & Source Independence**:
   - Detects wire agency syndication (ANI, PTI, IANS, UNI, Reuters) and duplicate press releases.
   - Transparently distinguishes total articles found vs. independent reports vs. syndicated copies to avoid artificial confirmation bias.

4. **Multi-Tier News Source Coverage**:
   - **National & International**: The Hindu, Times of India, BBC, The Indian Express, Hindustan Times, NDTV, News18, ANI, PTI.
   - **Tamil Nadu Media**: Puthiya Thalaimurai, Polimer News, Sun News, Dinamalar, Dinamani, Daily Thanthi, Vikatan, Nakkheeran, Tamil Samayam, OneIndia Tamil, News Tamil 24x7, BBC Tamil.
   - **Primary Government Portals**: Tamil Nadu Government DIPR, PIB India Fact Check, IMD Chennai Regional Met Centre.

5. **No Hallucinations**:
   Every displayed source, article headline, publication date, and snippet is strictly retrieved from live feeds and verified news web channels.

---

## 🎯 Verdict Types

| Verdict | Badge | Description |
| :--- | :--- | :--- |
| **TRUE / VERIFIED** | 🟢 | Corroborated by multiple independent news organizations and/or primary government announcements. |
| **FAKE / FALSE** | 🔴 | Positively contradicted or debunked by reliable reporting or official authorities. |
| **MISLEADING** | 🟡 | The core event occurred, but the context, date (recycled old news), location, or numbers are distorted. |
| **UNVERIFIED** | ⚪ | Insufficient independent evidence found. The system advises caution instead of guessing. |

---

## 🏗️ Architecture & Workflow

```
 USER
  │
  ▼
Enter Headline / Claim / URL
  │
  ▼
Language Detection (English / தமிழ் / Mixed)
  │
  ▼
Claim & Entity Extraction (Location, Org, Person, Date, Numbers, Action)
  │
  ▼
Multilingual Query Generation (Tamil + English phrase expansions)
  │
  ├───────────────────────────────────┐
  ▼                                   ▼
Tamil Nadu Sources               National & International Sources
(Puthiya Thalaimurai, Dinamalar, (The Hindu, TOI, BBC, Indian Express,
 Dinamani, Daily Thanthi, etc.)   NDTV, Hindustan Times, etc.)
  │                                   │
  └─────────────────┬─────────────────┘
                    ▼
           Primary Source Verification (TN DIPR, PIB, IMD)
                    │
                    ▼
           Article Parsing & Metadata Normalization
                    │
                    ▼
           Multi-Factor Semantic Matching (Headline, Claim, Entity, Date)
                    │
                    ▼
           Duplicate & Agency Wire Syndication Detection (ANI, PTI, IANS)
                    │
                    ▼
           Evidence Stance & Discrepancy Analyzer (Supports / Contradicts / Outdated)
                    │
                    ▼
           Verdict Engine & Confidence Calculation
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Interactive Web Dashboard                       │
│  - Verdict Badge (🟢 / 🔴 / 🟡 / ⚪) & Confidence Meter               │
│  - "Why?" Plain-Language Explanation                                   │
│  - Source Comparison Matrix Table                                      │
│  - Independence Stats (Total vs Independent vs Syndicated)             │
│  - Verified Article Cards with "Read Original" Links                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
news-de/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app, CORS, static frontend mount, lifespan
│   │   ├── config.py                   # Configuration, weights, thresholds, settings
│   │   │
│   │   ├── api/
│   │   │   ├── routes.py               # Endpoints: /check, /check-url, /sources, /history, /translate
│   │   │   └── schemas.py              # Pydantic request & response models
│   │   │
│   │   ├── services/
│   │   │   ├── language_detector.py    # English, Tamil, and Mixed script detector
│   │   │   ├── claim_extractor.py      # Entity, location, date, and assertion extractor
│   │   │   ├── query_generator.py      # Multilingual search query expansion
│   │   │   ├── news_search.py          # Parallel multi-source search orchestrator
│   │   │   ├── article_parser.py       # HTML parsing, JSON-LD, OpenGraph, date normalizer
│   │   │   ├── article_matcher.py      # Multi-factor similarity scoring & outdated news check
│   │   │   ├── duplicate_detector.py   # ANI/PTI wire detection & deduplication
│   │   │   ├── evidence_analyzer.py    # Stance classification (SUPPORTS/CONTRADICTS)
│   │   │   ├── source_reliability.py   # Heuristic reliability tiers & multipliers
│   │   │   └── verdict_engine.py       # Verdict logic & explanation generator
│   │   │
│   │   ├── sources/
│   │   │   ├── base_source.py          # BaseSourceAdapter abstract base class
│   │   │   ├── source_registry.py      # Central source manager & dynamic registrar
│   │   │   ├── the_hindu.py, times_of_india.py, bbc.py, indian_express.py, ndtv.py...
│   │   │   ├── puthiya_thalaimurai.py, polimer.py, dinamalar.py, dinamani.py, vikatan.py...
│   │   │   └── primary_sources.py      # TN Gov DIPR, PIB India, IMD Weather
│   │   │
│   │   ├── models/
│   │   │   └── models.py               # Internal Pydantic & database schemas
│   │   │
│   │   └── utils/
│   │       ├── text_cleaner.py         # Tamil/English text normalizer & HTML stripper
│   │       ├── url_validator.py        # SSRF security protection & URL normalizer
│   │       ├── database.py             # SQLite persistence for verifications & history
│   │       └── logger.py               # Structured logger
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html                      # Modern UI dashboard with dark/light mode
│   ├── style.css                       # Responsive CSS, accessible verdict badges
│   └── app.js                          # Stepper animations, result rendering, history modal
│
├── tests/
│   ├── test_language_detector.py
│   ├── test_claim_extractor.py
│   ├── test_query_generator.py
│   ├── test_matcher.py
│   ├── test_duplicate_detector.py
│   ├── test_verdict_engine.py
│   └── test_api.py
│
├── truth_checker.db                    # SQLite verification history database
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python 3.10, 3.11, 3.12, or 3.14+**
- Standard web browser (Chrome, Firefox, Safari, Edge)

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` if you wish to customize ports or limits:
```bash
cp backend/.env.example .env
```

### 4. Start the Application
Run the backend server using Uvicorn:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access the Web Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

API interactive documentation is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Running the Automated Test Suite

The project includes an extensive test suite verifying all 4 verdict conditions, multilingual script parsing, entity extraction, duplicate wire detection, and REST endpoints:

```bash
python -m pytest tests/ -v
```

Output:
```text
tests/test_api.py::test_health_endpoint PASSED                           [  4%]
tests/test_api.py::test_list_sources_endpoint PASSED                     [  9%]
tests/test_api.py::test_check_news_endpoint_validation PASSED            [ 14%]
tests/test_api.py::test_toggle_source_endpoint PASSED                    [ 19%]
tests/test_api.py::test_translate_endpoint PASSED                        [ 23%]
tests/test_claim_extractor.py::test_extract_english_claim_entities PASSED [ 28%]
tests/test_claim_extractor.py::test_extract_tamil_claim_entities PASSED  [ 33%]
tests/test_claim_extractor.py::test_extract_negation_debunk_claim PASSED [ 38%]
tests/test_duplicate_detector.py::test_detect_wire_agency_syndication PASSED [ 42%]
tests/test_language_detector.py::test_detect_english_headline PASSED     [ 47%]
tests/test_language_detector.py::test_detect_tamil_headline PASSED       [ 52%]
tests/test_language_detector.py::test_detect_mixed_headline PASSED       [ 57%]
tests/test_language_detector.py::test_detect_empty_or_numbers PASSED     [ 61%]
tests/test_matcher.py::test_matching_high_relevance_article PASSED       [ 66%]
tests/test_matcher.py::test_matching_outdated_article PASSED             [ 71%]
tests/test_query_generator.py::test_query_generation_english PASSED      [ 76%]
tests/test_query_generator.py::test_query_generation_tamil PASSED        [ 80%]
tests/test_verdict_engine.py::test_verdict_true_multiple_sources PASSED  [ 85%]
tests/test_verdict_engine.py::test_verdict_false_contradicted_by_official_source PASSED [ 90%]
tests/test_verdict_engine.py::test_verdict_misleading_outdated_news PASSED [ 95%]
tests/test_verdict_engine.py::test_verdict_unverified_absence_of_evidence PASSED [100%]

============================= 21 passed in 0.50s ==============================
```

---

## 🔌 Adding a New News Source

The application utilizes a modular **Source Adapter Pattern**. To register a new news website (e.g. `Maalai Malar`):

1. Create a new file `backend/app/sources/maalai_malar.py`:
```python
from backend.app.sources.base_source import BaseSourceAdapter

class MaalaiMalarAdapter(BaseSourceAdapter):
    source_id = "maalai_malar"
    name = "Maalai Malar"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "maalaimalar.com"
    rss_urls = [
        "https://www.maalaimalar.com/rss/tamilnadu",
    ]
```

2. Register the adapter in `backend/app/sources/source_registry.py`:
```python
from backend.app.sources.maalai_malar import MaalaiMalarAdapter

# Add MaalaiMalarAdapter to default_classes list in _register_default_adapters()
```

Or dynamically add custom sources via the REST API or `source_registry.add_custom_source()`.

---

## 📡 REST API Reference

### 1. `POST /api/check`
Verifies a news claim, headline, or text passage.
```json
{
  "text": "Chennai schools closed tomorrow because of heavy rain.",
  "url": null,
  "language": "auto"
}
```
**Response:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "verdict": "TRUE",
  "verdict_display": "🟢 VERIFIED TRUE",
  "confidence": 0.92,
  "confidence_display": "92.0%",
  "language": "en",
  "claim": "Chennai schools closed tomorrow because of heavy rain.",
  "reason": "The claim is supported by 3 independent news organizations including The Hindu, Times of India, Puthiya Thalaimurai.",
  "detailed_explanation": "### Why is this verdict reached?...",
  "supporting_sources": ["The Hindu", "Times of India", "Puthiya Thalaimurai"],
  "contradicting_sources": [],
  "primary_sources": ["Tamil Nadu Government (DIPR)"],
  "articles": [...],
  "stats": {
    "total_articles": 8,
    "independent_reports": 3,
    "syndicated_reports": 5,
    "primary_sources": 1
  }
}
```

### 2. `POST /api/check-url`
Fetches an article URL with SSRF protection, extracts the content, and executes fact-checking.
```json
{
  "url": "https://www.thehindu.com/news/cities/chennai/article.ece",
  "language": "auto"
}
```

### 3. `GET /api/sources`
Lists all registered source adapters with metadata.

### 4. `POST /api/sources/{source_id}/toggle`
Enables or disables a specific source dynamically.

### 5. `GET /api/history`
Returns past verification records stored in SQLite.

### 6. `DELETE /api/history/{id}`
Deletes a specific fact check record.

---

## 🛡️ Security & SSRF Protection

- **SSRF Prevention**: All user-submitted URLs are validated before outbound requests:
  - Private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1`) and `localhost` are strictly rejected.
  - DNS resolution is performed to prevent DNS rebinding attacks to internal infrastructure.
  - Only `http://` and `https://` protocols are allowed.
- **Copyright Integrity**: Only short snippets and metadata are retained with permanent links to original publications.

---

## ⚖️ Limitations & Ethical Considerations

- **Heuristic Confidence**: The confidence meter is an evidence-based mathematical estimate, not an infallible guarantee.
- **Rapidly Developing News**: For breaking news within minutes of occurrence, evidence may temporarily be `UNVERIFIED` until major news agencies report on it.
- **Fairness**: Source reliability tiers represent historical editorial track records and never override verifiable primary evidence.
