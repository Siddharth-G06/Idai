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
│                        YOUR LAPTOP (once)                       │
│                                                                 │
│   PDF Manifestos  →  manifesto_parser.py  →  promises.json     │
│   (DMK 2021,           pytesseract OCR         Structured      │
│    ADMK 2016)          + Llama 3 NLP           categorisation  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ git push
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS (every 6 hrs)                  │
│                                                                 │
│   news_fetcher.py  →  matcher.py  →  scorer.py                 │
│   RSS + NewsAPI       SBERT + FAISS    scores.json             │
│   Live articles       cosine sim       fulfillment %           │
│                       LLM Verify                               │
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
│   /keepalive script      │    │   Dead-link fallbacks          │
└──────────────────────────┘    └────────────────────────────────┘
```

---

## Promise Fulfillment Logic

### How a promise is scored

1. **Extraction**: Raw text is pulled from scanned PDF manifestos using robust OCR passes.
2. **Translation**: Tamil promises are mapped to English vectors via `MarianMT`.
3. **Embedding**: Promises and live news articles are embedded using `Sentence-BERT` (multilingual).
4. **Vector Search**: `FAISS` rapidly queries the index to find semantic matches despite vocabulary differences.
5. **Verification**: A Large Language Model (Llama 3 via Groq) validates the match context to confidently classify its status.

### Governance periods used for date-aware scoring

A promise fulfilled during the opposing party's tenure is **not counted** in the promising party's primary score. To ensure fairness, it is recorded as a secondary "Fulfilled by other" state — granting transparency to the voting public.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| PDF Parsing | pdfplumber + pytesseract | Extract text from difficult Tamil manifestos |
| Semantic Matching | paraphrase-multilingual-MiniLM | Multilingual Tamil+English matching |
| Vector Search | FAISS | Fast nearest-neighbour lookup |
| Verification NLP | Llama 3 / Groq API | Zero-shot evaluation of promise status |
| News Ingestion | NewsAPI + RSS feeds | Automated scraping of real-world impact |
| Scheduling | GitHub Actions CRON | Auto-refresh every 6 hours (`[skip vercel]`) |
| Backend API | FastAPI + keepalive.py | Serve pre-computed data continuously |
| Frontend | React + Vite + TailwindCSS | Mobile-first dynamic dashboard |
| UI Resilience | TanStack Query | Intelligent refetching & local caching |
| Hosting | Vercel (Front) / Render (API) | Cloud infrastructure |

---

## Project Structure

```
idai/
├── backend/
│   ├── manifesto_parser.py     # PDF → structured promises (run once locally)
│   ├── news_fetcher.py         # Live news ingestion routines
│   ├── matcher.py              # Semantic matching via SBERT + FAISS
│   ├── scorer.py               # Algorithmic date-aware fulfillment scoring
│   ├── keepalive.py            # Mitigates Render free-tier cold-starts
│   ├── main.py                 # FastAPI routing
│   └── data/                   # Pre-computed JSON (auto-updated)
│
├── frontend/
│   └── src/
│       ├── pages/              # Compare, PartyPage, Home, About
│       ├── components/         # HealthBanner, PromiseCard, ScoreRings
│       ├── hooks/              # API data fetching logic
│       └── i18n/               # Persistent Tamil/English Context
│
└── .github/
    └── workflows/
        └── update_pipeline.yml # CRON job — runs every 6 hours
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

# Run full pipeline
python run_pipeline.py

# Start API server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Point to local API
echo "VITE_API_URL=http://localhost:8000" > .env.development

npm run dev
# Opens at http://localhost:5173
```

---

## Known Limitations

| Limitation | Impact | Status |
|------------|--------|--------|
| Algorithmic Matching | Semantic matches indicate related coverage, not absolute completion. | By design — voters interpret. |
| Link Rot | Historic news URLs drop dead over time. | Mitigated via smart Google News fallbacks. |
| Render Cold Starts | 30s delays after server inactivity. | Mitigated via `keepalive.py` and UI Banners. |

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

*IDAI · இடை · 2016–2026*
