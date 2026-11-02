"""Evidence-first Enna decisions: guard against invented commercial success."""
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from growth.learning import decide, snapshot


class LearningTests(unittest.TestCase):
    def test_missing_data_never_implies_income_or_growth(self):
        state = decide({}, search_confirmed=False)
        self.assertEqual(state["phase"], "evidence_collection")
        self.assertEqual(state["commission_provider_evidenced_vnd"], 0)
        self.assertFalse(state["earnings_verified_as_paid"])
        codes = [r["code"] for r in state["next_actions"]]
        self.assertIn("metrics_baseline", codes)
        self.assertIn("affiliate_approval", codes)

    def test_only_provider_export_with_https_evidence_counts(self):
        data = {"commissions": [
            {"confirmed_commission_vnd": 10000,
             "evidence_url": "https://provider.example/receipt", "provenance": "provider_export"},
            {"confirmed_commission_vnd": 9999999,
             "evidence_url": "https://example.org/manual", "provenance": "owner_manual"},
            {"confirmed_commission_vnd": 20000,
             "evidence_url": "javascript:alert(1)", "provenance": "provider_export"},
        ]}
        out = decide(data)
        self.assertEqual(out["commission_provider_evidenced_vnd"], 10000)
        self.assertEqual(out["commission_needs_verification"], 2)
        self.assertFalse(out["earnings_verified_as_paid"])

    def test_real_metrics_are_required_for_an_experiment(self):
        rows = [{"measured_on": "2026-10-%02d" % day,
                 "post_views": 100, "interactions": 10, "published_posts": 1,
                 "followers": 1} for day in range(18, 25)]
        state = decide({"metricool": rows}, search_confirmed=True,
                       now=datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(state["phase"], "evidence_learning")
        self.assertEqual(state["metric_status"], "baseline_available")
        self.assertIn("controlled_test", [x["code"] for x in state["next_actions"]])

    def test_incomplete_or_stale_days_cannot_trigger_learning(self):
        now = datetime(2026, 11, 2, tzinfo=timezone.utc)
        rows = [{"measured_on": "2026-11-02", "post_views": 200, "interactions": 4, "published_posts": 2}] * 7
        self.assertEqual(decide({"metricool": rows}, now=now)["phase"], "evidence_collection")
        rows = [{"measured_on": "2026-01-01", "post_views": 200, "interactions": 4, "published_posts": 2}] * 7
        self.assertEqual(decide({"metricool": rows}, now=now)["phase"], "evidence_collection")

    def test_provider_failure_is_not_reported_as_real_zero(self):
        db = Mock()
        db.request.side_effect = RuntimeError("hidden server error")
        state = snapshot(db)
        self.assertEqual(state["status"], "partial_source_unavailable")
        self.assertIsNone(state["commission_provider_evidenced_vnd"])
        self.assertEqual(state["metric_status"], "source_unavailable")
        self.assertEqual(state["next_actions"][0]["code"], "repair_evidence_feed")

    def test_source_query_is_allowlisted(self):
        db = Mock()
        db.request.return_value = []
        snapshot(db)
        self.assertEqual(db.request.call_count, 7)
        for call in db.request.call_args_list:
            args, kwargs = call
            self.assertEqual(args[0], "GET")
            select = kwargs["params"]["select"]
            self.assertNotIn("draft_text", select)
            self.assertNotIn("token", select)
            self.assertNotIn("owner_notes", select)


if __name__ == "__main__":
    unittest.main()
