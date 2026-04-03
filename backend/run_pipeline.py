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

        section("Semantic Matcher + LLM")
        import matcher
        matcher.run()

        section("Scorer")
        import scorer
        scorer.run()

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    print(f"\nDone in {round(time.time()-start,1)}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    run(args.skip_fetch)