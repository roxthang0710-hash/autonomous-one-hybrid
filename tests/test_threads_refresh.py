import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from threads.refresh import refresh_next, MAX_TREND_POSTS_WEEK

NOW = datetime(2026, 11, 17, 3, 0, tzinfo=timezone.utc)
CHANNEL = {"id": "brand", "status": "connected", "authorized": True}
POST = {
    "id": "post1", "scheduled_at": (NOW + timedelta(hours=24)).isoformat(),
    "text_content": ("Mẹo đơn giản là chọn một vài đồ dùng văn phòng "
                     "thường xuyên sử dụng để bàn làm việc gọn hơn."),
    "origin_growth_opportunity_id": None,
}
TREND = {
    "pillar": "work", "opportunity_id": "trend_id",
    "topic": "Cách sắp xếp bàn làm việc và sử dụng hiệu quả không gian",
}
NEW = {
    "pillar": "work", "why_useful": "Hữu ích",
    "post_text": (
        "Không gian làm việc có hạn thì nên bắt đầu từ đâu? "
        "Thử nhóm đồ dùng theo tần suất sử dụng rồi mới quyết định "
        "món nào nên đặt gần tay nhất. Bạn đã thử cách nào?"
    ),
}


class TrendRefreshTests(unittest.TestCase):
    def test_disconnected_brand_never_uses_meta_or_edited_posts(self):
        db = MagicMock()
        with patch("threads.refresh.get_channel",
                   return_value={"id": "brand", "status": "awaiting_oauth"}), \
             patch("threads.refresh.generate_ai_post") as ai:
            self.assertEqual(refresh_next(db, NOW), "awaiting_owner_meta_oauth")
        ai.assert_not_called()
        db.request.assert_not_called()

    def test_never_replace_metricool_post(self):
        db = MagicMock()
        db.request.side_effect = [[], []]
        with patch("threads.refresh.get_channel", return_value=CHANNEL), \
             patch("threads.refresh.generate_ai_post") as ai:
            self.assertEqual(refresh_next(db, NOW), "no_upcoming_queued_post")
        ai.assert_not_called()

    def test_fresh_trend_replaces_only_one_future_queued_post(self):
        db = MagicMock()
        db.request.side_effect = [[], [POST], [{"id": "post1"}]]
        with patch("threads.refresh.get_channel", return_value=CHANNEL), \
             patch("threads.refresh.select_topic", return_value=TREND), \
             patch("threads.refresh.generate_ai_post", return_value=NEW):
            self.assertEqual(refresh_next(db, NOW), "trend_applied_to_tomorrow")
        update=db.request.call_args
        self.assertEqual(update.args[0], "PATCH")
        self.assertEqual(update.args[1], "/threads_posts")
        self.assertEqual(update.kwargs["params"]["status"], "eq.queued")
        self.assertEqual(update.kwargs["payload"]["origin_growth_opportunity_id"],
                         "trend_id")
        self.assertEqual(update.kwargs["payload"]["text_content"], NEW["post_text"])

    def test_weekly_limit_suppresses_new_trend(self):
        db = MagicMock()
        db.request.return_value = [{"id": str(i)}
                                   for i in range(MAX_TREND_POSTS_WEEK)]
        with patch("threads.refresh.get_channel", return_value=CHANNEL), \
             patch("threads.refresh.generate_ai_post") as ai:
            self.assertEqual(refresh_next(db, NOW), "weekly_trend_limit")
        ai.assert_not_called()

    def test_no_old_news_far_from_publish(self):
        db = MagicMock()
        later = dict(POST, scheduled_at=(NOW + timedelta(days=14)).isoformat())
        db.request.side_effect = [[], [later]]
        with patch("threads.refresh.get_channel", return_value=CHANNEL), \
             patch("threads.refresh.select_topic") as topic:
            self.assertEqual(refresh_next(db, NOW), "not_yet_near_publication")
        topic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
