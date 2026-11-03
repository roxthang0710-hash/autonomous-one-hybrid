import unittest
from unittest.mock import MagicMock
from growth.affiliate_selection import prioritize,run

class AffiliateSelectionTests(unittest.TestCase):
    def test_ranking_is_not_publishing_approval(self):
        products=[dict(candidate_key="cable_clips",internal_priority_score=90,
                       program_code="shopee_koc",stage="research_only",
                       publisher_approved=False,seller_verified=False,
                       product_verified=False,disclosure_ready=False,
                       owner_approved=False,affiliate_url=None)]
        summary=prioritize(products,[{"code":"shopee_koc","review_status":"research_only"}],
                           [{"status":"planned"}])
        self.assertEqual(summary["top_research"][0]["editorial_priority"],90)
        self.assertFalse(summary["publication_allowed"])
        self.assertFalse(summary["top_research"][0]["cleared_for_affiliate"])
        self.assertEqual(summary["active_placement_count"],0)
    def test_rejects_incomplete_evidence(self):
        with self.assertRaises(ValueError):
            prioritize(None,[],[])
    def test_read_only_backend(self):
        db=MagicMock()
        db.request.side_effect=[[],[],[]]
        result=run(db)
        self.assertEqual(result["hypothesis_count"],0)
        self.assertTrue(all(c.args[0]=="GET" for c in db.request.call_args_list))

if __name__=="__main__":unittest.main()
