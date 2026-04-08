"""
manifesto_parser_v3.py
Robust Tamil + English Manifesto Promise Extractor
  — with automatic OCR fallback for scanned PDFs

Usage:
    python manifesto_parser_v3.py --pdf file.pdf --party DMK --year 2021

Changes from v2:
    • Auto-detects scanned PDFs (< 100 chars/page average)
    • Falls back to Tesseract OCR (tam+eng) via pdf2image
    • OCR runs page-by-page with progress reporting
    • --ocr flag forces OCR even on text PDFs (useful for broken fonts)
    • --dpi flag controls render quality (default 200, higher = better accuracy, slower)
    • --pages flag limits OCR to first N pages (useful for quick testing)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter
import numpy as np

import pdfplumber
from transformers import pipeline

# ── Constants ────────────────────────────────────────────────────────────────

PROMISE_TRIGGERS_EN = [
    r"\bwill\b", r"\bshall\b", r"\bwe commit\b", r"\bwe promise\b",
    r"\bplan to\b", r"\bintend to\b", r"\bensure\b", r"\bprovide\b",
    r"\bestablish\b", r"\blaunch\b", r"\bimplement\b", r"\bcreate\b",
    r"\bdistribute\b", r"\bextend\b", r"\bstrengthen\b",
]

# ── Tamil promise triggers ───────────────────────────────────────────────────
# DMK / active-voice parties use first-person plural ("we will do"):
PROMISE_TRIGGERS_TA_ACTIVE = [
    "செய்வோம்", "வழங்குவோம்", "அமைப்போம்",
    "உறுதி", "திட்டம்", "வழங்க", "ஏற்படுத்துவோம்",
    "கொண்டுவருவோம்", "மேம்படுத்துவோம்",
    "அளிப்போம்", "நிறைவேற்றுவோம்", "உருவாக்குவோம்",
    "கட்டமைப்போம்", "தொடங்குவோம்", "விரிவுபடுத்துவோம்",
    "உயர்த்துவோம்", "பாதுகாப்போம்", "வழிவகை செய்வோம்",
    "கொண்டுவர", "செய்ய உறுதி",
]

# AIADMK / passive-voice parties use third-person passive future ("will be done"):
PROMISE_TRIGGERS_TA_PASSIVE = [
    "செய்யப்படும்",            # will be done
    "வழங்கப்படும்",            # will be provided
    "அமைக்கப்படும்",           # will be established
    "ஏற்படுத்தப்படும்",        # will be created
    "தொடங்கப்படும்",           # will be started
    "நடைமுறைப்படுத்தப்படும்",  # will be implemented
    "கொண்டுவரப்படும்",        # will be brought
    "உருவாக்கப்படும்",         # will be formed
    "விரிவுபடுத்தப்படும்",     # will be expanded
    "மேம்படுத்தப்படும்",       # will be improved
    "நீட்டிக்கப்படும்",        # will be extended
    "உயர்த்தப்படும்",          # will be raised
    "வலுப்படுத்தப்படும்",      # will be strengthened
    "கட்டமைக்கப்படும்",       # will be constructed
    "அறிவிக்கப்படும்",         # will be announced
    "நிறைவேற்றப்படும்",       # will be fulfilled
    "நிறுவப்படும்",            # will be established/installed
    "தரப்படும்",               # will be given
    "கிடைக்கும்",              # will be available
    "பெறுவர்", "பெறுவார்கள்",  # will receive
    "இயங்கும்",                # will operate
    "படும்",                   # generic passive future suffix (catch-all)
]

# AIADMK govt-style phrases
PROMISE_TRIGGERS_TA_GOVT = [
    "நமது அரசு",       # our government
    "அம்மா அரசு",      # Amma government
    "அரசு வழங்கும்",   # government will provide
    "புதிய திட்டம்",   # new scheme
    "சிறப்பு திட்டம்", # special scheme
    "இலவச",            # free (very AIADMK)
    "மானியம்",         # subsidy
    "நிவாரணம்",        # relief
    "உதவித்தொகை",     # assistance amount
    "ஊதிய உயர்வு",    # salary increase
    "ஓய்வூதியம்",     # pension
]

# ── Grantha-encoded triggers (AIADMK font encoding) ────────────────────────
# AIADMK PDFs use a custom Tamil font that maps to Latin+diacritic characters.
# pdfplumber extracts these as garbled Latin text — NOT Unicode Tamil.
# These triggers match the actual extracted bytes from their PDFs.
PROMISE_TRIGGERS_ENCODED = [
    # Core passive future tense (மிக முக்கியம்)
    "tH§f¥gL«",           # வழங்கப்படும் — will be provided
    "brašgL¤j¥gL«",       # செயல்படுத்தப்படும் — will be implemented
    "mik¡f¥gL«",          # அமைக்கப்படும் — will be established
    "V‰gL¤j¥gL«",         # ஏற்படுத்தப்படும் — will be created
    "Jt§f¥gL«",           # தொடங்கப்படும் — will be started
    "bjhl§f¥gL«",         # தொடங்கப்படும் — will be started
    "ca®¤j¥gL«",          # உயர்த்தப்படும் — will be raised
    "éçth¡f¥gL«",         # விரிவாக்கப்படும் — will be expanded
    "ãWt¥gL«",            # நிறுவப்படும் — will be installed/established
    "ãiwnt‰w¥gL«",        # நிறைவேற்றப்படும் — will be fulfilled
    "Ko¡f¥gL«",           # முடிக்கப்படும் — will be completed
    "nk«gL¤j¥gL«",        # மேம்படுத்தப்படும் — will be improved
    "vL¡f¥gL«",           # எடுக்கப்படும் — steps will be taken
    "cUth¡f¥gL«",         # உருவாக்கப்படும் — will be formed/created
    "Ïa¡f¥gL«",           # இயக்கப்படும் — will be operated
    "nk‰bfhŸs¥gL«",       # மேற்கொள்ளப்படும் — will be undertaken
    "tH§f¥gLtJl‹",        # வழங்கப்படுவதுடன் — along with providing
    "vL¡f¥g£LŸsd",        # எடுக்கப்பட்டுள்ளன — have been taken
    "bjhl®ªJ brašgL¤j¥gL«", # தொடர்ந்து செயல்படுத்தப்படும் — will continue
    "elto¡if vL¡f¥gL«",   # நடவடிக்கை எடுக்கப்படும் — action will be taken
    "Ô®Î fhz¥gL«",        # தீர்வு காணப்படும் — solution will be found
    "tèÍW¤Jnth«",         # வலியுறுத்துவோம் — we will advocate
    # Common promise keywords in encoded form
    "Â£l«",               # திட்டம் — scheme/plan
    "khåa«",              # மானியம் — subsidy
    "ÏšyK«",             # இலவசமும் — also free
    "Ïy£r«",              # இலட்சம் — lakh (monetary promise)
    "nfho",               # கோடி — crore (monetary promise)
    "éiyæšyh",           # விலையில்லா — free of cost
    "Ïytr",              # இலவச — free
    "cjé¤bjhif",         # உதவித்தொகை — assistance amount
    "ey thça«",          # நல வாரியம் — welfare board
    "ghJfh¥ò",           # பாதுகாப்பு — protection/security
    # Variant endings (same word, different punctuation in PDF)
    "tH§f¥gL©",          # வழங்கப்படும் variant (© instead of «)
    "brašgL¤j¥gL©",      # செயல்படுத்தப்படும் variant
    "mik¡f¥gL©",         # அமைக்கப்படும் variant
    "f£o¤ju¥gL«",        # கட்டித்தரப்படும் — will be built and given
    "jŸSgo brŒa¥gL«",   # தள்ளுபடி செய்யப்படும் — will be waived
    "¥gL«",              # generic passive suffix (catch-all for any form)
    "¥gL©",              # same catch-all with © variant
]

# Combined — used by is_promise_sentence()
PROMISE_TRIGGERS_TA = (
    PROMISE_TRIGGERS_TA_ACTIVE
    + PROMISE_TRIGGERS_TA_PASSIVE
    + PROMISE_TRIGGERS_TA_GOVT
    + PROMISE_TRIGGERS_ENCODED   # ← AIADMK font-encoded text
)

CATEGORIES = [
    "healthcare",
    "education",
    "infrastructure",
    "agriculture",
    "economy",
    "employment",
    "women and youth",
]

MIN_PROMISE_LENGTH = 20   # AIADMK uses shorter bullet-style promises
MAX_PROMISE_LENGTH = 600

# Heuristic: if average chars/page is below this, treat as scanned
SCANNED_THRESHOLD_CHARS_PER_PAGE = 100


# ── PDF Extraction ────────────────────────────────────────────────────────────

def extract_text_pdfplumber(pdf_path: str) -> tuple[str, int]:
    """Returns (full_text, page_count)."""
    full_text = []
    page_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        print(f"  PDF loaded: {page_count} pages")

        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            except Exception as e:
                print(f"  Warning: page {i+1} skipped — {e}")

    return "\n".join(full_text), page_count


def is_scanned_pdf(text: str, page_count: int) -> bool:
    """Detect if a PDF is image-only or uses legacy garbled encoding."""
    if page_count == 0:
        return True
    
    # 1. Chars per page check
    avg = len(text.strip()) / page_count
    if avg < SCANNED_THRESHOLD_CHARS_PER_PAGE:
        return True
    
    # 2. Garbled Latin check (Common in legacy AIADMK/DMK PDFs)
    # These PDFs look like "mmmmÃÃÃÃ" to a text extractor
    garbled_indicators = ["Ã", "Â", "Â®", "jjjj", "aaaa", "mmmm", "ffff"]
    count = sum(text.count(ind) for ind in garbled_indicators)
    if count > 200: # High density of garbled markers
        print(f"  ⚠ Garbled encoding detected ({count} markers). Forcing OCR for accuracy.")
        return True
        
    return False


def extract_text_ocr(
    pdf_path: str,
    dpi: int = 200,
    max_pages: int = None,
    poppler_path: str = None,
    tesseract_path: str = None,
) -> str:
    """
    Convert PDF pages to images and run Tesseract OCR (Tamil + English).
    Returns the full OCR'd text.

    On Windows, pass poppler_path and tesseract_path explicitly if they
    are not on the system PATH — avoids needing to edit environment variables.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("ERROR: pdf2image or pytesseract not installed.")
        print("  Run: pip install pdf2image pytesseract")
        sys.exit(1)

    # ── Windows: point pytesseract at the .exe directly ──────────────────
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"  Tesseract: {tesseract_path}")

    print(f"  Rendering pages at {dpi} DPI...")

    # Convert PDF → images (pass poppler_path for Windows)
    convert_kwargs = {"dpi": dpi, "fmt": "jpeg", "thread_count": 2}
    if max_pages:
        convert_kwargs["last_page"] = max_pages
    if poppler_path:
        convert_kwargs["poppler_path"] = poppler_path
        print(f"  Poppler : {poppler_path}")

    try:
        images = convert_from_path(pdf_path, **convert_kwargs)
    except Exception as e:
        print(f"\nERROR: Could not convert PDF to images — {e}")
        print("\nOn Windows you need Poppler binaries installed.")
        print("  Quick fix — pass the path directly:")
        print('    --poppler-path "C:\\poppler\\Library\\bin"')
        print("\nDownload Poppler for Windows:")
        print("  https://github.com/oschwartz10612/poppler-windows/releases/latest")
        sys.exit(1)

    total = len(images)
    print(f"  Rendered {total} pages. Starting OCR (tam+eng)...\n")

    ocr_text_parts = []

    for i, img in enumerate(images):
        page_num = i + 1

        try:
            text = pytesseract.image_to_string(
                img,
                lang="tam+eng",
                config="--oem 1 --psm 6",
            )
        except Exception as e:
            print(f"  Warning: OCR failed on page {page_num} — {e}")
            text = ""

        char_count = len(text.strip())
        print(f"  Page {page_num:>4}/{total} — {char_count:>5} chars extracted")

        if text.strip():
            ocr_text_parts.append(text)

    full_text = "\n".join(ocr_text_parts)
    print(f"\n  OCR complete — {len(full_text):,} total characters extracted")
    return full_text


