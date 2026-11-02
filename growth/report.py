"""Non-sensitive operational health report for Growth Radar."""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from agent import Database
from growth.optimizer import analyze
from growth.engage import MAX_DAILY_ATTEMPTS

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def snapshot(db):
    rows = db.request("GET", "/growth_metricool_daily", params={
        "select": "measured_on,followers,post_views,interactions,published_posts",
        "order": "measured_on.asc", "limit": "30",
    })
    score = analyze(rows)
    trends = db.request("GET", "/growth_signals", params={
        "select": "id,relevance_score", "order": "discovered_at.desc", "limit": "100",
    })
    drafts = db.request("GET", "/growth_opportunities", params={
        "select": "id,status,kind", "order": "created_at.desc", "limit": "100",
    })
    attempts = db.request("GET", "/growth_engagement_attempts", params={
        "select": "status,attempted_at", "order": "attempted_at.desc", "limit": "100",
    })
    vault = db.request("GET", "/threads_vault_credentials", params={
        "select": "enable_replies,status,expires_at",
        "brand_key": "eq.do_hay_di_lam", "limit": "1",
    })
    authorized = bool(vault and vault[0].get("enable_replies") is True
                      and vault[0].get("status") == "active")
    current_day = datetime.now(timezone.utc).astimezone(VN).date()
    today = []
    for a in attempts:
        try:
            timestamp = datetime.fromisoformat(
                str(a.get("attempted_at") or "").replace("Z","+00:00"))
            if timestamp.tzinfo and timestamp.astimezone(VN).date() == current_day:
                today.append(a)
        except (ValueError, TypeError):
            continue
    return {
        "signals_recorded_recent": len(trends),
        "drafts_saved_recent": len(drafts),
        "reply_suggestions_for_owner_review": sum(
            1 for x in drafts if x["kind"] == "reply_suggestion"
        ),
        "drafts_needing_review": sum(
            1 for x in drafts if x["status"] == "needs_review"
        ),
        "metricool_performance": score,
        "confirmed_brand_replies_recent": sum(1 for x in attempts if x["status"] == "posted"),
        "engagement_policy": {
            "reply_mode": "owner_authorized" if authorized else "waiting_for_meta_oauth",
            "daily_maximum_vietnam": MAX_DAILY_ATTEMPTS,
            "today_attempted": len(today),
            "today_confirmed": sum(x.get("status") == "posted" for x in today),
            "today_remaining_capacity": (
                max(0, MAX_DAILY_ATTEMPTS - len(today)) if authorized else 0
            ),
        },
        "engagement_note": (
            "Enna has owner OAuth permission, but external public keyword search "
            "may still require Meta App Review. Only fresh eligible Threads "
            "discussions can receive original brand replies; zero replies is "
            "normal when no such discussion is available."
            if authorized else
            "Threads commenting remains off until owner OAuth explicitly enables "
            "it; do not attempt to publish, bypass Meta or create fake replies."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(Database()), ensure_ascii=False))
