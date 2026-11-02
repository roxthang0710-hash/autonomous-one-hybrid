"""Official Meta Threads API publisher; off until OAuth and explicit owner activation.

Two-step text publishing; any ambiguous response stays 'uncertain' and is NOT retried.
No login scraping, OTP automation, mock profiles, affiliate links or group spam.
"""
import json
import os

import requests

from agent import Database
from threads.brand import BRAND_KEY
from threads.content import get_channel
from threads.planner import check_post

API = "https://graph.threads.net/v1.0"
TIMEOUT = 20

# Meta native topic_tag is not a hashtag embedded in text.
# Only directly published Enna posts use it; Metricool has a separate queue.
TOPIC_BY_PILLAR = {
    "work": "Công sở",
    "travel": "Du lịch",
    "organize": "Góc làm việc",
    "conversation": "Đời sống đi làm",
}


def enabled():
    return os.getenv("THREADS_PUBLISH_ENABLED", "").lower() == "true"


def access():
    """Secret token and owner-confirmed username are required for any live call."""
    if not enabled():
        return None
    token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    expected = os.getenv("THREADS_EXPECTED_USERNAME", "").strip().lstrip("@").lower()
    if not token or not expected:
        return None
    return token, expected


def thread_request(method, path, token, *, params=None, data=None):
    """No automatic write retries: uncertain outcomes must not cause duplicate posts."""
    req = requests.get if method == "GET" else requests.post
    response = req(
        API + path,
        headers={"Authorization": "Bearer " + token},
        params=params if method == "GET" else None,
        data=data if method == "POST" else None,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Unexpected Meta API response")
    return result


def authenticate(db, token, expected):
    """Verify granted OAuth token belongs to the intended Threads account."""
    profile = thread_request("GET", "/me", token,
                             params={"fields": "id,username"})
    name = str(profile.get("username") or "").lower()
    uid = str(profile.get("id") or "")
    if not uid or name != expected:
        raise ValueError("OAuth token does not belong to expected Threads account")
    channel = get_channel(db)
    if channel["username"] and channel["username"].lower().lstrip("@") != expected:
        raise ValueError("Connected account differs from registered channel")
    # Connection is activated ONLY with both a working account token and owner
    # switch THREADS_PUBLISH_ENABLED=true. Social account was created externally.
    if not channel["auto_publish_enabled"] or channel["status"] != "connected":
        # DB transaction starts the editorial calendar NEXT local morning.
        # This avoids publishing stale/due posts when a brand-new account connects.
        db.request("POST", "/rpc/activate_threads_channel", payload={
            "p_brand_key": BRAND_KEY,
            "p_username": name,
            "p_platform_user_id": uid,
        })
    elif str(channel["platform_user_id"]) != uid:
        raise ValueError("Account ID unexpectedly changed")
    return channel


def do_publish(token, text, topic_tag=None):
    """Use official two-step text flow; returned id is the published post id."""
    if check_post(text):
        raise ValueError("Text failed publishing safety gate")
    data = {"media_type": "TEXT", "text": text}
    if topic_tag is not None:
        if topic_tag not in TOPIC_BY_PILLAR.values():
            raise ValueError("Unknown native topic tag")
        data["topic_tag"] = topic_tag
    container = thread_request(
        "POST", "/me/threads", token, data=data,
    )
    container_id = str(container.get("id") or "")
    if not container_id:
        raise ValueError("Missing Threads container id")
    published = thread_request(
        "POST", "/me/threads_publish", token,
        data={"creation_id": container_id},
    )
    post_id = str(published.get("id") or "")
    if not post_id:
        raise ValueError("Missing published Threads post id")
    try:
        media = thread_request("GET", "/" + post_id, token,
                               params={"fields": "id,permalink"})
        permalink = str(media.get("permalink") or "")
    except (requests.RequestException, ValueError):
        permalink = ""
    return container_id, post_id, permalink


def publish_due(db):
    """Publish maximum one due, vetted original post. Never auto retry unknown state."""
    # The token is encrypted at rest in Supabase and periodically refreshed.
    # THREADS_ACCESS_TOKEN (a static legacy secret) is never used by production.
    from threads.credentials import load_credentials
    credential = load_credentials(db)
    if credential is None:
        return "waiting_for_owner_oauth_and_enable_switch"
    token, expected = credential
    authenticate(db, token, expected)
    # Recovery only changes 'publishing' to 'uncertain' — never requeues.
    db.request("POST", "/rpc/mark_stale_threads_uncertain", payload={})
    posts = db.request("POST", "/rpc/claim_threads_post",
                       payload={"p_brand_key": BRAND_KEY})
    if not posts:
        return "no_due_post"
    post = posts[0]
    if post["content_type"] != "editorial" or check_post(post["text_content"]):
        db.patch("threads_posts", post["id"], {"status": "blocked"})
        return "post_blocked_by_policy"

    attempt = db.insert("threads_publish_attempts", {
        "post_id": post["id"], "operation": "publish_text", "outcome": "started",
    })
    try:
        topic_tag = TOPIC_BY_PILLAR.get(post.get("pillar"))
        container_id, remote_id, link = do_publish(
            token, post["text_content"], topic_tag=topic_tag)
        db.patch("threads_posts", post["id"], {
            "status": "posted", "platform_post_id": remote_id,
            "permalink": link or None,
            "published_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
        })
        db.patch("threads_publish_attempts", attempt["id"], {
            "outcome": "posted", "remote_container_id": container_id,
            "remote_post_id": remote_id,
        })
        return "published"
    except Exception as exc:
        # A timeout/5xx may occur AFTER Meta publishes. Never retry automatically.
        # Missing server reply is not proof of failure.
        db.patch("threads_posts", post["id"], {"status": "uncertain"})
        db.patch("threads_publish_attempts", attempt["id"], {
            "outcome": "uncertain", "error_kind": type(exc).__name__[:80],
        })
        raise RuntimeError("Publishing needs manual reconciliation: "
                           + type(exc).__name__) from None


if __name__ == "__main__":
    print("Threads publish outcome:", publish_due(Database()))
