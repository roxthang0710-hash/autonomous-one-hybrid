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
from growth.voice import suitable_reply
from growth.scoring import normalize
from growth.scoring import classify
from threads.publisher import thread_request

EXPECTED = "dohay_dilam"
MAX_DAILY_ATTEMPTS = 3  # Atomically enforced by SQL in VN local time.


def get_credentials(db=None):
    # Owner's OAuth portal checkbox is the affirmative permission switch.
    # GitHub requires no additional secrets; explicit environment 'false'
    # can stop engagement immediately as an emergency override.
    if db is None or os.getenv("THREADS_AUTO_ENGAGE_ENABLED", "").lower() == "false":
        return None
    rows = db.request("POST", "/rpc/threads_read_vault_token",
                      payload={"p_brand_key": "do_hay_di_lam"})
    if not rows or rows[0].get("enable_replies") is not True or \
       rows[0].get("verified_username") != EXPECTED:
        return None
    from threads.credentials import load_credentials
    return load_credentials(db, refresh=False)


def eligible(row, now=None):
    """Only a fresh, specific, benign, non-commercial original response."""
    now = now or datetime.now(timezone.utc)
    if row.get("kind") != "reply_suggestion" or row.get("status") != "needs_review":
        return False
    if row.get("source") != "threads_keyword_api":
        return False
    if row.get("risk_flags") not in ([], "[]"):
        return False
    if (row.get("quality_score") or 0) < 75 or (row.get("relevance_score") or 0) < 60:
        return False
    if not row.get("target_post_id") or not str(row.get("target_post_url") or "").startswith(
        ("https://www.threads.net/", "https://www.threads.com/", "https://threads.net/", "https://threads.com/")
    ):
        return False
    if not row.get("target_published_at"):
        return False
    try:
        original_at = datetime.fromisoformat(
            row["target_published_at"].replace("Z", "+00:00")
        )
        if original_at.tzinfo is None or not timedelta(0) <= now - original_at <= timedelta(hours=24):
            return False
    except (ValueError, TypeError):
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
    db = db or Database()
    creds = get_credentials(db)
    if not creds:
        return "not_authorized"
    now = now or datetime.now(timezone.utc)
    # Database RPC owns the three/day Vietnam-time cap and author cooldown.
    # Multiple workflows cannot race to publish extra comments.
    token, expected = creds
    verify_meta_account(token, expected)
    candidates = db.request("GET", "/growth_engagement_queue", params={
        "select": "opportunity_id,status,kind,draft_text,quality_score,"
                  "target_post_id,target_post_url,expires_at,relevance_score,"
                  "risk_flags,source,niche,original_post_text,target_published_at",
        "status": "eq.needs_review", "order": "quality_score.desc", "limit": "15",
    })
    picked = next((row for row in candidates if eligible(row, now)), None)
    if not picked:
        return "no_eligible_replies"
    # Re-read the real target post through Meta before sending: no deleted,
    # inaccessible, changed-topic or newly-sensitive posts.
    target = thread_request("GET", "/" + picked["target_post_id"], token,
        params={"fields": "id,text,username"})
    current_text = target.get("text") or ""
    original_text = picked.get("original_post_text") or ""
    if str(target.get("id") or "") != str(picked["target_post_id"]) or \
       classify(current_text, now=now)["state"] != "candidate":
        return "target_changed_or_not_safe"
    # Refuse edited/bait-and-switch public posts after drafting.
    normalized_original = normalize(original_text)
    if not normalized_original or not normalize(current_text).startswith(
            normalized_original[:min(80, len(normalized_original))]):
        return "target_changed_or_not_safe"
    prior = db.request("GET", "/growth_engagement_attempts", params={
        "select": "opportunity_id", "order": "attempted_at.desc", "limit": "15",
    })
    prior_texts = []
    if prior:
        ids = [str(x.get("opportunity_id") or "") for x in prior if x.get("opportunity_id")]
        if ids:
            previous = db.request("GET", "/growth_opportunities", params={
                "select": "draft_text", "id": "in.(" + ",".join(ids) + ")",
                "limit": "15",
            })
            prior_texts = [x["draft_text"] for x in previous
                           if isinstance(x.get("draft_text"), str)]
    if not suitable_reply(picked["draft_text"], current_text, prior_texts):
        return "context_or_originality_gate_failed"
    # Atomic service-role-only RPC verifies owner OAuth, three/day,
    # original target and per-author cooldown. No claim = no Meta POST.
    claimed = db.request("POST", "/rpc/growth_claim_safe_reply",
        payload={"p_opportunity_id": picked["opportunity_id"],
                 "p_target_post_id": picked["target_post_id"]})
    if not claimed:
        return "safety_claim_rejected"
    attempt_id = claimed[0]["attempt_id"]
    try:
        container, reply = send_reply(
            token, picked["target_post_id"], picked["draft_text"])
        db.patch("growth_engagement_attempts", attempt_id, {
            "status": "posted", "meta_container_id": container,
            "meta_reply_id": reply, "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        db.patch("growth_opportunities", picked["opportunity_id"], {
            "status": "approved",
        })
        return "one_useful_reply_posted"
    except Exception as exc:
        # A timed-out Meta write may have posted. Never silently repeat.
        db.patch("growth_engagement_attempts", attempt_id, {
            "status": "uncertain", "error_kind": type(exc).__name__[:60],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        raise RuntimeError("Reply requires reconciliation: " + type(exc).__name__) from None


if __name__ == "__main__":
    print("Growth engagement:", run())
