import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from scripts.enna_visual_carousel import W,H,SLIDES,render,verified_photo

class PhotoCarouselTests(unittest.TestCase):
    def test_five_photo_driven_panels_and_license_metadata(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);sources=root/"sources";sources.mkdir()
            specs=[
                "kiem-tra-tien-do",
                "luu-file-lan-thu-17",
                "chuyen-doi-so",
            ]
            for stem in specs:
                path=sources/(stem+".png")
                # Pixel variation ensures valid compressed photo-like file sizes.
                photo=Image.effect_noise((1080,1350),40).convert("RGB")
                photo.save(path)
                meta={"status":"DRAFT_REQUIRES_HUMAN_REVIEW",
                      "published":False,
                      "output_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "source_media":[{"file":"File:Test.jpg","photographer":"A",
                                       "license":"CC0 1.0"}]}
                path.with_suffix(".rights.json").write_text(json.dumps(meta),encoding="utf-8")
            output=root/"output"
            rendered=render(sources,output)
            self.assertEqual(len(rendered),5)
            for file in rendered:
                with Image.open(file) as img:
                    self.assertEqual(img.size,(W,H))
            manifest=json.loads((output/"thu-hai-cua-toi.sources.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["published"])
            self.assertEqual(len(manifest["slides"]),5)
            self.assertTrue(all(src["license"]=="CC0 1.0" for src in manifest["sources"]))
            # Tampered media must be rejected before rendering a new carousel.
            (sources/"kiem-tra-tien-do.png").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"photo-hash-mismatch"):
                verified_photo(sources,"cat")
    def test_topic_and_slide_lengths(self):
        self.assertEqual(len(SLIDES),5)
        self.assertEqual(len({v[1] for v in SLIDES}),5)

if __name__=="__main__":
    unittest.main()
