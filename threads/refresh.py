"""Just-in-time trend overlay for TOMORROW's already queued editorial slot.

Keeps a stable evergreen backlog but replaces at most two queued posts per
rolling week with fresh, well-sourced, on-niche topics. Never modifies external
Metricool or already-published posts. Does not publish itself.
"""
import hashlib
from datetime import datetime, timedelta, timezone

from threads.brand import BRAND_KEY
from threads.content import get_channel, generate_ai_post
from threads.planner import check_post
from threads.trends import select_topic

MAX_TREND_POSTS_WEEK = 2


def refresh_next(db, now=None):
    now = now or datetime.now(timezone.utc)
    channel = get_channel(db)
    if channel.get("status") != "connected" or not channel.get("authorized"):
        return "awaiting_owner_meta_oauth"
    week_start = now - timedelta(days=7)
    recent = db.request("GET", "/threads_posts", params={
        "select": "id",
        "channel_id": "eq." + channel["id"],
        "origin_growth_opportunity_id": "not.is.null",
        "updated_at": "gte." + week_start.isoformat(),
        "limit": str(MAX_TREND_POSTS_WEEK),
    })
    if len(recent) >= MAX_TREND_POSTS_WEEK:
        return "weekly_trend_limit"
    # Only tomorrow's post, not today (that may be due any minute).
    upcoming = db.request("GET", "/threads_posts", params={
        "select": "id,scheduled_at,text_content,origin_growth_opportunity_id",
        "channel_id": "eq." + channel["id"], "status": "eq.queued",
        "scheduled_at": "gt." + (now + timedelta(hours=18)).isoformat(),
        "order": "scheduled_at.asc", "limit": "1",
    })
    if not upcoming:
        return "no_upcoming_queued_post"
    selected = upcoming[0]
    if selected.get("origin_growth_opportunity_id"):
        return "already_topical"
    planned_at = datetime.fromisoformat(
        selected["scheduled_at"].replace("Z", "+00:00"))
    if planned_at - now > timedelta(hours=42):
        return "not_yet_near_publication"
    source = select_topic(db, planned_at, now=now)
    if not source:
        return "no_fresh_trend"
    # The sourced headline is only inspiration; Groq must produce original,
    # timeless-useful advice with no unsupported factual claims.
    result = generate_ai_post(
        source["pillar"], source["topic"], previous_texts=[selected["text_content"]])
    body = result["post_text"]
    if check_post(body):
        return "new_draft_failed_quality_gate"
    digest = hashlib.sha256(
        (BRAND_KEY + "\n" + body).encode("utf-8")).hexdigest()
    rows = db.request("PATCH", "/threads_posts", params={
        "id": "eq." + selected["id"], "status": "eq.queued",
        "origin_growth_opportunity_id": "is.null",
    }, payload={
        "text_content": body,
        "content_key": digest,
        "pillar": result["pillar"],
        "origin_growth_opportunity_id": source["opportunity_id"],
        "updated_at": now.isoformat(),
    }, prefer="return=representation")
    return "trend_applied_to_tomorrow" if rows else "post_changed_concurrently"


if __name__ == "__main__":
    from agent import Database
    print("Threads near-term trends:", refresh_next(Database()))
