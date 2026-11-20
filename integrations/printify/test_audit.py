import unittest
from audit import PrintifyError, choose_shop, summarize_product, audit

PRODUCT = {
    "id": "a", "title": "Couple Case", "visible": True,
    "blueprint_id": 1, "print_provider_id": 2,
    "options": [{"type": "color", "name": "Color", "values": [
        {"id": 11, "title": "White"}, {"id": 12, "title": "Blush"}]}],
    "variants": [{"id": 1, "is_enabled": True, "options": [11]}],
    "print_areas": [{"background": "#ffffff"}],
}

class TestPrintifyAudit(unittest.TestCase):
    def test_selected_color_only(self):
        record = summarize_product(PRODUCT)
        self.assertEqual(record["manufacturer_colors"], ["White"])
        self.assertEqual(record["enabled_variants"], 1)
        self.assertIn("single-color-manufacturer-variant", record["warnings"])

    def test_printed_background_not_color(self):
        case = {**PRODUCT, "options": []}
        record = summarize_product(case)
        self.assertEqual(record["manufacturer_colors"], [])
        self.assertIn("no-color-option-check-printed-background", record["warnings"])

    def test_shop_ambiguity_safe(self):
        with self.assertRaises(PrintifyError):
            choose_shop([{"id":1,"title":"Other"},{"id":2,"title":"Else"}], None, "Pie & Po")

    def test_shop_match(self):
        self.assertEqual(choose_shop([{"id":1,"title":"Other"},{"id":2,"title":"Pie & Po Case Studio"}], None, "Pie & Po")["id"], 2)

    def test_audit_read_only(self):
        def fetch(path, token):
            if path == "/shops.json":
                return [{"id": 2, "title": "Pie & Po", "sales_channel": "shopify"}]
            if path == "/shops/2/products.json?limit=100&page=1":
                return {"data": [PRODUCT], "last_page": 1}
            raise AssertionError(path)
        report = audit("fake-token", fetch=fetch)
        self.assertEqual(report["product_count"], 1)
        self.assertEqual(report["warning_counts"]["single-color-manufacturer-variant"], 1)

if __name__ == "__main__":
    unittest.main()
