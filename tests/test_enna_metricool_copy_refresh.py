"""Regression guards for the owner-approved November 2026 Metricool copy refresh.
The LIVE publisher state must be verified separately through Metricool; these
tests only validate the frozen creative plan and prevent robotic copy regression.
"""
import json
import unittest
from pathlib import Path

PLAN=Path(__file__).resolve().parents[1]/"config"/"enna_metricool_copy_refresh_2026_11_06.json"

class MetricoolCaptionRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PLAN.read_text(encoding="utf-8"))
        cls.items=cls.data["items"]

    def test_only_pending_posts_and_no_implicit_reschedule(self):
        self.assertEqual(self.data["scope"],"PENDING_ONLY")
        self.assertEqual(self.data["intended_updates"],27)
        self.assertIn("never_edit_published_or_error",self.data["rules"])
        self.assertIn("preserve_uuid_media_schedule_alt_text_carousel_people_tags_provider_data",self.data["rules"])
        self.assertEqual(len(self.items),27)
        uuids=[x["metricool_uuid"] for x in self.items]
        self.assertEqual(len(uuids),len(set(uuids)))

    def test_copy_is_original_not_boilerplate_or_undisclosed_sales(self):
        lines=[]
        full=[]
        for x in self.items:
            copy=x["revised_text"].strip()
            self.assertTrue(110<=len(copy)<=1200,x["metricool_uuid"])
            self.assertNotIn("https://",copy)
            self.assertNotIn("http://",copy)
            self.assertNotIn("affiliate",copy.casefold())
            self.assertNotIn("shopee",copy.casefold())
            self.assertEqual(x["editorial_status"],"copy_approved_for_existing_schedule_only")
            self.assertEqual(x["image_status"],"preserve_existing_media_no_new_image_claims")
            lines.append(copy.splitlines()[0].casefold())
            full.append(copy.casefold())
        self.assertGreaterEqual(len(set(lines)),24)
        self.assertLessEqual(sum("theo dõi" in t or "follow " in t for t in full),8)
        self.assertGreaterEqual(sum("🫠" in t or "🥲" in t or "😭" in t or "💀" in t for t in full),12)
        self.assertGreaterEqual(sum("?" in t for t in full),8)
        self.assertLessEqual(sum("Hồ sơ công sở".casefold() in t for t in full),3)

if __name__=="__main__":
    unittest.main()
