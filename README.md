# IDAI — இடை

> **Closing the gap between promises and proof.**

A real-time, AI-powered political accountability dashboard tracking election promises made by Tamil Nadu's two major parties — DMK and ADMK — from 2016 through 2026.

Built as an independent, non-partisan civic tool. No affiliations. No agenda. Just evidence.

---

## What is IDAI?

**IDAI** (இடை) means *"the space between"* in Tamil.

It represents the gap that exists between what politicians promise and what they actually deliver. This platform makes that gap visible — promise by promise, category by category, year by year.

| Party | Manifesto Covered | Governance Period |
|-------|-------------------|-------------------|
| ADMK  | 2016 State Election | May 2016 – May 2021 |
| DMK   | 2021 State Election | May 2021 – May 2026 |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL (run once)                         │
│                                                                 │
│   PDF Manifestos  →  manifesto_parser.py  →  promises.json     │
│   (DMK 2021,           pytesseract OCR         Structured      │
│    ADMK 2016)          + Groq/Llama 3          categorisation  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ git push
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS (every 6 hrs)                  │
│                                                                 │
│   news_fetcher.py  →  matcher.py  →  scorer.py                 │
│   RSS + NewsAPI       SBERT + FAISS    scores.json             │
│   Live articles       cosine sim       fulfillment %           │
│                       Groq/Llama3 verify                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ auto-commit data/*.json
                                 ▼
┌──────────────────────────┐    ┌────────────────────────────────┐
│   RENDER (backend)       │    │   VERCEL (frontend)            │
│                          │    │                                │
│   FastAPI                │◄───│   React + Vite + Tailwind      │
│   Serves JSON via API    │    │   Mobile-first dashboard       │
│   /api/promises          │    │   Tamil / English toggle       │
│   /api/score             │    │   Live score cards             │
│   /health (keepalive)    │    │   Smart dead-link fallbacks    │
└──────────────────────────┘    └────────────────────────────────┘
```

---

## Promise Fulfillment Logic

### How a promise is scored

1. **Extraction**: Raw text is pulled from scanned PDF manifestos using OCR (pytesseract + pdfplumber).
2. **Classification**: Groq's Llama 3 categorises each promise (Healthcare, Education, Infrastructure, etc.).
3. **News Matching**: SBERT embeds both promises and scraped news articles; FAISS finds the closest semantic match.
4. **Verification**: A second Llama 3 pass confirms whether the matched article genuinely represents fulfillment.
5. **Date-Aware Scoring**: A promise fulfilled under the opposing party's tenure is recorded separately as "Fulfilled by Other" — not credited to the promising party.

### Governance periods used for scoring

```
ADMK rule:  May 2016  →  May 2021
DMK rule:   May 2021  →  May 2026
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| PDF Parsing | pdfplumber + pytesseract | Extract text from scanned Tamil manifestos |
| NLP & Classification | Llama 3 via Groq API | Zero-shot promise categorisation & verification |
| Semantic Matching | paraphrase-multilingual-MiniLM (SBERT) | Multilingual Tamil+English embedding |
| Vector Search | FAISS | Fast nearest-neighbour lookup |
| News Ingestion | NewsAPI + RSS feeds | Scraping real-world government actions |
| Scheduling | GitHub Actions CRON | Pipeline runs every 6 hours |
| Backend API | FastAPI | Serves pre-computed JSON data |
| Frontend | React + Vite + TailwindCSS | Mobile-first bilingual dashboard |
| Data Fetching | TanStack Query | Intelligent caching & background refetch |
| Cold-Start Resilience | keepalive.py + HealthBanner | Prevents and handles Render free-tier sleep |
| Hosting | Vercel (frontend) / Render (backend) | Cloud deployment |

---

## Project Structure

```
idai/
├── backend/
│   ├── manifesto_parser.py     # PDF → structured promises (run once locally)
│   ├── news_fetcher.py         # NewsAPI + RSS ingestion
│   ├── matcher.py              # SBERT + FAISS semantic matching
│   ├── scorer.py               # Date-aware fulfillment scoring
│   ├── run_pipeline.py         # Orchestrator for full pipeline run
│   ├── keepalive.py            # Pings /health to prevent cold-starts
│   ├── main.py                 # FastAPI — all API endpoints
│   ├── requirements.txt        # Full ML pipeline dependencies
│   ├── requirements.api.txt    # Lightweight API-only dependencies (for Render)
│   └── data/                   # Pre-computed JSON (auto-updated by GitHub Actions)
│
├── frontend/
│   └── src/
│       ├── pages/              # Home, PartyPage, Compare, About
│       ├── components/         # PromiseCard, ScoreRing, HealthBanner, Navbar
│       ├── hooks/              # usePromises, useScore, useSummary
│       ├── api/client.js       # API calls + wakeup detection
│       └── i18n/               # Tamil / English translations
│
└── .github/
    └── workflows/
        └── update_pipeline.yml # CRON — runs every 6 hours, skips Vercel rebuild
```

---

## Local Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Add your API keys
echo "NEWSAPI_KEY=your_key_here" > .env
echo "GROQ_API_KEY=your_groq_key" >> .env

# Run full pipeline (fetch news → match → score)
python run_pipeline.py

# Start API server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

echo "VITE_API_URL=http://localhost:8000" > .env.development

npm run dev
# Opens at http://localhost:5173
```

---

## Known Limitations

| Limitation | Impact |
|------------|--------|
| Algorithmic matching is approximate | A match means *related news exists*, not that a promise is 100% complete |
| Dead news links | Historic article URLs expire — mitigated by Google News fallback search |
| Render free tier sleep | 30–60s cold start delay — mitigated by `keepalive.py` and `HealthBanner` in UI |
| NewsAPI free tier | 100 results/query, English-heavy — supplemented by Tamil RSS feeds |

---

## Disclaimer

> This platform is **independent and non-partisan**. It is not affiliated with, funded by, or endorsed by the DMK, ADMK, or any political party, government body, or media organisation.
>
> All data is sourced from **publicly available** election manifestos and published news articles. Sources include The Hindu, NDTV, Times of India, PRS India, and NewsAPI.
>
> Promise matching is performed using **AI-assisted semantic search** and is intended for **informational purposes only**. A matched article indicates that related news coverage exists — it does not constitute a legal or factual verdict on whether a promise was fulfilled.
>
> IDAI presents evidence. **Voters decide.**

---

