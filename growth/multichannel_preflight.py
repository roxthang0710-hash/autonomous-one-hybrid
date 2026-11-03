"""Read-only, advance-check scheduler for Enna's Facebook/Instagram pipeline.

Checks the *last confirmed Metricool booking snapshot* in Supabase, NOT live
provider publication. This module cannot publish new posts by itself.
It writes only fixed, redacted event codes for the dashboard.
"""
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from agent import Database

VN = ZoneInfo("Asia/Ho_Chi_Minh")
BRAND = "do_hay_di_lam"
PROVIDERS = ("facebook", "instagram")
ERRORS = {
    "missing_slot": ("pending", "preflight_missing_slot"),
    "missing_media": ("failed", "preflight_missing_media"),
    "manual_publish": ("pending", "preflight_manual_publish"),
    "duplicate_slot": ("uncertain", "preflight_duplicate_slot"),
    "provider_error": ("failed", "preflight_provider_error"),
    "due_unverified": ("uncertain", "preflight_due_unverified"),
    "snapshot_stale": ("pending", "preflight_snapshot_stale"),
}


def parse_dt(value):
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Expected timezone aware datetime")
    return dt


def check(rows, *, now=None, ahead_days=3):
    """Return structured (date, provider, status, code) summaries.

    today and the next two local dates constitute a small rolling buffer.
    All results are strictly about booking readiness and snapshot freshness.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    if not 1 <= ahead_days <= 7:
        raise ValueError("Invalid preflight horizon")
    today = now.astimezone(VN).date()
    grouped = defaultdict(list)
    for row in rows:
        if row.get("provider") not in PROVIDERS:
            continue
        try:
            dt = parse_dt(row["scheduled_at"])
        except (KeyError, ValueError, TypeError):
            continue
        grouped[(dt.astimezone(VN).date(),row["provider"])].append((dt,row))
    outcomes = []
    for dayoffset in range(ahead_days):
        day = today + timedelta(days=dayoffset)
        for provider in PROVIDERS:
            items = grouped[(day,provider)]
            # Today's window may have already passed. A record remains valid
            # evidence that a booking existed, even if the provider status
            # has not been refreshed after its due time.
            if not items:
                outcomes.append((day.isoformat(),provider,"pending","preflight_missing_slot"))
                continue
            if len(items) > 1:
                outcomes.append((day.isoformat(),provider,"uncertain","preflight_duplicate_slot"))
                continue
            dt,row = items[0]
            status=row.get("provider_status")
            try:
                checked=parse_dt(row["checked_at"])
            except (KeyError,ValueError,TypeError):
                checked=None
            if status=="ERROR":
                key="provider_error"
            elif provider=="instagram" and not row.get("has_media"):
                key="missing_media"
            elif not row.get("auto_publish"):
                key="manual_publish"
            elif status=="PENDING" and dt < now - timedelta(minutes=20):
                key="due_unverified"
            elif status=="PENDING" and (
                checked is None or checked < now - timedelta(hours=24)):
                key="snapshot_stale"
            elif status not in ("PENDING","PUBLISHED"):
                key="provider_error"
            else:
                key=None
            if key:
                state,code=ERRORS[key]
                outcomes.append((day.isoformat(),provider,state,code))
            else:
                outcomes.append((day.isoformat(),provider,"success","preflight_ready"))
    return outcomes


def run(db=None, *, now=None, ahead_days=3):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    rows = db.request("GET","/enna_multichannel_posts",params={
        "select":"provider,scheduled_at,provider_status,auto_publish,has_media,checked_at",
        "brand_key":"eq."+BRAND,
        "order":"scheduled_at.asc",
        "limit":"250"
    })
    if not isinstance(rows,list):
        raise RuntimeError("Provider booking snapshot unavailable")
    outcomes=check(rows,now=now,ahead_days=ahead_days)
    for day,provider,status,code in outcomes:
        payload={
            "origin":"watchdog",
            "kind":"system",
            "status":status,
            "code":code,
            "dedup_key":"preflight:"+day+":"+provider+":"+code,
            "trigger_kind":"database",
            "occurred_at":now.isoformat()
        }
        # A reporting failure must not cause publication retries or
        # mutate external scheduling.
        try:
            db.request("POST","/enna_activity_events",
                params={"on_conflict":"dedup_key"},payload=payload,
                prefer="resolution=ignore-duplicates,return=representation")
        except Exception:
            print("Preflight audit sink unavailable")
    issues=[{"date":day,"provider":provider,"code":code}
            for day,provider,status,code in outcomes if status!="success"]
    return {"checked":len(outcomes),"ready":len(outcomes)-len(issues),
            "issues":issues,"snapshot_only":True}


if __name__=="__main__":
    try:
        print("Enna 72-hour preflight:",json.dumps(run(),ensure_ascii=False))
    except Exception as exc:
        print("Enna 72-hour preflight:",json.dumps({
            "status":"unavailable","error_class":type(exc).__name__}))
