import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.enna_doodle_batch import MEMES,draw_one,generate
from growth.enna_doodle_batch_upload import verify_original

class OriginalDoodleBatchTests(unittest.TestCase):
    def test_fourteen_unique_ideas_match_real_upcoming_calendar(self):
        self.assertEqual(len(MEMES),14)
        self.assertEqual(len({x["id"] for x in MEMES}),14)
        self.assertTrue(all(x["punch"] and x["hook"] and x["scene"] for x in MEMES))
        self.assertEqual(len({x["scene"] for x in MEMES}),14)

    def test_six_different_scenes_are_true_doodles_not_stock_photos(self):
        art_ids=["keyboard-rescue","twenty-urgent","pen-missing",
                 "weekend-brain","headphones-left","sunday-anxiety",
                 "cable-spaghetti","meeting-fast","five-desk-items"]
        for id in art_ids:
            art=draw_one(next(x for x in MEMES if x["id"]==id))
            self.assertEqual(art.size,(1080,1350))
            self.assertEqual(art.mode,"RGB")
            self.assertNotEqual(art.getpixel((12,12)),art.getpixel((530,475)))

    def test_exact_source_provenance_and_image_hash(self):
        with tempfile.TemporaryDirectory() as t:
            output=Path(t)
            results=generate(output)
            self.assertEqual(len(results),14)
            for rec in results:
                proof,sha,data=verify_original(output/rec["file"])
                self.assertFalse(proof["published"])
                self.assertFalse(proof["ai_generated_image"])
                self.assertEqual(sha,rec["sha256"])
                self.assertEqual(proof["status"],"DRAFT_REQUIRES_HUMAN_REVIEW")
                self.assertTrue(proof["source"].startswith("enna_original_drawing"))
            manifest=json.loads((output/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["social_published"],0)

    def test_drawing_is_deterministic_for_idempotent_storage(self):
        meme=next(x for x in MEMES if x["id"]=="keyboard-rescue")
        self.assertEqual(draw_one(meme).tobytes(),draw_one(meme).tobytes())

if __name__=="__main__":
    unittest.main()
