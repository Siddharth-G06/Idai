"""
main.py — Vaakazhipeer API
Pure data-serving FastAPI application.
Reads pre-computed JSON files from /data/ at startup — no ML, no writes.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# ENV & PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")
PORT = int(os.environ.get("PORT", 8000))

# ─────────────────────────────────────────────
# LOAD DATA AT MODULE LEVEL (once, on startup)
# ─────────────────────────────────────────────

def safe_load_json(path: Path, fallback):
    try:
        if not path.exists():
            print(f"WARNING: {path} not found, using fallback")
            return fallback
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"WARNING: {path} is empty")
                return fallback
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is malformed JSON — {e}")
        return fallback
    except Exception as e:
        print(f"ERROR reading {path} — {e}")
        return fallback

def _load_all_promises() -> dict[str, list[dict]]:
    """
    Scan data/ for every *_promises.json and return a dict keyed by stem.
    e.g.  {"aiadmk_2016": [...], "dmk_2021": [...], ...}
    Auto-picks up future manifesto files with zero code changes.
    """
    result: dict[str, list[dict]] = {}
    if not DATA_DIR.exists():
        print(f"Warning: DATA_DIR {DATA_DIR} does not exist.")
        return result
    for p in sorted(DATA_DIR.glob("*_promises.json")):
        stem = p.stem.replace("_promises", "")
        data = safe_load_json(p, [])
        # Check for new {metadata, promises} structure
        if isinstance(data, dict) and "promises" in data:
            result[stem] = data["promises"]
        else:
            result[stem] = data
    return result

# Named references kept for backward compat with the spec
_promises_by_stem = _load_all_promises()

# Convenience aliases (spec names)
dmk_promises     = _promises_by_stem.get("dmk_2021",   [])
aiadmk_promises  = _promises_by_stem.get("aiadmk_2016", [])

scores: dict = safe_load_json(DATA_DIR / "scores.json", {})

# Flat index: id → promise object  (across ALL stems)
_promise_index: dict[str, dict] = {}
for _promises in _promises_by_stem.values():
    for _p in _promises:
        pid = _p.get("id")
        if pid:
            _promise_index[pid] = _p

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Vaakazhipeer API",
    description="Tamil Nadu Political Promise Accountability Dashboard",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


# ─────────────────────────────────────────────
# GLOBAL EXCEPTION HANDLER
# ─────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    print(f"BASE_DIR : {BASE_DIR}")
    print(f"DATA_DIR : {DATA_DIR}")
    print(f"DATA_DIR exists: {DATA_DIR.exists()}")
    if DATA_DIR.exists():
        files = list(DATA_DIR.iterdir())
        print(f"Files found: {[f.name for f in files]}")
    else:
        print("ERROR: data directory not found!")
    
    total = sum(len(v) for v in _promises_by_stem.values())
    print(f"Scores loaded: {bool(scores)}")
    print(f"Promise files loaded: {list(_promises_by_stem.keys())}")
    print(f"Vaakazhipeer API — ready  |  promises={total}")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _parse_stem(stem: str) -> tuple[str, int | None]:
    """
    'aiadmk_2016' → ('AIADMK', 2016)
    'dmk_2021'    → ('DMK',    2021)
    """
    parts = stem.split("_")
    party = parts[0].upper()
    try:
        year = int(parts[1]) if len(parts) > 1 else None
    except ValueError:
        year = None
    return party, year


def _scores_key(stem: str) -> str:
    """Map a file stem to its key inside scores.json.

    scores.json uses keys like 'AIADMK 2016', 'DMK 2021', etc.
    """
    party, year = _parse_stem(stem)
    return f"{party} {year}" if year else party


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/")
@app.head("/")
def read_root():
    """Default root endpoint for Render/Cloudflare health checks."""
    return {"status": "ok", "app": "Vaakazhipeer API"}

@app.get("/health")
def health():
    """Liveness / readiness check + data freshness."""
    metadata_path = DATA_DIR / "metadata.json"
    score_path = DATA_DIR / "scores.json"
    age_hours = 0
    data_stale = False

    # Try metadata.json first (source of truth from pipeline)
    if metadata_path.exists():
        meta = safe_load_json(metadata_path, {})
        last_updated_str = meta.get("last_updated")
        if last_updated_str:
            try:
                # ISO format: 2026-04-10T09:34:43Z
                last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
                age_hours = round((datetime.now(timezone.utc) - last_updated).total_seconds() / 3600, 1)
            except Exception:
                pass

    # Fallback to file mtime if metadata failed or missing
    if age_hours == 0 and score_path.exists():
        mtime = score_path.stat().st_mtime
        age_hours = round((time.time() - mtime) / 3600, 1)

    if age_hours > 25:
        data_stale = True

    return {
        "status": "ok",
        "data_stale": data_stale,
        "last_updated_hours": age_hours,
        "uptime": "active"
    }

@app.get("/api/status")
def get_service_status():
    """Returns detailed loading status for all data files."""
    status = {}
    
    # Check promise files
    for pfile in sorted(DATA_DIR.glob("*_promises.json")):
        stem = pfile.stem.replace("_promises", "")
        mtime = datetime.fromtimestamp(pfile.stat().st_mtime, tz=timezone.utc).isoformat()
        
        plist = _promises_by_stem.get(stem, [])
        status[stem] = {
            "loaded": len(plist) > 0,
            "count": len(plist),
            "last_modified": mtime
        }
    
    # Check scores
    score_path = DATA_DIR / "scores.json"
    if score_path.exists():
        status["scores"] = {
            "loaded": bool(scores),
            "last_modified": datetime.fromtimestamp(score_path.stat().st_mtime, tz=timezone.utc).isoformat()
        }
        
    # Check news
    news_path = DATA_DIR / "news_articles.json"
    if news_path.exists():
        news_data = safe_load_json(news_path, [])
        status["news"] = {
            "loaded": len(news_data) > 0,
            "count": len(news_data),
            "last_modified": datetime.fromtimestamp(news_path.stat().st_mtime, tz=timezone.utc).isoformat()
        }
        
    return status


@app.get("/api/parties")
def get_parties():
    """
    Dynamically built from whatever *_promises.json files exist in /data/.
    Returns: {"parties": [{"name": "DMK", "years": [2016, 2021]}, ...]}
    """
    party_years: dict[str, list[int]] = defaultdict(list)
    for stem in _promises_by_stem:
        party, year = _parse_stem(stem)
        if year:
            party_years[party].append(year)

    parties = [
        {"name": party, "years": sorted(years)}
        for party, years in sorted(party_years.items())
    ]
    return {"parties": parties}


@app.get("/api/score")
def get_score():
    """Full scores.json content."""
    return scores


@app.get("/api/promises")
def get_promises(
    party: str | None = None,
    year: int | None = None,
    category: str | None = None,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    """
    Filtered and paginated list of promises.
    """
    results: list[dict] = []
    limit = min(max(1, limit), 50) # Cap at 50

    for stem, promises in _promises_by_stem.items():
        stem_party, stem_year = _parse_stem(stem)

        if party and stem_party.lower() != party.strip().lower():
            continue
        if year and stem_year != year:
            continue

        for p in promises:
            if category and p.get("category", "").lower() != category.strip().lower():
                continue
            if status and p.get("status", "").lower() != status.strip().lower():
                continue
            results.append(p)

    total = len(results)
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    start = (page - 1) * limit
    end   = start + limit
    
    paginated_data = results[start:end]

    return {
        "data": paginated_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filters_applied": {
            "party": party,
            "year": year,
            "category": category,
            "status": status
        }
    }


@app.get("/api/promises/{promise_id}")
def get_promise_by_id(promise_id: str):
    """Single promise object by its id field. Returns 404 if not found."""
    promise = _promise_index.get(promise_id)
    if not promise:
        raise HTTPException(status_code=404, detail=f"Promise '{promise_id}' not found.")
    return promise


@app.get("/api/summary")
def get_summary():
    """
    Per-party summary derived from scores.json.
    Returns score, fulfilled count, total count, and top category.
    """
    summary: dict[str, dict] = {}

    for key, data in scores.items():
        # key is like 'AIADMK 2016' or 'DMK 2021'
        parts = key.split()
        party = parts[0]           # 'DMK' or 'AIADMK'
        year  = parts[1] if len(parts) > 1 else ""

        categories: dict = data.get("categories", {})
        top_category = ""
        if categories:
            top_category = max(categories, key=lambda c: categories[c].get("score", 0))

        entry_key = f"{party} {year}".strip()
        summary[entry_key] = {
            "party":        party,
            "year":         int(year) if year.isdigit() else None,
            "context":      data.get("context", ""),
            "period":       data.get("period", ""),
            "score":        data.get("score", 0.0),
            "fulfilled":    data.get("fulfilled", 0),
            "total":        data.get("total", 0),
            "top_category": top_category,
            "categories":   categories,
        }

    return summary


# ─────────────────────────────────────────────
# DEV ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
