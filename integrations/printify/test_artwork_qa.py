import io
import unittest
from PIL import Image
from artwork_qa import permitted_source, transparency_from_bytes, source_urls


class TestArtworkPreflight(unittest.TestCase):
    def png(self, image):
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return buffer.getvalue()

    def test_transparent_rgba(self):
        img = Image.new("RGBA", (2, 2), (100, 80, 90, 0))
        self.assertEqual(transparency_from_bytes(self.png(img)), "transparent")

    def test_opaque_rgb(self):
        img = Image.new("RGB", (2, 2), (255, 255, 255))
        self.assertEqual(transparency_from_bytes(self.png(img)), "opaque")

    def test_opaque_rgba(self):
        img = Image.new("RGBA", (2, 2), (255, 255, 255, 255))
        self.assertEqual(transparency_from_bytes(self.png(img)), "opaque")

    def test_reject_ssrf(self):
        self.assertFalse(permitted_source("http://images.printify.com/test.png"))
        self.assertFalse(permitted_source("https://images.printify.com.evil.com/x.png"))
        self.assertFalse(permitted_source("https://localhost/secret"))
        self.assertTrue(permitted_source("https://images.printify.com/img.png"))
        self.assertTrue(permitted_source("https://pfy-prod-image-storage.s3.us-east-2.amazonaws.com/img.png"))

    def test_sources_deduplicated(self):
        product = {"print_areas": [
            {"placeholders": [{"images": [{"src": "https://images.printify.com/a.png"}, {"src": "https://images.printify.com/a.png"}]}]},
            {"placeholders": [{"images": [{"src": "https://images.printify.com/b.png"}]}]},
        ]}
        self.assertEqual(len(source_urls(product)), 2)


if __name__ == "__main__":
    unittest.main()
