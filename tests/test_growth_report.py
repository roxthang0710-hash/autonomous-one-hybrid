import unittest
from unittest.mock import Mock
from growth.report import snapshot


class GrowthReportTests(unittest.TestCase):
    def test_reports_only_grounded_provider_counts(self):
        db = Mock()
        db.request.side_effect = [
            [],
            [{"id": "1", "relevance_score": 78}],
            [{"id": "2", "status": "needs_review", "kind": "trend_post"}],
            [{"status": "posted", "attempted_at":"2026-10-30T02:15:00+00:00"}],
            [],
        ]
        result = snapshot(db)
        self.assertEqual(result["signals_recorded_recent"], 1)
        self.assertEqual(result["drafts_needing_review"], 1)
        self.assertEqual(
            result["metricool_performance"]["status"],
            "insufficient_observations",
        )
        self.assertEqual(result["confirmed_brand_replies_recent"], 1)
        self.assertEqual(result["engagement_policy"]["reply_mode"], "waiting_for_meta_oauth")
        self.assertEqual(result["engagement_policy"]["daily_maximum_vietnam"], 3)
        self.assertEqual(result["engagement_policy"]["today_remaining_capacity"], 0)
        self.assertIn("owner OAuth", result["engagement_note"])


if __name__ == "__main__":
    unittest.main()
