"""Quality and evidence tests for original micro-comedy Reel prototypes."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.enna_micro_reels_lab import DEFAULT, validate, evaluate, export


class MicroReelsLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads(DEFAULT.read_text(encoding="utf-8"))

    def test_three_original_single_location_micro_video_briefs(self):
        items=validate(self.plan)
        self.assertEqual(len(items),3)
        self.assertEqual(len({x["comic_mechanism"] for x in items}),3)
        self.assertTrue(all(6000<=x["duration_ms"]<=10000 for x in items))
        self.assertTrue(all(x["locations"]==1 for x in items))

    def test_block_claim_reference_video_was_watched(self):
        d=deepcopy(self.plan)
        d["reference"]["video_playback_verified"]=True
        with self.assertRaisesRegex(ValueError,"reference_is_not_frame_by_frame_verified"):
            validate(d)

    def test_no_fake_rendered_or_published_success(self):
        for field in ("mp4_rendered","published","claim_of_viral_probability"):
            d=deepcopy(self.plan)
            d["status"][field]=True
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"unverified_media_completion_claim"):
                validate(d)

    def test_refuse_long_video_and_unapproved_social_follow_overlay(self):
        d=deepcopy(self.plan)
        d["variants"][0]["duration_ms"]=15000
        with self.assertRaises(ValueError):validate(d)
        d=deepcopy(self.plan)
        d["variants"][0]["follow_cta"]="Đừng quên follow nha"
        with self.assertRaisesRegex(ValueError,"no_interrupting_follow_cta"):validate(d)

    def test_no_extra_text_cards_or_broken_timeline(self):
        d=deepcopy(self.plan)
        d["variants"][0]["overlays"]=[{"at_ms":0,"until_ms":100,"text":"x"}]*3
        with self.assertRaisesRegex(ValueError,"excessive_text_overlay"):validate(d)
        d=deepcopy(self.plan)
        d["variants"][0]["beats"][1]["start_ms"]=0
        with self.assertRaisesRegex(ValueError,"noncontiguous_shot_timeline"):validate(d)

    def test_forbid_reposting_reference_and_promotional_urls(self):
        d=deepcopy(self.plan)
        d["variants"][0]["caption"]="@threesingsters đây là link hay https://example.com"
        with self.assertRaises(ValueError):validate(d)
        d=deepcopy(self.plan)
        d["variants"][0]["caption"]="@threesingsters copied reference"
        with self.assertRaisesRegex(ValueError,"unlicensed_reference_or_promotional_link"):validate(d)

    def test_audio_rights_and_manual_review_are_required(self):
        for required in ("audio_rights_verified","human_visual_humor_review","keep_social_post_manual_approval"):
            d=deepcopy(self.plan)
            d["release_gates"][required]=False
            with self.subTest(required=required),self.assertRaisesRegex(ValueError,"unsafe_release_gates"):
                validate(d)

    def test_export_creates_storyboard_only_not_video_or_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            result=export(DEFAULT,out)
            self.assertEqual(result["actual_mp4_files"],0)
            self.assertEqual(result["publications"],0)
            self.assertEqual(len(list(out.glob("*.storyboard.json"))),3)
            self.assertFalse(list(out.glob("*.mp4")))
            self.assertTrue(all(
                not json.loads(f.read_text(encoding="utf-8"))["publish_approved"]
                for f in out.glob("*.storyboard.json")
            ))

    def test_missing_reach_or_shares_are_not_zero(self):
        result=evaluate({"views":500},8000)
        self.assertIsNone(result["reach"])
        self.assertIsNone(result["shares_per_reach"])
        self.assertIsNone(result["average_watch_to_duration"])
        self.assertTrue(result["metric_absence_is_not_zero"])

    def test_verified_metrics_rates_and_replay_aware_watch_ratio(self):
        result=evaluate({"reach":1000,"views":1400,"shares":34,"likes":77,
                         "comments":9,"avg_watch_seconds":9.6},8000)
        self.assertAlmostEqual(result["shares_per_reach"],.034)
        self.assertAlmostEqual(result["likes_per_reach"],.077)
        self.assertAlmostEqual(result["average_watch_to_duration"],1.2)
        self.assertEqual(result["interpretation"],"directional_review_only_not_causal_proof")
        self.assertIsNone(result["saves_per_reach"])

    def test_tiny_sample_not_dubbed_winner(self):
        value=evaluate({"reach":15,"shares":10,"likes":12},8000)
        self.assertEqual(value["interpretation"],"exploratory_only")

    def test_invalid_negative_and_nonfinite_data_rejected(self):
        for bad in (-5,float("nan"),float("inf"),"100"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                evaluate({"reach":bad},8000)

if __name__=="__main__":
    unittest.main()
