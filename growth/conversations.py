"""Discover public Threads discussions via official keyword-search API.

NEVER publishes replies, likes, follows or creates personas. An explicit OAuth
search scope and owner switch are required even to discover external posts.
"""
import os
from datetime import datetime, timedelta, timezone
import requests
from growth.scoring import classify

API = "https://graph.threads.net/v1.0/keyword_search"
QUERIES = (
    "bàn làm việc", "đi công tác", "góc học tập", "laptop văn phòng",
    "deadline công sở", "phụ kiện đi làm", "sắp xếp góc làm việc",
    "đồ dùng công nghệ", "hành lý công tác", "học tập hiệu quả",
    "dây sạc", "bàn phím",
)


def can_search(token=None):
    # Explicit token argument comes from owner's OAuth Vault consent.
    # A literal 'false' environment override is an emergency stop.
    setting = os.getenv("THREADS_DISCOVERY_ENABLED", "").lower()
    if setting == "false":
        return False
    if token:
        return True
    return setting == "true" and bool(
        os.getenv("THREADS_DISCOVERY_ACCESS_TOKEN", "").strip())


def search_threads(*, query=None, fetch=requests.get, token=None,
                   search_type="RECENT", now=None):
    if not can_search(token):
        return [], "not_authorized"
    if query is None:
        query = QUERIES[0]
    if query not in QUERIES:
        return [], "disallowed_query"
    if search_type not in ("RECENT", "TOP"):
        return [], "invalid_search_type"
    now = now or datetime.now(timezone.utc)
    resp = fetch(
        API,
        headers={"Authorization": "Bearer " + (token or os.environ["THREADS_DISCOVERY_ACCESS_TOKEN"])},
        params={"q": query, "search_type": search_type,
                "fields": "id,text,username,permalink,timestamp", "limit": 12},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    items = []
    own_seen = 0
    foreign_seen = 0
    raw_items = (payload.get("data") or [])[:12]
    for data in raw_items:
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
        age = now - published
        if not timedelta(0) <= age <= timedelta(hours=24):
            continue
        if str(data.get("username") or "").casefold().lstrip("@") == "dohay_dilam":
            own_seen += 1
            continue
        foreign_seen += 1
        if classify(text, published, now=now)["state"] != "candidate":
            continue
        items.append({"id": post_id, "url": url,
                      "username": str(data.get("username") or "")[:80],
                      "title": text, "published_at": published})
    # OAuth may authorize the keyword scope while App Review still limits
    # search to the account's own posts. Do not call that public discovery.
    if own_seen and not foreign_seen:
        return items, "own_posts_only_possible_app_review"
    if not raw_items:
        return items, "empty_keyword_results"
    if not items:
        return items, "no_relevant_recent_public_posts"
    return items, "ok"
