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


    def test_enna_blocks_near_duplicate_daily_draft(self):
        db=MagicMock()
        original = (
            "Bàn làm việc nhỏ vẫn có thể gọn hơn nếu bạn sắp xếp dây sạc "
            "và phụ kiện theo tần suất sử dụng mỗi ngày."
        )
        duplicate = original.replace("vẫn có thể gọn hơn", "có thể gọn hơn")
        def req(method,path,*,params=None,payload=None,prefer=None):
            if method=="GET" and path=="/threads_posts":
                if params.get("status")=="eq.queued":
                    return []
                if params.get("order")=="created_at.desc":
                    return [{"id":"past","text_content":original,
                             "pillar":"organize","scheduled_at":"2026-11-17T02:30:00+00:00"}]
                return []
            if method=="POST":
                raise AssertionError("Near-duplicate should never be saved")
            return []
        db.request.side_effect=req
        result={"pillar":"organize","post_text":duplicate,
                "why_useful":"Mẹo sắp xếp góc bàn"}
        with patch("threads.content.get_channel",return_value={
                 "id":"brand","status":"paused"}), \
             patch("threads.content.generate_ai_post",return_value=result), \
             patch("threads.content.scheduled_start",
                   return_value=datetime(2026,11,18,9,30,tzinfo=VN)):
            self.assertEqual(plan_next(db),"near_duplicate_generated")


if __name__ == "__main__":
    unittest.main()
