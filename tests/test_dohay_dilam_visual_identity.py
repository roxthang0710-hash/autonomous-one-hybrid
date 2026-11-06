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

    def test_owner_approved_clean_ui_variation_not_repetitive_waves(self):
        style = load_contract()
        self.assertEqual(style["style_revision"], "v4.1_clean_chat_balance")
        self.assertIn("clean_chat", style["approved_composition_modes"])
        self.assertIn("practical_ui_tip", style["approved_composition_modes"])
        self.assertIn("straight", style["style_contract"]["linework"])
        self.assertIn("wavy", style["visual_rules"]["no_repeated_frame"])
        self.assertTrue(style["approved_visual_reference"]["additional_confirmed_examples"])

        fake_chat = build_image_brief(
            "Nhóm dự án thêm nhiệm vụ đúng giờ tan ca",
            "8:30 - TÔI: HÔM NAY XONG 3 VIỆC",
            "8:35 - SẾP: HỌP VỀ 3 VIỆC ĐÓ NHA",
            composition="One large mostly-straight-edged faux chat window and a small shocked roundhead",
            character_emotion="stunned avatar with crown",
            layout_mode="clean_chat",
        )
        self.assertEqual(fake_chat["layout_mode"], "clean_chat")
        self.assertIn("Fictional", fake_chat["prompt"])
        self.assertIn("scalloped", fake_chat["prompt"])
        self.assertFalse(fake_chat["social_published"])
        self.assertTrue(fake_chat["requires_human_visual_review"])

        useful_ai = build_image_brief(
            "AI giúp nhân viên viết email follow-up sau họp",
            "CẦN EMAIL LỊCH SỰ",
            "AI GIÚP ĐỠ BÍ, NHƯNG VẪN PHẢI ĐỌC LẠI",
            composition="Minimal hand-drawn email app, one prominent practical prompt",
            character_emotion="roundhead relieved",
            layout_mode="practical_ui_tip",
        )
        self.assertEqual(useful_ai["layout_mode"], "practical_ui_tip")
        self.assertIn("Windows/Excel/AI tip", useful_ai["prompt"])
        self.assertNotEqual(fake_chat["prompt"], useful_ai["prompt"])

    def test_unauthorized_layout_cannot_enter_pipeline(self):
        with self.assertRaises(ValueError):
            build_image_brief(
                "Nhân viên làm việc", "ĐI LÀM", "XONG VIỆC",
                composition="Fake promo", character_emotion="bored",
                layout_mode="corporate_smooth_vector"
            )

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