def extract_text_from_pdf(
    pdf_path: str,
    force_ocr: bool,
    dpi: int,
    max_pages: int = None,
    poppler_path: str = None,
    tesseract_path: str = None,
) -> str:
    """
    Smart extractor:
    1. Try pdfplumber first
    2. If output looks like a scanned PDF (or --ocr forced), use Tesseract OCR
    """
    print("[1/4] Extracting text...")

    text, page_count = extract_text_pdfplumber(pdf_path)
    extracted_chars = len(text.strip())
    avg_chars = extracted_chars / max(page_count, 1)

    print(f"  Direct extraction: {extracted_chars:,} chars | avg {avg_chars:.0f} chars/page")

    if force_ocr:
        print("  --ocr flag set. Forcing OCR mode.")
        return extract_text_ocr(pdf_path, dpi=dpi, max_pages=max_pages,
                                poppler_path=poppler_path, tesseract_path=tesseract_path)

    if is_scanned_pdf(text, page_count):
        print(f"  ⚠ Scanned PDF detected (avg {avg_chars:.0f} chars/page < threshold {SCANNED_THRESHOLD_CHARS_PER_PAGE})")
        print("  Switching to OCR mode automatically...")
        return extract_text_ocr(pdf_path, dpi=dpi, max_pages=max_pages,
                                poppler_path=poppler_path, tesseract_path=tesseract_path)

    print("  Text PDF detected — using direct extraction.")
    return text


