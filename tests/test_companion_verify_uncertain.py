"""No-write verification tests for ambiguous Threads replies."""
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock,patch
import requests
from growth.companion_verify_uncertain import (
    matching_reply,read_own_replies,verify_ambiguous,
)

NOW=datetime(2026,11,4,9,0,tzinfo=timezone.utc)
ATTEMPT_AT=(NOW-timedelta(minutes=15)).isoformat()
PENDING={"id":"550e8400-e29b-41d4-a716-446655440000",
         "github_issue_id":6198184455,
         "target_post_id":"4022361496390728226",
         "status":"uncertain","attempted_at":ATTEMPT_AT}
RIGHT={"id":"4022361999999999999","text":"Verified comment",
       "timestamp":(NOW-timedelta(minutes=14)).isoformat(),
       "replied_to":{"id":"4022361496390728226"}}
WRONG={**RIGHT,"replied_to":{"id":"4022361496390720000"}}


class ReadOnlyVerificationTests(unittest.TestCase):
    def test_matching_exact_target_and_attempt_time(self):
        self.assertTrue(matching_reply(RIGHT,PENDING))
        self.assertFalse(matching_reply(WRONG,PENDING))
        self.assertFalse(matching_reply(
            {**RIGHT,"timestamp":(NOW-timedelta(days=3)).isoformat()},PENDING))
        self.assertFalse(matching_reply(
            {**RIGHT,"id":"unknown"},PENDING))

    @patch("growth.companion_verify_uncertain.verify_meta_account")
    def test_one_authoritative_own_reply_updates_ambiguous_row(self,_):
        db=MagicMock()
        db.request.return_value=[PENDING]
        read=MagicMock(return_value={"data":[WRONG,RIGHT]})
        result=verify_ambiguous(db,token="fake",expected="dohay_dilam",
                                read=read,now=NOW)
        self.assertEqual(result["verified"],1)
        self.assertEqual(result["state"],"verified")
        db.patch.assert_called_once()
        self.assertEqual(db.patch.call_args.args[0],"enna_companion_attempts")
        self.assertEqual(db.patch.call_args.args[2]["status"],"posted")
        self.assertEqual(db.patch.call_args.args[2]["meta_reply_id"],RIGHT["id"])
        self.assertEqual(read.call_count,1)
        self.assertEqual(read.call_args.args[0],"GET")

    @patch("growth.companion_verify_uncertain.verify_meta_account")
    def test_missing_or_wrong_parent_never_claimed_as_posted(self,_):
        db=MagicMock()
        db.request.return_value=[PENDING]
        result=verify_ambiguous(db,token="fake",expected="dohay_dilam",
             read=MagicMock(return_value={"data":[WRONG]}),now=NOW)
        self.assertEqual(result["state"],"no_matching_reply")
        db.patch.assert_not_called()

    @patch("growth.companion_verify_uncertain.verify_meta_account")
    def test_meta_read_denial_never_retries_or_marks_failure(self,_):
        db=MagicMock()
        db.request.return_value=[PENDING]
        response=requests.Response()
        response.status_code=403
        read=MagicMock(side_effect=requests.HTTPError("access",response=response))
        result=verify_ambiguous(db,token="fake",expected="dohay_dilam",
                                read=read,now=NOW)
        self.assertEqual(result["state"],"meta_read_http_403")
        self.assertEqual(result["verified"],0)
        db.patch.assert_not_called()
        read.assert_called_once()

    def test_unsupported_account_or_no_pending_stops_without_meta(self):
        db=MagicMock()
        db.request.return_value=[PENDING]
        result=verify_ambiguous(db,token="fake",expected="other",now=NOW)
        self.assertEqual(result["state"],"account_mismatch")
        db.patch.assert_not_called()
        db.request.return_value=[]
        result=verify_ambiguous(db,now=NOW)
        self.assertEqual(result["state"],"no_uncertain_attempts")

    def test_400_field_compatibility_uses_two_gets_only(self):
        response=requests.Response()
        response.status_code=400
        read=MagicMock(side_effect=[
            requests.HTTPError("unsupported fields",response=response),
            {"data":[RIGHT]}])
        data=read_own_replies("fake",read=read)
        self.assertEqual(len(data),1)
        self.assertEqual(read.call_count,2)
        self.assertTrue(all(x.args[0]=="GET" for x in read.call_args_list))


if __name__=="__main__":
    unittest.main()
