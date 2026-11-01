import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from growth.runner import build_candidates, key_for, run
from growth.generator import validate_draft
from growth.optimizer import analyze

NOW = datetime(2026, 11, 2, 9, tzinfo=timezone.utc)
FEED = [{
    "title": "Mẹo sắp xếp bàn làm việc nhỏ",
    "source": "google_news_vn",
    "source_url": "https://news.google.com/rss/articles/abc",
    "fingerprint": "hash_a",
    "published_at": NOW,
}]
DRAFT = {
    "post_text": ("Góc làm việc nhỏ có thể bắt đầu từ việc phân loại đồ dùng theo "
                  "tần suất sử dụng. Nếu bàn chỉ còn chỗ cho 5 món, bạn sẽ giữ gì?"),
    "hook": "Góc bàn nhỏ nhưng tiện",
    "relevance_reason": "Liên quan tới người làm việc tại văn phòng",
    "why_safe": "Câu hỏi đơn giản, không khẳng định giá, trải nghiệm hay sự kiện",
    "verification_needed": ["Xác minh bài gốc có đúng chủ đề"],
}


class GrowthRunnerTests(unittest.TestCase):
    def test_candidate_relevance(self):
        rows = build_candidates(FEED, now=NOW)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "google_news_vn")

    def test_sensitive_trend_not_selected(self):
        bad = dict(FEED[0], title="Bầu cử và cuộc tranh cãi nóng")
        self.assertEqual(build_candidates([bad], now=NOW), [])

    def test_draft_has_no_fake_persona_or_sales_link(self):
        self.assertEqual(validate_draft(DRAFT)["post_text"], DRAFT["post_text"])
        with self.assertRaises(ValueError):
            validate_draft(dict(DRAFT, post_text="Mua ngay https://example.com"))

    def test_idempotent_key(self):
        self.assertEqual(key_for(NOW, "123456"), "github:123456")
        self.assertEqual(key_for(NOW), key_for(NOW))

    def test_pipeline_stores_one_genuine_lead(self):
        db = MagicMock()
        def request(method, path, **kwargs):
            if path == "/growth_runs" and method == "POST":
                return [{"id": "run1"}]
            if path == "/growth_opportunities" and method == "GET":
                return []
            if path == "/growth_signals" and method == "POST":
                return [{"id": "sig1", "fingerprint": "hash_a"}]
            if path == "/growth_signals" and method == "GET":
                return [{"id": "sig1", "fingerprint": "hash_a"}]
            if path == "/growth_opportunities" and method == "POST":
                return [{"id": "idea1"}]
            return []
        db.request.side_effect = request
        with patch("growth.runner.discover", return_value=(FEED, {"news": 1})), \
             patch("growth.runner.compose", return_value=DRAFT), \
             patch("growth.runner.search_threads") as search:
            out = run(db=db, now=NOW)
        self.assertEqual(out["drafts"], 1)
        search.assert_not_called()
        self.assertTrue(any(
            call.args[1] == "/growth_opportunities"
            for call in db.request.call_args_list
        ))

    def test_no_external_source_does_not_invent_drafts(self):
        db = MagicMock()
        def request(method, path, **kwargs):
            if path == "/growth_runs" and method == "POST":
                return [{"id": "run1"}]
            if path == "/growth_opportunities" and method == "GET":
                return []
            return []
        db.request.side_effect = request
        with patch("growth.runner.discover", return_value=([], {"trends": "Error"})), \
             patch("growth.runner.compose") as ai:
            out = run(db=db, now=NOW)
        self.assertEqual(out["status"], "source_unavailable")
        ai.assert_not_called()

    def test_optimizer_requires_real_data(self):
        self.assertEqual(analyze([])["status"], "insufficient_observations")
        rows = [{"post_views": 100, "interactions": 5,
                 "published_posts": 1, "followers": 2} for _ in range(7)]
        out = analyze(rows)
        self.assertEqual(out["status"], "baseline_available")
        self.assertEqual(out["interaction_per_view"], 0.05)


if __name__ == "__main__":
    unittest.main()
