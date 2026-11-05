"""Enna: never retell the same Win+V / Win+L post with a new headline."""
import unittest
from datetime import date

from threads.shortcut_diversity import (
    WINDOWS_IDEAS,EXCEL_IDEAS,POWERPOINT_IDEAS,ALL_SHORTCUTS,
    canonical,is_present,is_repeated,recent_combos,repeated_combos_in_draft,
    make_brief,
)
from threads.tech_editorial import TECH_BRIEFS,choose_tech_brief

TODAY=date(2026,11,6)
PAST=[
    "3 phím tắt Windows: Win + V, Win + Shift + S, Ctrl + Shift + T.",
    "Win+L khóa máy và Win+V xem bảng tạm. Ctrl+Shift+T cứu tab.",
    "Ctrl + Shift + Esc, Win + E và Win + L.",
]

class ShortcutDiversityTests(unittest.TestCase):
    def test_windows_variety_and_different_real_office_lanes(self):
        self.assertGreaterEqual(len(WINDOWS_IDEAS),18)
        self.assertEqual(len(EXCEL_IDEAS),4)
        self.assertGreaterEqual(len(POWERPOINT_IDEAS),4)
        self.assertGreaterEqual(len({x["category"] for x in WINDOWS_IDEAS}),7)
        self.assertEqual(len({x["key"] for x in ALL_SHORTCUTS}),len(ALL_SHORTCUTS))
        self.assertEqual(len({canonical(x["shortcut"]) for x in ALL_SHORTCUTS}),len(ALL_SHORTCUTS))
        self.assertTrue(all(x["source"].startswith("https://support.microsoft.com/") for x in ALL_SHORTCUTS))

    def test_exact_shortcut_detection_not_keyword_or_prefix(self):
        self.assertTrue(is_present("Bấm Win + V mở lịch sử.", "Win+V"))
        self.assertTrue(is_present("Bạn dùng Ctrl+Shift+T chưa?", "Ctrl + Shift + T"))
        self.assertTrue(is_present("Thử Windows + Z để chia cửa sổ","Win+Z"))
        self.assertFalse(is_present("Windows có rất nhiều tổ hợp phím", "Win+V"))
        self.assertFalse(is_present("Ctrl+Shift+Tab chuyển tab", "Ctrl+Shift+T"))
        self.assertFalse(is_present("Win+Enter khác với Win+E","Win+E") is False) # actual Win+E is present
        self.assertFalse(is_present("Mẹo bàn phím sẽ tới vào thứ Tư", "Alt+Tab"))
        self.assertTrue(is_present("Win + Ctrl + ← để chuyển desktop","Win+Ctrl+←"))

    def test_old_frequent_shortcuts_are_cooled_down_for_30_days(self):
        for combo in ("Win+V","Win+Shift+S","Ctrl+Shift+T","Win+L","Win+E","Ctrl+Shift+Esc"):
            self.assertTrue(is_repeated(combo,(),today=TODAY),combo)
        self.assertFalse(is_repeated("Win+Z",PAST,today=TODAY))
        self.assertFalse(is_repeated("Win+V",(),today=date(2026,12,12)))
        self.assertTrue(is_repeated("Win+V",PAST,today=date(2026,12,12)))
        self.assertEqual(repeated_combos_in_draft(
            "Win + V và Ctrl + Shift + T đây", PAST,today=TODAY),
            ["CTRL+SHIFT+T","WIN+V"])
        self.assertFalse(repeated_combos_in_draft(
            "Win+Z mở bố cục và Win+Ctrl+D tạo desktop ảo", PAST,today=TODAY))

    def test_real_posts_rotate_apps_and_categories(self):
        self.assertGreaterEqual(len(TECH_BRIEFS),25)
        by_app=[x.get("app","other") for x in TECH_BRIEFS[:10]]
        self.assertIn("windows",by_app)
        self.assertIn("excel",by_app)
        self.assertIn("powerpoint",by_app)
        self.assertIn("other",by_app)
        self.assertEqual(len({row["key"] for row in TECH_BRIEFS}),len(TECH_BRIEFS))
        self.assertEqual(len(TECH_BRIEFS),len({row["key"] for row in TECH_BRIEFS}))

    def test_generated_tech_brief_skips_combo_from_actual_history(self):
        for slot in range(0,60):
            b=choose_tech_brief(slot*3, PAST,today=TODAY)
            if b and b.get("shortcut"):
                self.assertFalse(is_repeated(b["shortcut"],PAST,today=TODAY))
        self.assertIsNone(choose_tech_brief(2,PAST,today=TODAY))
        self.assertEqual(choose_tech_brief(0,PAST,today=TODAY)["shortcut"],"Win + Z")

    def test_prompts_are_grounded_and_do_not_create_more_repeats(self):
        for entry in ALL_SHORTCUTS:
            brief=make_brief(entry)
            self.assertIn(entry["shortcut"],brief["prompt"])
            self.assertIn(entry["scene"],brief["prompt"])
            self.assertIn(entry["limit"],brief["prompt"])
            self.assertNotIn("Win+V",brief["prompt"])
            self.assertNotIn("Ctrl+Shift+T",brief["prompt"])
            self.assertNotIn("https://",brief["prompt"])
            self.assertEqual(brief["source"],entry["source"])
            self.assertIn("Người Tròn",brief["prompt"])

if __name__=="__main__":
    unittest.main()
