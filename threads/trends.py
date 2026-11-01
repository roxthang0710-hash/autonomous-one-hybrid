"""Only use timely, attributed growth research for near-term editorial posts.

Source headlines are *topic prompts*, not verified product specifications.
No links or third-party text are copied into the final public post.
"""
from datetime import datetime, timedelta, timezone

ALLOWED = ("work", "travel", "organize")
MAX_FUTURE = timedelta(hours=72)
MAX_AGE = timedelta(hours=72)


def select_topic(db, scheduled_at, *, now=None):
    now = now or datetime.now(timezone.utc)
    if scheduled_at.tzinfo is None:
        return None
    if not timedelta(0) <= scheduled_at - now <= MAX_FUTURE:
        # Never post last week's news on the other side of an old backlog.
        return None
    rows = db.request("GET", "/growth_opportunities", params={
        "select": "id,signal_id,quality_score,expires_at",
        "kind": "eq.trend_post",
        "status": "eq.needs_review",
        "quality_score": "gte.80",
        "expires_at": "gte." + now.isoformat(),
        "order": "created_at.desc",
        "limit": "12",
    })
    for row in rows:
        try:
            expiry = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError, TypeError):
            continue
        if expiry.tzinfo is None or expiry < scheduled_at:
            continue
        used = db.request("GET", "/threads_posts", params={
            "select": "id",
            "origin_growth_opportunity_id": "eq." + row["id"],
            "limit": "1",
        })
        if used:
            continue
        signals = db.request("GET", "/growth_signals", params={
            "select": "id,title,niche,state,published_at,risk_flags,"
                      "source_url,relevance_score",
            "id": "eq." + row["signal_id"], "limit": "1",
        })
        if not signals:
            continue
        signal = signals[0]
        if (signal.get("state") != "candidate"
            or signal.get("niche") not in ALLOWED
            or signal.get("risk_flags") != []
            or (signal.get("relevance_score") or 0) < 65
            or not signal.get("published_at")):
            continue
        try:
            published = datetime.fromisoformat(
                signal["published_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if published.tzinfo is None or not timedelta(0) <= now - published <= MAX_AGE:
            continue
        if scheduled_at - published > MAX_AGE:
            continue
        return {
            "opportunity_id": row["id"],
            "pillar": signal["niche"],
            "topic": ("Thảo luận một ý tưởng hữu ích và luôn đúng đối với "
                      "người đi làm, liên quan đến chủ đề: " +
                      signal["title"][:190] + ". "
                      "Đây chỉ là tiêu đề nguồn, tuyệt đối không khẳng định "
                      "thông tin cụ thể là sự thật hoặc giả vờ đã dùng sản phẩm."),
        }
    return None
