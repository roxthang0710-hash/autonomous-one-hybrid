"""Regression checks for Enna's factual workplace tool editorial rotation."""
import unittest

from threads.tech_editorial import TECH_BRIEFS, choose_tech_brief
from threads.planner import check_post


class TestTechEditorial(unittest.TestCase):
    def test_verified_briefs_have_expected_metadata(self):
        self.assertGreaterEqual(len(TECH_BRIEFS), 8)
        self.assertEqual(len({row["key"] for row in TECH_BRIEFS}), len(TECH_BRIEFS))
        for row in TECH_BRIEFS:
            self.assertIn(row["pillar"], ("work", "organize", "conversation", "travel"))
            self.assertGreater(len(row["prompt"]), 70)
            self.assertTrue(row["source"].startswith(("https://", "docs/")))
            self.assertNotIn("https://", row["prompt"])
            self.assertNotIn("affiliate", row["prompt"].lower())

    def test_only_one_in_three_new_posts_get_tool_brief(self):
        self.assertIsNone(choose_tech_brief(49))
        self.assertIsNone(choose_tech_brief(50))
        self.assertIsNotNone(choose_tech_brief(48))
        self.assertIsNotNone(choose_tech_brief(51))
        self.assertNotEqual(choose_tech_brief(48)["key"], choose_tech_brief(51)["key"])

    def test_rotation_is_bounded_and_deterministic(self):
        for index in range(len(TECH_BRIEFS) * 2):
            self.assertEqual(
                choose_tech_brief(index * 3)["key"],
                TECH_BRIEFS[index % len(TECH_BRIEFS)]["key"],
            )

    def test_invalid_count_is_rejected(self):
        for value in (-1, "3", None):
            with self.assertRaises(ValueError):
                choose_tech_brief(value)

    def test_existing_post_safety_gate_unchanged(self):
        self.assertTrue(check_post("Đặt mua ngay món này qua https://example.com nhé!"))


if __name__ == "__main__":
    unittest.main()
