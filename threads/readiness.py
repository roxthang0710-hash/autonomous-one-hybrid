"""Read-only truthful account and Shopee-affiliate readiness snapshot.

Does NOT calculate fictional eligibility thresholds, follower counts, sales,
or estimated commission. These must be confirmed by the affiliate provider.
No credentials, post text, or private identifiers are emitted.
"""
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from agent import Database
from threads.brand import BRAND_KEY

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def _date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else None
    except (ValueError, TypeError):
        return None


def snapshot(db=None, *, now=None):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    channels = db.request("GET", "/threads_channels", params={
        "select": "brand_key,status,authorized,auto_publish_enabled,"
                  "account_created_at,shopee_channel_approved",
        "brand_key": "eq." + BRAND_KEY, "limit": "1",
    })
    if not channels:
        return {"status": "missing_brand_configuration"}
    channel = channels[0]
    posts = db.request("GET", "/threads_posts", params={
        "select": "status,scheduled_at,published_at", "limit": "365",
        "order": "scheduled_at.desc",
    })
    counts = {name: sum(p.get("status") == name for p in posts)
              for name in ("posted", "queued", "scheduled_external",
                           "publishing", "uncertain", "failed")}
    # Only most-recent observed metric count: never substitute scheduled
    # posts or zero for actual views/revenue.
    measurements = db.request("GET", "/threads_metrics", params={
        "select": "collected_at", "limit": "1",
        "order": "collected_at.desc",
    })
    vault_rows = db.request("GET", "/threads_vault_credentials", params={
        "select": "status,expires_at", "brand_key": "eq." + BRAND_KEY,
        "limit": "1",
    })
    expiry = _date(vault_rows[0]["expires_at"]) if vault_rows else None
    vault_valid = bool(vault_rows and vault_rows[0].get("status") == "active"
                       and expiry and expiry > now)
    posted_days = {
        local.date() for p in posts if p.get("status") == "posted"
        if (local := _date(p.get("scheduled_at"))) is not None
        for local in [local.astimezone(VN)]
    }
    future_by_day = {}
    for p in posts:
        if p.get("status") not in ("queued", "scheduled_external"):
            continue
        when = _date(p.get("scheduled_at"))
        if when is not None and when > now:
            day = when.astimezone(VN).date().isoformat()
            future_by_day.setdefault(day, set()).add(p["status"])
    collision_dates = sorted(day for day, types in future_by_day.items()
                             if len(types) > 1)
    account_created = _date(channel.get("account_created_at"))
    account_age_days = (
        max(0, (now - account_created).days)
        if account_created and account_created <= now else None
    )
    warnings = []
    if not channel.get("authorized") or channel.get("status") != "connected":
        warnings.append("threads_connection_not_authorized")
    if not vault_valid:
        warnings.append("no_valid_oauth_token")
    elif expiry - now < timedelta(days=14):
        warnings.append("oauth_token_needs_refresh")
    if collision_dates:
        warnings.append("potential_metricool_conflicting_dates")
    if counts["uncertain"]:
        warnings.append("uncertain_publication_requires_reconciliation")
    if counts["failed"]:
        warnings.append("failed_posts_need_review")
    shopee = (
        "approved_by_owner_record" if channel.get("shopee_channel_approved")
        else "not_yet_approved"
    )
    return {
        "status": "connected" if vault_valid and channel.get("authorized")
                  else "connection_attention_needed",
        "brand": "Đồ Hay Đi Làm",
        "threads_posts": counts,
        "days_with_confirmed_posts": len(posted_days),
        "next_queued_local_date": (
            min((day for day, status in future_by_day.items()
                 if "queued" in status), default=None)),
        "measured_insights_available": bool(measurements),
        "account_age_days_if_recorded": account_age_days,
        "shopee_affiliate": {
            "channel_approval": shopee,
            "eligibility_criteria": "require_official_provider_verification",
            "affiliate_tracking_link": "not_provisioned_by_agent",
            "revenue": "not_measured",
        },
        "warnings": warnings,
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False))
