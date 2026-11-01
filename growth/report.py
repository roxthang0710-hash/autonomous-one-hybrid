"""Non-sensitive operational health report for Growth Radar."""
import json

from agent import Database
from growth.optimizer import analyze


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
        "select": "status", "order": "attempted_at.desc", "limit": "100",
    })
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
        "engagement_note": "Replies only occur via separate official Meta OAuth and owner enable switch.",
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(Database()), ensure_ascii=False))
