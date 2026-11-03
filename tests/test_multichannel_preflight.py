import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from growth.multichannel_preflight import check,run

NOW=datetime(2026,11,3,7,35,tzinfo=timezone.utc)

def entry(provider,offset=0,**kwargs):
    local_dt=NOW+timedelta(days=offset,hours=3)
    base={
        "provider":provider,"scheduled_at":local_dt.isoformat(),
        "provider_status":"PENDING","auto_publish":True,
        "has_media":provider=="instagram",
        "checked_at":NOW.isoformat(),
    }
    return {**base,**kwargs}

class AdvancePlanningTests(unittest.TestCase):
    def test_full_buffer_is_ready(self):
        rows=[entry(provider,d) for d in range(3)
              for provider in ("facebook","instagram")]
        statuses=check(rows,now=NOW)
        self.assertEqual(len(statuses),6)
        self.assertTrue(all(t[-1]=="preflight_ready" for t in statuses))
    def test_missing_media_and_missing_slot_are_not_marked_ready(self):
        rows=[entry("instagram",has_media=False),entry("facebook")]
        outcomes=check(rows,now=NOW)
        self.assertIn(("2026-11-03","instagram","failed","preflight_missing_media"),outcomes)
        self.assertIn(("2026-11-04","facebook","pending","preflight_missing_slot"),outcomes)
    def test_stale_provider_confirmation_must_not_claim_publication(self):
        rows=[entry("facebook",checked_at=(NOW-timedelta(days=2)).isoformat()),
              entry("instagram")]
        outcomes=check(rows,now=NOW,ahead_days=1)
        self.assertIn(("2026-11-03","facebook","pending","preflight_snapshot_stale"),outcomes)
    def test_due_pending_remains_unverified(self):
        rows=[entry("facebook",scheduled_at=(NOW-timedelta(hours=1)).isoformat()),
              entry("instagram")]
        outcomes=check(rows,now=NOW,ahead_days=1)
        self.assertIn(("2026-11-03","facebook","uncertain","preflight_due_unverified"),outcomes)
    def test_idempotent_deduplicated_redacted_record(self):
        db=MagicMock()
        db.request.side_effect=[
          [entry("facebook"),entry("instagram")],[],[],[],[],[],[]
        ]
        result=run(db,now=NOW)
        self.assertEqual(result["checked"],6)
        written=[c.kwargs["payload"] for c in db.request.call_args_list
                 if c.args[0]=="POST"]
        self.assertEqual(len(written),6)
        self.assertTrue(all("text" not in p and "media" not in p for p in written))
        self.assertEqual(len({p["dedup_key"] for p in written}),6)

if __name__=="__main__": unittest.main()
