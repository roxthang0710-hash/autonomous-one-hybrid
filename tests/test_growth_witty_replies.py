"""No live Meta writes: owner-approved Vietnamese comment tests."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from growth.voice import VOICE_RULES, suitable_reply
from growth.engage import MAX_DAILY_ATTEMPTS, eligible, run

NOW = datetime(2026, 11, 2, 9, 20, tzinfo=timezone.utc)
ORIGINAL = (
    "Đi làm văn phòng mà dây sạc laptop cứ rối như tơ vò. "
    "Mọi người có cách nào sắp xếp đồ dùng để bàn làm việc gọn hơn không?"
)
COMMENT = (
    "Dây sạc laptop chắc có kế hoạch riêng: vừa cất xong đã toang 😭 "
    "Gom theo loại vào túi nhỏ có thể giúp bàn làm việc đỡ rối hơn."
)


def proposal():
    return {
        "opportunity_id": "11111111-1111-4111-8111-111111111111",
        "status": "needs_review", "kind": "reply_suggestion",
        "draft_text": COMMENT, "quality_score": 85,
        "target_post_id": "90000123456",
        "target_post_url": "https://www.threads.com/@realposter/post/abc",
        "expires_at": (NOW + timedelta(hours=36)).isoformat(),
        "relevance_score": 74, "risk_flags": [],
        "source": "threads_keyword_api", "niche": "work",
        "original_post_text": ORIGINAL,
        "target_published_at": (NOW-timedelta(hours=2)).isoformat()
    }


class WittyCommentTests(unittest.TestCase):
    def test_owner_requested_style_is_configured(self):
        self.assertIn("trẻ trung", VOICE_RULES)
        self.assertIn("vibe", VOICE_RULES)
        self.assertIn("thương hiệu", VOICE_RULES)
        self.assertEqual(MAX_DAILY_ATTEMPTS, 3)

    def test_relevant_witty_reply_is_allowed(self):
        self.assertTrue(suitable_reply(COMMENT, ORIGINAL))
        self.assertTrue(eligible(proposal(), NOW))

    def test_generic_engagement_bait_is_rejected(self):
        bad = (
            "Hay quá ạ, bạn theo dõi kênh mình nhé để xem các bí quyết "
            "hay về văn phòng và công nghệ vào mỗi ngày."
        )
        self.assertFalse(suitable_reply(bad, ORIGINAL))
        self.assertFalse(suitable_reply(
            "Cứ chill thôi mọi người, hôm nay vui quá quá quá nè!!!",
            ORIGINAL))

    def test_repetitive_joke_blocked(self):
        self.assertFalse(suitable_reply(COMMENT, ORIGINAL, [COMMENT]))

    def test_safety_filters_commercial_and_fake_persona(self):
        p=proposal()
        p["draft_text"]="Mua ngay link bio nè, mình đã mua laptop này rồi tốt lắm!"
        self.assertFalse(eligible(p, NOW))
        self.assertFalse(suitable_reply(
            "Văn phòng này chán ghê, follow mình ngay nhé! "
            "Laptop và bàn làm việc phải xịn mới đẹp.",
            ORIGINAL))


class VerifiedReplyWorkerTests(unittest.TestCase):
    def fake_db(self, *, claim=True, target=None):
        db=MagicMock()
        def request(method,path,**kwargs):
            if path=="/growth_engagement_queue":
                return [proposal()]
            if path=="/growth_engagement_attempts":
                return []
            if path=="/growth_opportunities":
                return []
            if path=="/rpc/growth_claim_safe_reply":
                return [{"attempt_id":"22222222-2222-4222-8222-222222222222"}] if claim else []
            raise AssertionError("Unexpected DB path "+path)
        db.request.side_effect=request
        return db

    def test_without_owner_meta_permission_never_posts(self):
        db=self.fake_db()
        with patch("growth.engage.get_credentials",return_value=None), \
             patch("growth.engage.send_reply") as publish:
            self.assertEqual(run(db=db,now=NOW),"not_authorized")
            publish.assert_not_called()

    def test_atomic_claim_denial_never_calls_meta_publish(self):
        db=self.fake_db(claim=False)
        with patch("growth.engage.get_credentials",return_value=("test_token","dohay_dilam")), \
             patch("growth.engage.verify_meta_account"), \
             patch("growth.engage.thread_request",return_value={
                 "id":"90000123456","text":ORIGINAL,"username":"realposter"}), \
             patch("growth.engage.send_reply") as send:
            self.assertEqual(run(db=db,now=NOW),"safety_claim_rejected")
            send.assert_not_called()

    def test_one_context_checked_reply_after_db_claim(self):
        db=self.fake_db()
        with patch("growth.engage.get_credentials",return_value=("test_token","dohay_dilam")), \
             patch("growth.engage.verify_meta_account"), \
             patch("growth.engage.thread_request",return_value={
                 "id":"90000123456","text":ORIGINAL,"username":"realposter"}), \
             patch("growth.engage.send_reply",return_value=("container","meta_reply")) as send:
            self.assertEqual(run(db=db,now=NOW),"one_useful_reply_posted")
            send.assert_called_once()
            self.assertEqual(send.call_args.args[1],"90000123456")
            rpc=[call for call in db.request.call_args_list
                 if call.args[1]=="/rpc/growth_claim_safe_reply"]
            self.assertEqual(len(rpc),1)

    def test_edited_hot_topic_cannot_be_replied_to(self):
        db=self.fake_db()
        with patch("growth.engage.get_credentials",return_value=("test_token","dohay_dilam")), \
             patch("growth.engage.verify_meta_account"), \
             patch("growth.engage.thread_request",return_value={
                 "id":"90000123456",
                 "text":"Đi làm văn phòng nhưng chuyện chính trị này rất đáng cãi nhau",
                 "username":"realposter"}), \
             patch("growth.engage.send_reply") as send:
            self.assertEqual(run(db=db,now=NOW),"target_changed_or_not_safe")
            send.assert_not_called()

    def test_uncertain_meta_write_never_automatically_retries(self):
        db=self.fake_db()
        with patch("growth.engage.get_credentials",return_value=("test_token","dohay_dilam")), \
             patch("growth.engage.verify_meta_account"), \
             patch("growth.engage.thread_request",return_value={
                 "id":"90000123456","text":ORIGINAL,"username":"realposter"}), \
             patch("growth.engage.send_reply",side_effect=TimeoutError("simulated")) as send:
            with self.assertRaises(RuntimeError):
                run(db=db,now=NOW)
            send.assert_called_once()
            self.assertEqual(db.patch.call_args.args[2]["status"],"uncertain")


if __name__=="__main__":
    unittest.main()
