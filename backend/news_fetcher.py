import json
import re
from pathlib import Path
from datetime import datetime, timezone

import feedparser
from newspaper import Article

OUTPUT_PATH = Path("../data/news_articles.json")

RSS_FEEDS = [
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-south-india",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://indianexpress.com/section/india/tamil-nadu/feed/",
    "https://www.newindianexpress.com/states/tamil-nadu/rss.xml",
]


def fetch_full_article(url):
    try:
        art = Article(url)
        art.download()
        art.parse()
        return art.text
    except:
        return ""


def load_existing():
    if not OUTPUT_PATH.exists():
        return [], set()
    data = json.load(open(OUTPUT_PATH, encoding="utf-8"))
    seen = {a["url"] for a in data}
    return data, seen


def run():
    print("\n=== News Fetcher ===")

    existing, seen = load_existing()
    new_articles = []

    for feed_url in RSS_FEEDS:
        print(f"  {feed_url}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            url = entry.get("link", "")
            if not url or url in seen:
                continue

            title = entry.get("title", "")
            published = entry.get("published", "")

            body = fetch_full_article(url)
            if not body:
                body = entry.get("summary", "")

            body = re.sub(r"\s+", " ", body)

            new_articles.append({
                "title": title,
                "body": body,
                "url": url,
                "published": published,
                "source": feed.feed.get("title", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            })

            seen.add(url)

    combined = existing + new_articles
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(combined, open(OUTPUT_PATH, "w", encoding="utf-8"), indent=2)

    print(f"Added {len(new_articles)} articles | Total {len(combined)}")