import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from scripts.enna_video_pilot import DEFAULT, validate_plan, episode_files, export


class VideoRevenuePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def test_three_different_original_pilots(self):
        episodes = validate_plan(self.plan)
        self.assertEqual(len(episodes), 3)
        self.assertEqual(
            {e["mode"] for e in episodes},
            {"clean_chat", "practical_ui_tip"}
        )
        for episode in episodes:
            manifest, srt = episode_files(episode)
            self.assertFalse(manifest["actually_published"])
            self.assertFalse(manifest["actual_video_rendered"])
            self.assertFalse(manifest["commercial"])
            self.assertIn("00:00:20,000", srt)

    def test_reject_unapproved_sales(self):
        plan = deepcopy(self.plan)
        plan["commercial_links_allowed"] = True
        with self.assertRaises(ValueError):
            validate_plan(plan)
        plan = deepcopy(self.plan)
        plan["experiments"][0]["commercial"] = True
        with self.assertRaises(ValueError):
            validate_plan(plan)

    def test_reject_missing_review_or_unsafe_beats(self):
        plan = deepcopy(self.plan)
        plan["release_gates"]["manual_visual_review"] = False
        with self.assertRaises(ValueError):
            validate_plan(plan)
        plan = deepcopy(self.plan)
        plan["experiments"][0]["beats"][2]["start"] = 0
        with self.assertRaises(ValueError):
            validate_plan(plan)
        plan = deepcopy(self.plan)
        plan["experiments"][0]["beats"][0]["text"] = "https://example.com/offer"
        with self.assertRaises(ValueError):
            validate_plan(plan)

    def test_output_is_a_review_only_package_not_false_video_claim(self):
        with tempfile.TemporaryDirectory() as t:
            result = export(DEFAULT, Path(t))
            self.assertEqual(result["episodes"], 3)
            self.assertEqual(result["video_files"], 0)
            self.assertEqual(result["affiliate_links"], 0)
            self.assertEqual(len(list(Path(t).glob("*.srt"))), 3)
            self.assertEqual(len(list(Path(t).glob("*.storyboard.json"))), 3)
            self.assertTrue(all(
                not json.loads(f.read_text(encoding="utf-8"))["actually_published"]
                for f in Path(t).glob("*.storyboard.json")
            ))


if __name__ == "__main__":
    unittest.main()
