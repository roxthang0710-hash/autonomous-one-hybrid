"""Evidence-only proactive alert regressions."""
import unittest
from datetime import datetime, timezone
from growth.enna_desk_monitor import build_notifications

NOW=datetime(2026,11,5,3,tzinfo=timezone.utc)
OWNERS=[{"user_id":"test-owner"}]

class DeskMonitorTests(unittest.TestCase):
    def test_missing_metric_is_not_zero_followers(self):
        rows=build_notifications(OWNERS,[],[],[],[],now=NOW)
        self.assertTrue(any("chưa nhận được số" in x["title"] for x in rows))
        self.assertFalse(any("còn thiếu 1000" in x["details"] for x in rows))
    def test_stale_and_gap(self):
        rows=build_notifications(OWNERS,[{"measured_on":"2026-11-02","followers":3}],[],[],[],now=NOW)
        self.assertTrue(any("quá hạn" in x["title"] for x in rows))
        self.assertTrue(any("997 follower" in x["details"] for x in rows))
    def test_planned_topic_not_claimed_published(self):
        rows=build_notifications(OWNERS,[],
          [{"status":"queued","topic_tag_planned":"Công sở","topic_tag_requested":None}],[],[],now=NOW)
        self.assertTrue(any(x["category"]=="topic" for x in rows))
    def test_published_topic_removes_unconfirmed_warning(self):
        rows=build_notifications(OWNERS,[],
          [{"status":"queued","topic_tag_planned":"Công sở"},
           {"status":"posted","topic_tag_requested":"Công sở"}],[],[],now=NOW)
        self.assertFalse(any(x["category"]=="topic" for x in rows))
    def test_video_ready_requires_real_url(self):
        rows=build_notifications(OWNERS,[],[],
          [{"media_type":"original_video","status":"ready","source_url":None}],[],now=NOW)
        self.assertTrue(any(x["category"]=="media" for x in rows))
    def test_uploaded_photo_drafts_trigger_review_alert_not_published_claim(self):
        asset={"media_type":"licensed_photo","status":"needs_review",
               "source_url":"https://gjdvdohylvsauphhkutw.supabase.co/storage/v1/object/public/enna-original-media/visual-review/aa/example.png"}
        result=build_notifications(OWNERS,[],[],[asset],[],now=NOW)
        self.assertTrue(any(x["title"]=="Enna có ảnh thật mới chờ duyệt" for x in result))
        self.assertFalse(any("đã đăng thành công" in x["details"].lower() for x in result))
        # Unreviewed external images are never treated as Enna's own finished drafts.
        asset["source_url"]="https://malicious.example/photo.png"
        result=build_notifications(OWNERS,[],[],[asset],[],now=NOW)
        self.assertFalse(any(x["title"]=="Enna có ảnh thật mới chờ duyệt" for x in result))

    def test_recent_error_emits_system_alert(self):
        rows=build_notifications(OWNERS,[],[],[],[
          {"status":"failed","code":"ops_failed","occurred_at":"2026-11-05T02:00:00Z"}],now=NOW)
        self.assertTrue(any(x["category"]=="system" for x in rows))
    def test_no_alert_data_claims_posted(self):
        rows=build_notifications(OWNERS,[{"measured_on":"2026-11-05","followers":1000}],
          [{"status":"posted","topic_tag_requested":"Công sở"}],
          [{"media_type":"original_video","status":"ready","source_url":"https://example.org/own.mp4"}],[],
          now=NOW)
        self.assertEqual(rows,[])

if __name__=="__main__":
    unittest.main()
