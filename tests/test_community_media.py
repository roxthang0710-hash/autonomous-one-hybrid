"""Safety tests: no fabricated high-engagement replies or copied meme media."""
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock,patch

from growth.community_care import eligible_question,validate_answer
from growth.media_scout import inspect_commons,allowed_source_url,run
from growth.meme_renderer import make_card
from threads.publisher import do_publish

NOW=datetime(2026,11,6,10,tzinfo=timezone.utc)


def comment(text="Dùng bảng tính trong công việc như thế nào cho gọn ạ?"):
    return {"id":"123456789012345","username":"nguoi_xem_that",
            "timestamp":(NOW-timedelta(hours=2)).isoformat(),"text":text,
            "is_reply_owned_by_me":False,"has_replies":False}


class CommunityTests(unittest.TestCase):
    def test_only_real_recent_questions(self):
        self.assertTrue(eligible_question(comment(),now=NOW))
        self.assertFalse(eligible_question(comment("Cảm ơn Enna, bài hay quá nè"),now=NOW))
        self.assertFalse(eligible_question({**comment(),"username":"dohay_dilam"},now=NOW))
        self.assertFalse(eligible_question({**comment(),"has_replies":True},now=NOW))
        self.assertFalse(eligible_question({**comment(),"timestamp":
            (NOW-timedelta(days=5)).isoformat()},now=NOW))

    def test_private_or_spam_questions_do_not_trigger(self):
        self.assertFalse(eligible_question(comment(
            "Mình có nên đưa mật khẩu công ty vào chatbot không?"),now=NOW))
        self.assertFalse(eligible_question(comment(
            "Mình dùng cách nào? https://spam.example"),now=NOW))

    def test_answer_must_be_original_and_contextual(self):
        q="Dùng Google Sheets cho báo cáo hàng tuần sao cho gọn?"
        parent="Mẹo dùng bộ lọc riêng trong Google Sheets khi làm báo cáo"
        good="Với báo cáo tuần, thử tạo chế độ xem bộ lọc riêng để mỗi người lọc phần mình phụ trách mà không ảnh hưởng cả nhóm nhé."
        self.assertTrue(validate_answer(good,q,parent))
        self.assertFalse(validate_answer("Bạn ơi, theo dõi kênh ngay nhé! "+good,q,parent))
        self.assertFalse(validate_answer("Bài này hay quá, cảm ơn bạn nhiều",q,parent))
        # The context is Vietnamese multi-word terms: "báo cáo", "bộ lọc".
        # Do not demand two >=5-character single words and block real answers.
        self.assertTrue(validate_answer(
            "Bộ lọc riêng cho báo cáo tuần giúp mọi người không sửa mất "
            "chế độ xem của nhau, thử dùng kiểu này nhé.", q, parent))
        self.assertFalse(validate_answer(
            "Ngày hôm nay thật là một cơ hội tuyệt vời để ai cũng "
            "trở thành phiên bản tốt hơn của chính mình.", q, parent))


class MediaTests(unittest.TestCase):
    def test_original_meme_has_real_png(self):
        data=make_card("Đồng hồ ở công ty có hai múi giờ.",
                       "Bình thường và còn 5 phút nữa tới hạn.")
        self.assertTrue(data.startswith(bytes([137,80,78,71,13,10,26,10])))
        self.assertLess(len(data),5*1024*1024)

    def test_third_party_is_never_auto_publishable(self):
        entry={"query":{"pages":{"12":{
            "title":"File:Keyboard and paper notebook.jpg",
            "imageinfo":[{"mime":"image/jpeg",
                "extmetadata":{"LicenseShortName":{"value":"CC0 1.0"}}}]},
            "13":{"title":"File:Unlicensed office.jpg",
            "imageinfo":[{"mime":"image/jpeg",
                "extmetadata":{"LicenseShortName":{"value":"All rights reserved"}}}]}}}}
        found=inspect_commons(entry,"office desk")
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["status"],"needs_review")
        self.assertEqual(found[0]["rights_status"],"review_required")
        self.assertTrue(allowed_source_url(found[0]["source_url"],"wikimedia_commons"))
        self.assertFalse(allowed_source_url("https://evil.tld/steal","pexels"))

    @patch("growth.media_scout.commons_candidates",return_value=[])
    @patch("growth.meme_ideas.generate",return_value=None)
    def test_idea_worker_does_not_publish_when_upload_off(self,_,__):
        db=MagicMock()
        db.request.side_effect=[[],[],[],[{"id":"first"}],[{"id":"second"}]]
        with patch.dict("os.environ",{"PEXELS_API_KEY":""}):
            result=run(db,now=NOW,enable_public_assets=False)
        self.assertEqual(result["original_concepts_new"],1)
        self.assertEqual(result["video_storyboards_new"],1)
        self.assertEqual([c.args[1] for c in db.request.call_args_list],
                         ["/enna_media_ideas","/threads_posts","/threads_metrics",
                          "/enna_media_ideas","/enna_media_ideas"])
        self.assertEqual(db.request.call_args_list[3].kwargs["payload"]["status"],"research")

    @patch("threads.publisher.thread_request")
    def test_media_publish_requires_verified_own_storage_url(self,request):
        text="Mỗi lần nhận một tệp mới, mình vẫn nên thống nhất cách đặt tên cho cả nhóm trước khi bảo là bản cuối."
        with self.assertRaises(ValueError):
            do_publish("test",text,image_url="https://evil.example/x.png",alt_text="Meme chuẩn")
        self.assertFalse(request.called)

    @patch("threads.publisher.thread_request")
    def test_original_image_uses_meta_two_step(self,request):
        request.side_effect=[{"id":"container123"},{"id":"post123"},{"id":"post123","permalink":"https://www.threads.com/@dohay_dilam/post/demo"}]
        url=("https://gjdvdohylvsauphhkutw.supabase.co/storage/v1/object/"
             "public/enna-original-media/meme/original-deadline_calendar.png")
        text="Hôm nay vừa nhận một deadline mới, mình thử chốt hạn cụ thể và việc quan trọng nhất trước để khỏi vỡ trận."
        result=do_publish("test",text,image_url=url,alt_text="Meme gốc về deadline công sở")
        self.assertEqual(result[1],"post123")
        self.assertEqual(request.call_args_list[0].kwargs["data"]["media_type"],"IMAGE")
        self.assertEqual(request.call_args_list[0].kwargs["data"]["image_url"],url)


if __name__=="__main__":
    unittest.main()
