"""Profile audits cannot edit Threads, and must not invent bio from local metadata."""
import unittest
from datetime import datetime,timezone
from unittest.mock import MagicMock
from growth.profile_conversion import profile_gap, audit, BIO

NOW=datetime(2026,11,5,2,tzinfo=timezone.utc)
class ProfileAuditTests(unittest.TestCase):
    def test_real_value_proposition(self):
        self.assertEqual(profile_gap(BIO),"healthy_copy")
        self.assertEqual(profile_gap("Góc mẹo nhỏ cho người đi làm và những chuyến công tác gọn nhẹ."),"needs_value_proposition")
        self.assertEqual(profile_gap(None),"unverifiable")
    def test_no_oauth_does_not_access_meta(self):
        db=MagicMock()
        db.request.side_effect=lambda method,path,**kw: [] if path=="/enna_desk_owners" else None
        read=MagicMock()
        result=audit(db,now=NOW,credentials=lambda db,refresh:None,read=read)
        self.assertEqual(result["status"],"needs_official_oauth")
        read.assert_not_called()
    def test_verified_profile_creates_only_owner_notice(self):
        db=MagicMock()
        def source(method,path,**kwargs):
            if path=="/enna_desk_owners":return [{"user_id":"owner-id"}]
            if path=="/enna_desk_notifications":
                self.assertEqual(method,"POST")
                self.assertIn("suggested_action",kwargs["payload"][0])
                self.assertEqual(kwargs["payload"][0]["category"],"growth")
                return [{"id":1}]
            raise AssertionError("No unexpected database writes")
        db.request.side_effect=source
        def read(method,path,token,params=None):
            self.assertEqual(method,"GET")
            if params["fields"]=="id,username":return {"id":"123","username":"dohay_dilam"}
            if params["fields"]=="id,username,threads_biography":
                return {"id":"123","username":"dohay_dilam","threads_biography":"Mẹo nhỏ văn phòng để bớt cực"}
            raise AssertionError("No Meta write or unexpected scope")
        out=audit(db,now=NOW,read=read,credentials=lambda db,refresh:("testtoken","dohay_dilam"))
        self.assertEqual(out["status"],"needs_value_proposition")
        self.assertTrue(out["owner_action_required"])
        self.assertFalse(out["status"]=="healthy_copy")
    def test_meta_bio_field_missing_never_claims_ready(self):
        db=MagicMock()
        db.request.return_value=[]
        def read(method,path,token,params=None):
            return {"id":"123","username":"dohay_dilam"}
        out=audit(db,now=NOW,read=read,credentials=lambda db,refresh:("token","dohay_dilam"))
        self.assertEqual(out["status"],"unverifiable")
        self.assertFalse(out["bio_verified"])

if __name__=="__main__":unittest.main()
