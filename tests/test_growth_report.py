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
        ]
        result = snapshot(db)
        self.assertEqual(result["signals_recorded_recent"], 1)
        self.assertEqual(result["drafts_needing_review"], 1)
        self.assertEqual(
            result["metricool_performance"]["status"],
            "insufficient_observations",
        )
        self.assertIn("No posts or replies", result["posting_claim"])


if __name__ == "__main__":
    unittest.main()
