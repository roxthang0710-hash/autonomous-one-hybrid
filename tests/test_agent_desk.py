"""Enna Desk safety and task-response regression tests."""
import base64
import unittest
from growth.agent_desk import parse_event, summarize, response


def event(text="Báo cáo KPI Threads hôm nay", kind="report", sender="roxthang0710-hash"):
    raw=base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")
    return {
        "action":"opened",
        "sender":{"login":sender},
        "issue":{"title":"enna-task:"+kind,"user":{"login":"roxthang0710-hash"},
                 "body":"ENNA_TASK_V1\nTYPE: "+kind+"\nREQUEST_BASE64URL: "+raw},
    }


class DeskTests(unittest.TestCase):
    def test_valid_owner_request(self):
        kind,text=parse_event(event(),"roxthang0710-hash")
        self.assertEqual(kind,"report")
        self.assertIn("KPI",text)
    def test_nonowner_rejected(self):
        with self.assertRaises(ValueError):
            parse_event(event(sender="other"),"roxthang0710-hash")
    def test_mismatched_type_rejected(self):
        obj=event();obj["issue"]["title"]="enna-task:ideas"
        with self.assertRaises(ValueError):
            parse_event(obj,"roxthang0710-hash")
    def test_multiline_payload_injection_rejected(self):
        obj=event()
        obj["issue"]["body"]+="\nARBITRARY: shell"
        with self.assertRaises(ValueError):
            parse_event(obj,"roxthang0710-hash")
    def test_unknown_task_rejected(self):
        with self.assertRaises(ValueError):
            parse_event(event(kind="shell"),"roxthang0710-hash")
    def test_no_fabricated_numbers(self):
        empty={"followers":[],"content":[],"media":[],"events":[]}
        stats=summarize("report",empty)
        self.assertIn("chưa có số liệu",stats["metrics"])
        self.assertIn("Không có bài đăng",response("report","Cho biết hiệu quả",stats))
    def test_read_only_snapshot_summary(self):
        s=summarize("diagnose",{"followers":[{"measured_on":"2026-11-04","followers":5}],
            "content":[{"status":"queued","topic_tag_planned":"Công sở"}],
            "media":[{"media_type":"original_meme","status":"ready"}],
            "events":[{"code":"ops_failed","status":"failed"}]})
        self.assertEqual(s["queued"],1)
        self.assertEqual(s["native_topics_verified_in_ledger"],0)
        self.assertEqual(s["ready_memes"],1)
        self.assertEqual(s["ready_videos"],0)


if __name__=="__main__":
    unittest.main()
