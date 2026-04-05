"""
llm_verifier.py — Vaakazhipeer

Runs fully LOCAL using Ollama — no API key, no cost, no rate limits.

Setup (one-time):
  1. Download Ollama: https://ollama.com/download  (Windows/Mac/Linux)
  2. Install a model (pick one based on your RAM):
       ollama pull llama3.2        # 2GB, needs 4GB RAM  ← recommended
       ollama pull gemma2:2b       # 1.6GB, needs 4GB RAM
       ollama pull mistral         # 4GB, needs 8GB RAM (better quality)
  3. Ollama runs automatically in the background after install.
     No need to start anything manually.
"""

import json
import requests

# ── Config — change model here if you pulled a different one ──────────
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"   # change to "gemma2:2b" or "mistral" if preferred
TIMEOUT      = 120          # seconds — local inference is slower than API


def verify_fulfillment(promise, articles, context="ruling", years="2016-2026"):
    """
    Uses a local Ollama model to check if a manifesto promise was fulfilled.

    context: "ruling"     → party was in power; check if they implemented the promise
             "opposition" → party was in opposition; check if they advocated for it
    """
    if context == "ruling":
        ctx_text = (
            f"This party was the RULING GOVERNMENT of Tamil Nadu during {years}. "
            "Check whether this manifesto promise was implemented, launched, or budgeted."
        )
    else:
        ctx_text = (
            f"This party was in OPPOSITION in Tamil Nadu during {years}. "
            "Check whether they advocated for this promise in the legislature/media, "
            "or whether the ruling party implemented something similar. "
            "Either counts as partial fulfillment."
        )

    article_text = "\n\n---\n\n".join(a for a in articles[:3] if a.strip())
    if not article_text:
        article_text = "No relevant articles found."

    prompt = f"""You are a Tamil Nadu political analyst fact-checking manifesto promises.

CONTEXT: {ctx_text}

PROMISE:
{promise}

RELEVANT NEWS ARTICLES:
{article_text}

TASK: Based ONLY on the articles above, determine if this promise was fulfilled.

RULES:
- verdict "yes" = clear evidence the promise was acted on, launched, or budgeted
- verdict "no"  = no evidence in articles, or contradicted
- Partial steps still count as "yes" with lower confidence (0.4-0.6)
- If articles don't mention this specific promise at all, say "no" with confidence 0.1
- Do NOT use outside knowledge — only what the articles say

You MUST respond with ONLY a JSON object, nothing else, no explanation:
{{"verdict": "yes" or "no", "confidence": 0.0-1.0, "reason": "one sentence"}}"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150,   # short output — just the JSON
                },
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        # Extract JSON even if the model adds surrounding text
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return {"verdict": "no", "confidence": 0.0, "reason": "model returned no JSON"}

        result  = json.loads(raw[start:end])
        verdict = str(result.get("verdict", "no")).lower().strip()

        return {
            "verdict":    "yes" if verdict in ("yes", "partial") else "no",
            "confidence": float(result.get("confidence", 0.0)),
            "reason":     str(result.get("reason", "")),
        }

    except requests.exceptions.ConnectionError:
        # Ollama not running — degrade gracefully instead of crashing
        return {
            "verdict":    "no",
            "confidence": 0.0,
            "reason":     "Ollama not running. Start it with: ollama serve",
        }
    except json.JSONDecodeError as e:
        return {"verdict": "no", "confidence": 0.0, "reason": f"JSON parse error: {e}"}
    except Exception as e:
        return {"verdict": "no", "confidence": 0.0, "reason": str(e)}


def check_ollama():
    """Call this at startup to verify Ollama is reachable and the model is pulled."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        if not models:
            print("WARNING: Ollama is running but no models are installed.")
            print(f"  Run: ollama pull {OLLAMA_MODEL}")
            return False
        if not any(OLLAMA_MODEL.split(":")[0] in m for m in models):
            print(f"WARNING: Model '{OLLAMA_MODEL}' not found.")
            print(f"  Installed models: {models}")
            print(f"  Run: ollama pull {OLLAMA_MODEL}")
            return False
        print(f"  Ollama OK — using model: {OLLAMA_MODEL}")
        return True
    except requests.exceptions.ConnectionError:
        print("ERROR: Ollama is not running.")
        print("  Install from: https://ollama.com/download")
        print(f"  Then run:     ollama pull {OLLAMA_MODEL}")
        return False