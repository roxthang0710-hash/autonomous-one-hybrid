"""A1 autonomy controller: deterministic incidents, one safe action, live proof."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from growth.autonomy_controller import (
    fresh_official_snapshot, inspect_provider, run,
)

NOW = datetime(2026, 11, 6, 12, 15, tzinfo=timezone.utc)


def follower(at=NOW, count=25, source="meta_official"):
    return {"source":source, "followers":count, "measured_at":at.isoformat(),
            "local_day":"2026-11-06"}


def schedule(provider="facebook", status="PENDING", hours=2,
             checked=NOW, media=True, uuid="407100825539987565"):
    return {"provider":provider, "provider_status":status,
            "metricool_uuid":uuid,
            "scheduled_at":(NOW+timedelta(hours=hours)).isoformat(),
            "checked_at":checked.isoformat(),
            "has_media":media}


class ControllerTests(unittest.TestCase):
    def test_requires_verified_count_and_timezone(self):
        self.assertIsNone(fresh_official_snapshot(
            [follower(source="manual"), follower(count=True),
             follower(at=NOW-timedelta(days=5)),
             {"source":"meta_official","followers":0,"measured_at":"2026-11-06T12:14:00"}], NOW))
        self.assertEqual(fresh_official_snapshot([follower()], NOW)["followers"], 25)

    def test_fresh_source_skips_meta_and_social_writes(self):
        db=MagicMock()
        db.request.side_effect=[[follower()], []]
        refresh=MagicMock()
        output=run(db,now=NOW,refresh=refresh)
        self.assertEqual(output["follower_action"],"already_fresh")
        self.assertEqual(output["status"],"no_incidents")
        refresh.assert_not_called()
        self.assertEqual([c.args[0] for c in db.request.call_args_list], ["GET","GET"])
        self.assertEqual(output["external_posts_created"],0)

    def test_stale_source_actually_refreshes_and_verifies_before_claim(self):
        db=MagicMock()
        db.request.side_effect=[
            [follower(at=NOW-timedelta(days=2),count=15)],
            [follower(at=NOW, count=26)],
            []
        ]
        refresh=MagicMock(return_value={"status":"saved_official_snapshot","followers":26})
        out=run(db,now=NOW,refresh=refresh)
        self.assertEqual(out["follower_action"],"verified_refresh")
        self.assertTrue(out["official_follower_evidence"])
        refresh.assert_called_once()
        self.assertEqual(out["status"],"no_incidents")
        self.assertFalse(any(c.args[0]=="POST" for c in db.request.call_args_list))

    def test_meta_says_saved_but_readback_missing_cannot_claim_repaired(self):
        db=MagicMock()
        db.request.side_effect=[
            [], [], [], [{"user_id":"owner1"}], [{"source_key":"x"}]
        ]
        out=run(db,now=NOW,refresh=lambda **_:{"status":"saved_official_snapshot"})
        self.assertEqual(out["follower_action"],"refresh_not_verified")
        self.assertFalse(out["official_follower_evidence"])
        self.assertEqual(out["selected_codes"],["official_followers_stale"])
        self.assertEqual(out["notices_written"],1)

    def test_provider_error_ranked_before_refresh_block_and_no_retry(self):
        db=MagicMock()
        db.request.side_effect=[
            [], [schedule(status="ERROR",hours=-1)], [{"user_id":"owner1"}],
            [{"source_key":"x"},{"source_key":"y"}]
        ]
        out=run(db,now=NOW,refresh=lambda **_:{"status":"awaiting_official_oauth"})
        self.assertEqual(out["selected_codes"],
                         ["provider_error","official_followers_stale"])
        writes=[c for c in db.request.call_args_list if c.args[0]=="POST"]
        self.assertEqual(len(writes),1)
        self.assertEqual(writes[0].args[1],"/enna_desk_notifications")
        self.assertEqual(len(writes[0].kwargs["payload"]),2)
        for item in writes[0].kwargs["payload"]:
            self.assertNotIn("access_token",str(item))
            self.assertNotIn("post_text",str(item))
        self.assertEqual(out["external_posts_created"],0)

    def test_only_last_known_provider_evidence_and_stable_identity(self):
        stale=schedule(checked=NOW-timedelta(days=2),hours=1)
        overdue=schedule(provider="instagram",hours=-2,
                         uuid="5037196619724113601")
        bad=schedule(uuid="bad-uuid",status="ERROR")
        found=inspect_provider([stale,overdue,bad],NOW)
        self.assertEqual([x["code"] for x in found],
                         ["overdue_unverified","schedule_snapshot_stale"])
        self.assertIn("KHÔNG phải dữ liệu Metricool trực tiếp",found[0]["details"])

    def test_notices_are_idempotent_when_db_reports_existing(self):
        db=MagicMock()
        db.request.side_effect=[
            [follower()],
            [schedule(status="ERROR",hours=-1)],
            [{"user_id":"owner1"}],
            []
        ]
        output=run(db,now=NOW,refresh=MagicMock())
        self.assertEqual(output["notices_written"],0)
        self.assertEqual(output["selected_codes"],["provider_error"])
        post=db.request.call_args_list[-1]
        self.assertEqual(post.kwargs["prefer"],
                         "resolution=ignore-duplicates,return=representation")

    def test_missing_db_evidence_fail_closed(self):
        db=MagicMock()
        db.request.return_value=None
        with self.assertRaises(RuntimeError):
            run(db,now=NOW,refresh=MagicMock())


if __name__=="__main__":
    unittest.main()
