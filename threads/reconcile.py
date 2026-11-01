"""Reconcile Metricool-scheduled text posts using verified official Meta posts.

No posted status is claimed from a Metricool 'PENDING' flag; only actual
Threads API media IDs are evidence. Never modify a post if matches are
ambiguous, changed, inaccessible or too far from the planned time.
"""
from datetime import datetime, timedelta, timezone

from agent import Database
from threads.credentials import load_credentials
from threads.publisher import authenticate, thread_request


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return ts if ts.tzinfo else None
    except (ValueError, OverflowError):
        return None


def find_matches(drafts, meta_rows):
    """Returns only exact unique text matches near scheduled publication."""
    match_rows = []
    used = set()
    for draft in drafts:
        planned = _parse_date(draft.get("scheduled_at"))
        text = draft.get("text_content")
        if not planned or not isinstance(text, str):
            continue
        matches = []
        for meta in meta_rows:
            when = _parse_date(meta.get("timestamp"))
            if (meta.get("text") == text and when is not None
                    and abs((when - planned).total_seconds()) <= 36*3600
                    and meta.get("id")):
                matches.append((meta,when))
        if len(matches) != 1:
            continue
        entry, when = matches[0]
        mid = str(entry["id"])
        if mid in used:
            continue
        used.add(mid)
        match_rows.append({
            "id": draft["id"],
            "platform_post_id": mid,
            "permalink": entry.get("permalink") or None,
            "published_at": when.astimezone(timezone.utc).isoformat(),
        })
    return match_rows


def reconcile(db=None, *, now=None):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    credentials = load_credentials(db, refresh=False)
    if credentials is None:
        return "waiting_for_owner_meta_oauth"
    token, expected = credentials
    authenticate(db, token, expected)
    drafts = db.request("GET", "/threads_posts", params={
        "select": "id,scheduled_at,text_content",
        "status": "eq.scheduled_external",
        "scheduled_at": "lte." + (now-timedelta(minutes=2)).isoformat(),
        "order": "scheduled_at.desc", "limit": "50",
    })
    if not drafts:
        return "no_due_metricool_posts"
    result = thread_request("GET", "/me/threads", token, params={
        "fields": "id,text,timestamp,permalink", "limit": "60",
    })
    meta_rows = result.get("data") if isinstance(result, dict) else None
    if not isinstance(meta_rows, list):
        return "meta_listing_unavailable"
    confirmed = 0
    for matched in find_matches(drafts, meta_rows):
        result = db.request("PATCH", "/threads_posts", params={
            "id": "eq." + matched["id"], "status": "eq.scheduled_external",
        }, payload={
            "status": "posted", "platform_post_id": matched["platform_post_id"],
            "permalink": matched["permalink"], "published_at": matched["published_at"],
            "updated_at": now.isoformat(),
        }, prefer="return=representation")
        confirmed += len(result)
    return "confirmed_metricool_posts:" + str(confirmed)


if __name__ == "__main__":
    print("Threads reconciliation:", reconcile())
