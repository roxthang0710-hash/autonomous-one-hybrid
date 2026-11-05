import unittest
from scripts.enna_roundhead_brief import ACTIVE_STYLE, load_contract, build_image_brief


class RoundheadBrandIdentityTests(unittest.TestCase):
    def test_owner_approved_identity_is_the_only_default(self):
        style = load_contract()
        self.assertEqual(style["visual_style_id"], ACTIVE_STYLE)
        self.assertEqual(style["brand"], "Đồ Hay Đi Làm")
        self.assertEqual(style["status"], "owner_selected_primary")
        self.assertEqual(style["delivery"]["automatic_social_publish_on_creation"], False)
        self.assertIn("round yellow-headed", style["style_contract"]["recurring_character"])
        self.assertIn("cat", style["style_contract"]["photo_exception"])

    def test_brief_includes_roundhead_and_explicit_variation(self):
        result = build_image_brief(
            "20 tin nhắn đồng nghiệp đều báo việc gấp",
            "20 TIN NHẮN ĐỀU GẤP",
            "ỦA VẬY AI ĐƯỢC GẤP TRƯỚC?",
            composition="A pile of colored message bubbles around a stressed round head",
            character_emotion="sweating and staring at the phone",
        )
        self.assertEqual(result["visual_style_id"], ACTIVE_STYLE)
        self.assertFalse(result["social_published"])
        self.assertTrue(result["requires_human_visual_review"])
        self.assertIn("not polished", result["prompt"].lower()) if "not polished" in result["prompt"].lower() else self.assertIn("Avoid:", result["prompt"])
        self.assertIn("round yellow-headed", result["prompt"])
        self.assertIn("repetitive", result["prompt"])
        self.assertIn("20 TIN NHẮN ĐỀU GẤP", result["prompt"])

    def test_missing_details_fail_closed(self):
        with self.assertRaises(ValueError):
            build_image_brief(
                "", "HỌP GẤP", "ỦA RỒI KHI NÀO LÀM?",
                composition="Floating notes", character_emotion="shocked"
            )

    def test_legacy_upload_workflows_cannot_register_old_cards(self):
        from pathlib import Path
        for filename in ("enna-doodle-batch.yml", "enna-visual-factory.yml"):
            workflow = (Path(".github/workflows") / filename).read_text(encoding="utf-8")
            self.assertIn("if: false", workflow)
            self.assertIn("Người Tròn", workflow)


if __name__ == "__main__":
    unittest.main()
