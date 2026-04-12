"""
scorer.py — Vaakazhipeer

Auto-discovers all *_promises.json files and scores them.
Knows which party was ruling vs opposition for each period.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT   = DATA_DIR / "scores.json"
META_OUT = DATA_DIR / "metadata.json"

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

        raw_data  = json.load(open(path, encoding="utf-8"))
        data      = raw_data["promises"] if isinstance(raw_data, dict) and "promises" in raw_data else raw_data
        
        total     = len(data)
        party_name = meta["label"].split()[0]
        context    = meta["context"]
        
        # Liberalized Fulfillment Logic
        def get_p_score(p):
            status = p.get("status", "unfulfilled")
            credit = p.get("credit_party", "")
            
            # Fulfilled (direct) — promising party always gets credit now
            if status == "fulfilled":
                return 1.0
            
            # fulfilled_by_other still counts for opposition advocacy
            if status == "fulfilled_by_other":
                if context == "opposition":
                    return 1.0   # they advocated, other party delivered
                return 0.5       # partial credit for ruling party
            
            # Pending = in-progress, 40% credit for ruling party
            if status == "pending" and context == "ruling":
                return 0.4
                
            return 0.0

        fulfilled = sum(get_p_score(p) for p in data)
        score     = round(fulfilled / total * 100, 1) if total else 0.0

        cats = {}
        for p in data:
            p_cats = p.get("categories") or [p.get("category", "general")]
            weight = 1.0 / len(p_cats)
            p_val  = get_p_score(p)

            for cat in p_cats:
                if cat == "general": continue
                cats.setdefault(cat, {"total": 0, "fulfilled": 0})
                cats[cat]["total"] += weight
                cats[cat]["fulfilled"] += p_val * weight

        for cat in cats:
            t = cats[cat]["total"]
            f = cats[cat]["fulfilled"]
            cats[cat]["score"] = round(f / t * 100, 1) if t > 0 else 0.0

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

    # Update metadata.json
    from datetime import datetime, timezone
    meta_content = {"last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta_content, f, indent=2)
    print(f"Updated → {META_OUT}")


if __name__ == "__main__":
    run()