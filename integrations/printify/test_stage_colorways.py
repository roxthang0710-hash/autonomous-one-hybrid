import unittest
from stage_colorways import build_payload, PAL

BASE = {
    "id":"source", "title":"Who Ate My Snack? — Phone Case | Pie & Po",
    "description":"<p>Test</p>", "tags":["couple"],
    "blueprint_id":421,"print_provider_id":99,
    "variants":[{"id":1,"price":2695,"cost":1148,"is_enabled":True,"is_available":True},
                {"id":2,"price":2695,"cost":1148,"is_enabled":False,"is_available":True}],
    "print_areas":[{"variant_ids":[1,2],"background":"#ffffff","placeholders":[{"position":"back","images":[
        {"id":"art","x":0.5,"y":0.5,"scale":1,"angle":0,"src":"https://irrelevant.example"}]}]}],
}
class Tests(unittest.TestCase):
    def test_background_is_only_changed(self):
        o=build_payload(BASE,"Blush Pink")
        self.assertEqual(o["print_areas"][0]["background"],PAL["Blush Pink"])
        self.assertEqual(o["print_areas"][0]["placeholders"][0]["images"][0]["id"],"art")
        self.assertEqual(o["print_areas"][0]["variant_ids"],[1])
        self.assertEqual(len(o["variants"]),1)
        self.assertNotIn("sku",o["variants"][0])
    def test_no_original_mutation(self):
        build_payload(BASE,"Blush Pink")
        self.assertEqual(BASE["print_areas"][0]["background"],"#ffffff")
    def test_min_margin(self):
        src={**BASE,"variants":[{**BASE["variants"][0],"price":1200}]}
        with self.assertRaises(ValueError):build_payload(src,"Blush Pink")
    def test_unknown_color_rejected(self):
        with self.assertRaises(ValueError):build_payload(BASE,"Jet Black")
    def test_missing_art_rejected(self):
        src={**BASE,"print_areas":[{"variant_ids":[1],"placeholders":[{"position":"back","images":[]}]}]}
        with self.assertRaises(ValueError):build_payload(src,"Sage Green")

if __name__=="__main__":
    unittest.main()
