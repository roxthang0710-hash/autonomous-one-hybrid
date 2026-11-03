"""Regression tests for the unattended content research autopilot."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from growth.editorial_autopilot import (
    MAX_READY, editorial_evidence, run, select_briefs)
from threads.tech_editorial import TECH_BRIEFS

NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def example(day, pillar, views, interactions):
    published = NOW - timedelta(days=day)
    return (
        {"id": "post" + str(day), "pillar": pillar, "status": "posted",
         "platform_post_id": str(10000 + day),
         "published_at": published.isoformat()},
        {"post_id": "post" + str(day), "views": views, "likes": interactions,
         "replies": 0, "collected_at": (published + timedelta(hours=30)).isoformat()},
    )


class EditorialAutopilotTests(unittest.TestCase):
    def test_zero_evidence_is_not_fake_performance(self):
        result = editorial_evidence([], [], now=NOW)
        self.assertEqual(result["status"], "collecting_evidence")
        self.assertIsNone(result["preferred_pillar"])

    def test_viral_post_does_not_drive_a_strategy_change(self):
        p, m = example(2, "organize", 99999, 30)
        result = editorial_evidence([p], [m], now=NOW)
        self.assertEqual(result["status"], "collecting_evidence")

    def test_requires_multiple_days_and_multiple_pillars(self):
        examples = [example(d, "organize", 600, 30) for d in (3, 4, 5, 6)]
        posts, metrics = zip(*examples)
        result = editorial_evidence(list(posts), list(metrics), now=NOW)
        self.assertEqual(result["status"], "collecting_evidence")

    def test_conservative_preference_after_verified_span(self):
        examples = (
            [example(d, "organize", 600, 30) for d in (4, 6, 8, 10)]
            + [example(d, "work", 200, 10) for d in (3, 5, 7)]
        )
        posts, metrics = zip(*examples)
        result = editorial_evidence(list(posts), list(metrics), now=NOW)
        self.assertEqual(result["status"], "provider_evidence")
        self.assertEqual(result["preferred_pillar"], "organize")

    def test_rotation_is_deduplicated(self):
        ids = [x["key"] for x in select_briefs(TECH_BRIEFS, [], week_number=10)]
        next_ids = [x["key"] for x in select_briefs(
            TECH_BRIEFS, ids, week_number=10)]
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(next_ids), 2)
        self.assertTrue(set(ids).isdisjoint(next_ids))

    def test_prepares_two_briefs_without_publishing(self):
        db = MagicMock()
        db.request.side_effect = [[], [], [], [{"id": "a"}], [{"id": "b"}]]
        result = run(db, now=NOW)
        self.assertEqual(result["added"], 2)
        calls = db.request.call_args_list
        self.assertEqual([call.args[0] for call in calls], [
            "GET", "GET", "GET", "POST", "POST"])
        self.assertTrue(all(
            call.args[1] == "/enna_editorial_plans"
            for call in calls if call.args[0] == "POST"))
        for call in calls[3:]:
            self.assertEqual(call.kwargs["payload"]["status"], "ready")
            self.assertEqual(call.kwargs["payload"]["rationale_code"], "balanced_evergreen")

    def test_pauses_when_plans_full(self):
        db = MagicMock()
        plans = [{"status": "ready", "created_at": (NOW-timedelta(days=1)).isoformat()}
                 for _ in range(MAX_READY)]
        db.request.side_effect = [[], [], plans]
        result = run(db, now=NOW)
        self.assertEqual(result["result"], "queue_healthy_or_daily_limit")
        self.assertEqual(db.request.call_count, 3)


if __name__ == "__main__":
    unittest.main()
