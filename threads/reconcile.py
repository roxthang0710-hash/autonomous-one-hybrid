"""Reconcile Metricool-scheduled text posts using verified official Meta posts.

No posted status is claimed from a Metricool 'PENDING' flag; only actual
Threads API media IDs are evidence. Never modify a post if matches are
ambiguous, changed, inaccessible or too far from the planned time.
"""
from datetime import datetime, timedelta, timezone

from agent import Database
from threads.credentials import load_credentials, verify_identity
from threads.publisher import thread_request


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
        # Official Threads published media IDs are numeric. Never use a
        # temporary container ID, malformed feed row, or a shared match.
        if not mid.isdecimal() or mid in used:
            continue
        used.add(mid)
        match_rows.append({
            "id": draft["id"],
            "platform_post_id": mid,
            "permalink": entry.get("permalink") or None,
            "published_at": when.astimezone(timezone.utc).isoformat(),
        })
    return match_rows


def reconcile(db=None, *, now=None, read=thread_request):
    """Read-only Meta verification; writes ONLY evidence to our own database.

    Crucially, this must not activate a publishing channel, which the old
    authenticate() helper could do while supposedly reconciling results.
    """
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    credentials = load_credentials(db, refresh=False)
    if credentials is None:
        return "waiting_for_owner_meta_oauth"
    token, expected = credentials
    try:
        username, uid = verify_identity(token, expected, read=read)
    except (ValueError, TypeError, KeyError):
        return "meta_identity_unavailable"
    if username != "dohay_dilam" or not uid:
        return "meta_identity_mismatch"
    drafts = db.request("GET", "/threads_posts", params={
        "select": "id,scheduled_at,text_content",
        "status": "eq.scheduled_external",
        "scheduled_at": "lte." + (now-timedelta(minutes=2)).isoformat(),
        "order": "scheduled_at.desc", "limit": "50",
    })
    if not isinstance(drafts, list):
        return "scheduled_ledger_unavailable"
    if not drafts:
        return "no_due_metricool_posts"
    result = read("GET", "/me/threads", token, params={
        "fields": "id,text,timestamp,permalink", "limit": "60",
    })
    meta_rows = result.get("data") if isinstance(result, dict) else None
    if not isinstance(meta_rows, list):
        return "meta_listing_unavailable"
    confirmed = 0
    for matched in find_matches(drafts, meta_rows):
        updated = db.request("PATCH", "/threads_posts", params={
            "id": "eq." + str(matched["id"]), "status": "eq.scheduled_external",
            "platform_post_id": "is.null",
        }, payload={
            "status": "posted", "platform_post_id": matched["platform_post_id"],
            "permalink": matched["permalink"], "published_at": matched["published_at"],
            "updated_at": now.isoformat(),
        }, prefer="return=representation")
        if not isinstance(updated, list) or len(updated) != 1:
            # An ambiguous/overlapping writer may already have changed it.
            # Never guess from a 2xx response and never send a Meta POST.
            continue
        readback = db.request("GET", "/threads_posts", params={
            "select": "id,status,platform_post_id,permalink,published_at",
            "id": "eq." + str(matched["id"]), "limit": "1",
        })
        if (not isinstance(readback, list) or len(readback) != 1 or
            readback[0].get("status") != "posted" or
            str(readback[0].get("platform_post_id")) != matched["platform_post_id"] or
            not readback[0].get("published_at")):
            # The local write outcome is uncertain; fail closed rather than
            # claiming a confirmed publication.
            return "meta_match_write_unverified"
        confirmed += 1
    return "confirmed_metricool_posts:" + str(confirmed)


if __name__ == "__main__":
    print("Threads reconciliation:", reconcile())
