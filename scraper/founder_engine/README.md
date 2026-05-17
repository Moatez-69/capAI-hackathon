# Founder Intelligence Aggregation Engine

Collects, normalizes, and exports public founder data as structured JSON.

**Input:** founder name + LinkedIn URL  
**Output:** enriched JSON profile in `/output`

---

## Setup

```bash
cd founder_engine

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Set optional GitHub token to avoid rate limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

---

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

---

## API

### POST /api/v1/collect

```json
{
  "name": "John Doe",
  "linkedin_url": "https://linkedin.com/in/johndoe"
}
```

**Response:** full `FounderProfile` JSON

### GET /api/v1/health

Returns `{"status": "ok"}`

---

## Pipeline

1. **LinkedIn collector** — Playwright scrapes public profile (name, headline, location, about, experience, education, skills, certifications)
2. **Identity resolution** — extracts GitHub username, personal site, Twitter handle from LinkedIn data
3. **GitHub collector** — GitHub REST API fetches profile, repos, orgs, top languages
4. **Web presence collector** — requests + BeautifulSoup scrapes personal site for title, meta, technologies, social links

Missing data never crashes pipeline. All fields are optional.

---

## Output

JSON files saved to `output/<name>_<timestamp>.json`.

```json
{
  "name": "...",
  "linkedin": { "url": "...", "headline": "...", ... },
  "github": { "username": "...", "repositories": [...], ... },
  "web_presence": { "personal_website": "...", "technologies": [...], ... },
  "metadata": { "collected_at": "...", "sources": [...], "missing_fields": [...] }
}
```

---

## Notes

- LinkedIn scraping targets public profiles only. No auth bypass.
- GitHub token optional but recommended (60 req/hr unauthenticated vs 5000 authenticated).
- `output/` directory is git-ignored — add `.gitignore` if needed.
