"""
matacher.py — Vaakazhipeer
Complete rewrite. No external llm_verifier.py needed.
Uses Groq API (free tier) — ultra-fast, no local GPU needed.

ONE-TIME SETUP:
  1. Sign up at https://console.groq.com and create a free API key.
  2. Add GROQ_API_KEY=<your_key> to backend/.env
  3. Run:  pip install groq
  4. Then run this script normally.

If you don't want to use Groq, set USE_LLM = False below.
Scores will be lower quality but will run instantly.
"""

import json
import os
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load .env so GROQ_API_KEY is available via os.getenv
load_dotenv(Path(__file__).parent / ".env")

# ─────────────────────────────────────────────
# CONFIG  — edit these if needed
# ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
NEWS_PATH  = DATA_DIR / "news_articles.json"
CACHE_PATH = DATA_DIR / "llm_cache.json"

USE_LLM      = True          # False = embedding-only, instant, no Groq needed
GROQ_MODEL   = "llama3-8b-8192"   # free & fast; alternatives: "llama3-70b-8192", "mixtral-8x7b-32768"

THRESHOLD       = 0.25          # score above this = "fulfilled" — kept liberal intentionally
TOP_K           = 5
BATCH_SIZE      = 5
MAX_ARTICLE_LEN = 600           # chars for embedding
MAX_LLM_LEN     = 800           # chars per article sent to Groq

# Which news period tags apply per promise file + ruling/opposition context
PERIOD_MAP = {
    "aiadmk_2016": {"periods": ["aiadmk_rule", "current", "unknown"], "context": "ruling",     "years": "2016-2021"},
    "aiadmk_2021": {"periods": ["opposition",  "current", "unknown"], "context": "opposition", "years": "2021-2026"},
    "dmk_2016":    {"periods": ["opposition",  "current", "unknown"], "context": "opposition", "years": "2016-2021"},
    "dmk_2021":    {"periods": ["dmk_rule",    "current", "unknown"], "context": "ruling",     "years": "2021-2026"},
}

# These strings in llm_reason mean the result is poisoned and must NOT be cached
POISON = ["429", "quota", "rate limit", "Connection error",
          "RateLimitError", "AuthenticationError", "Groq API key missing", "JSON parse error",
          "model_decommissioned", "deprecated", "Error code:"]


# ─────────────────────────────────────────────
# GROQ
# ─────────────────────────────────────────────

def _groq_ok():
    """Check GROQ_API_KEY is present in the environment."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        print("\n  ERROR: GROQ_API_KEY is not set.")
        print("  1. Sign up at https://console.groq.com")
        print("  2. Add GROQ_API_KEY=<your_key> to backend/.env\n")
        return False
    print(f"  Groq OK — model: {GROQ_MODEL}")
    return True


def _llm_verify(promise, articles, context, years):
    """Ask Groq (cloud LLM) whether a promise was fulfilled."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {"verdict": "no", "confidence": 0.0, "reason": "Groq API key missing"}

    if context == "ruling":
        ctx = (f"This party was the RULING GOVERNMENT of Tamil Nadu during {years}. "
               "Check whether this manifesto promise was implemented, launched, or budgeted.")
    else:
        ctx = (f"This party was in OPPOSITION in Tamil Nadu during {years} and could not "
               "directly implement policies. Check whether they advocated for this promise, "
               "or whether the ruling party implemented something similar. Either counts.")

    block = "\n\n---\n\n".join(a for a in articles[:3] if a.strip()) or "No articles."

    prompt = f"""You are a charitable Tamil Nadu political fact-checker. Your job is to find ANY evidence that a promise moved forward — even slightly.

CONTEXT: {ctx}

PROMISE:
{promise}

NEWS ARTICLES:
{block}

GIVE "yes" if ANY of the following is true (be very generous):
- The promise was fully implemented
- It was partially implemented or piloted
- Funds were allocated or a scheme was announced for it
- A committee/task force was formed to work on it
- The government or party publicly committed to it after the election
- A related or adjacent policy was launched that overlaps the spirit of the promise
- The articles mention the theme / sector of the promise positively
- An opposition party ADVOCATED for this promise even if not implemented

Only use "no" if the articles are completely silent on the topic AND there is zero overlap with the promise's subject area.

Confidence guide:
- 0.8-1.0 = direct, clear evidence
- 0.5-0.7 = partial or indirect evidence
- 0.3-0.5 = thematic overlap, spirit matches
- 0.1-0.3 = very weak but non-zero signal
- 0.0     = truly no relation whatsoever (rare — default to 0.2 when unsure)

Default to "yes" with confidence 0.3 rather than "no" when in doubt.

Reply with ONLY this JSON, nothing else:
{{"verdict": "yes" or "no", "confidence": 0.0-1.0, "reason": "one sentence"}}"""

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150,
        )
        raw = completion.choices[0].message.content.strip()
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
    except json.JSONDecodeError as ex:
        return {"verdict": "no", "confidence": 0.0, "reason": f"JSON parse error: {ex}"}
    except Exception as ex:
        # Surfaces Groq RateLimitError, AuthenticationError, etc. into the cache-poison list
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
        if not _groq_ok():
            print("  Groq unavailable — switching to embedding-only mode.")
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
                        # LLM confirms: blend base + llm confidence, weight toward LLM
                        final = 0.35 * base + 0.65 * llm_conf
                    else:
                        # LLM uncertain/no: still use base score — don't punish it
                        final = max(base, llm_conf * 0.5)

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