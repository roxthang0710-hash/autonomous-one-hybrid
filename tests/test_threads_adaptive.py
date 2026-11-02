import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from threads.adaptive import eligibility, qualify, plan

NOW = datetime(2026,11,3,8,5,tzinfo=timezone.utc)  # 15:05 Vietnam
CH = {"id":"c1","status":"connected","authorized":True,"auto_publish_enabled":True}
TEXT = ("17:29, Linh thực tập sinh được sếp giao một bản báo cáo trước giờ tan làm. "
        "Linh hỏi: “Nếu việc này gấp, mình dời bản báo cáo sáng mai được không?” "
        "Sếp đã xem nhưng chưa trả lời. Hỏi lại để sắp xếp việc liệu có bị xem là thiếu chủ động?")
REASON = "Một câu chuyện công sở rõ tình huống, tạo ra hai góc nhìn mà không bêu xấu cá nhân thật."
POSTS = [
    {"id":"a","status":"scheduled_external","created_by":"seed",
     "scheduled_at":"2026-11-03T02:30:00+00:00","published_at":None},
    {"id":"b","status":"scheduled_external","created_by":"seed",
     "scheduled_at":"2026-11-03T05:20:00+00:00","published_at":None},
    {"id":"c","status":"scheduled_external","created_by":"seed",
     "scheduled_at":"2026-11-03T10:40:00+00:00","published_at":None},
    {"id":"d","status":"scheduled_external","created_by":"seed",
     "scheduled_at":"2026-11-03T14:30:00+00:00","published_at":None},
]

class AdaptiveTests(unittest.TestCase):
    def test_gap_uses_actual_bookings_not_fixed_post_quota(self):
        self.assertEqual(eligibility(POSTS,[],now=NOW)[0],"eligible")
        self.assertEqual(eligibility(POSTS,[],now=datetime(2026,11,3,5,35,tzinfo=timezone.utc))[0],
                         "near_another_post")
        self.assertEqual(eligibility(POSTS,[],now=datetime(2026,11,3,17,0,tzinfo=timezone.utc))[0],
                         "quiet_hours")
    def test_day_ceiling_is_safety_not_target(self):
        self.assertEqual(eligibility(POSTS+[dict(POSTS[0],id="e")],[],now=NOW)[0],
                         "day_safety_ceiling")
    def test_quality_and_duplicate_filter(self):
        self.assertGreaterEqual(qualify(TEXT,REASON)[0],80)
        self.assertEqual(qualify(TEXT,REASON,[TEXT])[1],"too_similar_to_previous")
        self.assertEqual(qualify("Bạn nghĩ sao?",REASON)[0],0)
        self.assertEqual(qualify(TEXT+" Follow để biết thêm",REASON)[0],0)
    def test_no_data_allows_at_most_one_experiment(self):
        with_one=POSTS+[{"id":"e","status":"posted","created_by":"agent",
                         "scheduled_at":"2026-11-03T08:05:00+00:00",
                         "published_at":None}]
        self.assertEqual(eligibility(with_one,[],now=NOW)[0],"experimental_extra_limit")
    def test_bad_metrics_pause_not_fake_success(self):
        m=[{"post_id":str(i),"views":100,"likes":0,"replies":0} for i in range(3)]
        self.assertEqual(eligibility(POSTS,m,now=NOW)[0],"pause_until_real_engagement")
    def test_worker_creates_only_one_valid_queue_row(self):
        db=MagicMock()
        db.request.side_effect=[POSTS,[],[{"text_content":"Mẹo công sở: chọn 3 việc trước khi bắt đầu."}],POSTS,[{"id":"new"}]]
        generated={"post_text":TEXT,"pillar":"work","why_useful":REASON}
        with patch("threads.adaptive.get_channel",return_value=CH):
            result=plan(db,now=NOW,enabled=True,generator=lambda *a:generated)
        self.assertEqual(result,"adaptive_queued")
        post=db.request.call_args.kwargs["payload"]
        self.assertEqual(post["created_by"],"agent")
        self.assertEqual(post["status"],"queued")
        self.assertEqual(post["scheduled_at"],NOW.isoformat())
        self.assertEqual(db.request.call_count,5)
    def test_account_gate_precedes_generation(self):
        db=MagicMock()
        with patch("threads.adaptive.get_channel",return_value={**CH,"authorized":False}):
            result=plan(db,now=NOW,enabled=True,generator=lambda *a:None)
        self.assertEqual(result,"account_not_authorized")
        db.request.assert_not_called()

if __name__=="__main__": unittest.main()
