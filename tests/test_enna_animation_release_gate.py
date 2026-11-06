"""Regression tests for Enna's Flow-first animation policy."""
import json
from pathlib import Path
import unittest

from scripts.enna_animation_release_gate import review_episode

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "config" / "enna_animation_flow_first_2026_11_07.json").read_text(encoding="utf-8"))


def good():
    return {
        "series_id": "ong_ba_ba_tu",
        "reference_canva_asset": "MAHaKjcgNCw",
        "generator": "google_flow",
        "mp4_file_verified": True,
        "width": 720, "height": 1280,
        "duration_seconds": 8,
        "character_consistency_verified": True,
        "articulated_motion_verified": True,
        "story_setup_action_payoff_verified": True,
        "rights_verified": True,
        "original_copy_check_passed": True,
        "owner_visual_approved": True,
        "new_spend": 0,
        "published": False
    }


class FlowFirstReleaseGateTests(unittest.TestCase):
    def test_owner_approved_flow_output_can_pass_only_with_evidence(self):
        self.assertTrue(review_episode(good(), POLICY)["release_ready"])

    def test_actual_landscape_ltx_draft_is_rejected(self):
        m = good()
        m.update(generator="ltx_video_2_3", duration_seconds=5,
                 width=1536, height=1024,
                 owner_visual_approved=False, story_setup_action_payoff_verified=False)
        res = review_episode(m, POLICY)
        self.assertFalse(res["release_ready"])
        self.assertIn("fallback_generator_not_approved", res["reasons"])
        self.assertIn("not_portrait_9_16", res["reasons"])
        self.assertIn("missing_comedic_payoff", res["reasons"])

    def test_no_mp4_cannot_be_reported_complete(self):
        m = good()
        m["mp4_file_verified"] = False
        self.assertIn("no_verified_mp4", review_episode(m, POLICY)["reasons"])

    def test_slide_motion_fails(self):
        m = good()
        m["articulated_motion_verified"] = False
        self.assertIn("slide_motion_or_unverified", review_episode(m, POLICY)["reasons"])

    def test_reference_character_drift_fails(self):
        m = good()
        m["reference_canva_asset"] = "wrong"
        self.assertIn("reference_character_mismatch", review_episode(m, POLICY)["reasons"])

    def test_paid_generation_and_autopublish_fail(self):
        m = good()
        m.update(new_spend=1, published=True)
        self.assertFalse(review_episode(m, POLICY)["release_ready"])

    def test_unapproved_fallback_requires_explicit_owner_override(self):
        m = good()
        m["generator"] = "another_video_tool"
        self.assertIn("fallback_generator_not_approved", review_episode(m, POLICY)["reasons"])
        m["fallback_explicitly_owner_approved"] = True
        self.assertTrue(review_episode(m, POLICY)["release_ready"])


if __name__ == "__main__":
    unittest.main()
