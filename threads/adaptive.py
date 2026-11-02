"""Enna adaptive organic publishing.

A check can end in SKIP. This is not a daily posting quota or a viral
content generator. Only an approved Meta account may receive a bounded
original extra, away from Metricool bookings. The database claim RPC is the
authoritative atomic gate; this planner never bypasses it.
"""
import hashlib
import os
from datetime import datetime, time, timedelta, timezone
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

from growth.scoring import normalize
from threads.brand import BRAND_KEY
from threads.content import get_channel, generate_ai_post
from threads.planner import SEEDS, check_post

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_DAY_TOTAL = 5             # safety ceiling, NOT a target
MIN_GAP_MINUTES = 90           # both previous and next planned posts
QUALITY_THRESHOLD = 80
METRICS_MIN_SAMPLES = 3


def _at(raw):
    if not raw:
        return None
    try:
        v = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return v.astimezone(timezone.utc) if v.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def _booking_time(row):
    return _at(row.get("published_at")) or _at(row.get("scheduled_at"))


def qualify(text, reason, previous=()):
    """Conservative editorial score; a score is never a virality prediction."""
    if check_post(text):
        return 0, "content_policy"
    if not isinstance(reason, str) or len(reason.strip()) < 25:
        return 0, "missing_editorial_value"
    t = text.strip()
    if any(k in t.casefold() for k in (
        "follow để", "theo dõi ngay", "tag bạn bè",
        "bấm theo dõi", "chia sẻ để nhận", "chuyện thật 100%",
        "mình vừa gặp chuyện", "công ty mình vừa", "(tình huống giả định)",
    )):
        return 0, "forced_engagement_or_false_attribution"
    recent = [normalize(p) for p in previous if isinstance(p, str)]
    candidate = normalize(t)
    if any(SequenceMatcher(None, candidate, old).ratio() >= .75
           for old in recent[:65] if old):
        return 0, "too_similar_to_previous"
    # A specific scene, a grounded tip, or a useful interpersonal dilemma
    # can qualify. Generic "Bạn nghĩ sao?" alone cannot.
    specific = (any(ch.isdigit() for ch in t[:160]) or
                any(w in t.casefold() for w in
                    ("thử ", "nếu ", "trưởng nhóm", "đồng nghiệp",
                     "thực tập", "báo cáo", "sếp ", "cuộc họp", "bàn làm việc")))
    if not specific:
        return 0, "not_specific_enough"
    if len(t) < 125 or len(t) > 490:
        return 0, "not_substantial_or_too_long"
    # Hard necessities above; remaining points reward pacing and humanity.
    score = 65
    if "?" in t: score += 10
    if "\n" in t: score += 10
    if any(c in t for c in ("“", "”", ":", "😅", "🫠")): score += 5
    if len(t) >= 200: score += 5
    if len(reason.strip()) >= 45: score += 5
    return min(100, score), "qualified" if score >= QUALITY_THRESHOLD else "low_editorial_quality"


def _day_rows(db, channel_id, local_date):
    start = datetime.combine(local_date, time.min, tzinfo=VN).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    rows = db.request("GET", "/threads_posts", params={
        "select": "id,status,created_by,scheduled_at,published_at",
        "channel_id": "eq." + channel_id,
        "scheduled_at": "gte." + start.isoformat(),
        "and": "(scheduled_at.lt." + end.isoformat() + ")",
        "limit": "120",
    })
    # The start/end are date filters: failure to obtain them must STOP publishing.
    if not isinstance(rows, list):
        raise ValueError("Calendar unavailable")
    return rows


def eligibility(rows, observations, *, now=None):
    now = now or datetime.now(timezone.utc)
    vn = now.astimezone(VN)
    if not time(8, 0) <= vn.time() <= time(22, 15):
        return "quiet_hours", 0
    reserved = [r for r in rows if r.get("status") in (
        "posted", "scheduled_external", "publishing", "uncertain")]
    if len(reserved) >= MAX_DAY_TOTAL:
        return "day_safety_ceiling", 0
    for row in rows:
        when = _booking_time(row)
        if row.get("status") in ("posted", "scheduled_external", "publishing", "uncertain", "queued"):
            if when is None:
                return "invalid_booking_time", 0
            if abs((now - when).total_seconds()) < MIN_GAP_MINUTES * 60:
                return "near_another_post", 0
    samples = {str(x.get("post_id")):x for x in observations
               if isinstance(x, dict) and
               type(x.get("views")) is int and x.get("views") > 0}
    complete = list(samples.values())
    if len(complete) >= METRICS_MIN_SAMPLES:
        if not any((type(x.get("replies")) is int and x["replies"] > 0)
                   or (type(x.get("likes")) is int and x["likes"] > 0)
                   for x in complete):
            return "pause_until_real_engagement", 0
        max_extra = 2
    else:
        # Before data arrives, only one exploratory extra on a booked day.
        max_extra = 1
    added = sum(r.get("created_by") == "agent" and
                r.get("status") in ("queued", "posted", "publishing", "uncertain")
                for r in rows)
    if added >= max_extra:
        return "experimental_extra_limit", 0
    if any(r.get("status") == "queued" and r.get("created_by") == "agent"
           for r in rows):
        return "existing_agent_draft", 0
    return "eligible", max_extra


