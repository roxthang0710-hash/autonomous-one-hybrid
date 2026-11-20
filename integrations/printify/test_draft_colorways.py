import unittest
from draft_colorways import build_draft

class TestColorways(unittest.TestCase):
    def setUp(self):
        self.sample = {
            "title": "QA couple phone case",
            "description": "Test case",
            "blueprint_id": 421,
            "print_provider_id": 99,
            "variants": [
                {"id": i, "price": 2995, "is_enabled": True} for i in range(1, 13)
            ],
            "print_areas": [{
                "variant_ids": list(range(1, 13)),
                "placeholders": [{"position": "front", "images": [
                    {"id": "img1", "x": 0.5, "y": 0.5, "scale": 1, "angle": 0}
                ]}],
                "background": "#ffffff"
            }]
        }
    def test_cream_background(self):
        p = build_draft(self.sample, "cream")
        self.assertEqual(p["print_areas"][0]["background"], "#F2E9D9")
        self.assertEqual(len(p["variants"]), 12)
        self.assertEqual(p["variants"][0]["price"], 2995)
        self.assertEqual(p["print_areas"][0]["placeholders"][0]["images"][0]["id"], "img1")
        self.assertIn("DO NOT PUBLISH", p["title"])
    def test_invalid_color(self):
        with self.assertRaises(ValueError):
            build_draft(self.sample, "fake")
    def test_missing_print_file(self):
        self.sample["print_areas"][0]["placeholders"][0]["images"] = []
        with self.assertRaises(Exception):
            build_draft(self.sample, "cream")

if __name__ == "__main__":
    unittest.main()
