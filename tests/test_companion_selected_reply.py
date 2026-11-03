"""Safe, owner-selected Threads post -> Enna issue workflow tests."""
import base64
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock,patch

from growth.companion_selected_reply import (
    decode_issue_body,parse_threads_url,verified_meta_target,
    can_send,process,HEADER
)

KNOWN_CODE="DdcPsEkH3NZ"
KNOWN_ID="3989132369199067993"
TEXT=("Một bảng tính Excel dùng chung mà mỗi đồng nghiệp ghi một trạng thái "
      "khác nhau khiến mọi người khó theo dõi công việc và deadline mỗi tuần. "
      "Có cách nào để cả nhóm làm chung cho rõ ràng không?")
ANSWER=("Với bảng tính dùng chung, thử tạo danh sách chọn trạng thái và "
        "thống nhất ai cập nhật từng việc trước hạn chót. "
        "Đỡ cảnh cùng một việc mà ai cũng hiểu một kiểu.")
URL="https://www.threads.com/@nguoi_demo/post/"+KNOWN_CODE


def issue():
    payload=base64.urlsafe_b64encode(TEXT.encode("utf-8")).decode().rstrip("=")
    return {
      "sender":{"login":"roxthang0710-hash"},
      "repository":{"owner":{"login":"roxthang0710-hash"}},
      "issue":{"id":999123456,"number":99,
        "user":{"login":"roxthang0710-hash"},
        "title":"enna-pick:"+KNOWN_CODE,
        "body":HEADER+"\nTHREADS_URL: "+URL+
               "\nSELECTED_TEXT_BASE64URL: "+payload}
    }


class SelectionTests(unittest.TestCase):
    def test_shortcode_decoding_is_exact_integer(self):
        target=parse_threads_url(URL+"?ref=share")
        self.assertEqual(target["candidate_id"],KNOWN_ID)
        self.assertEqual(target["username"],"nguoi_demo")

    def test_only_threads_canonical_links(self):
        for value in (
            "http://www.threads.com/@user/post/"+KNOWN_CODE,
            "https://threads.com.evil.test/@user/post/"+KNOWN_CODE,
            "https://www.threads.com/",
            "https://www.threads.com/@dohay_dilam/post/"+KNOWN_CODE):
            with self.assertRaises(ValueError):
                parse_threads_url(value)

    def test_explicit_selection_is_structured_and_ends_at_one_post(self):
        target,body,classification=decode_issue_body(issue()["issue"]["body"])
        self.assertEqual(target["candidate_id"],KNOWN_ID)
        self.assertEqual(body,TEXT)
        self.assertEqual(classification["state"],"candidate")

    def test_rejects_nonowner_event_without_any_api_calls(self):
        e=issue()
        e["sender"]["login"]="random_user"
        db=MagicMock()
        result=process(e,db=db)
        self.assertEqual(result["state"],"not_project_owner")
        db.request.assert_not_called()

    def test_official_graph_read_required_even_with_known_shortcode(self):
        published=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        item={"id":KNOWN_ID,"username":"nguoi_demo","text":TEXT,
              "timestamp":published,
              "permalink":URL}
        target=parse_threads_url(URL)
        self.assertTrue(verified_meta_target(item,target,TEXT))
        self.assertFalse(verified_meta_target({**item,"username":"other"},target,TEXT))
        self.assertFalse(verified_meta_target({**item,"id":"123"},target,TEXT))
        self.assertFalse(verified_meta_target({**item,"text":"completely different"},target,TEXT))

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_cannot_auto_publish_if_meta_cannot_read_selected_post(self,_):
        db=MagicMock()
        credentials=lambda d:("fake_secure_token","dohay_dilam")
        read=MagicMock(side_effect=ValueError("Meta App Review prevents reading"))
        publish=MagicMock()
        create=MagicMock(return_value={"post_text":ANSWER})
        result=process(issue(),db=db,credentials=credentials,
            read=read,publish=publish,create=create)
        self.assertEqual(result["state"],"draft_only_meta_cannot_verify_target")
        publish.assert_not_called()
        db.request.assert_not_called()

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_one_verified_post_one_reply_with_atomic_claim(self,_):
        db=MagicMock()
        db.request.return_value=[{"attempt_id":"550e8400-e29b-41d4-a716-446655440000"}]
        credentials=lambda d:("fake_secure_token","dohay_dilam")
        item={"id":KNOWN_ID,"username":"nguoi_demo","text":TEXT,
              "timestamp":(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),
              "permalink":URL}
        publish=MagicMock(return_value=("container","actual_meta_reply_id"))
        result=process(issue(),db=db,credentials=credentials,
            read=lambda *a,**kw:item,publish=publish,
            create=lambda *a,**kw:{"post_text":ANSWER})
        self.assertEqual(result["state"],"posted_confirmed")
        publish.assert_called_once()
        self.assertEqual(db.request.call_args.kwargs["payload"]["p_target_post_id"],KNOWN_ID)
        db.patch.assert_called_once()

    def test_generic_promotional_comment_rejected(self):
        self.assertFalse(can_send("Theo dõi kênh và mua ngay!",TEXT,target=parse_threads_url(URL)))


if __name__=="__main__":
    unittest.main()