# ── Sentence Splitting (Tamil + English safe) ─────────────────────────────────

def split_sentences(text: str):
    """Custom sentence splitter supporting Tamil + English + OCR noise."""
    # Tamil full stop (।), common punctuation, and newlines
    sentences = re.split(r"[.!?।\n|]+", text)
    return [s.strip() for s in sentences if s.strip()]


# ── Promise Detection ─────────────────────────────────────────────────────────

def is_promise_sentence(sentence: str) -> bool:
    s = sentence.lower()
    for pattern in PROMISE_TRIGGERS_EN:
        if re.search(pattern, s):
            return True
    for word in PROMISE_TRIGGERS_TA:
        if word in sentence:
            return True
    return False


def clean_sentence(sentence: str) -> str:
    sentence = re.sub(r"\s+", " ", sentence).strip()
    sentence = sentence.replace("\u2013", "-").replace("\u2014", "-")
    # Remove common OCR artifacts
    sentence = re.sub(r"[_\|]{2,}", " ", sentence)
    sentence = re.sub(r"[^\w\s\u0B80-\u0BFF.,!?():;'\"-]", "", sentence)
    return sentence.strip()


def extract_promise_candidates(text: str):
    sentences = split_sentences(text)
    candidates = []

    for sent in sentences:
        sent = clean_sentence(sent)
        if MIN_PROMISE_LENGTH <= len(sent) <= MAX_PROMISE_LENGTH:
            if is_promise_sentence(sent):
                candidates.append(sent)

    return candidates


