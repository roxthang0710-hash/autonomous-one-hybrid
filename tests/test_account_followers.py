"""Meta account follower snapshots: official source only, no fake zeros."""
import unittest
from datetime import datetime,timezone
from unittest.mock import MagicMock
from growth.account_followers import parse_follower_count,collect

NOW=datetime(2026,11,5,2,tzinfo=timezone.utc)
class AccountFollowersTests(unittest.TestCase):
    def test_total_value(self):
        self.assertEqual(parse_follower_count({"data":[{"name":"followers_count",
                    "total_value":{"value":8}}]}),8)
    def test_missing_never_zero_fill(self):
        self.assertIsNone(parse_follower_count({"data":[{"name":"followers_count"}]}))
    def test_negative_invalid(self):
        self.assertIsNone(parse_follower_count({"data":[{"name":"followers_count",
                    "total_value":{"value":-5}}]}))
    def test_no_oauth_no_calls(self):
        db=MagicMock()
        result=collect(db,now=NOW,load=lambda db,refresh:None)
        self.assertEqual(result["status"],"awaiting_official_oauth")
        db.request.assert_not_called()
    def test_verified_identity_and_snapshots(self):
        db=MagicMock()
        db.request.return_value=[{"local_day":"2026-11-05","followers":8}]
        def request(method,path,token,params=None):
            if path=="/me":
                return {"id":"threads-user-1","username":"dohay_dilam"}
            if path=="/me/threads_insights":
                return {"data":[{"name":"followers_count","total_value":{"value":8}}]}
            raise AssertionError("No unapproved endpoint")
        got=collect(db,now=NOW,load=lambda db,refresh:("token","dohay_dilam"),request=request)
        self.assertEqual(got["status"],"saved_official_snapshot")
        self.assertEqual(got["followers"],8)
        write=db.request.call_args
        self.assertEqual(write.args[:2],("POST","/enna_threads_account_snapshots"))
        self.assertEqual(write.kwargs["payload"]["source"],"meta_official")
    def test_no_insights_no_db_write(self):
        db=MagicMock()
        def request(method,path,token,params=None):
            return {"id":"threads-user-1","username":"dohay_dilam"} if path=="/me" else {"data":[]}
        result=collect(db,now=NOW,load=lambda db,refresh:("token","dohay_dilam"),request=request)
        self.assertEqual(result["status"],"missing_provider_metric")
        db.request.assert_not_called()

if __name__=="__main__":unittest.main()
