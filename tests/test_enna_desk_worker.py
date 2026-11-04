"""Verify owner answers are model-generated and evidence-grounded, never canned."""
import os
import unittest
from unittest.mock import patch, MagicMock
from growth.enna_desk_worker import eligible, upgrade, run, evidence_snapshot, call_model, is_prompt_echo, verified_facts

def task(used="awaiting_model_v2",status="running",text="Tìm phương án tăng follower ngoài đăng bài"):
    return {"id":"00000000-0000-4000-8000-000000000001",
        "kind":"warroom","request_text":text,"status":status,
        "model_used":used,"response":{"evidence":{"follower_count":3}}}

def result(task,evidence):
    return {
        "direct_answer":"Vấn đề không chỉ nằm ở số lượng bài. Enna cần thử tăng tỷ lệ chuyển từ người xem sang người theo dõi và phân phối đúng các cộng đồng liên quan, sau đó đo lường kết quả có căn cứ.",
        "verified_findings":["Dữ liệu follower chưa được đồng bộ và không đủ để kết luận nguyên nhân chính."],
        "actions":[
            {"action":"Thiết kế lại hồ sơ và lời kêu gọi theo dõi của kênh",
             "rationale":"Người xem cần biết lợi ích của việc theo dõi", "executor":"enna",
             "success_check":"Lưu bản nháp và kiểm tra lượt truy cập hồ sơ", "status":"proposed"},
            {"action":"Thử bình luận hữu ích tại các cuộc thảo luận phù hợp",
             "rationale":"Tiếp cận người có nhu cầu cụ thể", "executor":"enna",
             "success_check":"Chỉ tính bình luận có mã xác nhận và tương tác thật", "status":"proposed"},
            {"action":"Làm một meme nguyên bản để người xem chia sẻ",
             "rationale":"Cải thiện tiếp cận tự nhiên và khả năng lưu nội dung", "executor":"enna",
             "success_check":"Đo lượt chia sẻ và follower mới trong 24 giờ", "status":"proposed"},
        ],
        "unknowns":["Số follower hiện tại chưa được xác minh."],
        "role_summaries":{
            "analyst":"Cần đối chiếu dữ liệu follower với số lượt xem từng định dạng.",
            "strategist":"Ưu tiên thí nghiệm chuyển đổi, tương tác hữu ích và tối ưu hồ sơ.",
            "operator":"Mỗi bước cần có bằng chứng, không tính dự kiến như đã hoàn thành."
        }
    }

class DeskWorkerTests(unittest.TestCase):
    def test_queue_and_legacy_are_eligible(self):
        self.assertTrue(eligible(task()))
        self.assertTrue(eligible(task("rule_based_multi_role","completed")))
        self.assertTrue(eligible(task("groq_multi_role_partial","completed")))
        self.assertFalse(eligible(task("groq_task_specific_v2","completed")))
        self.assertFalse(eligible(task("awaiting_model_v2","failed")))
    def test_model_response_replaces_old_template(self):
        t=task()
        out=upgrade(t,{"follower_snapshots":[{"followers":3}]},model_call=result)
        self.assertEqual(out["engine"],"groq_task_specific_v2")
        self.assertIn("ngoài",t["request_text"])
        self.assertIn("không chỉ",out["direct_answer"])
        self.assertEqual(len(out["action_plan"]),3)
        self.assertTrue(out["previous_response_replaced"])
        self.assertNotIn("rule_based_fallback",str(out))
    def test_distinct_prompts_are_preserved(self):
        a=upgrade(task(text="Hãy đưa cách tăng follow ngoài việc đăng bài"),{},model_call=result)
        b=upgrade(task(text="Lỗi workflow không chạy, kiểm tra nguyên nhân"),{},model_call=result)
        self.assertNotEqual(a["request"],b["request"])
    def test_no_key_does_not_fake_results(self):
        with patch.dict(os.environ,{"GROQ_API_KEY":""}):
            self.assertEqual(run(db=MagicMock()),"groq_key_unavailable")
    def test_empty_db_is_no_tasks(self):
        with patch.dict(os.environ,{"GROQ_API_KEY":"fake"}):
            db=MagicMock()
            db.request.return_value=[]
            self.assertEqual(run(db=db),"no_pending_tasks")
    def test_evidence_refresh_does_not_invent_metric(self):
        db=MagicMock()
        db.request.return_value=[]
        e=evidence_snapshot(db,task())
        self.assertEqual(e["follower_snapshots"],[])
        self.assertFalse(e["native_topic_visually_confirmed"])
        self.assertEqual(e["top_measured_posts"],[])
    def test_rejects_verbatim_user_echo(self):
        question="Enna hiện tại chỉ đưa ra lý thuyết rỗng chưa áp dụng thực tế, ngoài đăng bài thì còn cách nào khác"
        self.assertTrue(is_prompt_echo(question.replace(",",""),question))
        useful="Có ba hướng Enna nên thử: thay đổi hồ sơ, xây dựng tương tác hữu ích và đo lường số người theo dõi từ nguồn thật thay vì lặp lại lịch đăng bài."
        self.assertFalse(is_prompt_echo(useful,question))
    def test_verified_fact_summary_is_deterministic(self):
        e={"follower_snapshots":[{"measured_on":"2026-11-02","followers":3,"age_days":3}],
           "threads_status_counts":{"posted":10,"scheduled_external":30,"queued":8},
           "top_measured_posts":[{"views":2065,"likes":19}],
           "media_ready_by_type":{"original_meme":1,"original_video":0}}
        facts=verified_facts(e)
        self.assertTrue(any("dữ liệu quá hạn" in x for x in facts))
        self.assertTrue(any("10 ghi nhận" in x for x in facts))
        self.assertTrue(any("2065 view" in x for x in facts))
        self.assertTrue(any("0 video" in x for x in facts))

    def test_english_or_echo_is_rewritten_from_evidence_and_model_actions(self):
        class Resp:
            def raise_for_status(self): pass
            def json(self):
                return {"choices":[{"message":{"content":__import__("json").dumps(
                    {**result(task(),{}),"direct_answer":"This is a generic English message with no meaningful Vietnamese."})}}]}
        with patch.dict(os.environ,{"GROQ_API_KEY":"fake"}):
            value=call_model(task(),{},api=lambda *a,**kw:Resp())
            self.assertIn("Enna",value["direct_answer"])
            self.assertIn("ngoài",value["direct_answer"])
            self.assertNotIn("generic English",value["direct_answer"])

if __name__=="__main__":
    unittest.main()
