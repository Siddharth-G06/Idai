"""
news_fetcher.py
Fetches Tamil Nadu political news from RSS feeds and NewsAPI.
Appends new articles to /data/news_articles.json, deduplicating by URL.

Usage:
    python news_fetcher.py
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

NEWSAPI_KEY  = os.getenv("NEWSAPI_KEY", "")
OUTPUT_PATH  = Path("../data/news_articles.json")

RSS_FEEDS = [
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-south-india",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
]

NEWSAPI_QUERIES = [
    "DMK Tamil Nadu",
    "ADMK Tamil Nadu",
    "Stalin government Tamil Nadu",
    "Edappadi Palaniswami",
    "Tamil Nadu government scheme",
    "Tamil Nadu policy 2024",
]

NEWSAPI_FROM_DATE = "2016-01-01"   # Full coverage window


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_existing(path: Path) -> tuple[list[dict], set[str]]:
    """Loads existing articles and returns (list, seen_urls set)."""
    if not path.exists():
        return [], set()
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    seen = {a["url"] for a in articles if a.get("url")}
    return articles, seen


def save_articles(articles: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def make_article(title: str, body: str, url: str,
                 published: str, source: str) -> dict:
    return {
        "title":     title.strip(),
        "body":      body.strip(),
        "url":       url.strip(),
        "published": published,
        "source":    source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

def fetch_rss(seen_urls: set[str]) -> list[dict]:
    new_articles = []

    for feed_url in RSS_FEEDS:
        print(f"  RSS: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                url = entry.get("link", "").strip()
                if not url or url in seen_urls:
                    continue

                title     = entry.get("title", "")
                body      = entry.get("summary", entry.get("description", ""))
                published = entry.get("published", "")

                # Clean HTML tags from body
                body = re.sub(r"<[^>]+>", " ", body) if body else ""
                body = re.sub(r"\s+", " ", body).strip()

                source = feed.feed.get("title", feed_url)
                new_articles.append(make_article(title, body, url, published, source))
                seen_urls.add(url)
                count += 1

            print(f"    → {count} new articles")
        except Exception as e:
            print(f"    ERROR: {e}")

    return new_articles


# ── NewsAPI Fetcher ───────────────────────────────────────────────────────────

def fetch_newsapi(seen_urls: set[str]) -> list[dict]:
    if not NEWSAPI_KEY:
        print("  NewsAPI: NEWSAPI_KEY not set in .env — skipping.")
        return []

    new_articles = []
    base_url = "https://newsapi.org/v2/everything"

    for query in NEWSAPI_QUERIES:
        print(f"  NewsAPI query: '{query}'")
        try:
            # NewsAPI free tier allows 100 results per query
            params = {
                "q":        query,
                "from":     NEWSAPI_FROM_DATE,
                "language": "en",
                "sortBy":   "relevancy",
                "pageSize": 100,
                "apiKey":   NEWSAPI_KEY,
            }
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for art in data.get("articles", []):
                url = art.get("url", "").strip()
                if not url or url in seen_urls:
                    continue
                # Skip removed articles
                if "[Removed]" in art.get("title", ""):
                    continue

                title     = art.get("title", "")
                body      = art.get("description", "") or art.get("content", "")
                published = art.get("publishedAt", "")
                source    = art.get("source", {}).get("name", "NewsAPI")

                new_articles.append(make_article(title, body, url, published, source))
                seen_urls.add(url)
                count += 1

            print(f"    → {count} new articles")
            time.sleep(0.3)   # Be gentle to the API

        except requests.RequestException as e:
            print(f"    ERROR: {e}")

    return new_articles


# ── Main ──────────────────────────────────────────────────────────────────────

import re   # needed for RSS HTML stripping above

def run() -> None:
    print(f"\n{'='*55}")
    print(f"  Vaakazhipeer — News Fetcher")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    existing, seen_urls = load_existing(OUTPUT_PATH)
    print(f"  Existing articles: {len(existing)}\n")

    print("[1/2] Fetching RSS feeds...")
    rss_articles = fetch_rss(seen_urls)

    print(f"\n[2/2] Fetching NewsAPI...")
    api_articles = fetch_newsapi(seen_urls)

    all_new = rss_articles + api_articles
    combined = existing + all_new

    save_articles(combined, OUTPUT_PATH)

    print(f"\n  Fetch complete.")
    print(f"  New articles added : {len(all_new)}")
    print(f"  Total in database  : {len(combined)}")
    print(f"  Saved to           : {OUTPUT_PATH}\n")


if __name__ == "__main__":
    run()