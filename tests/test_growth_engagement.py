import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from growth.engage import (
    eligible, get_credentials, run, send_reply, verify_meta_account,
)

NOW = datetime(2026, 11, 2, 9, tzinfo=timezone.utc)
CANDIDATE = {
    "opportunity_id": "op1", "kind": "reply_suggestion",
    "status": "needs_review", "source": "threads_keyword_api",
    "quality_score": 91, "relevance_score": 84,
    "risk_flags": [], "target_post_id": "post1",
    "target_post_url": "https://www.threads.com/@other/post/abc",
    "original_post_text": "Tư vấn sắp xếp bàn làm việc nhỏ cho dân công sở",
    "expires_at": (NOW + timedelta(hours=24)).isoformat(),
    "draft_text": (
        "Một cách hữu ích là phân loại vật dụng theo tần suất sử dụng và "
        "để đồ thường cần ở vị trí dễ lấy. Bạn đang ưu tiên không gian "
        "hay thao tác nhanh khi sắp xếp bàn làm việc?"
    ),
}


class EngagementTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict("os.environ", {
            "THREADS_AUTO_ENGAGE_ENABLED": "false",
            "THREADS_ENGAGE_ACCESS_TOKEN": "secret",
            "THREADS_EXPECTED_USERNAME": "dohay_dilam"}):
            self.assertIsNone(get_credentials())
            db = MagicMock()
            self.assertEqual(run(db=db), "not_authorized")
            db.request.assert_not_called()

    def test_invalid_expected_account_disables_writes(self):
        with patch.dict("os.environ", {
            "THREADS_AUTO_ENGAGE_ENABLED": "true",
            "THREADS_ENGAGE_ACCESS_TOKEN": "secret",
            "THREADS_EXPECTED_USERNAME": "someone_else"}):
            self.assertIsNone(get_credentials())

    def test_legitimate_relevant_reply_eligible(self):
        self.assertTrue(eligible(CANDIDATE, NOW))
        self.assertFalse(eligible(dict(CANDIDATE, quality_score=70), NOW))
        self.assertFalse(eligible(dict(CANDIDATE, source="google_news_vn"), NOW))
        self.assertFalse(eligible(dict(CANDIDATE, target_post_id=None), NOW))
        self.assertFalse(eligible(dict(CANDIDATE,
            draft_text="Theo dõi kênh để xem nhiều mẹo hữu ích!"), NOW))

    def test_expired_or_tragedy_not_eligible(self):
        self.assertFalse(eligible(dict(CANDIDATE,
            expires_at=(NOW - timedelta(seconds=2)).isoformat()), NOW))
        bad = dict(CANDIDATE,
            draft_text=("Chúng ta hãy tranh luận về tai nạn thương tâm "
                        "và tăng lượt tương tác bằng cách chia sẻ thật nhiều."))
        self.assertFalse(eligible(bad, NOW))

    def test_wrong_user_cannot_reply(self):
        with patch("growth.engage.thread_request",
                   return_value={"id": "444", "username": "wrong"}):
            with self.assertRaises(ValueError):
                verify_meta_account("token", "dohay_dilam")

    def test_meta_reply_is_exactly_two_write_calls(self):
        calls = []
        def fake(method, path, token, **kwargs):
            calls.append((method, path, kwargs))
            if path.endswith("/threads"):
                return {"id": "container123"}
            return {"id": "reply123"}
        with patch("growth.engage.thread_request", side_effect=fake):
            container, reply = send_reply("token", "target", "Phản hồi hữu ích")
        self.assertEqual((container, reply), ("container123", "reply123"))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][2]["data"]["reply_to_id"], "target")

    def test_one_reply_per_day_before_meta_call(self):
        db = MagicMock()
        db.request.return_value = [{"id": "prior_attempt"}]
        with patch("growth.engage.get_credentials",
                   return_value=("token", "dohay_dilam")), \
             patch("growth.engage.thread_request") as meta:
            self.assertEqual(run(db=db, now=NOW), "daily_cap")
        meta.assert_not_called()

    def test_ambiguous_meta_result_is_not_retried(self):
        db = MagicMock()
        def select(method, path, **kwargs):
            if path == "/growth_engagement_attempts" and method == "GET":
                return []
            if path == "/growth_engagement_queue":
                return [CANDIDATE]
            if path == "/growth_engagement_attempts" and method == "POST":
                return [{"id": "attempt1"}]
            return []
        db.request.side_effect = select
        with patch("growth.engage.get_credentials",
                   return_value=("token", "dohay_dilam")), \
             patch("growth.engage.verify_meta_account"), \
             patch("growth.engage.thread_request",
                   return_value={"id": "post1",
                                 "text": CANDIDATE["original_post_text"]}), \
             patch("growth.engage.send_reply", side_effect=TimeoutError()) as send:
            with self.assertRaises(RuntimeError):
                run(db=db, now=NOW)
        send.assert_called_once()
        self.assertTrue(any(
            c.args[0] == "growth_engagement_attempts" and
            c.args[2].get("status") == "uncertain"
            for c in db.patch.call_args_list
        ))


if __name__ == "__main__":
    unittest.main()
