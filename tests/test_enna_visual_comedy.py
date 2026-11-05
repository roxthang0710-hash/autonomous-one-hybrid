"""Regression tests: humor must come from the situation, not slogans."""
import json
import os
import unittest
from unittest.mock import Mock,patch

from PIL import Image
from growth.visual_comedy_gate import signals
from growth.visual_humor_editor import generate_variant
from scripts.enna_visual_factory import load_bank, compose

BANK="scripts/enna_visual_source_bank.json"

class VisualComedyTests(unittest.TestCase):
    def test_all_curated_jokes_have_setup_and_twist(self):
        sources=load_bank(BANK)
        self.assertEqual(len(sources),8)
        self.assertTrue({"reaction","contrast","chat"}.issubset(
            {source["format"] for source in sources}))
        for source in sources:
            verdict=signals(source,source)
            self.assertTrue(verdict["pass"],source["id"]+" "+str(verdict["reasons"]))
            self.assertIsNone(verdict["human_funny_rating"])

    def test_generic_encouragement_is_not_comedy(self):
        src=load_bank(BANK)[0]
        verdict=signals(src,{"headline":"HÃY CÙNG LÀM VIỆC NĂNG SUẤT",
            "punchline":"Cùng nhau lan tỏa năng lượng tích cực ở công ty nhé!"})
        self.assertFalse(verdict["pass"])
        self.assertIn("generic-ad-copy",verdict["reasons"])

    def test_three_new_reaction_and_chat_layouts_render_without_overflow(self):
        photo=Image.effect_noise((1600,1100),28).convert("RGB")
        for src in load_bank(BANK):
            if src["format"] in ("reaction","contrast","chat"):
                art=compose(src,photo)
                self.assertEqual(art.size,(1080,1350))
                self.assertEqual(art.mode,"RGB")

    def test_groq_one_request_three_candidates_selects_non_generic(self):
        src=load_bank(BANK)[0]
        response=Mock()
        response.json.return_value={"choices":[{"message":{"content":json.dumps({
            "candidates":[
                {"headline":"HÃY CÙNG TÍCH CỰC MỖI NGÀY",
                 "punchline":"Cùng nhau lan tỏa tinh thần làm việc thật tốt nhé!"},
                {"headline":"SẾP: HỌP CHẮC 5 PHÚT THÔI",
                 "punchline":"10:47, CẢ PHÒNG VẪN ĐANG HỌP CHỐT LỊCH HỌP TIẾP."},
                {"headline":"SẾP BẢO HỌP NHANH THÔI",
                 "punchline":"MỞ MÁY LÚC 9 GIỜ, HỌP XONG THÌ ĐẾN GIỜ ĂN TRƯA."}
            ]},ensure_ascii=False)}}]}
        fn=Mock(return_value=response)
        with patch.dict(os.environ,{"GROQ_API_KEY":"test-only"}):
            picked=generate_variant(src,request=fn)
        self.assertIsNotNone(picked)
        self.assertNotIn("lan tỏa",(picked["headline"]+" "+picked["punchline"]).lower())
        self.assertEqual(fn.call_count,1)

if __name__=="__main__":
    unittest.main()
