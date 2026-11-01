"""Use a small number of official/public RSS feeds; no Threads screen scraping."""
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests

USER_AGENT = "AutonomousOneGrowth/1.7 (public RSS editorial research)"
SOURCES = (
    ("google_trends_vn", "https://trends.google.com/trending/rss?geo=VN"),
    ("google_news_vn", "https://news.google.com/rss/search?q="
        + quote('("bàn làm việc" OR "góc làm việc") when:3d') + "&hl=vi&gl=VN&ceid=VN:vi"),
    ("google_news_vn", "https://news.google.com/rss/search?q="
        + quote('("du lịch" OR "hành lý") when:3d') + "&hl=vi&gl=VN&ceid=VN:vi"),
    ("google_news_vn", "https://news.google.com/rss/search?q="
        + quote('("công sở" OR "đi làm") when:3d') + "&hl=vi&gl=VN&ceid=VN:vi"),
)
ALLOWED_DOMAINS = ("trends.google.com", "news.google.com")


def read_rss(content, source, *, limit=28):
    """Parse RSS titles/links; never trust feed text as instructions."""
    if len(content) > 900_000 or b"<!DOCTYPE" in content.upper():
        raise ValueError("Invalid or overly large RSS data")
    root = ET.fromstring(content)
    if root.tag != "rss":
        raise ValueError("Not an RSS 2.0 feed")
    items = []
    for item in root.findall("./channel/item")[:limit]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        if not 5 <= len(title) <= 350 or not url.startswith("https://"):
            continue
        published = None
        try:
            raw = item.findtext("pubDate")
            if raw:
                published = parsedate_to_datetime(raw).astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            published = None
        fingerprint = hashlib.sha256((source + "\n" + title.casefold()).encode()).hexdigest()
        items.append({
            "fingerprint": fingerprint, "source": source,
            "title": re.sub(r"\s+", " ", title), "source_url": url[:1000],
            "published_at": published,
        })
    return items


def discover(fetch=requests.get):
    all_items, states = [], {}
    seen = set()
    for source, url in SOURCES:
        try:
            response = fetch(url, headers={"User-Agent": USER_AGENT}, timeout=13)
            response.raise_for_status()
            rows = read_rss(response.content, source)
            states[url.split("?")[0]] = states.get(url.split("?")[0], 0) + len(rows)
            for row in rows:
                if row["fingerprint"] not in seen:
                    seen.add(row["fingerprint"])
                    all_items.append(row)
        except (requests.RequestException, ValueError, ET.ParseError) as exc:
            # Source failure is not a reason to invent trends.
            states[url.split("?")[0]] = type(exc).__name__
    return all_items[:75], states
