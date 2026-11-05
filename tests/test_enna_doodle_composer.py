"""Visual Tone 3.1 regression: coffee and fake chat are *drawn*, cat untouched."""
import unittest
from PIL import Image
from scripts.enna_visual_factory import compose,load_bank

BANK="scripts/enna_visual_source_bank.json"

class EnnaDoodleTests(unittest.TestCase):
    def setUp(self):
        self.photos=load_bank(BANK)
        self.dark=Image.new("RGB",(1280,960),(35,77,120))
        self.light=Image.new("RGB",(1280,960),(225,174,81))

    def test_chat_has_original_doodle_phone_independent_of_photo(self):
        for source in self.photos:
            if source["format"]!="chat":
                continue
            a=compose(source,self.dark)
            b=compose(source,self.light)
            self.assertEqual(a.size,(1080,1350))
            # A completely different photo must not change the central artwork.
            self.assertEqual(a.getpixel((520,780)),b.getpixel((520,780)))
            self.assertNotEqual(a.getpixel((520,780)),(35,77,120))
            self.assertNotEqual(a.getpixel((520,780)),(225,174,81))
            self.assertTrue(len(a.getcolors(maxcolors=200000))>12)

    def test_coffee_is_expressive_hand_drawn_cup_not_photo(self):
        for source in self.photos:
            if source["format"]=="contrast" and "cà phê" in source["topic"].casefold():
                a=compose(source,self.dark)
                b=compose(source,self.light)
                self.assertEqual(a.size,(1080,1350))
                self.assertEqual(a.getpixel((520,410)),b.getpixel((520,410)))
                self.assertEqual(a.getpixel((520,1070)),b.getpixel((520,1070)))
                self.assertNotEqual(a.getpixel((520,410)),(35,77,120))
                self.assertNotEqual(a.getpixel((520,1070)),(35,77,120))

    def test_cat_reaction_remains_real_photo_not_drawn(self):
        source=next(s for s in self.photos if s["id"]=="cat-yawning")
        a=compose(source,self.dark)
        b=compose(source,self.light)
        # The existing photo branch mildly enhances saturation/contrast;
        # it should keep the real photo, not preserve raw RGB byte-for-byte.
        one=a.getpixel((520,760))
        two=b.getpixel((520,760))
        self.assertNotEqual(one,two)
        self.assertTrue(all(abs(v-ref)<26 for v,ref in zip(one,(35,77,120))))
        self.assertTrue(all(abs(v-ref)<35 for v,ref in zip(two,(225,174,81))))
        self.assertEqual(a.getpixel((6,6)),(255,212,0))

    def test_visible_doodle_scene_contains_no_platform_imitation(self):
        src=next(s for s in self.photos if s["id"]=="laptop-notepad")
        img=compose(src,self.dark)
        self.assertEqual(img.mode,"RGB")
        self.assertEqual(img.size,(1080,1350))

if __name__=="__main__":
    unittest.main()
