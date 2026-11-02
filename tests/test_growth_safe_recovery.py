"""Grow only from sources that pass the safety and originality gates."""
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from growth.runner import run, MAX_CONTENT_ATTEMPTS

NOW = datetime(2026, 11, 2, 9, tzinfo=timezone.utc)
FEED = [
    {"title": "Mẹo sắp xếp bàn làm việc nhỏ", "source": "google_news_vn",
     "source_url": "https://news.google.com/rss/articles/abc",
     "fingerprint": "a", "published_at": NOW},
    {"title": "Cách phân loại đồ dùng công tác tiện lợi", "source": "google_news_vn",
     "source_url": "https://news.google.com/rss/articles/def",
     "fingerprint": "b", "published_at": NOW},
    {"title": "Sắp xếp dây sạc ở góc văn phòng", "source": "google_news_vn",
     "source_url": "https://news.google.com/rss/articles/ghi",
     "fingerprint": "c", "published_at": NOW},
]
VALID = {
    "post_text": ("Mỗi góc bàn có những vật dụng cần thiết khác nhau. "
                  "Bạn thường phân loại đồ dùng theo tần suất sử dụng "
                  "hay theo công việc để dễ tìm lại khi cần?"),
    "hook": "Phân loại góc bàn",
    "relevance_reason": "Hữu ích cho những người làm việc tại văn phòng",
    "why_safe": "Không khẳng định trải nghiệm, không liên kết thương mại",
    "verification_needed": ["Xác nhận nội dung nguồn"],
}


def db_fixture():
    db = MagicMock()
    def request(method, path, **kwargs):
        if path == "/growth_runs" and method == "POST":
            return [{"id": "run1"}]
        if path == "/growth_opportunities" and method == "GET":
            return []
        if path == "/growth_signals" and method == "POST":
            row = kwargs["payload"]
            return [{"id": "id_" + row["fingerprint"],
                     "fingerprint": row["fingerprint"]}]
        if path == "/growth_signals" and method == "GET":
            return [{"id": "id_" + k, "fingerprint": k}
                    for k in ("a", "b", "c")]
        if path == "/growth_opportunities" and method == "POST":
            return [{"id": "idea"}]
        return []
    db.request.side_effect = request
    return db


class SafeRecoveryTests(unittest.TestCase):
    def test_rejected_post_falls_back_to_next_eligible_signal(self):
        db = db_fixture()
        with patch("growth.runner.discover", return_value=(FEED, {"news": 3})), \
             patch("growth.runner.compose", side_effect=[
                 ValueError("unsafe draft"), VALID]) as llm:
            result = run(db=db, now=NOW)
        self.assertEqual(result["drafts"], 1)
        self.assertEqual(result["rejected_unsafe_drafts"], 1)
        self.assertEqual(llm.call_count, 2)
        saved = [c for c in db.request.call_args_list
                 if c.args[0] == "POST" and c.args[1] == "/growth_opportunities"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].kwargs["payload"]["signal_id"], "id_b")
        self.assertEqual(saved[0].kwargs["payload"]["status"], "needs_review")

    def test_all_unsafe_drafts_are_skipped_and_job_still_completes(self):
        db = db_fixture()
        with patch("growth.runner.discover", return_value=(FEED, {"news": 3})), \
             patch("growth.runner.compose", side_effect=ValueError("unsafe")) as llm:
            result = run(db=db, now=NOW)
        self.assertEqual(result["drafts"], 0)
        self.assertEqual(result["rejected_unsafe_drafts"], MAX_CONTENT_ATTEMPTS)
        self.assertEqual(llm.call_count, MAX_CONTENT_ATTEMPTS)
        self.assertEqual(db.patch.call_args.args[2]["status"], "success")
        self.assertFalse(any(c.args[0]=="POST" and c.args[1]=="/growth_opportunities"
                             for c in db.request.call_args_list))

    def test_real_groq_outage_does_not_silently_look_like_success(self):
        db = db_fixture()
        with patch("growth.runner.discover", return_value=(FEED, {"news": 3})), \
             patch("growth.runner.compose", side_effect=RuntimeError("GroqRateLimit")):
            with self.assertRaises(RuntimeError):
                run(db=db, now=NOW)
        self.assertEqual(db.patch.call_args.args[2]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