def deduplicate_promises(candidates: list[str]) -> list[str]:
    """Remove duplicates using substring checks and semantic similarity."""
    if not candidates: return []
    
    # 1. Exact substring deduplication
    unique = []
    candidates = sorted(candidates, key=len, reverse=True)
    for c in candidates:
        if not any(c in u for u in unique if c != u):
            unique.append(c)
    
    # 2. Semantic deduplication
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    # Process in reverse order (longest first) to keep more specific ones
    final = []
    embeddings = model.encode(unique, convert_to_tensor=True)
    
    to_remove = set()
    for i in range(len(unique)):
        if i in to_remove: continue
        for j in range(i + 1, len(unique)):
            if j in to_remove: continue
            
            sim = util.cos_sim(embeddings[i], embeddings[j]).item()
            if sim > 0.85:
                # Keep longer one (i is longer than or equal to j because of sort)
                to_remove.add(j)
    
    final = [unique[i] for i in range(len(unique)) if i not in to_remove]
    print(f"  Deduplication removed {len(candidates) - len(final)} duplicates from {len(candidates)} candidates")
    return final


# ── Models ───────────────────────────────────────────────────────────────────

def build_models():
    print("\n  Loading models...")

    # Use MarianMT directly — the pipeline "translation" task was removed
    # in newer versions of transformers. This works on all versions.
    from transformers import MarianMTModel, MarianTokenizer

    ta_en_model_name = "Helsinki-NLP/opus-mt-dra-en"  # Dravidian→EN covers Tamil
    print(f"  Downloading translation model ({ta_en_model_name})...")
    ta_tokenizer = MarianTokenizer.from_pretrained(ta_en_model_name)
    ta_model     = MarianMTModel.from_pretrained(ta_en_model_name)

    def translator(sentences, max_length=512):
        """Translate a list of Tamil sentences to English."""
        import torch
        inputs = ta_tokenizer(
            sentences, return_tensors="pt", padding=True,
            truncation=True, max_length=max_length
        )
        with torch.no_grad():
            translated = ta_model.generate(**inputs, max_length=max_length)
        return ta_tokenizer.batch_decode(translated, skip_special_tokens=True)

    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,
    )

    print("  Models ready.\n")
    return translator, classifier


