import json
from pathlib import Path

DATA_DIR = Path("../data")
OUTPUT = DATA_DIR / "scores.json"

FILES = [
    ("DMK_2016", DATA_DIR / "dmk_2016_promises.json"),
]


def run():
    output = {}

    for name, path in FILES:
        if not path.exists():
            continue

        data = json.load(open(path, encoding="utf-8"))

        total = len(data)
        fulfilled = sum(1 for p in data if p["status"] == "fulfilled")

        score = round((fulfilled / total * 100), 1) if total else 0

        output[name] = {
            "total": total,
            "fulfilled": fulfilled,
            "score": score
        }

        print(f"{name}: {score}%")

    json.dump(output, open(OUTPUT, "w"), indent=2)
    print("Saved scores.json")


if __name__ == "__main__":
    run()