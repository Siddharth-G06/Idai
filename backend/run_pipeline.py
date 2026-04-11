import argparse
import sys
import time
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def section(title: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  STEP: {title}")
    print(f"{'─'*55}")

def run(skip_fetch: bool = False, skip_parse: bool = False) -> None:
    start = time.time()
    print(f"\n{'='*55}")
    print(f"  VAAKAZHIPEER — Full Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    try:
        if not skip_parse:
            section("Manifesto Parser")
            import manifesto_parser
            
            # Paths for Windows OCR support (only used if they exist)
            POPPLER = r"C:\Users\SIDDHARTH\poppler-25.12.0\Library\bin"
            TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            
            if not os.path.exists(POPPLER): POPPLER = None
            if not os.path.exists(TESSERACT): TESSERACT = None
            
            manifestos = [
                ("manifestos/dmk_2021.pdf", "DMK", 2021),
                ("manifestos/aiadmk_2021.pdf", "AIADMK", 2021),
                ("manifestos/dmk_2016.pdf", "DMK", 2016),
                ("manifestos/aiadmk_2016.pdf", "AIADMK", 2016),
            ]
            for pdf, party, year in manifestos:
                pdf_path = BASE_DIR / pdf
                if pdf_path.exists():
                    manifesto_parser.run(
                        pdf_path=str(pdf_path),
                        party=party,
                        year=int(year),
                        output_dir=str(DATA_DIR),
                        force_ocr=False,
                        dpi=200,
                        max_pages=None,
                        poppler_path=POPPLER,
                        tesseract_path=TESSERACT
                    )
                else:
                    print(f"  Warning: {pdf} not found, skipping.")

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

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\nDone in {round(time.time()-start,1)}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--skip-parse", action="store_true")
    args = parser.parse_args()
    run(args.skip_fetch, args.skip_parse)