"""Only one validated private Enna Desk task is updated with real Groq roles."""
import os
import unittest
from unittest.mock import patch, MagicMock
from growth.enna_desk_worker import eligible, upgrade, run

def sample():
    return {"id":"00000000-0000-4000-8000-000000000001","kind":"plan",
      "request_text":"Phân tích cách phát triển kênh Threads tự nhiên",
      "status":"completed","model_used":"rule_based_multi_role",
      "response":{"evidence":{"follower_count":3,"follower_stale":True},
       "roles":[{"role":r,"status":"rule_based_fallback","summary":"Dữ liệu chưa đủ.",
                 "actions":["Đo lại dữ liệu","Kiểm tra nguồn"],"risks":[]}
                for r in ("analyst","strategist","operator")]}}

class DeskWorkerTests(unittest.TestCase):
    def test_exclude_unfinished_and_already_model_answered(self):
        obj=sample()
        self.assertTrue(eligible(obj))
        obj["status"]="running"
        self.assertFalse(eligible(obj))
        obj["status"]="completed"
        obj["model_used"]="groq_multi_role_async"
        self.assertFalse(eligible(obj))

    def test_three_roles_upgrade_and_retains_evidence(self):
        def fake(role, task):
            return {"role":role,"status":"completed",
                    "summary":"Đề xuất thử nghiệm dựa trên dữ liệu đã kiểm chứng.",
                    "actions":["Đồng bộ dữ liệu từ Meta và Metricool",
                               "Tổng hợp tương tác của từng bài trong 24 giờ"],
                    "risks":[]}
        data, model = upgrade(sample(),caller=fake)
        self.assertEqual(model,"groq_multi_role_async")
        self.assertEqual(data["ai_upgrade"]["confirmed_roles"],3)
        self.assertEqual(data["evidence"]["follower_count"],3)

    def test_missing_role_retains_labelled_fallback(self):
        def fake(role, task):
            return None if role=="operator" else {
              "role":role,"status":"completed","summary":"Phân tích có kiểm chứng.",
              "actions":["Thực hiện báo cáo","Đề xuất Topic"],"risks":[]}
        data, model=upgrade(sample(),caller=fake)
        self.assertEqual(model,"groq_multi_role_partial")
        self.assertEqual(data["ai_upgrade"]["confirmed_roles"],2)
        self.assertEqual(data["roles"][2]["status"],"rule_based_fallback")

    def test_bounded_no_key_no_db_connection(self):
        with patch.dict(os.environ,{"GROQ_API_KEY":""}):
            self.assertEqual(run(db=MagicMock()),"ai_key_unavailable")


if __name__=="__main__":
    unittest.main()
