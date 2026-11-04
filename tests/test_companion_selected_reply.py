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
ANSWER=("Bảng tính dùng chung mà mỗi người ghi một trạng thái thì rối thật. "
        "Chốt vài trạng thái cố định là đỡ đoán ý nhau.")
URL="https://www.threads.com/@nguoi_demo/post/"+KNOWN_CODE
LIFE_TEXT=("Cuối tuần cả nhóm đi chơi, bất ngờ thấy một chú chó nằm ngủ ngon lành "
           "ở quán cà phê. Ai cũng bật cười vì chú chó trông còn thư thái "
           "hơn cả chúng tôi. Một khoảnh khắc vui khiến ngày dài dễ chịu hơn.")
LIFE_REPLY=("Chú chó nằm ở quán cà phê mà thư thái hơn cả hội đi chơi. "
            "Chắc bí quyết là không có lịch hẹn.")



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
        reply = ("Chú lo tới mức phải tra cách nấu cháo cho ngon, "
                 "thương cháu kiểu này đúng là nói ít làm nhiều.")
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
    def test_owner_explicit_official_api_command_on_browser_mode_issue(self, _):
        import requests
        e=issue()
        e["issue"]["created_at"]=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        e["issue"]["body"]+="\nENNA_LOCAL_BROWSER_MODE: true"
        e["comment"]={"body":"/enna official",
                     "user":{"login":"roxthang0710-hash"}}
        read_response=requests.Response()
        read_response.status_code=403
        direct=MagicMock(return_value=("container","meta_reply_id"))
        db=MagicMock()
        db.request.return_value=[{"attempt_id":"550e8400-e29b-41d4-a716-446655440000"}]
        result=process(e,db=db,
            read=MagicMock(side_effect=requests.HTTPError("forbidden",response=read_response)),
            direct_publish=direct,allow_direct_trial=True,
            credentials=lambda d:("safe_test_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,
                                  "post_text":ANSWER,"content_angle":"Thảo luận bảng chung"})
        self.assertEqual(result["state"],"posted_confirmed")
        self.assertEqual(result["verification"],"meta_publish_confirmed")
        direct.assert_called_once()

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

    def test_meta_stage_diagnostics_never_retry_after_container(self):
        from growth.selected_direct_reply import (
            MetaStageError, direct_reply, ConfirmedMetaRejection)
        import requests
        http=requests.Response()
        http.status_code=503
        create=MagicMock(side_effect=requests.HTTPError("gateway",response=http))
        with self.assertRaises(MetaStageError) as ctx:
            direct_reply("token",KNOWN_ID,ANSWER,request=create)
        self.assertEqual(ctx.exception.stage,"create")
        self.assertEqual(ctx.exception.http_status,503)
        self.assertEqual(create.call_count,1)

        http.status_code=403
        after_create=MagicMock(side_effect=[
            {"id":"fake_container"},
            requests.HTTPError("publish denied",response=http)
        ])
        with self.assertRaises(MetaStageError) as again:
            direct_reply("token",KNOWN_ID,ANSWER,request=after_create)
        self.assertEqual(again.exception.stage,"publish")
        self.assertEqual(again.exception.http_status,403)
        self.assertEqual(after_create.call_count,2)

    @patch("growth.companion_selected_reply.verify_meta_account")
    def test_browser_mode_never_launches_direct_meta_write_on_read_denial(self,_):
        import requests
        e=issue()
        e["issue"]["created_at"]=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        e["issue"]["body"]+="\nENNA_LOCAL_BROWSER_MODE: true"
        info=decode_issue_body(e["issue"]["body"])
        self.assertTrue(info[2]["local_browser_mode"])
        r=requests.Response()
        r.status_code=403
        direct=MagicMock()
        publish=MagicMock()
        db=MagicMock()
        result=process(e,db=db,read=MagicMock(side_effect=
            requests.HTTPError("read forbidden",response=r)),
            direct_publish=direct,publish=publish,allow_direct_trial=True,
            credentials=lambda d:("fake_secure_token","dohay_dilam"),
            create=lambda *a,**k:{"should_reply":True,"post_text":ANSWER,
                "content_angle":"Quy trình thống nhất công việc"})
        self.assertEqual(result["state"],"draft_only_meta_cannot_verify_target")
        direct.assert_not_called()
        publish.assert_not_called()
        db.request.assert_not_called()

    def test_rejects_forged_handoff_flag(self):
        e=issue()
        e["issue"]["body"]+="\nENNA_LOCAL_BROWSER_MODE: surely"
        with self.assertRaises(ValueError):
            decode_issue_body(e["issue"]["body"])

    def test_owner_draft_diagnostic_never_calls_meta_or_claim(self):
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        e["sender"]["login"]="roxthang0710-hash"
        db=MagicMock()
        read=MagicMock()
        publish=MagicMock()
        credentials=MagicMock()
        result=process(e,db=db,read=read,publish=publish,
            credentials=credentials,create=lambda *a,**k:{
                "should_reply":True,"post_text":ANSWER,
                "content_angle":"Cách thống nhất bảng tính nhóm"})
        self.assertEqual(result["state"],"draft_prepared_only")
        self.assertEqual(result["draft"],ANSWER)
        read.assert_not_called()
        publish.assert_not_called()
        credentials.assert_not_called()
        db.request.assert_not_called()

    def test_groq_429_status_is_classified_and_not_retried(self):
        from growth.companion_editor import _groq_completion,EnnaModelServiceError
        response=MagicMock(status_code=429)
        api=MagicMock(return_value=response)
        with self.assertRaises(EnnaModelServiceError) as caught:
            _groq_completion(api,"fake_key",{"response_format":{"type":"json_schema"}})
        self.assertEqual(caught.exception.safe_reason,"provider_rate_limited_429")
        api.assert_called_once()

    def test_groq_400_tries_json_object_once(self):
        from growth.companion_editor import _groq_completion
        bad=MagicMock(status_code=400)
        good=MagicMock(status_code=200)
        api=MagicMock(side_effect=[bad,good])
        result=_groq_completion(api,"fake_key",{
            "model":"openai/gpt-oss-20b",
            "response_format":{"type":"json_schema","json_schema":{"strict":True}},
            "max_completion_tokens":1400,
        })
        self.assertIs(result,good)
        self.assertEqual(api.call_count,2)
        self.assertEqual(api.call_args.kwargs["json"]["response_format"],
                         {"type":"json_object"})

    def test_generic_positive_reply_is_not_auto_publishable(self):
        selected=("Đang giờ nghỉ trưa mà đồng nghiệp gõ bàn phím cạch cạch "
                  "và kéo ghế liên tục, mình thật sự không ngủ nổi. "
                  "Nói rồi mà ngày nào cũng vậy.")
        unrelated=("Chỉ cần một chút nụ cười, có thể làm thay đổi cả ngày "
                   "làm việc của ai đó. Một lời khen ngọt ngào cũng đủ "
                   "làm thoải mái tâm hồn.")
        grounded=("Giờ nghỉ trưa mà bàn phím cạch cạch liên tục "
                  "thì đúng là có báo thức miễn phí.")
        self.assertFalse(can_send(unrelated,selected,target=parse_threads_url(URL)))
        off_target=("Đúng là lúc cần một chút yên, nhưng bạn có thể "
                    "nhắc nhẹ nhàng rồi thử nghỉ ngơi vài phút, "
                    "nghe nhạc và tiếp tục làm việc.")
        self.assertFalse(can_send(off_target,selected,target=parse_threads_url(URL)))
        self.assertTrue(can_send(grounded,selected,target=parse_threads_url(URL)))

    def test_verbatim_quote_of_selected_post_is_not_a_comment(self):
        source=("Gõ bàn phím cạch cạch, đập chuột, mang vòng cẩm thạch "
                "chạm vào bàn phát ra tiếng. Ngày nào như ngày nấy. "
                "Tôi đã nhắc nhở mà vẫn không thấy thay đổi.")
        copied=("Gõ bàn phím cạch cạch, đập chuột, mang vòng cẩm thạch "
                "chạm vào bàn phát ra tiếng. Ngày nào như ngày nấy.")
        self.assertFalse(can_send(copied,source,target=parse_threads_url(URL)))
        novel=("Nghỉ trưa mà bàn phím cạch cạch với đập chuột liên tục "
               "thì đúng là báo thức bất đắc dĩ.")
        context=("Đang giờ nghỉ trưa thì người cùng phòng gõ bàn phím "
                 "cạch cạch, đập chuột ầm ầm. Đã nhắc nhở mà ngày nào "
                 "cũng vậy, ảnh hưởng cả phòng.")
        self.assertTrue(can_send(novel,context,target=parse_threads_url(URL)))

    def test_frustrated_owner_post_rejects_false_positive_tone(self):
        from growth.companion_fit import user_is_frustrated
        src=("Tôi ghét nhất giờ nghỉ trưa mà đồng nghiệp vẫn gõ bàn phím "
             "cạch cạch rồi đập chuột, đã nhắc nhở mà ngày nào cũng vậy. "
             "Mệt thực sự, chỉ muốn yên tĩnh.")
        false_praise=("Gõ bàn phím cạch cạch, còn vòng cẩm thạch "
                      "chạm vào bàn. Có vẻ anh ấy đang cố gắng hết mình "
                      "và thêm điểm nhấn thú vị cho giờ nghỉ trưa.")
        self.assertTrue(user_is_frustrated(src))
        self.assertFalse(can_send(false_praise,src,target=parse_threads_url(URL)))
        useful=("Giờ nghỉ trưa còn nghe bàn phím cạch cạch với đập chuột "
                "thì khó chịu thật. Đã nhắc rồi mà vẫn vậy mới mệt.")
        self.assertTrue(can_send(useful,src,target=parse_threads_url(URL)))

    def test_gen_z_decor_post_can_get_grounded_playful_reply(self):
        post=("Team mình mới có bé Gen Z vào làm. Hôm nay thấy ẻm "
              "bắt đầu mang đồ để decor bàn làm việc rồi. "
              "Này là dấu hiệu ẻm sẽ gắn bó lâu dài với công ty "
              "đúng không mọi người? Chắc ẻm không nghỉ việc sớm đâu nhỉ?")
        reply=("Mới vào đã decor bàn làm việc thì gắn bó với chiếc bàn "
               "trước rồi, công ty còn phải xem đã 😄")
        self.assertTrue(can_send(reply,post,target=parse_threads_url(URL)))

    def test_semantic_judge_allows_grounded_paraphrase_only_in_draft_test(self):
        text=("Mỗi nhiệm vụ nên có tên người nhận và mốc hẹn cụ thể. "
              "Nhìn vào là biết ai đang chờ ai, khỏi mất công đoán.")
        self.assertFalse(can_send(text,TEXT,target=parse_threads_url(URL)))
        self.assertTrue(can_send(text,TEXT,target=parse_threads_url(URL),
                                 semantic_override=True))
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        read,publish=MagicMock(),MagicMock()
        reviewer=MagicMock(return_value=True)
        result=process(e,db=MagicMock(),read=read,publish=publish,
            credentials=MagicMock(),semantic_judge=reviewer,
            create=lambda *a,**kw:{"should_reply":True,"post_text":text,
                                    "content_angle":"Cách thiết kế bảng theo dõi chung"})
        self.assertEqual(result["state"],"draft_prepared_only")
        reviewer.assert_called_once()
        read.assert_not_called()
        publish.assert_not_called()
        from growth.companion_selected_reply import safe_comment
        output=safe_comment(result)
        self.assertIn("KIỂM THỬ NỘI DUNG",output)
        self.assertNotIn("Bản nháp để bạn xem và tự đăng nếu phù hợp",output)

    def test_semantic_judge_cannot_override_safety_prohibitions(self):
        promo=("Muốn xử lý bảng tính công việc nhanh thì theo dõi kênh và "
               "bấm link bio ngay để nhận ưu đãi bạn nhé, rất dễ làm luôn.")
        self.assertFalse(can_send(promo,TEXT,target=parse_threads_url(URL),
                                  semantic_override=True))

    def test_semantic_judge_can_reject_unrelated_draft_without_posting(self):
        irrelevant=("Ngày nào cũng nên mỉm cười, uống cà phê và tận hưởng "
                    "một bầu không khí tích cực để mọi thứ nhẹ nhàng hơn.")
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        db,read,publish=MagicMock(),MagicMock(),MagicMock()
        judge=MagicMock(return_value=False)
        result=process(e,db=db,read=read,publish=publish,
            credentials=MagicMock(),semantic_judge=judge,
            create=lambda *a,**kw:{"should_reply":True,
                                  "post_text":irrelevant,
                                  "content_angle":"Sự lạc đề"})
        self.assertEqual(result["state"],"ai_reply_not_contextual_enough")
        self.assertGreaterEqual(judge.call_count,1)
        read.assert_not_called()
        publish.assert_not_called()
        db.request.assert_not_called()

    def test_self_healing_three_options_finds_safe_relevant_reply(self):
        irrelevant=("Mỗi ngày hãy thật vui và cố gắng giữ tinh thần "
                    "lạc quan để cuộc sống thêm tốt đẹp hơn nhé.")
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        source=MagicMock(return_value={"should_reply":True,
            "post_text":irrelevant,"content_angle":"Tư duy tích cực"})
        three=MagicMock(return_value=[
            {"post_text":irrelevant,"content_angle":"Khởi đầu"},
            {"post_text":ANSWER,"content_angle":"Thống nhất bảng theo dõi"},
            {"post_text":irrelevant,"content_angle":"Khác"},
        ])
        db,read,publish,credentials=MagicMock(),MagicMock(),MagicMock(),MagicMock()
        result=process(e,db=db,create=source,option_generator=three,
                       semantic_judge=lambda a,b:b==ANSWER,
                       read=read,publish=publish,credentials=credentials)
        self.assertEqual(result["state"],"draft_prepared_only")
        self.assertEqual(result["draft"],ANSWER)
        self.assertEqual(source.call_count,2)
        three.assert_called_once()
        db.request.assert_not_called()
        read.assert_not_called()
        publish.assert_not_called()
        credentials.assert_not_called()

    def test_three_bad_drafts_never_trigger_threads_publish(self):
        unrelated=("Ngày nào cũng nên uống cà phê và mỉm cười trước "
                   "mọi thử thách của cuộc sống để vui hơn.")
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        candidates=MagicMock(return_value=[
            {"post_text":unrelated,"content_angle":"Không liên quan"}]*3)
        publish=MagicMock()
        db=MagicMock()
        result=process(e,db=db,option_generator=candidates,
            create=lambda *a,**kw:{"should_reply":True,
                  "post_text":unrelated,"content_angle":"Thử"},
            read=MagicMock(),publish=publish,credentials=MagicMock())
        self.assertEqual(result["state"],"ai_reply_not_contextual_enough")
        candidates.assert_called_once()
        publish.assert_not_called()
        db.request.assert_not_called()

    def test_rejects_patchwork_quotes_and_unjustified_future_predictions(self):
        original=("Team mình mới có bé Gen Z vào làm. Hôm nay thấy ẻm "
                  "bắt đầu mang đồ để decor bàn làm việc rồi. "
                  "Này là dấu hiệu ẻm sẽ gắn bó lâu dài với cty "
                  "đúng không mọi người? Chắc ẻm sẽ không nghỉ việc sớm đâu nhỉ?")
        model_bad=("Bè Gen Z đang làm đồ decor bàn làm việc thật đáng yêu! "
                   "Có vẻ như anh ấy sẽ gắn bó lâu dài rồi, "
                   "không phải nghỉ việc sớm đâu. 😄")
        better=("Decor bàn làm việc là cắm cờ nhận chỗ trước thôi. "
                "Gắn bó với công ty còn phải xem nhiều thứ.")
        self.assertFalse(can_send(model_bad,original,target=parse_threads_url(URL)))
        self.assertTrue(can_send(better,original,target=parse_threads_url(URL)))

    def test_bad_json_recovers_through_approved_three_option_generator(self):
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        options=MagicMock(return_value=[
          {"post_text":ANSWER,"content_angle":"Quản lý bảng chung"},
          {"post_text":"Nội dung không đủ dài","content_angle":"Không đạt"},
          {"post_text":ANSWER,"content_angle":"Lựa chọn dự phòng"},
        ])
        db,read,publish=MagicMock(),MagicMock(),MagicMock()
        result=process(e,db=db,
          create=MagicMock(side_effect=ValueError("truncated response")),
          option_generator=options,
          semantic_judge=lambda source,candidate:True,
          read=read,publish=publish,credentials=MagicMock())
        self.assertEqual(result["state"],"draft_prepared_only")
        self.assertEqual(result["draft"],ANSWER)
        options.assert_called_once()
        read.assert_not_called()
        publish.assert_not_called()
        db.request.assert_not_called()

    def test_generated_comment_cannot_invent_theft_risk(self):
        source=("Team mình mới có bé Gen Z vào làm. Hôm nay thấy ẻm "
                "mang đồ để decor bàn làm việc rồi. Có phải dấu hiệu "
                "bạn ấy muốn gắn bó lâu dài với công ty không?")
        invented=("Nhìn bé Gen Z decor bàn làm việc, sếp phải mua thêm "
                  "tủ đựng đồ để tránh trộm chỗ làm. Có lẽ đây là "
                  "một tín hiệu gắn bó lâu dài với công ty đó.")
        self.assertFalse(can_send(invented,source,target=parse_threads_url(URL)))

    def test_selected_future_tenure_question_rejects_certain_prediction(self):
        post=("Mới có bạn Gen Z vào công ty, đã đem đồ để decor bàn "
              "làm việc. Liệu đó có nghĩa bạn sẽ gắn bó lâu dài "
              "hay nghỉ việc sớm không nhỉ?")
        bad=("Bạn Gen Z đã mang đồ decor bàn làm việc nên chắc chắn "
             "sẽ không muốn rời đi đâu. Rõ là có nhiều ý tưởng "
             "sáng tạo, ở lại công ty lâu thôi!")
        self.assertFalse(can_send(bad,post,target=parse_threads_url(URL)))

    def test_short_natural_comment_allowed_without_extra_padding(self):
        original=("Có bạn mới vào công ty đã decor bàn làm việc rất nhanh. "
                  "Mọi người đoán bạn ấy gắn bó với công ty lâu không?")
        good=("Decor bàn làm việc là gắn bó với cái bàn trước thôi. "
              "Còn công ty thì phải xem đã 😄")
        self.assertTrue(can_send(good,original,target=parse_threads_url(URL)))
        self.assertLessEqual(len(good),140)

    def test_long_winded_or_cringe_comment_rejected(self):
        original=("Có bạn mới vào công ty đã decor bàn làm việc rất nhanh. "
                  "Mọi người đoán bạn ấy gắn bó với công ty lâu không?")
        long_reply=("Decor bàn làm việc từ lúc mới vào công ty thật sự là "
                    "một câu chuyện truyền cảm hứng cho tất cả mọi người. "
                    "Đôi khi cuộc sống chỉ cần một góc nhỏ ấm áp để "
                    "chúng ta thấy sự trân trọng và nguồn năng lượng tích cực.")
        cringe=("Bắt đầu decor bàn làm việc thật là một khoảnh khắc "
                "đáng yêu, ai cũng nên lan tỏa năng lượng tích cực mỗi ngày!")
        self.assertFalse(can_send(long_reply,original,target=parse_threads_url(URL)))
        self.assertFalse(can_send(cringe,original,target=parse_threads_url(URL)))

    def test_bland_gen_z_recap_rejected_even_when_short(self):
        original=("Team mình mới có bé Gen Z vào làm, bắt đầu mang đồ "
                  "để decor bàn làm việc. Liệu bạn ấy có gắn bó "
                  "lâu dài với công ty không nhỉ?")
        bland=("Gen Z vừa đến, bàn làm việc đã sẵn sàng decor, "
               "có vẻ họ đang tìm cảm hứng mới rồi!")
        self.assertFalse(can_send(bland,original,target=parse_threads_url(URL)))

    def test_generic_hr_style_signal_comment_rejected(self):
        original=("Bé Gen Z mới vào công ty đã mang đồ decor bàn làm việc. "
                  "Mọi người đoán bạn này sẽ làm lâu không?")
        bland=("Món đồ mới để bàn làm việc là tín hiệu nhiệt huyết, "
               "hy vọng sẽ ở lâu cùng công ty nhé.")
        self.assertFalse(can_send(bland,original,target=parse_threads_url(URL)))

    def test_independent_judge_can_veto_grounded_draft(self):
        e=issue()
        e["comment"]={"body":"/enna draft","user":{"login":"roxthang0710-hash"}}
        judge=MagicMock(return_value=False)
        result=process(e,db=MagicMock(),
                       create=lambda *args,**kw:{"should_reply":True,
                           "post_text":ANSWER,"content_angle":"Example"},
                       semantic_judge=judge,option_generator=lambda *args,**kw:[])
        self.assertEqual(result["state"],"ai_reply_not_contextual_enough")
        self.assertGreaterEqual(judge.call_count,1)

    def test_threads_ui_noise_removed_without_losing_actual_joke(self):
        raw=("sample_writer\n14 giờ✳ Gửi Enna\n"
             "Mình phỏng vấn ứng viên F&B làm thêm, em ấy hỏi về "
             "ưu đãi đồ ăn trước tiên.\n"
             "Hỏi lý do em chuyển nơi làm thì em bảo vì đã dùng "
             "hết mã giảm giá để ăn ở chỗ cũ.\n"
             "=))))\n1\n/\n2\n3,4K\nHàng đầu\n"
             "Xem hoạt động\nTrả lời sample_writer...")
        cleaned=clean_selected_excerpt(raw,author="sample_writer")
        self.assertIn("hết mã giảm giá để ăn",cleaned)
        self.assertNotIn("Hàng đầu",cleaned)
        self.assertNotIn("Trả lời sample_writer",cleaned)
        self.assertNotIn("✳ Gửi Enna",cleaned)
        self.assertNotIn("sample_writer",cleaned)

    def test_source_context_includes_final_punchline_not_only_setup(self):
        from growth.companion_editor import important_source_clauses
        post=("T làm F&B. Hôm qua phỏng vấn một em làm part-time.\n"
              "Em hỏi có ăn giảm giá không?\n"
              "T hỏi sao đã nói chuyện lương chưa mà hỏi đồ ăn.\n"
              "Em nói đang làm bên pizza.\n"
              "Rồi em kể là hết mã giảm giá để ăn ở nơi cũ "
              "nên mới ứng tuyển qua đây.\n=))))")
        focus=important_source_clauses(post)
        self.assertIn("hết mã giảm giá",focus[-1])
        self.assertLessEqual(len(focus),5)

    def test_original_discount_story_can_be_replied_to_without_ads(self):
        """Issue 49: the source itself is about running out of discount codes."""
        original=("Phỏng vấn sinh viên làm thêm ở F&B. Em nói muốn chuyển "
                  "chỗ làm vì đã dùng hết mã giảm giá để ăn ở tiệm pizza, "
                  "nên giờ đang ứng tuyển qua bên mình.")
        good=("Hết mã giảm giá là em cập nhật CV luôn, đúng là lịch "
              "nhảy việc chạy theo voucher rồi =)))")
        unrelated=("Sinh viên cần chăm chỉ và cố gắng làm việc "
                   "để bù lại chi phí ăn uống trong cuộc sống.")
        self.assertTrue(can_send(good,original,target=parse_threads_url(URL)))
        self.assertFalse(can_send(unrelated,original,target=parse_threads_url(URL)))
        self.assertFalse(can_send("Mua ngay giảm giá siêu sốc ở link bio nhé!",original,
                                  target=parse_threads_url(URL)))

    def test_live_issue_49_false_recovery_rejected(self):
        original=("Em định nghỉ bên pizza vì đã dùng hết mã giảm giá "
                  "để ăn rồi, nên em qua bên mình ứng tuyển làm thêm.")
        bad=("Thì ra mã giảm giá còn là điểm cộng khi tuyển dụng, "
             "em chắc đang tính toán lợi nhuận ăn uống rồi đấy!")
        self.assertFalse(can_send(bad,original,target=parse_threads_url(URL)))
        good=("Hết mã giảm giá là em cập nhật CV luôn, "
              "lịch nhảy việc chạy theo voucher mất rồi =)))")
        self.assertTrue(can_send(good,original,target=parse_threads_url(URL)))

    def test_issue_49_shift_change_is_not_job_change_punchline(self):
        original=("Em định nghỉ bên pizza vì dùng hết mã giảm giá "
                  "để ăn nên giờ chuyển chỗ làm mới.")
        fake=("Nếu em dùng hết mã giảm giá, lần tới có kế hoạch "
              "đổi ca làm để được nhận thêm ưu đãi không?")
        self.assertFalse(can_send(fake,original,target=parse_threads_url(URL)))

    def test_generic_promotional_comment_rejected(self):
        self.assertFalse(can_send("Theo dõi kênh và mua ngay!",TEXT,target=parse_threads_url(URL)))

    def test_generic_story_paraphrase_rejected(self):
        summary=("Chú ở chung nhà, rồi chú múc tô cháo để trước cửa,"
                 " mở YouTube xem lại. Thật là một khoảnh khắc đời thường ngọt ngào!")
        self.assertFalse(can_send(summary,TEXT,target=parse_threads_url(URL)))


if __name__=="__main__":
    unittest.main()
