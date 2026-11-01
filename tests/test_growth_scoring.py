import unittest
from datetime import datetime, timedelta, timezone

from growth.scoring import classify, normalize


class GrowthScoringTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, tzinfo=timezone.utc)

    def test_diacritics_normalization(self):
        self.assertIn("ban lam viec", normalize("Bàn làm việc gọn gàng"))

    def test_relevant_fresh_topic(self):
        result = classify("5 cách sắp xếp bàn làm việc gọn gàng",
                          self.now - timedelta(hours=6), self.now)
        self.assertEqual(result["state"], "candidate")
        self.assertIn(result["niche"], ("work", "organize"))
        self.assertGreaterEqual(result["score"], 50)

    def test_popular_but_unrelated_must_not_hijack(self):
        self.assertEqual(classify("Trận bóng Chelsea gặp MU",
                                  self.now, self.now)["state"], "rejected")

    def test_rejects_politics_tragedy_and_gambling(self):
        for topic in ("Bầu cử đang gây tranh cãi",
                      "Tin nóng tai nạn gây chết người",
                      "Xổ số miền nam mới nhất",
                      "Cơn sốt crypto và cách kiếm tiền"):
            with self.subTest(topic=topic):
                x = classify(topic, self.now, self.now)
                self.assertEqual(x["state"], "rejected")

    def test_generic_labor_abroad_news_is_not_workplace_lifestyle(self):
        title = "Đi làm việc ở nước ngoài theo hợp đồng: chuyển dịch mới"
        result = classify(title, self.now, self.now)
        self.assertEqual(result["state"], "rejected")

    def test_old_headline_not_a_fresh_trend(self):
        self.assertEqual(classify("Mẹo du lịch hành lý",
                                  self.now - timedelta(days=8), self.now)["state"],
                         "expired")


if __name__ == "__main__":
    unittest.main()
