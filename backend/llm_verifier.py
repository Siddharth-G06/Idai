import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def verify_fulfillment(promise, articles):
    context = "\n\n".join(articles[:3])

    prompt = f"""
PROMISE:
{promise}

ARTICLES:
{context}

Has this promise been fulfilled?

Return JSON:
{{
  "verdict": "yes" or "no",
  "confidence": 0-1,
  "reason": "short explanation"
}}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return json.loads(res.choices[0].message.content)

    except Exception as e:
        return {"verdict": "no", "confidence": 0.0, "reason": str(e)}