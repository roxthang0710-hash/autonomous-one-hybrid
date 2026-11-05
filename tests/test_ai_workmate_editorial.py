"""Regression checks for the approved 'AI — Đồng nghiệp thứ hai' content lane."""
import unittest
from threads.ai_workmate_editorial import (
    AI_IDEAS, SERIES, STYLE, ai_briefs, validate_ideas, as_tech_brief,
)
from threads.tech_editorial import TECH_BRIEFS, choose_tech_brief

class AIWorkmateTests(unittest.TestCase):
    def test_sixteen_distinct_practical_ideas(self):
        self.assertEqual(SERIES, "AI — Đồng nghiệp thứ hai")
        self.assertEqual(STYLE, "dohay_roundhead_doodle_v4")
        self.assertTrue(validate_ideas())
        self.assertEqual(len(AI_IDEAS), 16)
        self.assertEqual(len({x["key"] for x in AI_IDEAS}), 16)
        self.assertGreaterEqual(len({x["lane"] for x in AI_IDEAS}), 6)
        self.assertEqual(len({x["visual"] for x in AI_IDEAS}), 16)
        self.assertTrue(any("3 mẹo" in row["title"].lower() or "3 thứ" in row["title"].lower()
                            for row in AI_IDEAS))

    def test_prompts_copyable_and_safe_for_real_office_work(self):
        for row in AI_IDEAS:
            self.assertGreater(len(row["copy_prompt"]), 95)
            self.assertIn("Người Tròn", row["visual"])
            self.assertTrue(row["source"].startswith(("https://help.openai.com/",
                                                       "https://learn.microsoft.com/")))
            brief=as_tech_brief(row)
            self.assertEqual(brief["visual_style_id"], STYLE)
            self.assertEqual(brief["pillar"],"work")
            self.assertEqual(brief["series"],SERIES)
            self.assertEqual(brief["app"],"ai")
            self.assertIn(row["title"][:0],brief["prompt"])
            self.assertIn(row["copy_prompt"],brief["prompt"])
            self.assertNotIn("https://",brief["prompt"])
            self.assertLessEqual(len(brief["prompt"]), 1000,
                                 "Supabase ready-plan limit exceeded: "+row["key"])

    def test_rotation_adds_ai_but_keeps_traditional_productivity(self):
        self.assertEqual(len({row["key"] for row in TECH_BRIEFS}),len(TECH_BRIEFS))
        first=TECH_BRIEFS[:14]
        apps=[row.get("app","other") for row in first]
        self.assertGreaterEqual(apps.count("ai"),3)
        self.assertIn("windows",apps)
        self.assertIn("excel",apps)
        self.assertIn("powerpoint",apps)
        self.assertIn("other",apps)
        self.assertEqual(len(ai_briefs()),16)
        picked=[choose_tech_brief(index*3,[],today=None) for index in range(14)]
        self.assertTrue(any(x and x.get("app")=="ai" for x in picked))
        self.assertEqual(len({x["key"] for x in picked if x}),
                         len([x for x in picked if x]))

    def test_fails_closed_for_unknown_and_duplicate_ideas(self):
        with self.assertRaises(ValueError):
            as_tech_brief({"key":"fabricated","task":"fake"})
        with self.assertRaises(ValueError):
            validate_ideas((AI_IDEAS[0],)*16)

if __name__=="__main__":
    unittest.main()
