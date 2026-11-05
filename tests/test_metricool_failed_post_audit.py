"""Provider error audit is strictly read-only on Meta and never double-posts."""
import unittest
from unittest.mock import MagicMock,patch
from growth.metricool_failed_post_audit import find_exact,audit

POST={
 "id":"c652568c-1b96-4cd3-8644-344e74c5e8f5",
 "status":"scheduled_external","scheduled_at":"2026-11-05T11:30:00+00:00",
 "text_content":"Huy làm bảng báo cáo mất 2 tiếng",
 "platform_post_id":None
}
META_ID="18123456789012345"
LIVE={"id":META_ID,"text":POST["text_content"],"timestamp":"2026-11-05T11:30:10+00:00",
      "permalink":"https://www.threads.com/@dohay_dilam/post/test"}

class ErrorAuditTests(unittest.TestCase):
    def test_only_exact_unique_match(self):
        self.assertIsNotNone(find_exact(POST,[LIVE]))
        self.assertIsNone(find_exact(POST,[LIVE,{**LIVE,"id":"18123456789099999"}]))
        self.assertIsNone(find_exact(POST,[{**LIVE,"text":"changed"}]))
        self.assertIsNone(find_exact(POST,[{**LIVE,"timestamp":"2026-11-08T11:30:10+00:00"}]))
    def test_if_meta_absent_never_publishes(self):
        db=MagicMock()
        def route(method,path,**kwargs):
            if path=="/threads_posts":return [dict(POST)]
            if path=="/enna_desk_owners":return []
            raise AssertionError("Unexpected database mutation "+path)
        db.request.side_effect=route
        def read(method,path,token,params=None):
            self.assertEqual(method,"GET")
            if path=="/me":return {"username":"dohay_dilam","id":"100"}
            if path=="/me/threads":return {"data":[]}
            raise AssertionError("No Meta posting permitted")
        with patch("growth.metricool_failed_post_audit.load_credentials",
                   return_value=("fake","dohay_dilam")):
            result=audit(db,metricool_id="416708580",
                         ledger_id=POST["id"],read=read)
        self.assertEqual(result["state"],"not_seen_on_meta_yet")
        self.assertFalse(result["auto_retry_performed"])
    def test_verified_meta_match_updates_ledger_without_new_post(self):
        db=MagicMock()
        def route(method,path,**kwargs):
            if method=="GET" and path=="/threads_posts":return [dict(POST)]
            if method=="PATCH" and path=="/threads_posts":
                self.assertEqual(kwargs["payload"]["platform_post_id"],META_ID)
                self.assertEqual(kwargs["params"]["status"],"eq.scheduled_external")
                return [{"status":"posted"}]
            if path=="/enna_publication_evidence":return [{"meta_post_id":META_ID}]
            if path=="/enna_desk_owners":return []
            raise AssertionError("Unexpected database request")
        db.request.side_effect=route
        def read(method,path,token,params=None):
            self.assertEqual(method,"GET")
            if path=="/me":return {"username":"dohay_dilam","id":"100"}
            if path=="/me/threads":return {"data":[LIVE]}
            raise AssertionError("No Meta writing allowed")
        with patch("growth.metricool_failed_post_audit.load_credentials",
                   return_value=("fake","dohay_dilam")):
            result=audit(db,metricool_id="416708580",
                         ledger_id=POST["id"],read=read)
        self.assertEqual(result["state"],"meta_verified_posted")
        self.assertFalse(result["auto_retry_performed"])
    def test_already_published_never_queries_meta(self):
        db=MagicMock()
        db.request.return_value=[{**POST,"status":"posted","platform_post_id":"22"}]
        with patch("growth.metricool_failed_post_audit.load_credentials") as auth:
            result=audit(db,metricool_id="416708580",ledger_id=POST["id"])
        self.assertEqual(result["state"],"already_verified_posted")
        auth.assert_not_called()

if __name__=="__main__":unittest.main()
