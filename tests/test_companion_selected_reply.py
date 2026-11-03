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
        grounded=("Giờ nghỉ trưa mà bàn phím vẫn cạch cạch rồi còn kéo "
                  "ghế liên tục thì đúng là khó ngủ nổi. Mong mọi người "
                  "tôn trọng giờ nghỉ của nhau chút.")
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
        novel=("Nghỉ trưa mà bàn phím cứ cạch cạch rồi còn đập chuột "
               "liên tục thì đúng là mất cả giờ yên tĩnh. Đã nhắc rồi "
               "mà không thay đổi mới khiến người ta mệt.")
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
        useful=("Nghỉ trưa mà bàn phím cứ cạch cạch rồi còn đập chuột "
                "thì đúng là một ca thử thách sự bình tĩnh. "
                "Đã nhắc rồi mà vẫn ồn mới mệt.")
        self.assertTrue(can_send(useful,src,target=parse_threads_url(URL)))

    def test_gen_z_decor_post_can_get_grounded_playful_reply(self):
        post=("Team mình mới có bé Gen Z vào làm. Hôm nay thấy ẻm "
              "bắt đầu mang đồ để decor bàn làm việc rồi. "
              "Này là dấu hiệu ẻm sẽ gắn bó lâu dài với công ty "
              "đúng không mọi người? Chắc ẻm không nghỉ việc sớm đâu nhỉ?")
        reply=("Mới vào đã mang đồ decor bàn làm việc thì ít nhất "
               "ẻm đang có kế hoạch gắn bó với chiếc bàn trước đã 😂 "
               "Còn có ở lâu với công ty hay không chắc phải chờ "
               "qua vài đợt deadline mới biết.")
        self.assertTrue(can_send(reply,post,target=parse_threads_url(URL)))

    def test_semantic_judge_allows_grounded_paraphrase_only_in_draft_test(self):
        text=("Thử thống nhất cách ghi tình trạng của từng nhiệm vụ, có tên "
              "người phụ trách và mốc chốt cụ thể. Nhìn danh sách là thấy "
              "việc nào còn vướng, khỏi phải đoán ý nhau.")
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
                       semantic_judge=lambda a,b:False,
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
        better=("Mang đồ decor bàn làm việc là đặt cọc tinh thần với "
                "chiếc bàn thôi 😂 Còn gắn bó lâu dài hay không "
                "chắc phải xem đồng nghiệp và văn hóa công ty nữa.")
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

    def test_generic_promotional_comment_rejected(self):
        self.assertFalse(can_send("Theo dõi kênh và mua ngay!",TEXT,target=parse_threads_url(URL)))

    def test_generic_story_paraphrase_rejected(self):
        summary=("Chú ở chung nhà, rồi chú múc tô cháo để trước cửa,"
                 " mở YouTube xem lại. Thật là một khoảnh khắc đời thường ngọt ngào!")
        self.assertFalse(can_send(summary,TEXT,target=parse_threads_url(URL)))


if __name__=="__main__":
    unittest.main()
