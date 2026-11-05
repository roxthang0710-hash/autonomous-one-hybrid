"""Near-limit external-booking watcher never mutates or republishes posts."""
import unittest
from datetime import datetime,timezone
from unittest.mock import MagicMock
from growth.threads_external_length_guard import check,run

NOW=datetime(2026,11,5,11,32,tzinfo=timezone.utc)
ID="c652568c-1b96-4cd3-8644-344e74c5e8f5"

def row(chars,status="scheduled_external",at="2026-11-05T11:30:00+00:00"):
    return {"id":ID,"status":status,"text_content":"a"*chars,"scheduled_at":at}

class ExternalGuardTests(unittest.TestCase):
    def test_flags_close_to_api_cap_but_not_ordinary_text(self):
        r=check([row(495),row(479),row(501)],now=NOW)
        self.assertEqual(len(r),2)
        self.assertEqual(r[0]["chars"],495)
        self.assertEqual(r[1]["code"],"caption_over_threads_limit")
    def test_never_flags_posted_or_unrelated_future(self):
        self.assertEqual(check([row(502,status="posted"),
                row(502,at="2026-12-01T11:30:00+00:00")],now=NOW),[])
    def test_run_notifies_owner_but_never_republishes(self):
        db=MagicMock()
        def mock_request(method,path,**kwargs):
            if path=="/threads_posts":return [row(495)]
            if path=="/enna_desk_owners":return [{"user_id":"owner-id"}]
            if path=="/enna_desk_notifications":
                self.assertEqual(method,"POST")
                self.assertEqual(kwargs["payload"][0]["source_key"],"threads-caption-risk:"+ID)
                return [{"id":1}]
            raise AssertionError("Unexpected Meta or Metricool write")
        db.request.side_effect=mock_request
        result=run(db,now=NOW)
        self.assertEqual(result["risk_count"],1)
        self.assertFalse(result["changed_scheduled_posts"])
        self.assertEqual([x.args[1] for x in db.request.call_args_list],
                         ["/threads_posts","/enna_desk_owners","/enna_desk_notifications"])

if __name__=="__main__":unittest.main()
