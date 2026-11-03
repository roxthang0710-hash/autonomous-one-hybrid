"""Offline tests; no API keys or external accounts needed."""
import copy
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from affiliate.runner import (
    SCHEMA, validate_draft, scoring, run_key, week_start, main,
)

VALID = {
    "title": "Những đồ dùng cần cân nhắc cho chuyến công tác",
    "target_audience": "Người đi công tác",
    "customer_problem": "Mang nhiều đồ không tiện",
    "organic_channel": "Facebook Fanpage chính chủ",
    "content_format": "Bài viết dạng checklist",
    "draft_text": "Checklist cách sắp xếp đồ khi đi công tác; các gợi ý cần kiểm chứng.",
    "validation_plan": "Viết bản nháp và cho chủ sở hữu đánh giá trước khi đăng",
    "success_metric": "Tối thiểu 20 lượt xem tự nhiên và 3 lượt click được xác nhận",
    "stop_rule": "Ngừng thử sau 14 ngày nếu không có nhu cầu",
    "claims_to_verify": ["Nguồn gốc sản phẩm", "Công dụng thực tế"],
    "risks": ["Chưa có sản phẩm được kiểm chứng", "Chưa có tài khoản liên kết"],
    "owner_next_action": "Đăng ký và xác minh điều kiện chương trình",
    "expected_spend_vnd": 0,
}
PROGRAM = {
    "code": "shopee_koc", "name": "Shopee KOC Affiliate",
    "review_status": "research_only", "commission_notes": "unknown",
    "official_url": "https://shopee.vn/affiliate/",
    "evidence_url": "https://help.shopee.vn/portal/4/article/91992",
}


class AffiliateRunnerTests(unittest.TestCase):
    def test_strict_schema(self):
        self.assertEqual(set(VALID), set(SCHEMA["required"]))
        self.assertFalse(SCHEMA["additionalProperties"])

    def test_draft_is_review_only_and_has_no_affiliate_link(self):
        out = validate_draft(copy.deepcopy(VALID))
        self.assertEqual(out["draft_status"], "needs_owner_review")
        self.assertIsNone(out["affiliate_link"])
        self.assertEqual(out["expected_spend_vnd"], 0)
        self.assertIn("hoa hồng", out["disclosure_instruction"])
        self.assertIn("chủ sở hữu", out["distribution_guardrail"])

    def test_paid_campaign_rejected(self):
        data = dict(VALID, expected_spend_vnd=50000)
        with self.assertRaises(ValueError):
            validate_draft(data)

    def test_unverified_blog_or_groups_rejected(self):
        for channel in ("Blog cá nhân", "Nhóm Facebook công khai"):
            with self.subTest(channel=channel):
                data = dict(VALID, organic_channel=channel)
                with self.assertRaises(ValueError):
                    validate_draft(data)

    def test_links_rejected(self):
        data = dict(VALID, draft_text="Đặt tại https://shop.example/?x=2")
        with self.assertRaises(ValueError):
            validate_draft(data)

    def test_missing_claims_field_rejected(self):
        data = dict(VALID)
        del data["claims_to_verify"]
        with self.assertRaises(ValueError):
            validate_draft(data)

    def test_score_is_not_profit_prediction(self):
        score, notes = scoring(PROGRAM, validate_draft(dict(VALID)))
        self.assertTrue(0 <= score <= 100)
        self.assertTrue(any("không dự báo lợi nhuận" in s for s in notes))

    def test_schedule_key_dedup_same_day(self):
        dt = datetime(2026, 11, 3, 3, tzinfo=timezone.utc)
        self.assertEqual(run_key("scheduled", dt), run_key("scheduled", dt))
        self.assertEqual(run_key("manual", dt, "123456"), "manual:123456")
        with self.assertRaises(ValueError):
            run_key("manual", dt, "abc")

    def test_week_start_utc(self):
        dt = datetime(2026, 11, 5, tzinfo=timezone.utc)
        self.assertEqual(week_start(dt), "2026-11-02T00:00:00+00:00")

    def test_no_groq_call_when_pending_backlog_full(self):
        fake = MagicMock()
        fake.request.side_effect = [
            [],  # recent runs
            [{"id": str(i)} for i in range(6)],  # pending
        ]
        with patch("affiliate.runner.Database", return_value=fake), \
             patch("affiliate.runner.generate") as generate, \
             patch.dict("os.environ", {"AFFILIATE_TRIGGER": "scheduled"}):
            main()
        generate.assert_not_called()
        self.assertEqual(fake.request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
