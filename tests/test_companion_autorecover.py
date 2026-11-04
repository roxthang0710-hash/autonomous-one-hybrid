"""Autonomous Enna recovery: no spam, no Meta publish, bounded retries."""
import datetime as dt
import unittest
from unittest.mock import MagicMock, patch
from growth.companion_autorecover import (
    eligible, state_marker, run, make_recovery_draft, Github,
)

NOW=dt.datetime(2026,11,4,8,0,tzinfo=dt.timezone.utc)
OWNER="roxthang0710-hash"


def sample_issue(number=49):
    return {"number":number,"title":"enna-pick:DfSTHg2k_oi",
            "user":{"login":OWNER},
            "created_at":(NOW-dt.timedelta(minutes=120)).isoformat(),
            "body":"ENNA_PICK_V2\nTHREADS_URL: https://www.threads.com/@example/post/DfSTHg2k_oi\nSELECTED_TEXT_BASE64URL: test"}


def failed_comment():
    return {"id":100,"user":{"login":"github-actions[bot]"},
            "body":"Enna đã soạn nội dung nhưng bộ kiểm tra không thấy "
                   "bình luận bám đủ sát bài gốc. Không tự đăng."}


def progress(attempts,status="retrying",when=None,ident=101):
    when=when or (NOW-dt.timedelta(hours=1))
    stamp=when.isoformat(timespec="seconds").replace("+00:00","Z")
    return {"id":ident,"user":{"login":"github-actions[bot]"},
            "body":f"<!-- ENNA_SELFHEAL_V1 attempts={attempts} "
                   f"last={stamp} status={status} -->\nĐang xử lý."}


class SelfHealingTests(unittest.TestCase):
    def test_only_explicit_recent_owner_issue_is_eligible(self):
        self.assertTrue(eligible(sample_issue(),[failed_comment()],
                                 owner=OWNER,now=NOW))
        other=sample_issue()
        other["user"]["login"]="random_user"
        self.assertFalse(eligible(other,[failed_comment()],owner=OWNER,now=NOW))
        ancient=sample_issue()
        ancient["created_at"]=(NOW-dt.timedelta(days=7)).isoformat()
        self.assertFalse(eligible(ancient,[failed_comment()],owner=OWNER,now=NOW))

    def test_declared_meta_result_or_previous_draft_prevents_retry(self):
        uncertain={"user":{"login":"github-actions[bot]"},
                   "body":"⚠️ Meta không trả về kết quả chắc chắn."}
        published={"user":{"login":"github-actions[bot]"},
                   "body":"✅ Enna đã nhận xác nhận phản hồi từ Meta."}
        draft={"user":{"login":"github-actions[bot]"},
               "body":"🧪 KIỂM THỬ NỘI DUNG, KHÔNG ĐĂNG THREADS"}
        for result in (uncertain,published,draft):
            self.assertFalse(eligible(sample_issue(),[failed_comment(),result],
                                      owner=OWNER,now=NOW))

    def test_regression_failed_after_ai_failure_still_eligible(self):
        # Reproduces real Issue #49, whose last message is a failing CI test
        # rather than the original Groq/editorial failure.
        ci={"id":102,"user":{"login":"github-actions[bot]"},
            "body":"Enna đã dừng trước khi đăng vì bộ kiểm thử biên tập "
                   "chưa đạt. Không có bình luận Threads nào được gửi."}
        self.assertTrue(eligible(sample_issue(),
                                 [failed_comment(),ci],
                                 owner=OWNER,now=NOW))

    def test_repair_state_has_cooldown_and_max_attempts(self):
        comments=[failed_comment(),progress(1,when=NOW-dt.timedelta(minutes=5))]
        self.assertFalse(eligible(sample_issue(),comments,owner=OWNER,now=NOW))
        last=progress(2,when=NOW-dt.timedelta(hours=1))
        self.assertTrue(eligible(sample_issue(),[failed_comment(),last],
                                 owner=OWNER,now=NOW))
        exhausted=progress(3,status="needs_attention")
        self.assertFalse(eligible(sample_issue(),[failed_comment(),exhausted],
                                  owner=OWNER,now=NOW))

    def test_autorepair_success_writes_once_without_posting(self):
        gh=MagicMock()
        gh.repo=OWNER+"/autonomous-one-hybrid"
        gh.issues.return_value=[sample_issue()]
        gh.comments.return_value=[failed_comment()]
        gh.status.return_value={}
        recover=MagicMock(return_value={"draft":"Vậy là đi làm theo vòng đời voucher rồi!",
                                        "model":"model","target":"url"})
        outcome=run(github=gh,recover=recover,now=NOW)
        self.assertEqual(outcome["status"],"repaired")
        self.assertEqual(outcome["issue"],49)
        gh.status.assert_called_once()
        args=gh.status.call_args.args
        self.assertIn("KHÔNG TỰ ĐĂNG THREADS",args[3])
        self.assertNotIn("Bản nháp để bạn xem và tự đăng nếu phù hợp",args[3])
        self.assertNotIn("Meta chưa cho phép",args[3])
        recover.assert_called_once()

    def test_failed_repair_reuses_one_comment_not_repost(self):
        gh=MagicMock()
        gh.repo=OWNER+"/autonomous-one-hybrid"
        gh.issues.return_value=[sample_issue()]
        gh.comments.return_value=[failed_comment(),progress(1)]
        outcome=run(github=gh,recover=lambda issue:None,now=NOW)
        self.assertEqual(outcome["status"],"retrying")
        self.assertEqual(outcome["attempt"],2)
        self.assertEqual(gh.status.call_args.args[1]["id"],101)
        self.assertEqual(gh.status.call_args.kwargs["status"],"retrying")

    def test_github_status_patch_only_updates_existing_progress(self):
        client=MagicMock()
        reply=MagicMock(content=b"{}")
        reply.json.return_value={"id":101}
        client.request.return_value=reply
        gh=Github(OWNER+"/autonomous-one-hybrid","fake_token",client=client)
        gh.status(49,{"id":101},2,"Đang sửa",status="retrying",now=NOW)
        self.assertEqual(client.request.call_args.args[0],"PATCH")
        self.assertTrue(client.request.call_args.args[1].endswith(
            "/issues/comments/101"))
        self.assertIn("ENNA_SELFHEAL_V1",
                      client.request.call_args.kwargs["json"]["body"])
        self.assertNotIn("fake_token",
                         client.request.call_args.kwargs["json"]["body"])

    def test_manual_issue_limits_to_named_owner_selection(self):
        gh=MagicMock()
        gh.repo=OWNER+"/autonomous-one-hybrid"
        gh.issues.return_value=[sample_issue(49),sample_issue(48)]
        gh.comments.return_value=[failed_comment()]
        outcome=run(github=gh,recover=lambda issue:None,
                    now=NOW,manual_issue=48)
        self.assertEqual(outcome["issue"],48)
        gh.comments.assert_called_once_with(48)

    def test_groq_schema_failure_cannot_cause_meta_post(self):
        # Wrongly shaped issue is rejected locally, not sent to an API.
        with self.assertRaises(ValueError):
            make_recovery_draft(sample_issue(),
                propose=lambda *a,**kw:[],writer=lambda *a,**kw:None,
                reviewer=lambda *a,**kw:False)


if __name__=="__main__":
    unittest.main()
