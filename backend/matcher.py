"""
matcher.py — Vaakazhipeer
Complete rewrite. No external llm_verifier.py needed.
Uses local Ollama — no API key, no rate limits, no cost.

ONE-TIME SETUP:
  1. Download Ollama: https://ollama.com/download
  2. Open a terminal and run: ollama pull llama3.2
  3. Then run this script normally — Ollama starts automatically.

If you don't want to install Ollama, set USE_LLM = False below.
Scores will be lower quality but will run instantly.
"""

import json
import requests as _req
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# CONFIG  — edit these if needed
# ─────────────────────────────────────────────
DATA_DIR   = Path("../data")
NEWS_PATH  = DATA_DIR / "news_articles.json"
CACHE_PATH = DATA_DIR / "llm_cache.json"

USE_LLM         = True          # False = embedding-only, instant, no Ollama needed
OLLAMA_MODEL    = "llama3.2"    # change to "gemma2:2b" or "mistral" if you pulled those
OLLAMA_URL      = "http://localhost:11434/api/generate"

THRESHOLD       = 0.50          # score above this = "fulfilled"
TOP_K           = 5
BATCH_SIZE      = 5
MAX_ARTICLE_LEN = 600           # chars for embedding
MAX_LLM_LEN     = 800           # chars per article sent to Ollama

# Which news period tags apply per promise file + ruling/opposition context
PERIOD_MAP = {
    "aiadmk_2016": {"periods": ["aiadmk_rule", "current", "unknown"], "context": "ruling",     "years": "2016-2021"},
    "aiadmk_2021": {"periods": ["opposition",  "current", "unknown"], "context": "opposition", "years": "2021-2026"},
    "dmk_2016":    {"periods": ["opposition",  "current", "unknown"], "context": "opposition", "years": "2016-2021"},
    "dmk_2021":    {"periods": ["dmk_rule",    "current", "unknown"], "context": "ruling",     "years": "2021-2026"},
}

# These strings in llm_reason mean the result is poisoned and must NOT be cached
POISON = ["429", "quota", "rate limit", "Connection error",
          "RateLimitError", "Ollama not running", "JSON parse error"]


# ─────────────────────────────────────────────
# OLLAMA
# ─────────────────────────────────────────────

def _ollama_ok():
    """Check Ollama is running and the model is installed."""
    try:
        r = _req.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(OLLAMA_MODEL.split(":")[0] in m for m in models):
            print(f"\n  WARNING: model '{OLLAMA_MODEL}' not found in Ollama.")
            print(f"  Run this in a terminal:  ollama pull {OLLAMA_MODEL}")
            print(f"  Installed models: {models}\n")
            return False
        print(f"  Ollama OK — model: {OLLAMA_MODEL}")
        return True
    except _req.exceptions.ConnectionError:
        print("\n  ERROR: Ollama is not running.")
        print("  Install from https://ollama.com/download")
        print(f"  Then run:  ollama pull {OLLAMA_MODEL}\n")
        return False


def _llm_verify(promise, articles, context, years):
    """Ask local Ollama whether a promise was fulfilled."""
    if context == "ruling":
        ctx = (f"This party was the RULING GOVERNMENT of Tamil Nadu during {years}. "
               "Check whether this manifesto promise was implemented, launched, or budgeted.")
    else:
        ctx = (f"This party was in OPPOSITION in Tamil Nadu during {years} and could not "
               "directly implement policies. Check whether they advocated for this promise, "
               "or whether the ruling party implemented something similar. Either counts.")

    block = "\n\n---\n\n".join(a for a in articles[:3] if a.strip()) or "No articles."

    prompt = f"""You are a Tamil Nadu political analyst fact-checking manifesto promises.

CONTEXT: {ctx}

PROMISE:
{promise}

NEWS ARTICLES:
{block}

Based ONLY on the articles, was this promise fulfilled?
- "yes" = evidence it was acted on, launched, budgeted, or advocated for
- "no"  = no evidence or contradicted
- Partial steps still count as "yes" with confidence 0.3-0.6
- If articles don't address this specific promise, say "no" confidence 0.1

Reply with ONLY this JSON, nothing else:
{{"verdict": "yes" or "no", "confidence": 0.0-1.0, "reason": "one sentence"}}"""

    try:
        resp = _req.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt,
                  "stream": False, "options": {"temperature": 0.1, "num_predict": 150}},
            timeout=120,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()
        s, e = raw.find("{"), raw.rfind("}") + 1
        if s == -1 or e == 0:
            return {"verdict": "no", "confidence": 0.0, "reason": "no JSON in response"}
        result  = json.loads(raw[s:e])
        verdict = str(result.get("verdict", "no")).lower().strip()
        return {
            "verdict":    "yes" if verdict in ("yes", "partial") else "no",
            "confidence": float(result.get("confidence", 0.0)),
            "reason":     str(result.get("reason", "")),
        }
    except _req.exceptions.ConnectionError:
        return {"verdict": "no", "confidence": 0.0, "reason": "Ollama not running"}
    except json.JSONDecodeError as ex:
        return {"verdict": "no", "confidence": 0.0, "reason": f"JSON parse error: {ex}"}
    except Exception as ex:
        return {"verdict": "no", "confidence": 0.0, "reason": str(ex)}


# ─────────────────────────────────────────────
# CACHE  (with automatic purge of poisoned entries)
# ─────────────────────────────────────────────