def plan(db, *, now=None, enabled=None, generator=generate_ai_post):
    provided_now = now is not None
    now = now or datetime.now(timezone.utc)
    if enabled is None:
        enabled = os.getenv("THREADS_ADAPTIVE_ENABLED", "").lower() == "true"
    if not enabled:
        return "adaptive_disabled"
    channel = get_channel(db)
    if not (channel.get("status") == "connected"
            and channel.get("authorized") and channel.get("auto_publish_enabled")):
        return "account_not_authorized"
    rows = _day_rows(db, channel["id"], now.astimezone(VN).date())
    observations = db.request("GET", "/threads_metrics", params={
        "select": "post_id,views,replies,likes,collected_at",
        "order":"collected_at.desc","limit":"24",
    })
    if not isinstance(observations,list):
        return "metrics_unavailable"
    gate, _ = eligibility(rows, observations, now=now)
    if gate != "eligible":
        return gate

    history = db.request("GET", "/threads_posts", params={
        "select":"text_content",
        "channel_id":"eq."+channel["id"],
        "order":"created_at.desc","limit":"80",
    })
    if not isinstance(history,list):
        return "history_unavailable"
    previous = [r["text_content"] for r in history if isinstance(r.get("text_content"),str)]
    # Different angles per evaluation; never a fabricated live-news claim.
    idx = (now.astimezone(VN).date().toordinal() + now.hour // 3) % len(SEEDS)
    pillar, topic = SEEDS[idx]

    # Learn only from provider-verified post metrics. A missing/invalid policy
    # must never block the safe "balanced" fallback or silently change safety caps.
    format_pref = "balanced"
    if os.getenv("ENNA_SELF_IMPROVEMENT_ENABLED", "").lower() == "true":
        try:
            policy = db.request("GET", "/enna_learning_policy", params={
                "select":"preferred_format", "brand_key":"eq.do_hay_di_lam",
                "limit":"1"})
            if isinstance(policy,list) and policy and policy[0].get(
                "preferred_format") in ("balanced","story","practical"):
                format_pref = policy[0]["preferred_format"]
        except Exception:
            pass
    if format_pref == "story":
        pillar = "conversation"
        topic = ("Chuyện công sở sáng tác: nhân vật như thực tập sinh mới, "
                 "lời thoại tự nhiên, nút thắt và hai góc nhìn; "
                 "không nhận là trải nghiệm thật. Bối cảnh: " + topic)
    elif format_pref == "practical":
        topic = ("Một mẹo cụ thể, có ích ngay cho nhân viên văn phòng; "
                 "không viết thành chuyện drama. Bối cảnh: " + topic)
    try:
        candidate = generator(pillar, topic, previous)
        score, quality = qualify(candidate.get("post_text"),
                                  candidate.get("why_useful"), previous)
        if score < QUALITY_THRESHOLD:
            return "quality_rejected:" + quality
    except (ValueError, KeyError, TypeError):
        return "generation_rejected"
    # Check live feed a second time: generation may have taken a minute.
    current = now if provided_now else datetime.now(timezone.utc)
    if eligibility(_day_rows(db,channel["id"],current.astimezone(VN).date()),
                   observations,now=current)[0] != "eligible":
        return "calendar_changed_before_commit"
    text = candidate["post_text"].strip()
    digest = hashlib.sha256((BRAND_KEY+"\nadaptive\n"+text).encode()).hexdigest()
    saved = db.request("POST","/threads_posts",
        params={"on_conflict":"content_key"},
        payload={"channel_id":channel["id"],
                 "content_key":digest,"pillar":candidate["pillar"],
                 "text_content":text,"status":"queued",
                 "scheduled_at":current.isoformat(),
                 "content_type":"editorial","risk_flags":[],
                 "created_by":"agent"},
        prefer="resolution=ignore-duplicates,return=representation")
    return "adaptive_queued" if saved else "already_queued"


if __name__ == "__main__":
    from agent import Database
    try:
        print("Enna adaptive evaluation:",plan(Database()))
    except Exception as exc:
        print("Enna adaptive evaluation: unavailable:"+type(exc).__name__)
