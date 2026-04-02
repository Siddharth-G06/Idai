"""
scorer.py
Builds the accountability scores.json from matched promise files.
Run this after matcher.py.

Usage:
    python scorer.py
"""

import json
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR      = Path("../data")
OUTPUT_PATH   = DATA_DIR / "scores.json"

PROMISE_FILES = {
    "DMK":  {"path": DATA_DIR / "dmk_2021_promises.json",  "year": 2021},
    "ADMK": {"path": DATA_DIR / "admk_2016_promises.json", "year": 2016},
}

CATEGORIES = [
    "healthcare",
    "education",
    "infrastructure",
    "agriculture",
    "economy",
    "employment",
    "women and youth",
]


# ── Scorer ────────────────────────────────────────────────────────────────────

def compute_party_score(promises: list[dict]) -> dict:
    """
    Computes overall and per-category accountability scores.
    Returns a structured score object.
    """
    total     = len(promises)
    fulfilled = [p for p in promises if p.get("status") == "fulfilled"]

    overall_pct = round((len(fulfilled) / total * 100), 1) if total > 0 else 0.0

    # Per-category breakdown
    by_category = {}
    for cat in CATEGORIES:
        cat_promises  = [p for p in promises if p.get("category") == cat]
        cat_fulfilled = [p for p in cat_promises if p.get("status") == "fulfilled"]
        cat_total     = len(cat_promises)

        by_category[cat] = {
            "total":     cat_total,
            "fulfilled": len(cat_fulfilled),
            "score":     round(len(cat_fulfilled) / cat_total * 100, 1) if cat_total > 0 else 0.0,
        }

    # Average similarity score across all fulfilled promises
    sim_scores = [
        p["similarity_score"] for p in fulfilled
        if p.get("similarity_score") is not None
    ]
    avg_similarity = round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else 0.0

    return {
        "total":           total,
        "fulfilled":       len(fulfilled),
        "unfulfilled":     total - len(fulfilled),
        "score":           overall_pct,
        "avg_similarity":  avg_similarity,
        "by_category":     by_category,
    }


def run() -> None:
    print(f"\n{'='*55}")
    print(f"  Vaakazhipeer — Scorer")
    print(f"{'='*55}\n")

    output = {}

    for party, config in PROMISE_FILES.items():
        path = config["path"]
        if not path.exists():
            print(f"  Skipping {party}: {path} not found")
            continue

        with open(path, encoding="utf-8") as f:
            promises = json.load(f)

        score_data = compute_party_score(promises)
        score_data["party"] = party
        score_data["year"]  = config["year"]
        output[party] = score_data

        print(f"  {party} ({config['year']})")
        print(f"    Overall score  : {score_data['score']}%")
        print(f"    Fulfilled      : {score_data['fulfilled']} / {score_data['total']}")
        print(f"    Avg similarity : {score_data['avg_similarity']}")
        print(f"    By category    :")
        for cat, s in score_data["by_category"].items():
            bar = "█" * int(s["score"] / 10)
            print(f"      {cat:<22} {s['score']:>5.1f}%  {bar}")
        print()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Scores saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()