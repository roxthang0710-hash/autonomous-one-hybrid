"""Enna health diagnostics are based on evidence, not guessed performance."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from enna import AGENT_NAME, health, summary

NOW = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
THREADS = {
    "status": "connected",
    "threads_posts": {"scheduled_external": 15, "queued": 3, "posted": 0},
    "next_queued_local_date": "2026-11-18",
    "warnings": [],
    "shopee_affiliate": {"channel_approval": "not_yet_approved"},
}
GROWTH = {
    "drafts_needing_review": 5,
    "engagement_policy": {
        "reply_mode": "owner_authorized",
        "daily_maximum_vietnam": 3,
        "today_attempted": 0,
        "today_confirmed": 0,
    },
    "metricool_performance": {"status": "insufficient_observations"},
}


class EnnaOperationsTests(unittest.TestCase):
    def test_name_and_fact_only_summary(self):
        self.assertEqual(AGENT_NAME, "Enna")
        db = MagicMock()
        db.request.return_value = [{
            "status": "success", "started_at": (NOW - timedelta(hours=3)).isoformat(),
            "source_summary": {"threads": "empty_keyword_results"},
        }]
        with patch("enna.threads_snapshot", return_value=THREADS), \
             patch("enna.growth_snapshot", return_value=GROWTH):
            state = health(db, now=NOW)
        self.assertEqual(state["agent"], "Enna")
        self.assertEqual(state["state"], "operating_with_limits")
        self.assertEqual(state["threads"]["metricool_reserved"], 15)
        self.assertEqual(state["threads"]["ai_queued"], 3)
        self.assertEqual(state["threads"]["ai_confirmed_posted"], 0)
        self.assertFalse(state["affiliate"]["shopee_approved"])
        self.assertFalse(state["affiliate"]["revenue_verified"])
        self.assertIn("public_threads_discovery_not_confirmed", state["findings"])
        display = summary(state)
        self.assertIn("## Enna", display)
        self.assertIn("0 / 3", display)
        self.assertIn("Chưa xác minh", display)
        self.assertNotIn("đã có doanh thu", display)

    def test_failed_growth_run_is_attention(self):
        db=MagicMock()
        db.request.return_value=[{
            "status":"failed",
            "started_at":NOW.isoformat(),
            "source_summary":{"threads":"source_unavailable"},
        }]
        with patch("enna.threads_snapshot", return_value=THREADS), \
             patch("enna.growth_snapshot", return_value=GROWTH):
            state=health(db,now=NOW)
        self.assertEqual(state["state"],"attention")
        self.assertIn("growth_radar_latest_run_failed",state["findings"])

    def test_stale_growth_is_reported_not_success(self):
        db=MagicMock()
        db.request.return_value=[]
        with patch("enna.threads_snapshot", return_value=THREADS), \
             patch("enna.growth_snapshot", return_value=GROWTH):
            state=health(db,now=NOW)
        self.assertIn("growth_radar_not_recently_verified",state["findings"])


if __name__=="__main__":
    unittest.main()
