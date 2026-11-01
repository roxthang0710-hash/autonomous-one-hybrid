import unittest
from unittest.mock import Mock
from dashboard import report
from backfill import backfill


class ReportTests(unittest.TestCase):
    def test_summary_does_not_expose_plan_or_revenue(self):
        db = Mock()
        db.request.side_effect = [
            [{"approval_status": "pending", "review_score": 85,
              "verdict": "review", "experiments": 0, "observed_signals": 0}],
            [{"status": "success"}],
        ]
        summary = report(db)
        self.assertIn("Chờ chủ sở hữu duyệt | 1", summary)
        self.assertIn("Supabase Table Editor", summary)
        self.assertNotIn("revenue_received_vnd", summary)

    def test_backfill_creates_missing_evaluation(self):
        db = Mock()
        db.request.side_effect = [
            [{"id": "1", "proposal": {"title": "Create a useful tool"},
              "research_sources": []}],
            [],
        ]
        self.assertEqual(backfill(db), 1)
        self.assertEqual(db.insert.call_args.args[0], "agent_evaluations")

    def test_backfill_skips_existing(self):
        db = Mock()
        db.request.side_effect = [
            [{"id": "1", "proposal": {"title": "Example"}, "research_sources": []}],
            [{"proposal_id": "1"}],
        ]
        self.assertEqual(backfill(db), 0)
        db.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
