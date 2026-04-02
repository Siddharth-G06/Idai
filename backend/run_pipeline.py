"""
run_pipeline.py
Master orchestrator. Runs the full pipeline in order:
  1. news_fetcher  — pull latest articles
  2. matcher       — semantic matching
  3. scorer        — rebuild scores.json

This is what GitHub Actions calls every 6 hours.

Usage:
    python run_pipeline.py
    python run_pipeline.py --skip-fetch   (skip news fetch, re-match only)
"""

import argparse
import sys
import time
from datetime import datetime


def section(title: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  STEP: {title}")
    print(f"{'─'*55}")


def run(skip_fetch: bool = False) -> None:
    start = time.time()
    print(f"\n{'='*55}")
    print(f"  VAAKAZHIPEER — Full Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    try:
        if not skip_fetch:
            section("News Fetcher")
            import news_fetcher
            news_fetcher.run()
        else:
            print("\n  [Skipping news fetch as requested]")

        section("Semantic Matcher")
        import matcher
        matcher.run()

        section("Scorer")
        import scorer
        scorer.run()

    except FileNotFoundError as e:
        print(f"\n  PIPELINE ERROR: {e}")
        print("  Make sure you have run manifesto_parser.py first.")
        sys.exit(1)

    except Exception as e:
        print(f"\n  UNEXPECTED ERROR: {e}")
        raise

    elapsed = round(time.time() - start, 1)
    print(f"\n{'='*55}")
    print(f"  Pipeline complete in {elapsed}s")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vaakazhipeer Pipeline")
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip news fetching, run matcher + scorer only"
    )
    args = parser.parse_args()
    run(skip_fetch=args.skip_fetch)