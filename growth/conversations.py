"""Discover public Threads discussions via official keyword-search API.

NEVER publishes replies, likes, follows or creates personas. An explicit OAuth
search scope and owner switch are required even to discover external posts.
"""
import os
from datetime import datetime, timedelta, timezone
import requests
from growth.scoring import classify

API = "https://graph.threads.net/v1.0/keyword_search"
QUERIES = ("bàn làm việc", "đi công tác", "sắp xếp góc làm việc")


def can_search(token=None):
    return (os.getenv("THREADS_DISCOVERY_ENABLED", "").lower() == "true"
            and bool(token or os.getenv("THREADS_DISCOVERY_ACCESS_TOKEN", "").strip()))


def search_threads(*, query=None, fetch=requests.get, token=None):
    if not can_search(token):
        return [], "not_authorized"
    if query is None:
        query = QUERIES[0]
    if query not in QUERIES:
        return [], "disallowed_query"
    resp = fetch(
        API,
        headers={"Authorization": "Bearer " + (token or os.environ["THREADS_DISCOVERY_ACCESS_TOKEN"])},
        params={"q": query, "search_type": "RECENT",
                "fields": "id,text,username,permalink,timestamp", "limit": 12},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    items = []
    for data in (payload.get("data") or [])[:12]:
        if not isinstance(data, dict):
            continue
        text = str(data.get("text") or "")[:350]
        post_id = str(data.get("id") or "")
        url = str(data.get("permalink") or "")
        if not post_id or not url.startswith(("https://www.threads.net/",
                                             "https://www.threads.com/")):
            continue
        # Replies to trending discussions must be timely. Meta timestamp is
        # ISO-8601 with a numeric offset (often +0000), or Z.
        try:
            raw_time = str(data.get("timestamp") or "").replace("Z", "+00:00")
            published = datetime.fromisoformat(raw_time).astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue
        age = datetime.now(timezone.utc) - published
        if not timedelta(0) <= age <= timedelta(hours=24):
            continue
        if classify(text, published)["state"] != "candidate":
            continue
        items.append({"id": post_id, "url": url,
                      "username": str(data.get("username") or "")[:80],
                      "title": text, "published_at": published})
    return items, "ok"