def is_tamil(text: str) -> bool:
    return any("\u0B80" <= ch <= "\u0BFF" for ch in text)


# ── Processing ────────────────────────────────────────────────────────────────

def process_promises(candidates, translator, classifier):
    results = []
    print("[3/4] Processing + Classifying...\n")

    for i, sentence in enumerate(candidates):
        # Translate if Tamil
        if is_tamil(sentence):
            try:
                translated = translator([sentence], max_length=512)[0]
            except Exception:
                translated = sentence
        else:
            translated = sentence

        # ── CLASSIFICATION PAS 1 ──
        res = classifier(
            translated,
            candidate_labels=CATEGORIES,
            hypothesis_template="This sentence is about {}.",
        )
        
        cat1, conf1 = res["labels"][0], res["scores"][0]
        cat2, conf2 = res["labels"][1], res["scores"][1]
        
        # ── SECOND PASS IF LOW CONFIDENCE ──
        if conf1 < 0.40:
            res2 = classifier(
                translated,
                candidate_labels=CATEGORIES,
                hypothesis_template="This text is primarily about {}.",
            )
            cat1, conf1 = res2["labels"][0], res2["scores"][0]
            cat2, conf2 = res2["labels"][1], res2["scores"][1]
            
            if conf1 < 0.40:
                cat1 = "general"

        # ── AMBIGUITY CHECK (Multi-Category) ──
        multi_cat = False
        final_cats = [cat1]
        if cat1 != "general" and abs(conf1 - conf2) < 0.08:
            final_cats = [cat1, cat2]
            multi_cat = True

        conf_label = "high" if conf1 > 0.70 else "medium" if conf1 >= 0.40 else "low"

        results.append({
            "promise": sentence,
            "translated": translated,
            "category": cat1, # primary
            "categories": final_cats,
            "multi_category": multi_cat,
            "confidence": round(conf1, 4),
            "classification_confidence": conf_label
        })

        label_str = "/".join(final_cats)
        print(f"[{i+1}/{len(candidates)}] {label_str:<25} ({conf1:.2f}) [{conf_label}]")
        if multi_cat: print(f"  (Multi-Category detected)")

    return results


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run(pdf_path, party, year, output_dir, force_ocr, dpi, max_pages, poppler_path=None, tesseract_path=None):
    print(f"\n{'='*60}")
    print(f"  Vaakazhipeer — Manifesto Parser (v3)")
    print(f"  Party: {party} | Year: {year}")
    if force_ocr:
        print(f"  Mode : OCR (forced) | DPI: {dpi}")
    if max_pages:
        print(f"  Pages: first {max_pages} only")
    print(f"{'='*60}\n")

    # Step 1 — Extract
    text = extract_text_from_pdf(pdf_path, force_ocr=force_ocr, dpi=dpi, max_pages=max_pages,
                                 poppler_path=poppler_path, tesseract_path=tesseract_path)

    if not text.strip():
        print("ERROR: No text extracted after OCR. Check the PDF.")
        sys.exit(1)

    print(f"  Total characters available: {len(text):,}")

    # Always save raw extracted text for inspection
    debug_path = Path(output_dir) / f"{party.lower()}_{year}_raw_text.txt"
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(text, encoding="utf-8")
    print(f"  Raw text saved → {debug_path}")

    # Step 2 — Filter
    print("\n[2/4] Extracting promise candidates...")
    candidates = extract_promise_candidates(text)
    print(f"  Found {len(candidates)} candidates")

    if not candidates:
        print("\nNo promises found. Possible causes:")
        # ... (error messages)
        sys.exit(1)

    # NEW: Deduplication
    print("  Deduplicating...")
    deduped = deduplicate_promises(candidates)
    
    # Step 3 — Models
    translator, classifier = build_models()
    processed = process_promises(deduped, translator, classifier)

    # Step 4 — Save
    print("[4/4] Saving results...")
    promise_data = []
    for i, item in enumerate(processed):
        promise_data.append({
            "id": f"{party.lower()}_{year}_{str(i+1).zfill(3)}",
            "promise": item["promise"],
            "translated": item["translated"],
            "category": item["category"],
            "categories": item.get("categories", [item["category"]]),
            "multi_category": item.get("multi_category", False),
            "confidence": item["confidence"],
            "classification_confidence": item.get("classification_confidence", "medium"),
            "party": party.upper(),
            "year": year,
            "status": "pending",
            "similarity_score": None,
            "matched_headline": None,
            "matched_url": None,
            "matched_date": None,
        })

    output_results = {
        "metadata": {
            "party": party.upper(),
            "year": year,
            "raw_candidates": len(candidates),
            "after_dedup": len(deduped),
            "removed_duplicates": len(candidates) - len(deduped)
        },
        "promises": promise_data
    }

    out_path = Path(output_dir) / f"{party.lower()}_{year}_promises.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_results, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ Saved {len(promise_data)} promises → {out_path}")

    # Stats
    print("\nCategory breakdown:")
    counts = Counter(r["category"] for r in promise_data)
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {count}")


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Vaakazhipeer — Tamil/English Manifesto Parser v3"
    )
    parser.add_argument("--pdf", required=True, help="Path to manifesto PDF")
    parser.add_argument("--party", required=True, help="Party name (e.g. DMK)")
    parser.add_argument("--year", required=True, type=int, help="Election year")
    parser.add_argument("--out", default="data", help="Output directory")
    parser.add_argument(
        "--ocr", action="store_true",
        help="Force OCR mode even if text is extractable (useful for broken fonts)"
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help="DPI for PDF rendering during OCR (default: 200, use 300 for better accuracy)"
    )
    parser.add_argument(
        "--pages", type=int, default=None,
        help="Limit OCR to first N pages (useful for quick testing)"
    )

    parser.add_argument(
        "--poppler-path", default=None,
        help="Path to Poppler bin dir (Windows). E.g. C:\\poppler\\Library\\bin"
    )
    parser.add_argument(
        "--tesseract-path", default=None,
        help="Path to tesseract.exe (Windows). E.g. C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    )

    args = parser.parse_args()
    run(args.pdf, args.party, args.year, args.out, args.ocr, args.dpi, args.pages,
        poppler_path=args.poppler_path, tesseract_path=args.tesseract_path)
