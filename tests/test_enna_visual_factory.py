import hashlib
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from scripts.enna_visual_factory import choose_batch, compose, load_bank, render
from growth.visual_humor_editor import check_copy, generate_variant

BANK = "scripts/enna_visual_source_bank.json"

class VisualFactoryTests(unittest.TestCase):
    def test_bank_has_distinct_human_curated_sources(self):
        rows=load_bank(BANK)
        self.assertEqual(len(rows),6)
        self.assertEqual(len({r["id"] for r in rows}),6)
        self.assertTrue(all(r["title"].startswith("File:") for r in rows))

    def test_rotation_does_not_repeat_next_day(self):
        rows=load_bank(BANK)
        a=choose_batch(rows,date(2026,11,6))
        b=choose_batch(rows,date(2026,11,7))
        self.assertEqual(len(a),3)
        self.assertFalse({x["id"] for x in a} & {x["id"] for x in b})
        self.assertEqual(a,choose_batch(rows,date(2026,11,6)))

    def test_real_png_artifacts_have_per_source_rights_and_no_social_publish(self):
        photo=Image.effect_noise((1280,960),32).convert("RGB")
        def fake_fetch(typed):
            return photo,{"source_page":"https://commons.wikimedia.org/wiki/"+typed[1].replace(" ","_"),
                "photographer":typed[2],"file":typed[1],
                "photo_sha256":"a"*64}
        with tempfile.TemporaryDirectory() as folder:
            result=render(BANK,folder,day=date(2026,11,6),fetch=fake_fetch)
            self.assertEqual(len(result),3)
            self.assertEqual(len({r["commons_filename"] for r in result}),3)
            for entry in result:
                file=Path(folder)/entry["file"]
                with Image.open(file) as im:
                    self.assertEqual(im.size,(1080,1350))
                    self.assertEqual(im.format,"PNG")
                meta=json.loads(file.with_suffix(".rights.json").read_text(encoding="utf-8"))
                self.assertEqual(meta["license"],"CC0 1.0")
                self.assertFalse(meta["published"])
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),meta["image_sha256"])
            manifest=json.loads((Path(folder)/"manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["no_social_actions"])
            self.assertEqual(manifest["source_count"],3)

    def test_rate_limited_one_source_uses_only_curated_backup(self):
        import requests
        photo=Image.effect_noise((1280,960),29).convert("RGB")
        seen=[]
        def simulated_fetch(entry):
            seen.append(entry[1])
            if len(seen)==1:
                raise requests.HTTPError("429 rate limit")
            return photo, {"source_page":"https://commons.wikimedia.org/wiki/"+entry[1].replace(" ","_"),
                "photographer":entry[2],"file":entry[1],"photo_sha256":"a"*64}
        with tempfile.TemporaryDirectory() as folder:
            items=render(BANK,folder,day=date(2026,11,6),fetch=simulated_fetch)
            self.assertEqual(len(items),3)
            self.assertEqual(len(seen),4)
            report=json.loads((Path(folder)/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["source_failures"]),1)
            self.assertEqual(report["source_failures"][0]["error_class"],"HTTPError")
            known={x["title"] for x in load_bank(BANK)}
            self.assertTrue(all(x["commons_filename"] in known for x in items))

    def test_no_unlicensed_image_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            def prohibited(_):
                raise ValueError("license-not-verified-CC0")
            with self.assertRaisesRegex(RuntimeError,"insufficient_live_verified_cc0_sources"):
                render(BANK,folder,day=date(2026,11,6),fetch=prohibited)
            report=json.loads((Path(folder)/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_count"],0)
            self.assertFalse(report["no_social_actions"] is False)

    def test_unsafe_creative_input_rejected_before_output(self):
        rows=load_bank(BANK)
        pic=Image.new("RGB",(1200,800))
        with self.assertRaises(ValueError):
            compose(rows[0],pic,{"headline":"x","punchline":"Buy this now!"})
        with self.assertRaises(ValueError):
            choose_batch(rows,date(2026,11,6),99)

    def test_humor_guard_rejects_cliches_fake_people_and_links(self):
        row=load_bank(BANK)[0]
        good={"headline":"CUỘC HỌP VỪA XONG","punchline":"Máy tính vẫn mở, còn não đang xin thêm 5 phút nghỉ trưa."}
        self.assertEqual(check_copy(row,good),good)
        self.assertIsNone(check_copy(row,{"headline":"BẠN CÓ BAO GIỜ","punchline":"Hãy cùng lan tỏa năng lượng tích cực nhé!"}))
        self.assertIsNone(check_copy(row,{"headline":"CÔNG VIỆC HÔM NAY","punchline":"Người trong ảnh đang đi làm và mệt quá."}))
        self.assertIsNone(check_copy(row,{"headline":"BÁO CÁO CUỐI NGÀY","punchline":"Link http://untrusted.example mua ngay nhé."}))
        self.assertIsNone(check_copy(row,{"headline":row["headline"],"punchline":row["punchline"]}))

    def test_oversized_ai_word_falls_back_to_human_caption(self):
        photo=Image.effect_noise((1280,960),22).convert("RGB")
        def fake_fetch(row):
            return photo, {"source_page":"https://commons.wikimedia.org/wiki/"+row[1].replace(" ","_"),
                "photographer":row[2],"file":row[1],"photo_sha256":"a"*64}
        def bad_ai(_):
            return {"headline":"G"*58,"punchline":"Laptop và sổ đây, sao chưa làm xong?"}
        with tempfile.TemporaryDirectory() as folder:
            rows=render(BANK,folder,day=date(2026,11,6),
                        fetch=fake_fetch,rewrite=bad_ai)
            self.assertEqual(len(rows),3)
            self.assertTrue(any(x["copy_origin"]=="human_curated" for x in rows))

    def test_no_groq_key_keeps_human_written_caption(self):
        with patch.dict("os.environ",{"GROQ_API_KEY":""}):
            self.assertIsNone(generate_variant(load_bank(BANK)[0],request=Mock()))

if __name__=="__main__":
    unittest.main()
