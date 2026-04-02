"""
manifesto_parser.py
Extracts structured promises from Tamil Nadu party manifesto PDFs.

Usage:
    python manifesto_parser.py --pdf path/to/file.pdf --party DMK --year 2021
"""

import argparse
import json
import re
import sys
from pathlib import Path

import nltk
import pdfplumber
from transformers import pipeline

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ── Constants ────────────────────────────────────────────────────────────────

PROMISE_TRIGGERS_EN = [
    r"\bwill\b", r"\bshall\b", r"\bwe commit\b", r"\bwe promise\b",
    r"\bplan to\b", r"\bintend to\b", r"\bensure\b", r"\bprovide\b",
    r"\bestablish\b", r"\blaunch\b", r"\bimplement\b", r"\bcreate\b",
    r"\bdistribute\b", r"\bextend\b", r"\bstrengthen\b",
]

PROMISE_TRIGGERS_TA = [
    "செய்வோம்", "வழங்குவோம்", "அமைப்போம்", "நாம்",
    "உறுதி", "திட்டம்", "வழங்க", "ஏற்படுத்துவோம்",
    "கொண்டுவருவோம்", "மேம்படுத்துவோம்",
]

CATEGORIES = [
    "healthcare",
    "education",
    "infrastructure",
    "agriculture",
    "economy",
    "employment",
    "women and youth",
]

MIN_PROMISE_LENGTH = 30   # characters — filters out noise
MAX_PROMISE_LENGTH = 500  # characters — filters out paragraph-length blobs


# ── PDF Text Extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from a PDF using pdfplumber.
    Falls back to empty string for unreadable pages.
    """
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  PDF loaded: {len(pdf.pages)} pages")
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            except Exception as e:
                print(f"  Warning: could not read page {i+1} — {e}")

    return "\n".join(full_text)


# ── Sentence Filtering ────────────────────────────────────────────────────────

def is_promise_sentence(sentence: str) -> bool:
    """
    Returns True if the sentence contains a promise trigger word.
    Checks both English and Tamil triggers.
    """
    s = sentence.lower()

    for pattern in PROMISE_TRIGGERS_EN:
        if re.search(pattern, s):
            return True

    for word in PROMISE_TRIGGERS_TA:
        if word in sentence:
            return True

    return False


def clean_sentence(sentence: str) -> str:
    """Strips extra whitespace and normalises unicode hyphens."""
    sentence = re.sub(r"\s+", " ", sentence).strip()
    sentence = sentence.replace("\u2013", "-").replace("\u2014", "-")
    return sentence


def extract_promise_candidates(raw_text: str) -> list[str]:
    """
    Tokenizes raw PDF text into sentences and returns those
    that pass the promise filter and length constraints.
    """
    sentences = nltk.sent_tokenize(raw_text)
    candidates = []

    for sent in sentences:
        sent = clean_sentence(sent)
        if MIN_PROMISE_LENGTH <= len(sent) <= MAX_PROMISE_LENGTH:
            if is_promise_sentence(sent):
                candidates.append(sent)

    return candidates


# ── Zero-Shot Classification ──────────────────────────────────────────────────

def build_classifier():
    """
    Loads the BART MNLI zero-shot classifier once.
    Uses CPU by default — change device=0 if you have a GPU.
    """
    print("  Loading BART MNLI classifier (first run downloads ~1.6 GB)...")
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,   # -1 = CPU. Change to 0 for CUDA GPU.
    )
    print("  Classifier ready.")
    return classifier


def classify_promise(classifier, sentence: str) -> tuple[str, float]:
    """
    Runs zero-shot classification on a single sentence.
    Returns (category_label, confidence_score).
    """
    result = classifier(
        sentence,
        candidate_labels=CATEGORIES,
        hypothesis_template="This sentence is about {}.",
        multi_label=False,
    )
    top_label = result["labels"][0]
    top_score = round(result["scores"][0], 4)
    return top_label, top_score


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run(pdf_path: str, party: str, year: int, output_dir: str = "data") -> None:
    print(f"\n{'='*55}")
    print(f"  Vaakazhipeer — Manifesto Parser")
    print(f"  Party: {party}  |  Year: {year}")
    print(f"  Input: {pdf_path}")
    print(f"{'='*55}\n")

    # Step 1 — Extract text
    print("[1/4] Extracting text from PDF...")
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        print("  ERROR: No text extracted. PDF may be image-only.")
        print("  Tip: Run OCR first using: ocrmypdf input.pdf output.pdf")
        sys.exit(1)
    print(f"  Extracted {len(raw_text):,} characters of text.")

    # Step 2 — Filter promise sentences
    print("\n[2/4] Filtering promise sentences...")
    candidates = extract_promise_candidates(raw_text)
    print(f"  Found {len(candidates)} promise candidates from text.")

    if len(candidates) == 0:
        print("  WARNING: No promise sentences found. Check trigger words or PDF language.")
        sys.exit(1)

    # Step 3 — Classify each promise
    print("\n[3/4] Classifying promises into categories...")
    classifier = build_classifier()

    results = []
    for i, sentence in enumerate(candidates):
        category, confidence = classify_promise(classifier, sentence)
        promise_id = f"{party.lower()}_{year}_{str(i+1).zfill(3)}"

        results.append({
            "id": promise_id,
            "promise": sentence,
            "category": category,
            "confidence": confidence,
            "party": party.upper(),
            "year": year,
            # Fields to be filled by matcher.py later:
            "status": "pending",
            "similarity_score": None,
            "matched_headline": None,
            "matched_url": None,
            "matched_date": None,
        })

        print(f"  [{i+1}/{len(candidates)}] {category:<20} ({confidence:.2f})  {sentence[:60]}...")

    # Step 4 — Save output
    print("\n[4/4] Saving results...")
    out_path = Path(output_dir) / f"{party.lower()}_{year}_promises.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n  Done. {len(results)} promises saved to {out_path}")
    print(f"  Category breakdown:")

    from collections import Counter
    counts = Counter(r["category"] for r in results)
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {cat:<25} {count}")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vaakazhipeer Manifesto Parser")
    parser.add_argument("--pdf",   required=True,  help="Path to manifesto PDF")
    parser.add_argument("--party", required=True,  help="Party name e.g. DMK or ADMK")
    parser.add_argument("--year",  required=True,  type=int, help="Election year e.g. 2021")
    parser.add_argument("--out",   default="../data", help="Output directory (default: ../data)")
    args = parser.parse_args()

    run(args.pdf, args.party, args.year, args.out)