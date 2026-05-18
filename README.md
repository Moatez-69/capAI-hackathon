# capAI — Founder Intelligence Platform

AI-powered platform that aggregates public founder data, enriches it, and predicts startup success.

---

## Architecture

```
capAI/
├── server/scraper/     # Founder data aggregation engine
├── feature-filling/    # LLM-based feature normalization pipeline
├── model/              # ML pipeline — startup success prediction
└── client/             # Frontend
```

---

## Modules

### 1. Founder Intelligence Scraper (`server/scraper/`)

Collects and normalizes public founder profiles from multiple sources.

**Input:** founder name + optional LinkedIn URL  
**Output:** structured JSON profile

**Data sources:**
- LinkedIn (via ReverseContact API)
- GitHub (REST API — profile, repos, languages, README, activity)
- Personal website (BeautifulSoup)
- Product Hunt
- DEV.to

**Stack:** Python 3.12 · FastAPI · aiohttp · asyncio · BeautifulSoup · Pydantic v2

```bash
cd server/scraper/founder_engine
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `POST /api/v1/collect` with `{ "name": "John Doe", "linkedin_url": "..." }`

---

### 2. Feature Filling Pipeline (`feature-filling/`)

LLM-based pipeline that normalizes and fills missing fields in founder profiles using rule-based tiers and language model inference.

---

### 3. Startup Success ML Model (`model/`)

Predicts whether a startup will be acquired or IPO using Crunchbase data.

**Model:** LightGBM · ROC-AUC: **0.839** · Recall: **0.795**  
**Features:** 16 engineered features from funding, investors, founders, education, milestones, and location data  
**Dataset:** 196,553 companies · 17.7:1 class imbalance

```bash
cd model/
python3 -m venv venv && source venv/bin/activate
pip install pandas scikit-learn lightgbm imbalanced-learn
python3 startup_success_pipeline.py
```

See [`model/README.md`](model/README.md) for full details.

---

### 4. Frontend (`client/`)

Next.js web interface for the platform.

---

## Team

Built at a hackathon by [Moatez-69](https://github.com/Moatez-69) and teammates.
