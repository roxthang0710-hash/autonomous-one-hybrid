"""Integration-style E2 tests: real action dispatch only in fake Meta/DB."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import unittest
from unittest.mock import Mock

from growth.agent_goal_cycle import (
  run,run_key,build_proposals,read_sources,save_and_verify
)

NOW=datetime(2026,11,6,16,0,tzinfo=timezone.utc)

def time_before(hours):
    return (NOW-timedelta(hours=hours)).isoformat()

class FakeDb:
    def __init__(self, *, follower_age=2,feed_age=1,history=None):
        self.followers=[{"source":"meta_official","measured_at":time_before(follower_age),
                         "followers":25}]
        self.feed=[{"source":"meta_official","last_observed_at":time_before(feed_age)}]
        self.history=deepcopy(history or [])
        self.claims={}
        self.calls=[]

    def request(self,method,path,params=None,payload=None,prefer=None):
        self.calls.append((method,path))
        if method=="GET" and path=="/enna_threads_account_snapshots":
            return deepcopy(self.followers)
        if method=="GET" and path=="/enna_official_threads_observations":
            return deepcopy(self.feed)
        if method=="GET" and path=="/enna_agent_goal_runs":
            if params.get("run_key"):
                key=params["run_key"].removeprefix("eq.")
                return [deepcopy(self.claims[key])] if key in self.claims else []
            return deepcopy(self.history)
        if method=="POST" and path=="/enna_agent_goal_runs":
            key=payload["run_key"]
            if key in self.claims:
                return []
            self.claims[key]=deepcopy(payload)
            return [deepcopy(payload)]
        if method=="PATCH" and path=="/enna_agent_goal_runs":
            key=params["run_key"].removeprefix("eq.")
            item=self.claims.get(key)
            if item is None or item["status"]!="running":
                return []
            item.update(deepcopy(payload))
            return [deepcopy(item)]
        raise AssertionError("Unexpected call "+str((method,path)))


class E2CycleTests(unittest.TestCase):
    def test_run_key_is_stable_in_two_hour_slot(self):
        self.assertEqual(run_key(NOW),"enna-e2:20261106:8")
        self.assertEqual(run_key(NOW+timedelta(hours=1)),"enna-e2:20261106:8")

    def test_no_safe_action_is_a_verified_stop_not_fake_progress(self):
        db=FakeDb()
        follower=Mock()
        feed=Mock()
        out=run(db,now=NOW,refresh_feed=feed,refresh_followers=follower)
        self.assertEqual(out["status"],"no_safe_action")
        self.assertEqual(out["action"],None)
        self.assertEqual(out["candidates"],2)
        self.assertEqual(out["external_social_writes"],0)
        feed.assert_not_called()
        follower.assert_not_called()
        self.assertIsNone(db.claims[run_key(NOW)]["verified_at"])

    def test_select_stale_feed_act_once_and_independently_verify(self):
        db=FakeDb(feed_age=7,follower_age=3)
        invoked=Mock()
        def refresh(db,now):
            invoked()
            db.feed[0]["last_observed_at"]=NOW.isoformat()
            return {"state":"verified_official_feed","verified_count":23}
        out=run(db,now=NOW,refresh_feed=refresh,refresh_followers=Mock())
        self.assertEqual(out["action"],"refresh_official_meta_feed")
        self.assertEqual(out["status"],"verified")
        self.assertEqual(out["result_code"],"official_provider_readback_verified")
        invoked.assert_called_once()
        self.assertNotIn("/threads_publish",[x[1] for x in db.calls])
        self.assertEqual(out["money_spent_vnd"],0)

    def test_select_stale_follower_act_and_verify_count(self):
        db=FakeDb(feed_age=1,follower_age=16)
        def refresh(db,now):
            db.followers[0]={"source":"meta_official",
                 "measured_at":NOW.isoformat(),"followers":26}
            return {"status":"saved_official_snapshot","followers":26}
        out=run(db,now=NOW,refresh_followers=refresh)
        self.assertEqual(out["action"],"refresh_official_followers")
        self.assertEqual(out["status"],"verified")
        self.assertIsNotNone(db.claims[run_key(NOW)]["verified_at"])

    def test_when_two_sources_are_stale_feed_wins_using_goal_priority(self):
        db=FakeDb(feed_age=9,follower_age=20)
        calls=[]
        def feed(db,now):
            calls.append("feed")
            db.feed[0]["last_observed_at"]=NOW.isoformat()
            return {"state":"verified_official_feed","verified_count":23}
        out=run(db,now=NOW,refresh_feed=feed,refresh_followers=lambda **_:calls.append("followers"))
        self.assertEqual(calls,["feed"])
        self.assertEqual(out["status"],"verified")

    def test_after_two_failures_switches_to_unblocked_alternative(self):
        history=[{"selected_action":"refresh_official_meta_feed","status":"blocked",
                  "finished_at":time_before(2)},
                 {"selected_action":"refresh_official_meta_feed","status":"unverified",
                  "finished_at":time_before(4)}]
        db=FakeDb(feed_age=9,follower_age=20,history=history)
        calls=[]
        def follower(db,now):
            calls.append("followers")
            db.followers[0]={"source":"meta_official","measured_at":NOW.isoformat(),
                              "followers":30}
            return {"status":"saved_official_snapshot","followers":30}
        out=run(db,now=NOW,refresh_feed=lambda **_:calls.append("feed"),
                refresh_followers=follower)
        self.assertEqual(calls,["followers"])
        self.assertEqual(out["action"],"refresh_official_followers")

    def test_missing_credential_remains_blocked_and_is_not_retried_same_slot(self):
        db=FakeDb(feed_age=12)
        action=Mock(return_value={"state":"meta_owner_oauth_unavailable"})
        first=run(db,now=NOW,refresh_feed=action)
        second=run(db,now=NOW+timedelta(minutes=20),refresh_feed=action)
        self.assertEqual(first["status"],"blocked")
        self.assertEqual(first["result_code"],"meta_owner_oauth_unavailable")
        self.assertEqual(second["status"],"already_processed")
        action.assert_called_once()
        self.assertEqual(db.claims[run_key(NOW)]["external_social_writes"],0)

    def test_provider_says_saved_but_readback_stale_must_be_unverified(self):
        db=FakeDb(feed_age=12)
        out=run(db,now=NOW,refresh_feed=lambda **_:{
            "state":"verified_official_feed","verified_count":23})
        self.assertEqual(out["status"],"unverified")
        self.assertEqual(out["result_code"],"provider_saved_but_source_readback_missing")
        self.assertIsNone(db.claims[run_key(NOW)]["verified_at"])

    def test_missing_evidence_aborts_instead_of_creating_fake_status(self):
        class Broken(FakeDb):
            def request(self,method,path,params=None,payload=None,prefer=None):
                if method=="GET" and path=="/enna_official_threads_observations":
                    return None
                return super().request(method,path,params=params,payload=payload,prefer=prefer)
        db=Broken()
        with self.assertRaises(RuntimeError):
            run(db,now=NOW,refresh_feed=Mock())
        self.assertEqual(db.claims[run_key(NOW)]["status"],"running")

    def test_wrong_persistent_result_readback_cannot_claim_verified(self):
        class Corrupt(FakeDb):
            def request(self,method,path,params=None,payload=None,prefer=None):
                result=super().request(method,path,params=params,payload=payload,prefer=prefer)
                if method=="GET" and path=="/enna_agent_goal_runs" and params.get("run_key"):
                    result[0]["external_social_writes"]=1
                return result
        db=Corrupt()
        with self.assertRaises(RuntimeError):
            run(db,now=NOW,refresh_feed=Mock())

    def test_source_and_history_never_injected_into_unregistered_tool(self):
        db=FakeDb(feed_age=7)
        db.history.append({"selected_action":"publish_social_post","status":"blocked",
                           "finished_at":time_before(2)})
        f,p,h=read_sources(db)
        proposals=build_proposals(f,p,h,NOW)
        self.assertTrue(all(x["action"] in ("refresh_official_meta_feed",
                         "refresh_official_followers") for x in proposals))

if __name__=="__main__":
    unittest.main()
