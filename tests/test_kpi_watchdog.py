"""Unit tests for autonomous KPI alerts; no network calls."""
import unittest
from datetime import datetime, timezone
from growth.kpi_watchdog import assess

NOW = datetime(2026, 11, 5, 2, 0, tzinfo=timezone.utc)

class KPIWatchdogTests(unittest.TestCase):
    def test_stale_source_does_not_claim_live_progress(self):
        result = assess([{"measured_on":"2026-11-02","followers":3}], now=NOW)
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["remaining"], 997)
        self.assertFalse(result["fresh"])
    def test_fresh_shortfall_proposes_action(self):
        result = assess([{"measured_on":"2026-11-04","followers":5}], now=NOW)
        self.assertEqual(result["status"], "at_risk")
        self.assertEqual(result["remaining"], 995)
        self.assertEqual(result["action"], "run_safe_growth_experiments")
        self.assertEqual(result["daily_needed"], 497.5)
    def test_missing_does_not_invent_followers(self):
        result = assess([{"measured_on":"2026-11-05","followers":None}], now=NOW)
        self.assertEqual(result["status"], "missing")
        self.assertNotIn("followers", result)
    def test_deadline_passed(self):
        result = assess([{"measured_on":"2026-11-07","followers":25}],
            now=datetime(2026,11,8,2,tzinfo=timezone.utc))
        self.assertEqual(result["status"],"deadline_missed")
    def test_follower_change_uses_real_elapsed_days(self):
        result = assess([{"measured_on":"2026-11-03","followers":3},
            {"measured_on":"2026-11-05","followers":5}], now=NOW)
        self.assertEqual(result["observed_daily_change"], 1.0)
    def test_future_dated_and_invalid_rows_are_excluded(self):
        result = assess([{"measured_on":"2026-11-09","followers":1000},
            {"measured_on":"2026-11-04","followers":4}], now=NOW)
        self.assertEqual(result["followers"],4)
        self.assertEqual(result["status"],"at_risk")
    def test_verified_goal_not_predicted_from_views(self):
        result = assess([{"measured_on":"2026-11-05","followers":1000}],now=NOW)
        self.assertEqual(result["status"],"verified_goal_met")

if __name__=="__main__":
    unittest.main()
