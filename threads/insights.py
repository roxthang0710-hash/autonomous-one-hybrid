"""Read Meta Threads post insights, storing only genuine provider metrics."""
import json
from datetime import datetime, timezone

import requests

from agent import Database
from threads.content import get_channel
from threads.publisher import access, authenticate, thread_request

METRICS = ("views", "likes", "replies", "reposts", "quotes")


def parse_insights(payload):
    """Meta may not return every metric; unknown != zero."""
    result = {}
    items = payload.get("data")
    if not isinstance(items, list):
        raise ValueError("Missing Meta metrics collection")
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("name")
        if key not in METRICS:
            continue
        values = item.get("values", [])
        val = (values[0].get("value") if isinstance(values, list)
               and values and isinstance(values[0], dict) else None)
        # API may omit experimental metrics. Never invent missing values.
        if type(val) is int and val >= 0:
            result[key] = val
    return result


def collect(db, max_posts=10):
    """Requires OAuth token and official insights scope; no fake analytics."""
    credential = access()
    if credential is None:
        return "waiting_for_owner_oauth_and_enable_switch"
    token, expected = credential
    authenticate(db, token, expected)
    channel = get_channel(db)
    posted = db.request("GET", "/threads_posts", params={
        "select": "id,platform_post_id",
        "channel_id": "eq." + channel["id"],
        "status": "eq.posted",
        "order": "published_at.desc", "limit": str(min(10, max(1, max_posts))),
    })
    if not posted:
        return "no_published_posts"
    written = 0
    for post in posted:
        try:
            data = thread_request("GET", "/" + post["platform_post_id"] + "/insights",
                                  token, params={"metric": ",".join(METRICS)})
            observed = parse_insights(data)
            # Partial data is not a zero; skip until a supported metric exists.
            if not observed:
                continue
            row = {"post_id": post["id"],
                   "collected_at": datetime.now(timezone.utc).isoformat(),
                   **observed}
            # Unreturned metrics cannot be represented as 0 without misleading
            # consumers. For now require full coverage before storing snapshot.
            if set(observed) != set(METRICS):
                continue
            db.insert("threads_metrics", row)
            written += 1
        except (requests.RequestException, ValueError):
            # Missing Meta insights scope or unavailable metric: remain accurate.
            continue
    return "snapshots_saved:" + str(written)


if __name__ == "__main__":
    print("Threads insights:", collect(Database()))
