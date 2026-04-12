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
from datetime import datetime
import re

# Load .env so GROQ_API_KEY is available via os.getenv
load_dotenv(Path(__file__).parent / ".env")

# ─────────────────────────────────────────────
# GOVERNANCE CONFIG
# ─────────────────────────────────────────────
GOVERNANCE = {
    "AIADMK": {"start": "2016-05-23", "end": "2021-05-07"},
    "DMK":    {"start": "2021-05-07", "end": None},  # ongoing
}

def get_ruling_party(date_str: str) -> str:
    """Returns which party was in power on a given date."""
    if not date_str:
        return "unknown"
    try:
        # news_fetcher usually saves ISO format or RFC-822
        # Try a few common formats
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.split('+')[0].split('Z')[0])
        else:
            # Fallback for RSS dates like "Mon, 06 Apr 2026 01:54:20 +0530"
            from dateutil import parser
            dt = parser.parse(date_str).replace(tzinfo=None)
    except:
        return "unknown"

    admk_start = datetime(2016, 5, 23)
    admk_end   = datetime(2021, 5, 7)
    
    if admk_start <= dt < admk_end:
        return "AIADMK"
    elif dt >= admk_end:
        return "DMK"
    return "unknown"

def is_temporally_valid(promise_year: int, article_date_str: str) -> bool:
    """Ensures article isn't ancient history vs the promise."""
    if not article_date_str: return False
    try:
        from dateutil import parser
        adt = parser.parse(article_date_str).replace(tzinfo=None)
    except:
        return False
    
    # Define election/manifesto dates
    if promise_year == 2016:
        # Grace window: ~1 year before 2016-05-23
        start_valid = datetime(2015, 5, 1)
    elif promise_year == 2021:
        # Grace window: ~1 year before 2021-05-07
        start_valid = datetime(2020, 5, 1)
    else:
        start_valid = datetime(promise_year - 1, 1, 1)

    return adt >= start_valid

def assess_promise_specificity(text: str) -> float:
    """Returns a specificity score 0.0 to 1.0."""
    if not text: return 0.0
    score = 0.0
    t = text.lower()

    # Numbers / Quantities (+0.3)
    if re.search(r'\d+|crore|lakh|percent|%|கோடி|லட்சம்|சதவீதம்', t):
        score += 0.3
    
    # Named Locations (+0.2)
    districts = ['chennai', 'madurai', 'coimbatore', 'salem', 'trichy', 'vellore', 'thanjavur', 
                 'rural', 'district', 'village', 'சென்னை', 'மதுரை', 'கோவை', 'மாவட்டம்', 'கிராமம்']
    if any(d in t for d in districts):
        score += 0.2
    
    # Timeframe (+0.2)
    if re.search(r'year|month|day|20\d{2}|நாட்கள்|வருடம்|மாதம்|ஆண்டு', t):
        score += 0.2
    
    # Beneficiary Group (+0.1)
    groups = ['farmer', 'women', 'student', 'youth', 'elder', 'disabl', 'worker',
              'விவசாயி', 'பெண்கள்', 'மாணவர்', 'இளைஞர்', 'தொழிலாளர்']
    if any(g in t for g in groups):
        score += 0.1
    
    # Length metrics
    if len(text) > 80: score += 0.1
    if len(text) < 30: score -= 0.4
    
    return round(max(0.0, min(1.0, score)), 2)

# ─────────────────────────────────────────────
# CONFIG  — edit these if needed
# ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
NEWS_PATH  = DATA_DIR / "news_articles.json"
CACHE_PATH = DATA_DIR / "llm_cache.json"

USE_LLM      = True          # False = embedding-only, instant, no Groq needed
GROQ_MODEL   = "llama-3.3-70b-versatile"   # stable, currently supported model

