"""Scheduled Meta posts must begin AFTER Metricool's 15 pre-booked days."""
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from threads.content import seed_calendar, VN

class SeedCalendarHandoffTests(unittest.TestCase):
    def test_seed_calendar_starts_after_last_metricool_day(self):
        db=MagicMock()
        calls=[]
        def req(method,path,*,params=None,payload=None,prefer=None):
            calls.append((method,path,params,payload))
            if method=="GET" and params.get("status")=="eq.scheduled_external":
                return [{"scheduled_at":"2026-11-17T02:30:00+00:00"}]
            if method=="POST":
                return payload
            return []
        db.request.side_effect=req
        with patch("threads.content.get_channel", return_value={"id":"brand"}), \
             patch("threads.content.scheduled_start",return_value=datetime(2026,11,3,9,30,tzinfo=VN)):
            count=seed_calendar(db)
        self.assertEqual(count,14)
        posts=[x[3] for x in calls if x[0]=="POST"][0]
        self.assertEqual(posts[0]["scheduled_at"],"2026-11-18T09:30:00+07:00")
        self.assertEqual(posts[-1]["scheduled_at"],"2026-12-01T09:30:00+07:00")
        self.assertTrue(all(p["status"]=="queued" for p in posts))

    def test_seed_without_external_schedule_starts_next_day(self):
        db=MagicMock()
        db.request.side_effect=[[],[]]
        with patch("threads.content.get_channel",return_value={"id":"brand"}), \
             patch("threads.content.scheduled_start",return_value=datetime(2026,11,3,9,30,tzinfo=VN)), \
             patch("threads.content.planned_seed_rows",return_value=[]) as seed:
            self.assertEqual(seed_calendar(db),0)
        self.assertEqual(seed.call_args.kwargs["start"],
                         datetime(2026,11,3,9,30,tzinfo=VN))

if __name__=="__main__":
    unittest.main()
