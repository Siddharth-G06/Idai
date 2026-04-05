"""
scorer.py — Vaakazhipeer

Auto-discovers all *_promises.json files and scores them.
Knows which party was ruling vs opposition for each period.
"""

import json
from pathlib import Path

DATA_DIR = Path("../data")
OUTPUT   = DATA_DIR / "scores.json"

FILE_META = {
    "aiadmk_2016_promises": {
        "label": "AIADMK 2016", "context": "ruling",     "period": "2016-2021",
        "note":  "AIADMK ruled TN 2016-2021; score = promises implemented",
    },
    "aiadmk_2021_promises": {
        "label": "AIADMK 2021", "context": "opposition", "period": "2021-2026",
        "note":  "AIADMK in opposition 2021-2026; score = promises advocated for",
    },
    "dmk_2016_promises": {
        "label": "DMK 2016",    "context": "opposition", "period": "2016-2021",
        "note":  "DMK in opposition 2016-2021; score = promises advocated for",
    },
    "dmk_2021_promises": {
        "label": "DMK 2021",    "context": "ruling",     "period": "2021-2026",
        "note":  "DMK ruled TN 2021-2026; score = promises implemented",
    },
}


def run():
    files = sorted(DATA_DIR.glob("*_promises.json"))

    if not files:
        print("No *_promises.json files found in data/")
        return

    output = {}
    print("\n=== Scorer ===\n")
    print(f"{'Party':<20} {'Context':<12} {'Score':>6}  {'Done':>5}/{'':<5} Period")
    print("─" * 65)

    for path in files:
        stem = path.stem
        meta = FILE_META.get(stem, {
            "label":   stem.replace("_promises","").replace("_"," ").upper(),
            "context": "ruling",
            "period":  "unknown",
            "note":    "",
        })

        data      = json.load(open(path, encoding="utf-8"))
        total     = len(data)
        fulfilled = sum(1 for p in data if p.get("status") == "fulfilled")
        score     = round(fulfilled / total * 100, 1) if total else 0.0

        cats = {}
        for p in data:
            cat = p.get("category", "unknown")
            cats.setdefault(cat, {"total": 0, "fulfilled": 0})
            cats[cat]["total"] += 1
            if p.get("status") == "fulfilled":
                cats[cat]["fulfilled"] += 1
        for cat in cats:
            t = cats[cat]["total"]
            f = cats[cat]["fulfilled"]
            cats[cat]["score"] = round(f / t * 100, 1) if t else 0.0

        confs    = [p.get("llm_confidence", 0) for p in data
                    if p.get("llm_verdict") == "yes"]
        avg_conf = round(sum(confs) / len(confs) * 100, 1) if confs else 0.0

        label, context, period = meta["label"], meta["context"], meta["period"]
        print(f"{label:<20} {context:<12} {score:>5}%  {fulfilled:>5}/{total:<5} {period}")

        output[label] = {
            "context":             context,
            "period":              period,
            "note":                meta.get("note", ""),
            "total":               total,
            "fulfilled":           fulfilled,
            "score":               score,
            "avg_llm_confidence":  avg_conf,
            "categories":          cats,
        }

    # Ensure output directory exists before writing
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    run()