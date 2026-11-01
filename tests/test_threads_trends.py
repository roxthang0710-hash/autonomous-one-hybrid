import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from threads.trends import select_topic

NOW = datetime(2026, 11, 17, 3, 0, tzinfo=timezone.utc)


def example():
    return {
        "opportunity_id": "idea", "signal_id": "source",
        "quality_score": 91,
        "expires_at": (NOW + timedelta(hours=60)).isoformat()
    }


def signal():
    return {
        "id": "source",
        "title": "Góc làm việc nhỏ nên sắp xếp như thế nào?",
        "niche": "work", "state": "candidate",
        "published_at": (NOW - timedelta(hours=3)).isoformat(),
        "risk_flags": [], "source_url": "https://news.google.com/example",
        "relevance_score": 88,
    }


class GrowthHandoffTests(unittest.TestCase):
    def test_never_apply_old_news_to_far_future_slot(self):
        db = MagicMock()
        future = NOW + timedelta(days=11)
        self.assertIsNone(select_topic(db, future, now=NOW))
        db.request.assert_not_called()

    def test_fresh_credible_relevant_topic_can_be_used(self):
        db = MagicMock()
        db.request.side_effect = [
            [{"id": "idea", "signal_id": "source", "quality_score": 91,
              "expires_at": (NOW + timedelta(hours=60)).isoformat()}],
            [],
            [signal()],
        ]
        result = select_topic(db, NOW + timedelta(days=1), now=NOW)
        self.assertEqual(result["opportunity_id"], "idea")
        self.assertEqual(result["pillar"], "work")
        self.assertIn("tuyệt đối không khẳng định", result["topic"])

    def test_deduplicate_same_trend_source(self):
        db = MagicMock()
        db.request.side_effect = [
            [{"id": "idea", "signal_id": "source", "quality_score": 91,
              "expires_at": (NOW + timedelta(hours=60)).isoformat()}],
            [{"id": "already_posted"}],
        ]
        self.assertIsNone(select_topic(db, NOW + timedelta(hours=20), now=NOW))

    def test_reject_non_fresh_unrelated_signal(self):
        db = MagicMock()
        old = signal()
        old["published_at"] = (NOW - timedelta(days=5)).isoformat()
        db.request.side_effect = [
            [{"id": "idea", "signal_id": "source", "quality_score": 91,
              "expires_at": (NOW + timedelta(hours=60)).isoformat()}],
            [],
            [old],
        ]
        self.assertIsNone(select_topic(db, NOW + timedelta(hours=20), now=NOW))


if __name__ == "__main__":
    unittest.main()
