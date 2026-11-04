"""Provider-grounded KPI watchdog; no publishing, engagement or spending."""
import json
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from agent import Database

VN = ZoneInfo("Asia/Ho_Chi_Minh")
GOAL = 1000
DEADLINE = date(2026, 11, 7)


def assess(rows, *, now=None, goal=GOAL, deadline=DEADLINE):
    now = now or datetime.now(timezone.utc)
    local_day = now.astimezone(VN).date()
    valid = []
    for r in rows or []:
        try:
            day = date.fromisoformat(str(r.get("measured_on", "")))
            followers = r.get("followers")
            if type(followers) is not int or followers < 0 or day > local_day:
                continue
            valid.append((day, followers))
        except (ValueError, TypeError, AttributeError):
            continue
    valid.sort(key=lambda x: x[0])
    if not valid:
        return {"status": "missing", "goal": goal, "deadline": deadline.isoformat(),
                "action": "sync_provider_metrics", "owner_action": None}
    day, followers = valid[-1]
    age_days = (local_day - day).days
    remaining = max(0, goal - followers)
    days_left = (deadline - local_day).days
    stale = age_days > 1
    if followers >= goal:
        status, action = "verified_goal_met", "verify_provider_snapshot"
    elif days_left < 0:
        status, action = "deadline_missed", "postmortem_and_reset_goal"
    elif stale:
        status, action = "stale", "sync_provider_metrics"
    else:
        status, action = "at_risk", "run_safe_growth_experiments"
    daily_needed = None if days_left < 0 else remaining / max(1, days_left)
    # Observed daily increase from a different dated snapshot, not an assumed
    # causal follower conversion rate.
    baseline = next(((d, n) for d, n in reversed(valid[:-1]) if d < day), None)
    observed_per_day = (followers - baseline[1]) / (day-baseline[0]).days if baseline else None
    return {
        "status": status, "goal": goal, "followers": followers,
        "snapshot_date": day.isoformat(), "age_days": age_days,
        "fresh": not stale, "deadline": deadline.isoformat(), "days_left": days_left,
        "remaining": remaining, "daily_needed": round(daily_needed, 2) if daily_needed is not None else None,
        "observed_daily_change": round(observed_per_day, 2) if observed_per_day is not None else None,
        "action": action, "owner_action": None,
        "recommendations": ([
            "Metricool/Meta snapshot is stale: refresh actual follower count before claiming progress.",
            "Do not auto-increase posting frequency or repeat uncertain Meta writes.",
        ] if stale else [
            "Compare practical tips, original media, and discussion posts using verified reach and follow growth.",
            "Use native Threads Topic when supported; textual hashtag alone is not verified Topic tagging.",
            "Never buy followers, tag unrelated users or spam replies.",
        ]),
    }


def run(db=None, *, now=None):
    db = db or Database()
    rows = db.request("GET", "/growth_metricool_daily", params={
        "select": "measured_on,followers",
        "order": "measured_on.desc", "limit": "30",
    })
    if not isinstance(rows, list):
        return {"status": "source_unavailable", "action": "check_supabase_connection"}
    return assess(rows, now=now)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
