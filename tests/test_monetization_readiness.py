import unittest
from datetime import datetime,timezone
from unittest.mock import MagicMock
from growth.monetization import summarize,run
NOW=datetime(2026,11,3,8,tzinfo=timezone.utc)

def track(k,**fields):
    return dict(track_key=k,stage="hypothesis",owner_approved=False,
                fulfillment_verified=False,claims_verified=False,
                disclosures_ready=False,**fields)

class MonetizationReadinessTests(unittest.TestCase):
    def test_no_unverified_revenue_and_no_auto_commerce(self):
        r=summarize([
            track("affiliate_work_gear"),
            track("brand_partnerships"),
            track("office_digital_goods"),
        ],[{"review_status":"research_only"}],
          [{"review_status":"pending"}],[],now=NOW)
        self.assertEqual(r["phase"],"pre_revenue")
        self.assertEqual(r["received_vnd"],0)
        self.assertEqual(r["tracks_live"],0)
        self.assertEqual(r["affiliate_proposals_pending"],1)
        self.assertIn("keep_commercial_posts_unpublished",r["actions"])

    def test_commission_is_not_received_cash(self):
        r=summarize([],[],[],[
          {"amount_received_vnd":200000,"verification_method":"owner_manual",
           "evidence_reference":"provider estimate only"},
          {"amount_received_vnd":20000,"verification_method":"provider_settlement_export",
           "evidence_reference":"verified-provider-export-2026-11-03"}
        ],now=NOW)
        self.assertEqual(r["received_vnd"],20000)

    def test_disclosure_required_for_live_track(self):
        row=track("affiliate_work_gear")
        row.update(stage="live",owner_approved=True,fulfillment_verified=True,
                   claims_verified=True,disclosures_ready=False)
        result=summarize([row],[],[],[],now=NOW)
        self.assertEqual(result["tracks_live"],0)

    def test_fail_closed_on_source_unavailable(self):
        db=MagicMock()
        db.request.side_effect=[[],[],None]
        with self.assertRaises(ValueError):
            run(db,now=NOW)

    def test_reads_private_allowlisted_columns_only(self):
        db=MagicMock()
        db.request.side_effect=[[],[],[],[]]
        res=run(db,now=NOW)
        self.assertEqual(res["received_vnd"],0)
        calls=db.request.call_args_list
        self.assertEqual(len(calls),4)
        self.assertTrue(all(call.args[0]=="GET" for call in calls))
        self.assertNotIn("credentials",str(calls))

if __name__=="__main__":unittest.main()
