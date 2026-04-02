"""
matcher.py
Core ML engine. Encodes promises + articles using Sentence-BERT,
builds a FAISS index, finds top matches, scores fulfillment.

Usage:
    python matcher.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR        = Path("../data")
ARTICLES_PATH   = DATA_DIR / "news_articles.json"

PROMISE_FILES = {
    "DMK":  DATA_DIR / "dmk_2021_promises.json",
    "ADMK": DATA_DIR / "admk_2016_promises.json",
}

# Sentence-BERT multilingual model — handles Tamil + English
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Similarity threshold — promises above this score → fulfilled
FULFILLMENT_THRESHOLD = 0.55

# Number of top articles to retrieve per promise
TOP_K = 3


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Text Preparation ──────────────────────────────────────────────────────────

def article_to_text(article: dict) -> str:
    """
    Combines title + body for richer semantic representation.
    Title gets double weight by repeating it.
    """
    title = article.get("title", "").strip()
    body  = article.get("body",  "").strip()
    return f"{title}. {title}. {body}"[:1000]   # cap at 1000 chars


def promise_to_text(promise: dict) -> str:
    return promise.get("promise", "").strip()


# ── Encoding + FAISS Index ────────────────────────────────────────────────────

def build_article_index(
    articles: list[dict],
    model: SentenceTransformer,
) -> tuple[faiss.IndexFlatIP, np.ndarray]:
    """
    Encodes all articles and builds a FAISS inner-product index.
    Normalised vectors → inner product == cosine similarity.
    """
    print(f"  Encoding {len(articles)} articles...")
    texts = [article_to_text(a) for a in articles]

    # Batch encoding — much faster than one-by-one
    vectors = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,   # L2 normalise for cosine similarity
        convert_to_numpy=True,
    )

    dim   = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)   # Inner Product index
    index.add(vectors.astype(np.float32))

    print(f"  FAISS index built: {index.ntotal} vectors, dim={dim}")
    return index, vectors


def encode_promises(
    promises: list[dict],
    model: SentenceTransformer,
) -> np.ndarray:
    texts = [promise_to_text(p) for p in promises]
    return model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )


# ── Matching ──────────────────────────────────────────────────────────────────

def match_promises_to_articles(
    promises: list[dict],
    articles: list[dict],
    index: faiss.IndexFlatIP,
    model: SentenceTransformer,
    threshold: float = FULFILLMENT_THRESHOLD,
) -> list[dict]:
    """
    For each promise, finds the top-K most similar articles.
    Annotates each promise with match results and fulfillment status.
    """
    promise_vectors = encode_promises(promises, model)

    scores_matrix, indices_matrix = index.search(
        promise_vectors.astype(np.float32), TOP_K
    )

    enriched = []
    for i, promise in enumerate(promises):
        best_score   = float(scores_matrix[i][0])
        best_idx     = int(indices_matrix[i][0])
        best_article = articles[best_idx] if best_idx < len(articles) else {}

        updated = dict(promise)   # copy
        updated["status"]           = "fulfilled" if best_score >= threshold else "unfulfilled"
        updated["similarity_score"] = round(best_score, 4)
        updated["matched_headline"] = best_article.get("title", "")
        updated["matched_url"]      = best_article.get("url", "")
        updated["matched_date"]     = best_article.get("published", "")
        updated["matched_source"]   = best_article.get("source", "")

        enriched.append(updated)

    return enriched


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run() -> None:
    print(f"\n{'='*55}")
    print(f"  Vaakazhipeer — Semantic Matcher")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    # Load articles
    print("[1/4] Loading news articles...")
    articles = load_json(ARTICLES_PATH)
    print(f"  {len(articles)} articles loaded.")

    if len(articles) < 10:
        print("  WARNING: Very few articles. Run news_fetcher.py first.")

    # Load model once — shared across all parties
    print("\n[2/4] Loading Sentence-BERT model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Model loaded: {MODEL_NAME}")

    # Build FAISS index once — shared across all parties
    print("\n[3/4] Building FAISS index...")
    index, _ = build_article_index(articles, model)

    # Process each party
    print("\n[4/4] Matching promises to articles...")
    for party, path in PROMISE_FILES.items():
        if not path.exists():
            print(f"  Skipping {party}: {path} not found")
            continue

        print(f"\n  ── {party} ──")
        promises = load_json(path)
        print(f"  {len(promises)} promises to match")

        enriched = match_promises_to_articles(promises, articles, index, model)
        save_json(enriched, path)

        fulfilled   = sum(1 for p in enriched if p["status"] == "fulfilled")
        unfulfilled = len(enriched) - fulfilled
        print(f"  Results: {fulfilled} fulfilled / {unfulfilled} unfulfilled")

    print(f"\n  Matching complete. Run scorer.py next.\n")


if __name__ == "__main__":
    run()