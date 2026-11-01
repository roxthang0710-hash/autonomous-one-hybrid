"""Strictly opt-in, single-account, useful Threads replies through official API.

No fake persona, purchased engagement, unsolicited mass posting, or retrying
ambiguous writes. The publish switch and Meta OAuth scopes must be provided
by the legitimate account owner. Default = disabled.
"""
import os
import re
from datetime import datetime, timedelta, timezone

from agent import Database
from growth.generator import validate_draft
from growth.scoring import classify
from threads.publisher import thread_request

EXPECTED = "dohay_dilam"
MAX_DAILY_ATTEMPTS = 1


def get_credentials():
    if os.getenv("THREADS_AUTO_ENGAGE_ENABLED", "").lower() != "true":
        return None
    token = os.getenv("THREADS_ENGAGE_ACCESS_TOKEN", "").strip()
    expected = os.getenv("THREADS_EXPECTED_USERNAME", "").strip().lstrip("@").casefold()
    if not token or expected != EXPECTED:
        return None
    return token, expected


def eligible(row, now=None):
    """Only a fresh, specific, benign, non-commercial original response."""
    now = now or datetime.now(timezone.utc)
    if row.get("kind") != "reply_suggestion" or row.get("status") != "needs_review":
        return False
    if row.get("source") != "threads_keyword_api":
        return False
    if row.get("risk_flags") not in ([], "[]"):
        return False
    if (row.get("quality_score") or 0) < 85 or (row.get("relevance_score") or 0) < 65:
        return False
    if not row.get("target_post_id") or not str(row.get("target_post_url") or "").startswith(
        ("https://www.threads.net/", "https://www.threads.com/", "https://threads.net/", "https://threads.com/")
    ):
        return False
    if not row.get("expires_at"):
        return False
    due = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if due.tzinfo is None or due <= now or due > now + timedelta(hours=73):
        return False
    text = row.get("draft_text") or ""
    if len(text) > 380 or not 60 <= len(text):
        return False
    if re.search(r"https?://|www\.|shopee|affiliate|hoa hồng|mua ngay|"
                 r"theo dõi kênh|nhắn tin riêng|giảm giá|link bio", text, re.I):
        return False
    if classify(text, now=now)["risk_flags"]:
        return False
    return True


def verify_meta_account(token, expected):
    profile = thread_request("GET", "/me", token,
        params={"fields": "id,username"})
    if str(profile.get("username") or "").casefold() != expected or \
       not str(profile.get("id") or ""):
        raise ValueError("Meta OAuth identity mismatch")


def send_reply(token, target_id, text):
    """Official Meta 2-step workflow. No automatic retries."""
    container = thread_request("POST", "/me/threads", token,
        data={"media_type": "TEXT", "text": text, "reply_to_id": target_id})
    container_id = str(container.get("id") or "")
    if not container_id:
        raise ValueError("Meta reply container missing")
    posted = thread_request("POST", "/me/threads_publish", token,
        data={"creation_id": container_id})
    reply_id = str(posted.get("id") or "")
    if not reply_id:
        raise ValueError("Meta published reply missing")
    return container_id, reply_id


def run(db=None, now=None):
    creds = get_credentials()
    if not creds:
        return "not_authorized"
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    attempts = db.request("GET", "/growth_engagement_attempts", params={
        "select": "id",
        "attempted_at": "gte." + now.strftime("%Y-%m-%dT00:00:00+00:00"),
        "limit": str(MAX_DAILY_ATTEMPTS),
    })
    if len(attempts) >= MAX_DAILY_ATTEMPTS:
        return "daily_cap"
    token, expected = creds
    verify_meta_account(token, expected)
    candidates = db.request("GET", "/growth_engagement_queue", params={
        "select": "opportunity_id,status,kind,draft_text,quality_score,"
                  "target_post_id,target_post_url,expires_at,relevance_score,"
                  "risk_flags,source,niche,original_post_text",
        "status": "eq.needs_review", "order": "quality_score.desc", "limit": "15",
    })
    picked = next((row for row in candidates if eligible(row, now)), None)
    if not picked:
        return "no_eligible_replies"
    # Re-read the real target post through Meta before sending: no deleted,
    # inaccessible, changed-topic or newly-sensitive posts.
    target = thread_request("GET", "/" + picked["target_post_id"], token,
        params={"fields": "id,text,username"})
    if str(target.get("id") or "") != str(picked["target_post_id"]) or \
       classify(target.get("text") or "", now=now)["state"] != "candidate":
        return "target_changed_or_not_safe"
    # Unique target and unique opportunity prevent coordinated engagement.
    claimed = db.request("POST", "/growth_engagement_attempts",
        params={"on_conflict": "opportunity_id"},
        payload={"opportunity_id": picked["opportunity_id"],
                 "target_post_id": picked["target_post_id"]},
        prefer="resolution=ignore-duplicates,return=representation")
    if not claimed:
        return "already_attempted"
    attempt = claimed[0]
    try:
        container, reply = send_reply(
            token, picked["target_post_id"], picked["draft_text"])
        db.patch("growth_engagement_attempts", attempt["id"], {
            "status": "posted", "meta_container_id": container,
            "meta_reply_id": reply, "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        db.patch("growth_opportunities", picked["opportunity_id"], {
            "status": "approved",
        })
        return "one_useful_reply_posted"
    except Exception as exc:
        # A timed-out Meta write may have posted. Never silently repeat.
        db.patch("growth_engagement_attempts", attempt["id"], {
            "status": "uncertain", "error_kind": type(exc).__name__[:60],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        raise RuntimeError("Reply requires reconciliation: " + type(exc).__name__) from None


if __name__ == "__main__":
    print("Growth engagement:", run())
