"""Official Meta Threads API publisher; off until OAuth and explicit owner activation.

Two-step text publishing; any ambiguous response stays 'uncertain' and is NOT retried.
No login scraping, OTP automation, mock profiles, affiliate links or group spam.
"""
import json
import os
import re

import requests

from agent import Database
from threads.brand import BRAND_KEY
from threads.content import get_channel
from threads.planner import check_post

API = "https://graph.threads.net/v1.0"
TIMEOUT = 20

# Meta native topic_tag is not a hashtag embedded in text.
# Only directly published Enna posts use it; Metricool has a separate queue.
# Native Threads Topic tagging uses the API's topic_tag parameter,
# not a visible text hashtag. Keep known vocabulary plus already-queued plans.
TOPIC_BY_PILLAR = {
    "work": "Công sở",
    "travel": "Du lịch",
    "organize": "Góc làm việc",
    "conversation": "Công sở",
}
ALLOWED_TOPIC_TAGS = frozenset({
    *TOPIC_BY_PILLAR.values(),
    "Đời sống đi làm", "Học tập", "Đồ dùng",
})


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


def do_publish(token, text, topic_tag=None, *, image_url=None, alt_text=None):
    """Use official Meta two-step flow for text or OWN original PNG image."""
    if check_post(text):
        raise ValueError("Text failed publishing safety gate")
    data = {"media_type": "TEXT", "text": text}
    if image_url is not None:
        if (not isinstance(image_url, str) or
            not re.fullmatch(
                r"https://gjdvdohylvsauphhkutw[.]supabase[.]co/storage/v1/object/public/enna-original-media/meme/original-[a-z0-9_-]+[.]png",
                image_url) or
            not isinstance(alt_text, str) or not 12 <= len(alt_text) <= 180):
            raise ValueError("Only own verified meme PNG assets are publishable")
        data.update({"media_type": "IMAGE", "image_url": image_url,
                     "alt_text": alt_text})
    elif alt_text is not None:
        raise ValueError("Alt text without an original image is invalid")
    if topic_tag is not None:
        if topic_tag not in ALLOWED_TOPIC_TAGS:
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
    media = post.get("media_url")
    if media:
        if not post.get("media_idea_id"):
            db.patch("threads_posts", post["id"], {"status": "blocked"})
            return "unverified_media_not_publishable"
        provenance = db.request("GET", "/enna_media_ideas", params={
            "select": "id,source_url,rights_status,source_provider,status,media_type",
            "id": "eq." + str(post["media_idea_id"]), "limit": "1",
        })
        if not isinstance(provenance, list) or not provenance or not (
            provenance[0].get("source_url") == media
            and provenance[0].get("rights_status") == "original"
            and provenance[0].get("source_provider") == "original"
            and provenance[0].get("media_type") == "original_meme"
            and provenance[0].get("status") in ("ready", "used")
        ):
            db.patch("threads_posts", post["id"], {"status": "blocked"})
            return "unverified_media_not_publishable"
    attempt = db.insert("threads_publish_attempts", {
        "post_id": post["id"], "operation": "publish_text", "outcome": "started",
    })
    try:
        topic_tag = post.get("topic_tag_planned") or TOPIC_BY_PILLAR.get(post.get("pillar"))
        if topic_tag is not None and topic_tag not in ALLOWED_TOPIC_TAGS:
            raise ValueError("Unknown planned native Threads topic")
        container_id, remote_id, link = do_publish(
            token, post["text_content"], topic_tag=topic_tag,
            image_url=media, alt_text=post.get("media_alt_text"))
        db.patch("threads_posts", post["id"], {
            "status": "posted", "platform_post_id": remote_id,
            "topic_tag_requested": topic_tag,
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
