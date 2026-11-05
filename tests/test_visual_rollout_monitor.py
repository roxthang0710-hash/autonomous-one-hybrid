import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import Mock
from growth.visual_rollout_monitor import inspect,run
NOW=datetime(2026,11,7,10,tzinfo=timezone.utc)

def item(when,status="PENDING",name="photo_meme"):
 return {"scheduled_at":when.isoformat(),"provider_status":status,
   "platform":"facebook","metricool_uuid":"abc123","format_key":name,
   "media_keys":["source1"],"media_count":1,
   "verified_publication_id":None,"published_at":None}

class VisualTests(unittest.TestCase):
 def test_scheduled_is_not_published(self):
  x=inspect([item(NOW+timedelta(hours=2))],now=NOW)
  self.assertEqual(x[0]["outcome"],"pending_scheduled_only")
 def test_overdue_still_unverified(self):
  x=inspect([item(NOW-timedelta(hours=2))],now=NOW)
  self.assertEqual(x[0]["outcome"],"due_not_verified")
 def test_posted_requires_evidence(self):
  self.assertEqual(inspect([item(NOW,"POSTED")],now=NOW)[0]["outcome"],"not_verified")
  x=item(NOW,"POSTED")
  x["verified_publication_id"]="authoritative-meta-id"
  x["published_at"]=(NOW-timedelta(hours=1)).isoformat()
  self.assertEqual(inspect([x],now=NOW)[0]["outcome"],"verified_published")
 def test_no_external_post_or_false_success(self):
  db=Mock()
  db.request.side_effect=[[item(NOW+timedelta(hours=2))]]
  r=run(db,now=NOW)
  self.assertEqual(r["verified_published"],0)
  self.assertTrue(r["no_external_social_actions"])
  self.assertEqual(db.request.call_count,1)
  self.assertEqual(db.request.call_args.args[0],"GET")
if __name__=="__main__":unittest.main()
