import unittest
from unittest.mock import patch
from growth.own_conversations import observe

class OwnConversationsTests(unittest.TestCase):
    @patch("growth.own_conversations.load_credentials",return_value=("token","dohay_dilam"))
    def test_read_only_counts_no_text_or_identity(self,_auth):
        calls=[]
        def read(method,path,token,*,params):
            calls.append((method,path,params))
            if path=="/me": return {"id":"1","username":"dohay_dilam"}
            if path=="/me/threads": return {"data":[{"id":"42"}]}
            if path=="/42/replies": return {"data":[{"id":"501"},{"id":"502"}]}
            raise AssertionError(path)
        report=observe(object(),request=read)
        self.assertEqual(report["visible_direct_replies_sample"],2)
        self.assertTrue(all(m=="GET" for m,_,_ in calls))
        self.assertNotIn("username",report)
        self.assertNotIn("text",str(report))
        self.assertFalse(report["automated_reply_posted"])

    @patch("growth.own_conversations.load_credentials",return_value=("token","dohay_dilam"))
    def test_missing_scope_not_zero_reply_evidence(self,_auth):
        def read(method,path,token,*,params):
            if path=="/me":return {"id":"1","username":"dohay_dilam"}
            if path=="/me/threads":return {"data":[{"id":"42"}]}
            raise PermissionError("no scope")
        report=observe(object(),request=read)
        self.assertEqual(report["state"],"partial")
        self.assertEqual(report["unavailable_post_reply_reads"],1)

    @patch("growth.own_conversations.load_credentials",return_value=None)
    def test_off_without_oauth(self,_auth):
        self.assertEqual(observe(object())["state"],"oauth_unavailable")

if __name__=="__main__": unittest.main()