def _load_cache():
    if not CACHE_PATH.exists():
        return {}
    raw = json.load(open(CACHE_PATH, encoding="utf-8"))
    clean, n = {}, 0
    for k, v in raw.items():
        if any(p in str(v.get("reason", "")) for p in POISON):
            n += 1          # silently drop poisoned entries
        else:
            clean[k] = v
    if n:
        print(f"  Purged {n} poisoned cache entries (429s / connection errors)")
    print(f"  Cache: {len(clean)} valid entries")
    return clean


def _save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# SCORING HELPERS
# ─────────────────────────────────────────────

def _cosine(l2):
    """FAISS squared-L2 → cosine similarity (unit vectors). Range 0→1."""
    return float(np.clip(1.0 - l2 / 2.0, 0.0, 1.0))


def _kw(a, b):
    A, B = set(a.lower().split()), set(b.lower().split())
    return len(A & B) / len(A) if A else 0.0


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run():
    print("\n=== Matcher ===")

    # Decide whether to use LLM
    use_llm = USE_LLM
    if use_llm:
        if not _ollama_ok():
            print("  Ollama unavailable — switching to embedding-only mode.")
            use_llm = False

    # Load articles
    if not NEWS_PATH.exists():
        print(f"ERROR: {NEWS_PATH} not found. Run news_fetcher.py first.")
        return

    articles = json.load(open(NEWS_PATH, encoding="utf-8"))
    texts = []
    for a in articles:
        body = a.get("body", "").strip() or a.get("title", "")
        texts.append((a.get("title", "") + " " + body)[:MAX_ARTICLE_LEN])
    print(f"Articles loaded: {len(texts)}")

    # Embed all articles once
    print("Loading SentenceTransformer...")
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    print("Encoding articles...")
    all_embs = model.encode(
        texts, batch_size=16, show_progress_bar=True, normalize_embeddings=True
    )
    global_idx = faiss.IndexFlatL2(all_embs.shape[1])
    global_idx.add(np.array(all_embs, dtype="float32"))

    cache = _load_cache()

    promise_files = sorted(DATA_DIR.glob("*_promises.json"))
    if not promise_files:
        print("No *_promises.json files found in data/. Run manifesto_parser first.")
        return

    for pfile in promise_files:
        stem = pfile.stem.replace("_promises", "")
        meta = PERIOD_MAP.get(stem, {
            "periods": [], "context": "ruling", "years": "2016-2026"
        })
        allowed = meta["periods"]
        context = meta["context"]
        years   = meta["years"]

        promises = json.load(open(pfile, encoding="utf-8"))
        print(f"\n── {pfile.name}  ({context}, {years}) ──")

        # Build period-filtered sub-index
        valid = ([i for i, a in enumerate(articles)
                  if a.get("period", "unknown") in allowed]
                 if allowed else list(range(len(articles))))
        if not valid:
            valid = list(range(len(articles)))   # fallback: use everything

        print(f"  {len(promises)} promises | {len(valid)} articles in scope")

        sub_embs = np.array([all_embs[i] for i in valid], dtype="float32")
        sub_idx  = faiss.IndexFlatL2(sub_embs.shape[1])
        sub_idx.add(sub_embs)
        sub_arts  = [articles[i] for i in valid]
        sub_texts = [texts[i]    for i in valid]

        for bi in range(0, len(promises), BATCH_SIZE):
            batch = promises[bi : bi + BATCH_SIZE]
            print(f"  Batch {bi}→{bi+len(batch)}")

            for p in batch:
                raw     = p.get("promise", "")
                english = p.get("translated", raw)
                query   = english if english and english != raw else raw

                if not query.strip():
                    p["status"] = "unfulfilled"
                    p["similarity_score"] = 0.0
                    continue

                q_emb = model.encode(
                    [query], normalize_embeddings=True
                ).astype("float32")

                k = min(TOP_K, len(sub_texts))
                D, I = sub_idx.search(q_emb, k)

                emb_sims  = [_cosine(D[0][r]) for r in range(k)]
                kw_sims   = [_kw(query, sub_texts[idx]) for idx in I[0]]
                top_texts = [sub_texts[idx][:MAX_LLM_LEN] for idx in I[0]]

                base = 0.7 * float(np.mean(emb_sims)) + 0.3 * float(np.mean(kw_sims))

                if use_llm:
                    key = (query.strip().lower() + "|" + context)[:200]

                    if key in cache:
                        result = cache[key]
                    else:
                        print(f"    LLM → {query[:65]}...")
                        result = _llm_verify(query, top_texts, context, years)
                        # Only cache clean results — never cache errors
                        if not any(p in str(result.get("reason","")) for p in POISON):
                            cache[key] = result
                            _save_cache(cache)   # save after each new result

                    verdict  = result.get("verdict", "no")
                    llm_conf = float(result.get("confidence", 0.0))

                    if verdict == "yes":
                        final = 0.4 * base + 0.6 * llm_conf
                    else:
                        final = base * 0.5

                    p["llm_verdict"]    = verdict
                    p["llm_confidence"] = llm_conf
                    p["llm_reason"]     = result.get("reason", "")
                else:
                    final = base

                p["similarity_score"] = round(final, 4)
                p["status"] = "fulfilled" if final >= THRESHOLD else "unfulfilled"

                if I[0].size > 0:
                    top = int(I[0][0])
                    p["matched_headline"] = sub_arts[top].get("title", "")
                    p["matched_url"]      = sub_arts[top].get("url", "")
                    p["matched_date"]     = sub_arts[top].get("published", "")

        json.dump(promises, open(pfile, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"  Saved {pfile.name}")

    print("\n✅ Matching complete")


if __name__ == "__main__":
    run()