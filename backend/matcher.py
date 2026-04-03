import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

from llm_verifier import verify_fulfillment

# ────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────

DATA_DIR = Path("../data")

NEWS_PATH = DATA_DIR / "news_articles.json"
PROMISE_PATH = DATA_DIR / "dmk_2016_promises.json"

CACHE_PATH = DATA_DIR / "llm_cache.json"

THRESHOLD = 0.35
TOP_K = 5
BATCH_SIZE = 5
USE_LLM = True

MAX_ARTICLE_LEN = 500   # 🔥 CRITICAL FIX (prevents freeze)

# ────────────────────────────────────────────────────────
# CACHE
# ────────────────────────────────────────────────────────

def load_cache():
    if CACHE_PATH.exists():
        return json.load(open(CACHE_PATH))
    return {}

def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

# ────────────────────────────────────────────────────────
# UTILS
# ────────────────────────────────────────────────────────

def keyword_overlap(a, b):
    A = set(a.lower().split())
    B = set(b.lower().split())
    return len(A & B) / (len(A) + 1e-5)

# ────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────

def run():
    print("\n=== Matcher ===")

    # ── Load data ─────────────────────────
    print("Loading articles...")
    articles = json.load(open(NEWS_PATH, encoding="utf-8"))

    # 🔥 LIMIT TEXT SIZE BEFORE EMBEDDING
    texts = [
        (a["title"] + " " + a["body"])[:MAX_ARTICLE_LEN]
        for a in articles
    ]

    print(f"Total articles: {len(texts)}")

    # ── Load model ────────────────────────
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # ── Encode articles (FIXED) ───────────
    print("Encoding articles (this was the freeze point before)...")

    embeddings = model.encode(
        texts,
        batch_size=16,              # ✅ faster
        show_progress_bar=True      # ✅ visible progress
    )

    # ── Build FAISS index ────────────────
    print("Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))

    # ── Load promises ────────────────────
    print("Loading promises...")
    promises = json.load(open(PROMISE_PATH, encoding="utf-8"))

    # ── Load cache ───────────────────────
    cache = load_cache()

    print(f"Processing {len(promises)} promises...\n")

    # ── Batch processing ─────────────────
    for i in range(0, len(promises), BATCH_SIZE):
        batch = promises[i:i+BATCH_SIZE]

        print(f"Batch {i} → {i+len(batch)}")

        for p in batch:
            query = p["promise"]

            # ── Encode query ─────────────
            q_emb = model.encode([query]).astype("float32")

            # ── Retrieve Top-K ───────────
            D, I = index.search(q_emb, TOP_K)

            scores = []
            top_articles = []

            for rank, idx in enumerate(I[0]):
                text = texts[idx]

                # ✅ LIMIT TOKENS FOR LLM
                top_articles.append(text[:1500])

                emb_sim = 1 / (1 + D[0][rank])
                key_sim = keyword_overlap(query, text)

                scores.append(0.7 * emb_sim + 0.3 * key_sim)

            base_score = sum(scores) / len(scores)

            # ── LLM + CACHE ──────────────
            cache_key = query.strip().lower()

            if USE_LLM:
                if cache_key in cache:
                    result = cache[cache_key]
                else:
                    print(f"LLM checking: {query[:60]}...")
                    result = verify_fulfillment(query, top_articles)
                    cache[cache_key] = result

                llm_yes = 1 if result["verdict"] == "yes" else 0
                llm_conf = result["confidence"]

                final_score = 0.6 * base_score + 0.4 * (llm_yes * llm_conf)

                p["llm_verdict"] = result["verdict"]
                p["llm_confidence"] = llm_conf
                p["llm_reason"] = result["reason"]

            else:
                final_score = base_score

            # ── Final status ─────────────
            p["similarity_score"] = float(final_score)
            p["status"] = "fulfilled" if final_score > THRESHOLD else "unfulfilled"

    # ── Save cache ───────────────────────
    save_cache(cache)

    # ── Save updated promises ────────────
    json.dump(promises, open(PROMISE_PATH, "w", encoding="utf-8"), indent=2)

    print("\n✅ Matching complete")


# ────────────────────────────────────────────────────────

if __name__ == "__main__":
    run()