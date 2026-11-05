"""Unattended, evidence-gated content R&D for Enna.

This worker prepares source-checked editorial briefs independently of ChatGPT.
It does NOT publish, alter booked posts, shop, pay or manufacture metrics.
Its database table is private to the GitHub service worker.
"""
import json
from datetime import date, datetime, timedelta, timezone
from statistics import median
from zoneinfo import ZoneInfo

from agent import Database
from threads.brand import BRAND_KEY
from threads.tech_editorial import TECH_BRIEFS

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_READY = 8
MAX_PER_LOCAL_DAY = 2
MIN_PUBLISHED_DAYS = 7
MIN_POSTS_PER_PILLAR = 3


def _date(s):
    try:
        value = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def editorial_evidence(posts, metrics, *, now=None):
    """Aggregate only latest official per-post snapshots from real own IDs.

    This is an editorial routing hint, not a causal inference or follower KPI.
    """
    now = now or datetime.now(timezone.utc)
    latest = {}
    for m in metrics:
        if not isinstance(m, dict) or not m.get("post_id"):
            continue
        at = _date(m.get("collected_at"))
        if not at or at > now:
            continue
        key = str(m["post_id"])
        if key not in latest or at > latest[key][0]:
            latest[key] = (at, m)
    groups, days = {}, set()
    for p in posts:
        if (not isinstance(p, dict) or p.get("status") != "posted"
            or not p.get("platform_post_id") or not p.get("id")):
            continue
        published = _date(p.get("published_at"))
        if not published or not timedelta(hours=24) <= now - published <= timedelta(days=30):
            continue
        sample = latest.get(str(p["id"]))
        if not sample or sample[0] < published + timedelta(hours=24):
            continue
        data = sample[1]
        views, likes, replies = data.get("views"), data.get("likes"), data.get("replies")
        if any(type(v) is not int or v < 0 for v in (views, likes, replies)) or views == 0:
            continue
        pillar = p.get("pillar")
        if pillar not in ("work", "organize", "travel", "conversation"):
            continue
        groups.setdefault(pillar, []).append((views, likes + replies))
        days.add(published.astimezone(VN).date())
    qualifying = {k:v for k,v in groups.items() if len(v) >= MIN_POSTS_PER_PILLAR}
    observed = sum(len(v) for v in groups.values())
    base = {"status":"collecting_evidence","observed_posts":observed,
            "distinct_published_days":len(days),"preferred_pillar":None}
    if len(days) < MIN_PUBLISHED_DAYS or len(qualifying) < 2:
        return base
    stats = {k:{"median_views":median([a for a,_ in values]),
                "interaction_density":sum(b for _,b in values)/sum(a for a,_ in values)}
             for k,values in qualifying.items()}
    ranked = sorted(stats, key=lambda k:(stats[k]["median_views"],stats[k]["interaction_density"]),reverse=True)
    leader, second = ranked[:2]
    # Conservative, dual-metric evidence and a meaningful 35% advantage;
    # never optimize from a single viral post.
    if (stats[leader]["median_views"] < 1.35*stats[second]["median_views"]
        or stats[leader]["interaction_density"] < 0.8*stats[second]["interaction_density"]):
        return {**base,"status":"mixed_evidence"}
    return {**base,"status":"provider_evidence",
            "preferred_pillar":leader}


def select_briefs(ideas, previous, *, week_number, favored=None, limit=2):
    """Deterministic rotation with weekly topic dedup and bounded preference."""
    prior = set(previous)
    n = len(ideas)
    if n == 0:
        return []
    start = (week_number * 3) % n
    rotated = list(ideas[start:])+list(ideas[:start])
    remaining = [x for x in rotated if x["key"] not in prior]
    if favored:
        # Preference is only a tie-break; it never suppresses diverse lanes.
        remaining.sort(key=lambda x: 0 if x["pillar"] == favored else 1)
    return remaining[:limit]


def run(db=None, *, now=None):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(VN)
    monday = local.date() - timedelta(days=local.weekday())
    posts = db.request("GET","/threads_posts",params={
        "select":"id,pillar,status,published_at,platform_post_id",
        "order":"published_at.desc","limit":"150"})
    metrics = db.request("GET","/threads_metrics",params={
        "select":"post_id,views,likes,replies,collected_at",
        "order":"collected_at.desc","limit":"450"})
    plans = db.request("GET","/enna_editorial_plans",params={
        "select":"id,idea_key,week_start,status,created_at",
        "brand_key":"eq."+BRAND_KEY,"order":"created_at.desc","limit":"100"})
    if not all(isinstance(x,list) for x in (posts,metrics,plans)):
        raise RuntimeError("Autopilot source unavailable")
    evidence = editorial_evidence(posts,metrics,now=now)
    ready = [x for x in plans if x.get("status") == "ready"]
    created_today = sum(_date(x.get("created_at")) is not None
        and _date(x.get("created_at")).astimezone(VN).date() == local.date()
        for x in plans)
    remaining = max(0,min(MAX_READY-len(ready),MAX_PER_LOCAL_DAY-created_today))
    if remaining == 0:
        return {"result":"queue_healthy_or_daily_limit","ready":len(ready),
                "observed_posts":evidence["observed_posts"],
                "evidence_status":evidence["status"]}
    week_key = monday.isoformat()
    # Prevent last week's same tool/shortcut from resurfacing just because
    # its week_start differs. Parked and ready ideas count as already offered.
    cutoff=monday-timedelta(days=30)
    used_recent=[]
    for row in plans:
        try:
            week=date.fromisoformat(str(row.get("week_start")))
        except (TypeError,ValueError):
            continue
        if cutoff <= week <= monday and row.get("idea_key"):
            used_recent.append(row["idea_key"])
    choices = select_briefs(TECH_BRIEFS,used_recent,
        week_number=monday.toordinal()//7,
        favored=evidence["preferred_pillar"],limit=remaining)
    inserted = 0
    for brief in choices:
        payload = {"brand_key":BRAND_KEY,"week_start":week_key,
            "idea_key":brief["key"],"series":brief["series"],
            "pillar":brief["pillar"],"topic_prompt":brief["prompt"],
            "source_url":brief["source"],"status":"ready",
            "rationale_code":("provider_evidence" if evidence["status"]=="provider_evidence"
                              and brief["pillar"]==evidence["preferred_pillar"]
                              else "balanced_evergreen"),
            "evidence":evidence}
        result=db.request("POST","/enna_editorial_plans",
            params={"on_conflict":"brand_key,week_start,idea_key"},
            payload=payload,prefer="resolution=ignore-duplicates,return=representation")
        if result:
            inserted+=1
    return {"result":"new_ideas_saved" if inserted else "already_prepared",
            "added":inserted,"ready_before":len(ready),
            "evidence_status":evidence["status"],
            "observed_posts":evidence["observed_posts"]}


if __name__ == "__main__":
    try:
        result = run()
        # Public GitHub logs only show counters and predefined status labels.
        print("Enna autonomous editorial:",json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        print("Enna autonomous editorial unavailable:",type(exc).__name__)
        raise SystemExit(1)
