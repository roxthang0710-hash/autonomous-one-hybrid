import unittest
from affiliate.catalog import NICHES, choose_niche, score_lead, select_lead


class AffiliateCatalogTests(unittest.TestCase):
    def setUp(self):
        self.programs = [
            {"code": "accesstrade", "review_status": "research_only",
             "official_url": "https://accesstrade.vn", "evidence_url": "https://help.accesstrade.vn"},
            {"code": "shopee_koc", "review_status": "research_only",
             "official_url": "https://shopee.vn", "evidence_url": "https://help.shopee.vn"},
            {"code": "tiktok_shop", "review_status": "research_only",
             "official_url": "https://seller-vn.tiktok.com", "evidence_url": "https://seller-vn.tiktok.com"},
        ]

    def test_scores_are_not_profit_probabilities(self):
        scores = [score_lead(p) for p in self.programs]
        self.assertTrue(all(0 <= n <= 100 for n in scores))
        self.assertNotEqual(len(set(scores)), 1)

    def test_selects_least_researched_program(self):
        self.assertEqual(select_lead(self.programs, [])["code"], "shopee_koc")
        prior = [{"program_code": "shopee_koc", "status": "success"}]
        self.assertEqual(select_lead(self.programs, prior)["code"], "accesstrade")

    def test_rejects_unknown_program(self):
        with self.assertRaises(RuntimeError):
            select_lead([{"code": "fake_network", "review_status": "active"}], [])

    def test_rotates_niche(self):
        self.assertEqual(choose_niche([]), NICHES[0])
        self.assertEqual(choose_niche([{"status": "success"}]), NICHES[1])


if __name__ == "__main__":
    unittest.main()
