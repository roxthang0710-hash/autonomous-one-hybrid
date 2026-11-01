"""Avoid overlapping any day reserved in Metricool when creating new drafts."""
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from threads.content import plan_next, VN


class ContentHandoffTests(unittest.TestCase):
    def test_first_meta_draft_starts_after_metricool_calendar(self):
        db = MagicMock()
        channel = {"id": "channel1", "brand_key": "do_hay_di_lam"}
        def request(method, path, *, params=None, payload=None, prefer=None):
            if path == "/threads_posts" and method == "GET":
                if params.get("status") == "eq.queued":
                    return []
                if params.get("order") == "created_at.desc":
                    return [{"text_content": "Một ý tưởng cũ về văn phòng",
                             "pillar": "work", "scheduled_at":
                             "2026-11-17T02:30:00+00:00"}]
                if params.get("status") == "in.(queued,scheduled_external,posted,publishing,uncertain)":
                    return [{"scheduled_at": "2026-11-17T02:30:00+00:00"}]
            if path == "/threads_posts" and method == "POST":
                return [{"id": "new"}]
            return []
        db.request.side_effect = request
        post = {
            "pillar": "travel",
            "post_text": ("Lúc chuẩn bị hành lý cho chuyến công tác ngắn, "
                          "bạn ưu tiên chọn túi nhỏ hay giảm số món mang theo?"),
            "why_useful": "Hỏi cách chọn hành lý",
        }
        with patch("threads.content.get_channel", return_value=channel), \
             patch("threads.content.generate_ai_post", return_value=post), \
             patch("threads.content.scheduled_start",
                   return_value=datetime(2026, 11, 3, 9, 30, tzinfo=VN)):
            result = plan_next(db)
        self.assertEqual(result, "created_one")
        writes = [x for x in db.request.call_args_list if x.args[0] == "POST"]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0].kwargs["payload"]["scheduled_at"],
                         "2026-11-18T09:30:00+07:00")


if __name__ == "__main__":
    unittest.main()