THRESHOLD       = 0.15          # Minimum baseline to even consider a match
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
    # NEW: Quality Filter
    all_count = len(articles)
    articles = [a for a in articles if a.get("quality_score", 1.0) >= 0.3]
    print(f"  Using {len(articles)} of {all_count} articles after quality filter")

    texts = []
    for a in articles:
        title = a.get("title", "")
        body = a.get("body", "").strip()
        # NEW: Weighted Headline for short articles
        if len(body) < 100:
            text = (title + " ") * 3
        else:
            text = (title + " " + body)
        texts.append(text[:MAX_ARTICLE_LEN])
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

        raw_data = json.load(open(pfile, encoding="utf-8"))
        if isinstance(raw_data, dict) and "promises" in raw_data:
            promises = raw_data["promises"]
            pmeta = raw_data.get("metadata", {})
        else:
            promises = raw_data
            pmeta = {}

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

                # ─────────────────────────────────────────────
                # TEMPORAL VALIDATION LOOP
                # Try to find a temporally-valid article first.
                # If none found, fall back to best-scoring article
                # (don't hard-fail — we have limited news coverage).
                # ─────────────────────────────────────────────
                best_idx  = None
                p_year    = int(p.get("year", 2021))
                
                for r in range(k):
                    idx = I[0][r]
                    art_date = sub_arts[idx].get("published", "")
                    if is_temporally_valid(p_year, art_date):
                        best_idx = r
                        break
                
                # FALLBACK: if no temporally-valid article, use best cosine match
                if best_idx is None:
                    best_idx = 0  # I[0][0] is always the closest
                    p["match_valid"] = False  # flag it, but don't skip
                else:
                    p["match_valid"] = True

                top = int(I[0][best_idx])
                p["matched_headline"] = sub_arts[top].get("title", "")
                p["matched_url"]      = sub_arts[top].get("url", "")
                p["matched_date"]     = sub_arts[top].get("published", "")

                valid_emb_sim = _cosine(D[0][best_idx])
                valid_kw_sim  = _kw(query, sub_texts[best_idx])
                base = 0.7 * valid_emb_sim + 0.3 * valid_kw_sim
                top_texts_for_llm = [sub_texts[idx][:MAX_LLM_LEN] for idx in I[0][best_idx:best_idx+3]]

                if use_llm:
                    key = (query.strip().lower() + "|" + context)[:200]

                    if key in cache:
                        result = cache[key]
                    else:
                        print(f"    LLM → {query[:65]}...")
                        result = _llm_verify(query, top_texts_for_llm, context, years)
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
                
                # ─────────────────────────────────────────────
                # SPECIFICITY FILTER & DYNAMIC THRESHOLD
                # Vague promises need more evidence; specific ones
                # get credit even with moderate similarity.
                # ─────────────────────────────────────────────
                spec_score = assess_promise_specificity(query)
                p["specificity_score"] = spec_score
                p["specificity"] = "high" if spec_score >= 0.6 else "medium" if spec_score >= 0.3 else "low"
                
                # Liberal thresholds — favour recognition over skepticism
                if spec_score < 0.3:
                    dyn_threshold = 0.35   # vague promise: still needs decent evidence
                elif spec_score < 0.6:
                    dyn_threshold = 0.28   # medium specificity
                else:
                    dyn_threshold = 0.22   # specific promise: low bar is fine

                p["status"] = "fulfilled" if final >= dyn_threshold else "unfulfilled"

                # ── GOVERNANCE ATTRIBUTION ──
                # Whichever party made the promise gets credit.
                # We still record ruling_at_time for transparency.
                promising_party = "DMK" if "dmk" in stem.lower() else "AIADMK"
                article_date    = p.get("matched_date", "")
                ruling_at_time  = get_ruling_party(article_date)

                p["promising_party"] = promising_party
                p["ruling_at_time"]  = ruling_at_time

                if p["status"] == "fulfilled":
                    p["credit_party"] = promising_party

                # Mark pending for any unfulfilled promise still in active term
                if p["status"] == "unfulfilled" and final < 0.25:
                    stem_base = stem.replace("_promises", "")
                    if stem_base in ("dmk_2021", "aiadmk_2021"):
                        p["status"] = "pending"
            if (bi // BATCH_SIZE) % 5 == 0:
                out_data = {"metadata": pmeta, "promises": promises} if pmeta else promises
                json.dump(out_data, open(pfile, "w", encoding="utf-8"),
                          indent=2, ensure_ascii=False)

        out_data = {"metadata": pmeta, "promises": promises} if pmeta else promises
        json.dump(out_data, open(pfile, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"  Saved {pfile.name}")

    print("\n✅ Matching complete")


if __name__ == "__main__":
    run()