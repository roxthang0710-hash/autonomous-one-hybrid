"""Safe, owner-selected Threads post -> Enna issue workflow tests."""
import base64
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock,patch

from growth.companion_selected_reply import (
    decode_issue_body,parse_threads_url,verified_meta_target,
    can_send,process,clean_selected_excerpt,HEADER
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
LIFE_TEXT=("Cuối tuần cả nhóm đi chơi, bất ngờ thấy một chú chó nằm ngủ ngon lành "
           "ở quán cà phê. Ai cũng bật cười vì chú chó trông còn thư thái "
           "hơn cả chúng tôi. Một khoảnh khắc vui khiến ngày dài dễ chịu hơn.")
LIFE_REPLY=("Chú chó ngủ ngon lành giữa quán cà phê đúng là chuyên gia nghỉ ngơi! "
            "Cả nhóm bật cười vì gặp một khoảnh khắc nhỏ mà dễ thương thật.")



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

    def test_owner_can_select_everyday_humor_without_office_keywords(self):
        from growth.companion_fit import assess_selected
        verdict = assess_selected(LIFE_TEXT)
        self.assertEqual(verdict["state"], "candidate")
        self.assertTrue(verdict["human_selected"])
        self.assertFalse(verdict["viral_metrics_verified"])
        self.assertTrue(can_send(LIFE_REPLY, LIFE_TEXT, target=parse_threads_url(URL)))
        self.assertEqual(assess_selected(
            "Đăng số điện thoại 0901234567 để mọi người gọi hỏi cho vui"
        )["state"],"rejected")

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_selected_everyday_post_can_be_reviewed_and_drafted(self,_):
        e=issue()
        import base64
        encoded=base64.urlsafe_b64encode(LIFE_TEXT.encode("utf-8")).decode().rstrip("=")
        e["issue"]["body"]=(
          HEADER+"\nTHREADS_URL: "+URL+"\nSELECTED_TEXT_BASE64URL: "+encoded)
        db=MagicMock()
        result=process(e,db=db,
            credentials=lambda d:("fake_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,
                "post_text":LIFE_REPLY,"content_angle":"Những khoảnh khắc nhỏ giúp ngày vui hơn"},
            read=MagicMock(side_effect=ValueError("third_party_scope_blocked")),
            publish=MagicMock())
        self.assertEqual(result["state"],"draft_only_meta_cannot_verify_target")
        self.assertIn("khoảnh khắc",result["content_angle"])

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_enna_can_decide_not_to_interject(self,_):
        e=issue()
        result=process(e,db=MagicMock(),
            credentials=lambda d:("fake_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":False,
                "post_text":"","content_angle":"Câu chuyện có thể trở thành meme gốc"},
            read=MagicMock(),publish=MagicMock())
        self.assertEqual(result["state"],"not_worth_interjecting")

    def test_clean_clicked_post_excludes_our_button_and_engagement_counters(self):
        raw=("tac_gia\n6 giờ✳ Gửi Enna\n"
             "Một câu chuyện về chú nấu cháo và lịch sử tìm kiếm âm thầm "
             "khiến người đọc cảm động.\n2,8K\n25\n73\n12")
        clean=clean_selected_excerpt(raw)
        self.assertIn("nấu cháo",clean)
        self.assertNotIn("Gửi Enna",clean)
        self.assertNotIn("2,8K",clean)
        self.assertNotIn("6 giờ",clean)

    def test_usable_draft_survives_missing_meta_oauth(self):
        post = MagicMock()
        graph = MagicMock()
        db = MagicMock()
        result = process(issue(), db=db,
            credentials=lambda d:None, read=graph, publish=post,
            create=lambda *a,**k:{
                "should_reply":True, "post_text":ANSWER,
                "content_angle":"Làm bảng chung mà không loạn trạng thái"})
        self.assertEqual(result["state"],"draft_only_meta_not_authorized")
        self.assertEqual(result["draft"],ANSWER)
        graph.assert_not_called()
        post.assert_not_called()
        db.request.assert_not_called()

    def test_selected_family_story_has_real_context_not_office_keywords(self):
        from growth.companion_fit import assess_selected
        story = ("Chú ruột nhận ra cháu mệt nên lặng lẽ nấu cháo, "
                 "để trước cửa phòng rồi đi. Tối đó cháu mở YouTube "
                 "và thấy lịch sử tìm kiếm cách nấu cháo không bị khét. "
                 "Một chuyện nhỏ nhưng làm cả nhà xúc động.")
        reply = ("Chú để tô cháo trước cửa đã ấm lòng rồi, mà lịch sử "
                 "tìm kiếm cách nấu cháo không bị khét còn dễ thương hơn. "
                 "Quan tâm đôi khi lặng lẽ vậy đó.")
        self.assertEqual(assess_selected(story)["state"],"candidate")
        self.assertTrue(can_send(reply,story,target=parse_threads_url(URL)))

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_invalid_ai_draft_is_diagnosed_without_touching_meta(self,_):
        event=issue()
        send=MagicMock()
        result=process(event,db=MagicMock(),
            credentials=lambda d:("fake_token","dohay_dilam"),
            create=MagicMock(side_effect=ValueError("invalid_format")),
            read=MagicMock(),publish=send)
        self.assertEqual(result["state"],"ai_draft_invalid_or_unavailable")
        send.assert_not_called()

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_owner_opt_in_official_direct_reply_after_read_scope_denied(self, _):
        import requests
        from growth.selected_direct_reply import ConfirmedMetaRejection
        response=requests.Response()
        response.status_code=403
        read=MagicMock(side_effect=requests.HTTPError("read access denied",response=response))
        e=issue()
        e["issue"]["created_at"]=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        db=MagicMock()
        db.request.return_value=[{"attempt_id":"550e8400-e29b-41d4-a716-446655440000"}]
        direct=MagicMock(return_value=("container","meta_direct_reply_id"))
        regular=MagicMock()
        result=process(e,db=db,read=read,
            publish=regular,direct_publish=direct,allow_direct_trial=True,
            credentials=lambda d:("fake_secure_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,"post_text":ANSWER,
                "content_angle":"Bảng chung rõ trạng thái"})
        self.assertEqual(result["state"],"posted_confirmed")
        self.assertEqual(result["verification"],"meta_publish_confirmed")
        direct.assert_called_once()
        regular.assert_not_called()
        db.patch.assert_called_once()

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_direct_meta_create_rejection_is_not_false_success(self, _):
        import requests
        from growth.selected_direct_reply import ConfirmedMetaRejection
        response=requests.Response()
        response.status_code=403
        e=issue()
        e["issue"]["created_at"]=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        db=MagicMock()
        db.request.return_value=[{"attempt_id":"550e8400-e29b-41d4-a716-446655440000"}]
        result=process(e,db=db,read=MagicMock(side_effect=
            requests.HTTPError("read forbidden",response=response)),
            direct_publish=MagicMock(side_effect=ConfirmedMetaRejection(403)),
            allow_direct_trial=True,
            credentials=lambda d:("fake_secure_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,"post_text":ANSWER,
                "content_angle":"Tối ưu việc nhóm"})
        self.assertEqual(result["state"],"meta_rejected_direct_reply")
        self.assertEqual(db.patch.call_args.args[2]["status"],"meta_rejected")

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_direct_fallback_never_follows_bad_or_old_meta_read(self, _):
        import requests
        e=issue()
        e["issue"]["created_at"]=(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()
        response=requests.Response()
        response.status_code=403
        direct=MagicMock()
        db=MagicMock()
        result=process(e,db=db,read=MagicMock(side_effect=
            requests.HTTPError("read forbidden",response=response)),
            direct_publish=direct,allow_direct_trial=True,
            credentials=lambda d:("fake_secure_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,"post_text":ANSWER,
                "content_angle":"Việc nhóm"})
        self.assertEqual(result["state"],"draft_only_meta_cannot_verify_target")
        direct.assert_not_called()
        db.request.assert_not_called()

    def test_official_meta_direct_reply_api_rejected_at_create_stage(self):
        from growth.selected_direct_reply import (
            ConfirmedMetaRejection, direct_reply, target_read_limited)
        import requests
        response=requests.Response()
        response.status_code=403
        err=requests.HTTPError("permission",response=response)
        self.assertTrue(target_read_limited(err))
        writer=MagicMock(side_effect=err)
        with self.assertRaises(ConfirmedMetaRejection):
            direct_reply("token",KNOWN_ID,ANSWER,request=writer)
        writer.assert_called_once()

    def test_generic_promotional_comment_rejected(self):
        self.assertFalse(can_send("Theo dõi kênh và mua ngay!",TEXT,target=parse_threads_url(URL)))

    def test_generic_story_paraphrase_rejected(self):
        summary=("Chú ở chung nhà, rồi chú múc tô cháo để trước cửa,"
                 " mở YouTube xem lại. Thật là một khoảnh khắc đời thường ngọt ngào!")
        self.assertFalse(can_send(summary,TEXT,target=parse_threads_url(URL)))


if __name__=="__main__":
    unittest.main()
