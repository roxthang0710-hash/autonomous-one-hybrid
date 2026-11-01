import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from threads.planner import SEEDS, VN, check_post, planned_seed_rows, scheduled_start


class PlannerTests(unittest.TestCase):
    def test_14_original_posts_pass(self):
        self.assertEqual(len(SEEDS), 14)
        rows = planned_seed_rows("some-test-uuid")
        self.assertEqual(len(rows), 14)
        self.assertEqual(len({x["content_key"] for x in rows}), 14)
        self.assertTrue(all(not check_post(x["text_content"]) for x in rows))
        self.assertTrue(all(x["status"] == "queued" for x in rows))

    def test_no_fake_testimonial_or_links(self):
        self.assertIn("blocked_pattern", check_post(
            "Mình đã mua một sản phẩm và trải nghiệm cực tốt, hãy mua ngay theo link https://example.com"
        ))
        self.assertFalse(check_post(
            "Bàn làm việc nhỏ nên chọn cách sắp xếp theo thói quen nào? Mỗi người có một cách dùng không gian khác nhau."
        ))

    def test_schedule_uses_vietnam_time(self):
        now = datetime(2026, 11, 2, 10, 0, tzinfo=VN)
        target = scheduled_start(now)
        self.assertEqual(target.day, 3)
        self.assertEqual(target.hour, 9)
        self.assertEqual(target.minute, 30)

    def test_schedule_before_slot(self):
        now = datetime(2026, 11, 2, 8, 0, tzinfo=VN)
        self.assertEqual(scheduled_start(now).day, 2)


if __name__ == "__main__":
    unittest.main()
