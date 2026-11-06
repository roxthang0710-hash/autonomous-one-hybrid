"""Regression checks for the owner-approved 06/11 visual backfill snapshot.

This tests creative briefs only; no provider publishing or media mutation.
"""
import json
import unittest
from pathlib import Path
from scripts.enna_roundhead_brief import build_image_brief

MANIFEST=Path(__file__).resolve().parents[1]/"config"/"enna_visual_backfill_2026_11_06.json"

class VisualBackfillPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_complete_immutable_provider_snapshot(self):
        plan=self.plan
        self.assertEqual(plan["owner_style_revision"],"v4.1_clean_chat_balance")
        self.assertEqual(plan["changes_to_existing_posts"],0)
        self.assertEqual(plan["approved_rendered_images_added"],0)
        rows=plan["slots"]
        self.assertEqual(len(rows),31)
        self.assertEqual(len({r["metricool_post_id"] for r in rows}),len(rows))
        self.assertEqual(sum(r["media_count_at_audit"]==0 for r in rows),13)
        self.assertEqual(sum(r["media_count_at_audit"]>0 for r in rows),18)
        self.assertTrue(all(r["status"]=="pending_manual_visual_review" for r in rows))
        self.assertTrue(all(r["proposed_only"] is True for r in rows))
        self.assertTrue(all(r["channel"] in ("threads","facebook","instagram") for r in rows))

    def test_each_missing_image_has_specific_safe_approved_mode(self):
        proposals=[r for r in self.plan["slots"] if not r["media_count_at_audit"]]
        for r in proposals:
            self.assertEqual(r["action"],"render_and_review_proposed_illustration")
            b=r["brief"]
            result=build_image_brief(b["scene"],b["setup"],b["payoff"],
                composition=b["composition"],character_emotion=b["character_emotion"],
                layout_mode=r["layout_mode"])
            self.assertEqual(result["layout_mode"],r["layout_mode"])
            self.assertFalse(result["social_published"])
            self.assertTrue(result["requires_human_visual_review"])
            self.assertIn(b["payoff"],result["prompt"])
            self.assertNotIn("https://shopee.",result["prompt"])

    def test_media_bearing_posts_are_audits_not_false_replacements(self):
        existing=[r for r in self.plan["slots"] if r["media_count_at_audit"]]
        self.assertTrue(all(r["action"]=="audit_existing_media" for r in existing))
        self.assertTrue(all(r["brief"] is None and r["layout_mode"] is None for r in existing))
        self.assertIn("do not change scheduled copy",self.plan["instructions"])
        self.assertIn("No affiliate",self.plan["instructions"])

if __name__=="__main__":
    unittest.main()
