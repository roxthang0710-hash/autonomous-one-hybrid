"""A1.2: durable incident lifecycle must not self-certify cached Metricool."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from growth.autonomy_incident_lifecycle import (
    FOLLOWER_KEY, active_candidates, plan_actions, run, valid_prior,
)

NOW = datetime(2026, 11, 6, 13, 30, tzinfo=timezone.utc)
BRAND = "do_hay_di_lam"
PROVIDER_KEY = "autonomy-v1:provider_error:facebook:407100825539987565"


def followers(at=NOW, count=25):
    return [{"brand_key": BRAND, "source": "meta_official",
             "followers": count, "measured_at": at.isoformat()}]


def fb(status="ERROR", checked=NOW, when=NOW-timedelta(hours=1)):
    return [{"provider": "facebook", "metricool_uuid": "407100825539987565",
             "scheduled_at": when.isoformat(), "checked_at": checked.isoformat(),
             "provider_status": status, "has_media": True}]


def prior(key, state, **kw):
    return {
        "brand_key": BRAND, "incident_key": key,
        "incident_code": key.split(":")[1],
        "state": state,
        "first_seen_at": (NOW-timedelta(hours=1)).isoformat(),
        "evidence_at": (NOW-timedelta(hours=1)).isoformat(),
        "resolution_evidence_at": None, **kw
    }


class FakeDb:
    def __init__(self, followers_data=None, providers=None, incidents=None):
        self.followers = deepcopy(followers_data if followers_data is not None else followers())
        self.providers = deepcopy(providers if providers is not None else fb())
        self.incidents = {v["incident_key"]: deepcopy(v) for v in (incidents or [])}
        self.calls = []

    def request(self, method, path, *, params=None, payload=None, prefer=None):
        self.calls.append((method, path, deepcopy(params), deepcopy(payload)))
        if method == "GET":
            if path == "/enna_threads_account_snapshots":
                return deepcopy(self.followers)
            if path == "/enna_multichannel_posts":
                return deepcopy(self.providers)
            if path == "/enna_autonomy_incidents":
                return deepcopy(list(self.incidents.values()))
        if method == "POST" and path == "/enna_autonomy_incidents":
            key = payload["incident_key"]
            if key in self.incidents:
                return []
            self.incidents[key] = deepcopy(payload)
            return [deepcopy(payload)]
        if method == "PATCH" and path == "/enna_autonomy_incidents":
            key = params["incident_key"].removeprefix("eq.")
            existing = self.incidents.get(key)
            if existing is None:
                return []
            gate = params.get("state")
            if gate == "eq.resolved" and existing["state"] != "resolved":
                return []
            if gate == "in.(open,blocked)" and existing["state"] not in {"open","blocked"}:
                return []
            existing.update(deepcopy(payload))
            return [deepcopy(existing)]
        raise AssertionError("Unexpected database request: " + str((method,path)))


class LifecycleTests(unittest.TestCase):
    def test_stale_meta_source_creates_open_issue_without_claiming_a_refresh(self):
        observed = active_candidates(followers(NOW-timedelta(days=1)),[],NOW)
        self.assertEqual(len(observed),1)
        self.assertEqual(observed[0]["incident_key"], FOLLOWER_KEY)
        self.assertEqual(observed[0]["state"],"open")
        self.assertIsNone(observed[0]["evidence_at"])

    def test_metricool_error_is_blocked_not_auto_resolved(self):
        issues = active_candidates(followers(),fb(),NOW)
        self.assertEqual(issues[0]["incident_key"],PROVIDER_KEY)
        self.assertEqual(issues[0]["state"],"blocked")
        self.assertEqual(issues[0]["source_kind"],"supabase_snapshot")

    def test_priority_retains_follower_incident_behind_multiple_provider_errors(self):
        providers=[]
        for i in range(4):
            sample=fb()[0]
            sample["metricool_uuid"]=str(407100825539987565+i)
            providers.append(sample)
        issues=active_candidates(followers(NOW-timedelta(days=2)),providers,NOW)
        self.assertEqual(len(issues),3)
        self.assertIn(FOLLOWER_KEY,[x["incident_key"] for x in issues])

    def test_old_cached_error_cannot_reopen_resolved_provider_incident(self):
        old=prior(PROVIDER_KEY,"resolved",
                  resolved_at=(NOW-timedelta(minutes=20)).isoformat(),
                  resolution_evidence_at=(NOW-timedelta(minutes=20)).isoformat())
        cases=plan_actions(active_candidates(followers(),
                           fb(checked=NOW-timedelta(hours=2)),NOW),[old],followers(),NOW)
        self.assertEqual(cases,[])

    def test_newer_provider_error_after_resolution_may_reopen_but_not_republish(self):
        old=prior(PROVIDER_KEY,"resolved",
                  resolved_at=(NOW-timedelta(minutes=50)).isoformat(),
                  resolution_evidence_at=(NOW-timedelta(minutes=50)).isoformat())
        cases=plan_actions(active_candidates(followers(),fb(),NOW),[old],followers(),NOW)
        self.assertEqual(cases[0][0],"reopen")
        db=FakeDb(incidents=[old])
        out=run(db,now=NOW)
        self.assertEqual(out["status"],"verified")
        self.assertEqual(db.incidents[PROVIDER_KEY]["state"],"blocked")
        self.assertEqual(db.incidents[PROVIDER_KEY]["first_seen_at"],NOW.isoformat())
        self.assertFalse(any(call[1].startswith("/threads") for call in db.calls))
        self.assertEqual(out["social_writes"],0)

    def test_recurrence_of_stale_meta_after_previous_resolution(self):
        old=prior(FOLLOWER_KEY,"resolved",
                  resolved_at=(NOW-timedelta(days=1)).isoformat(),
                  resolution_evidence_at=(NOW-timedelta(days=1)).isoformat())
        cases=plan_actions(active_candidates(followers(NOW-timedelta(days=1)),
                           [],NOW),[old],followers(NOW-timedelta(days=1)),NOW)
        self.assertEqual([action for action,_,_ in cases],["reopen"])

    def test_meta_resolution_requires_newer_official_evidence_than_detection(self):
        old=prior(FOLLOWER_KEY,"open",
                  first_seen_at=(NOW-timedelta(minutes=30)).isoformat())
        stale=followers(NOW-timedelta(minutes=45))
        cases=plan_actions([], [old], stale, NOW)
        self.assertEqual(cases,[])

    def test_official_follower_readback_closes_open_stale_incident(self):
        old=prior(FOLLOWER_KEY,"open",evidence_at=None,
                  first_seen_at=(NOW-timedelta(hours=2)).isoformat())
        db=FakeDb(followers_data=followers(),providers=[],incidents=[old])
        out=run(db,now=NOW)
        self.assertEqual(out["status"],"verified")
        self.assertEqual(out["resolved_from_verified_meta"],1)
        record=db.incidents[FOLLOWER_KEY]
        self.assertEqual(record["state"],"resolved")
        self.assertEqual(record["resolution_source"],"meta_official")
        self.assertEqual(record["resolution_evidence_at"],NOW.isoformat())
        self.assertEqual(out["social_writes"],0)

    def test_cached_disappearance_does_not_close_provider_error(self):
        old=prior(PROVIDER_KEY,"blocked")
        db=FakeDb(providers=fb(status="PUBLISHED"),incidents=[old])
        result=run(db,now=NOW)
        self.assertEqual(result["transitions_verified"],0)
        self.assertEqual(db.incidents[PROVIDER_KEY]["state"],"blocked")

    def test_persistence_is_idempotent_and_does_not_touch_owner_acknowledgement(self):
        db=FakeDb()
        first=run(db,now=NOW)
        second=run(db,now=NOW+timedelta(minutes=2))
        self.assertEqual(first["transitions_verified"],1)
        self.assertEqual(second["transitions_verified"],1)
        self.assertEqual(len(db.incidents),1)
        self.assertEqual(db.incidents[PROVIDER_KEY]["state"],"blocked")
        self.assertFalse(any(c[1]=="/enna_desk_notifications" for c in db.calls))
        self.assertFalse(any(c[1] in ("/threads_posts","/enna_multichannel_posts") and c[0]!="GET" for c in db.calls))

    def test_missing_ledger_fails_closed_not_simulated_success(self):
        class Broken(FakeDb):
            def request(self,method,path,**kwargs):
                if method=="GET" and path=="/enna_autonomy_incidents":
                    return None
                return super().request(method,path,**kwargs)
        with self.assertRaises(RuntimeError):
            run(Broken(),now=NOW)


if __name__ == "__main__":
    unittest.main()
