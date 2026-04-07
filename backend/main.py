"""
main.py — Vaakazhipeer API
Pure data-serving FastAPI application.
Reads pre-computed JSON files from /data/ at startup — no ML, no writes.
"""

from __future__ import annotations

import json
import os
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
load_dotenv(Path(__file__).parent / ".env")

DATA_DIR = Path("/data")
PORT = int(os.environ.get("PORT", 8000))

# ─────────────────────────────────────────────
# LOAD DATA AT MODULE LEVEL (once, on startup)
# ─────────────────────────────────────────────

def _load_json(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load JSON from {path}: {e}")
        return {}

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
        result[stem] = _load_json(p)
    return result

# Named references kept for backward compat with the spec
_promises_by_stem = _load_all_promises()

# Convenience aliases (spec names)
dmk_promises   = _promises_by_stem.get("dmk_2021",   [])
admk_promises  = _promises_by_stem.get("aiadmk_2016", [])

scores: dict = _load_json(DATA_DIR / "scores.json")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    total = sum(len(v) for v in _promises_by_stem.values())
    print(f"Vaakazhipeer API — ready  |  stems={list(_promises_by_stem.keys())}  |  promises={total}")


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

@app.get("/health")
def health():
    """Liveness / readiness check."""
    return {"status": "ok"}


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
):
    """
    Filtered list of promises.
    Query params (all optional): party, year, category, status
    Example: /api/promises?party=DMK&category=healthcare&status=fulfilled
    """
    results: list[dict] = []

    for stem, promises in _promises_by_stem.items():
        stem_party, stem_year = _parse_stem(stem)

        # Party filter (case-insensitive)
        if party and stem_party.lower() != party.strip().lower():
            continue
        # Year filter
        if year and stem_year != year:
            continue

        for p in promises:
            # Category filter (case-insensitive)
            if category and p.get("category", "").lower() != category.strip().lower():
                continue
            # Status filter (case-insensitive)
            if status and p.get("status", "").lower() != status.strip().lower():
                continue
            results.append(p)

    return {"count": len(results), "promises": results}


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
