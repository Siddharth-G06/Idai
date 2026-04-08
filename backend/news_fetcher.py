"""
news_fetcher.py — Vaakazhipeer

Fixes:
  1. RSS summary used as body fallback (was storing empty bodies)
  2. Timeout on Article.download()
  3. Existing articles with 'unknown' period retroactively tagged 'current'
  4. NewsAPI support for historical articles (optional, needs NEWSAPI_KEY in .env)
"""

import json, re, os, time
from pathlib import Path
from datetime import datetime, timezone

import feedparser
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "news_articles.json"

RSS_FEEDS = [
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-south-india",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://indianexpress.com/section/india/tamil-nadu/feed/",
    "https://www.newindianexpress.com/states/tamil-nadu/rss.xml",
]

NEWSAPI_QUERIES = [
    ("Tamil Nadu AIADMK government scheme Jayalalithaa Palaniswami",
     "2016-05-23", "2021-05-06", "aiadmk_rule"),
    ("Tamil Nadu free housing gas stove welfare policy AIADMK",
     "2016-05-23", "2021-05-06", "aiadmk_rule"),
    ("Tamil Nadu DMK government Stalin scheme welfare 2021 2022 2023",
     "2021-05-07", "2026-04-01", "dmk_rule"),
    ("Tamil Nadu free breakfast school health insurance DMK",
     "2021-05-07", "2026-04-01", "dmk_rule"),
    ("AIADMK opposition protest Tamil Nadu legislature 2022 2023",
     "2022-01-01", "2026-04-01", "opposition"),
    ("DMK opposition Tamil Nadu assembly 2017 2018 2019 2020",
     "2017-01-01", "2021-05-06", "opposition"),
]

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


def fetch_body_safe(url, timeout=10):
    try:
        from newspaper import Article
        art = Article(url, request_timeout=timeout)
        art.download()
        art.parse()
        body = art.text.strip()
        if len(body) > 100:
            return body
    except Exception:
        pass
    return ""


def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def load_existing():
    if not OUTPUT_PATH.exists():
        return [], set()
    data = json.load(open(OUTPUT_PATH, encoding="utf-8"))
    # Fix: retroactively tag 'unknown' period as 'current'
    fixed = 0
    for a in data:
        if a.get("period", "unknown") == "unknown":
            a["period"] = "current"
            fixed += 1
    if fixed:
        print(f"  Fixed {fixed} articles with unknown period → 'current'")
    seen = {a["url"] for a in data}
    return data, seen


def fetch_rss(seen):
    new_articles = []
    for feed_url in RSS_FEEDS:
        print(f"  RSS: {feed_url[:65]}")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"    error: {e}"); continue
        for entry in feed.entries:
            url = entry.get("link", "")
            if not url or url in seen:
                continue
            title   = clean(entry.get("title", ""))
            summary = clean(entry.get("summary", ""))
            body    = fetch_body_safe(url)
            if not body:
                body = summary   # FIX: use summary not empty string
            if not body and not title:
                continue
            new_articles.append({
                "title":      title,
                "body":       body,
                "url":        url,
                "published":  entry.get("published", ""),
                "source":     feed.feed.get("title", ""),
                "period":     "current",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
            seen.add(url)
    return new_articles


def fetch_newsapi(seen):
    if not NEWSAPI_KEY:
        print("\n  [NewsAPI] No NEWSAPI_KEY — skipping historical articles.")
        print("  Add NEWSAPI_KEY=your_key to .env for historical promise verification.\n")
        return []
    import requests
    new_articles = []
    for query, from_date, to_date, period in NEWSAPI_QUERIES:
        print(f"  [NewsAPI] {query[:55]} [{from_date}→{to_date}]")
        try:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "from": from_date, "to": to_date,
                        "language": "en", "sortBy": "relevancy",
                        "pageSize": 100, "apiKey": NEWSAPI_KEY},
                timeout=15,
            )
            data = r.json()
        except Exception as e:
            print(f"    error: {e}"); continue
        if data.get("status") != "ok":
            print(f"    API error: {data.get('message')}"); continue
        for art in data.get("articles", []):
            url = art.get("url", "")
            if not url or url in seen:
                continue
            title = clean(art.get("title", ""))
            body  = clean(art.get("content") or art.get("description") or "")
            if not body and not title:
                continue
            new_articles.append({
                "title": title, "body": body, "url": url,
                "published": art.get("publishedAt", ""),
                "source": art.get("source", {}).get("name", ""),
                "period": period,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
            seen.add(url)
        time.sleep(0.5)
    return new_articles


def run():
    print("\n=== News Fetcher ===")
    existing, seen = load_existing()
    rss_new  = fetch_rss(seen)
    api_new  = fetch_newsapi(seen)
    combined = existing + rss_new + api_new

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(combined, open(OUTPUT_PATH, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    by_period = {}
    for a in combined:
        p = a.get("period", "unknown")
        by_period[p] = by_period.get(p, 0) + 1

    print(f"\n  RSS new:      {len(rss_new)}")
    print(f"  NewsAPI new:  {len(api_new)}")
    print(f"  Total corpus: {len(combined)}")
    for period, n in sorted(by_period.items()):
        print(f"    {period:<22} {n}")


if __name__ == "__main__":
    run()