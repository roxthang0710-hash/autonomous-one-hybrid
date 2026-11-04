"""The growth sprint must change real policy only on verified short-window data."""
import unittest
from datetime import datetime,timezone
from unittest.mock import MagicMock
from growth.conversion_loop import clean_days,select_policy,measure,run

NOW=datetime(2026,11,5,2,tzinfo=timezone.utc)
ROWS=[
 {"measured_on":"2026-11-04","followers":6,"new_followers":1,"profile_views":324},
 {"measured_on":"2026-11-03","followers":5,"new_followers":2,"profile_views":1033},
]

class GrowthConversionTests(unittest.TestCase):
    def test_observed_proxy_not_claimed_causal(self):
        s=select_policy(ROWS,now=NOW)
        self.assertEqual(s["status"],"ready")
        self.assertEqual(s["focus"],"practical_follow_value")
        self.assertEqual(s["baseline_followers"],6)
        self.assertLess(s["proxy_new_followers_per_profile_view"],.01)
        self.assertIn("not a verified conversion rate",s["note"])
    def test_stale_data_cannot_auto_change_strategy(self):
        s=select_policy([{"measured_on":"2026-11-01","followers":5,
             "new_followers":1,"profile_views":900},
             {"measured_on":"2026-10-31","followers":4,
             "new_followers":1,"profile_views":900}],now=NOW)
        self.assertEqual(s["status"],"insufficient_or_stale")
    def test_follower_with_no_profile_metric_is_not_zero(self):
        s=select_policy([{"measured_on":"2026-11-04","followers":5},
            {"measured_on":"2026-11-03","followers":4}],now=NOW)
        self.assertIsNone(s["focus"])
    def test_one_great_day_is_not_baseline(self):
        s=select_policy(ROWS[:1],now=NOW)
        self.assertEqual(s["status"],"insufficient_or_stale")
    def test_real_post_trial_samples_only(self):
        sprint={"baseline_day":"2026-11-04",
         "latest_observation":{"proxy_new_followers_per_profile_view":.00221}}
        later=ROWS+[
            {"measured_on":"2026-11-05","followers":7,"new_followers":1,"profile_views":300},
            {"measured_on":"2026-11-06","followers":7,"new_followers":0,"profile_views":300}]
        result=measure(sprint,later,datetime(2026,11,7,2,tzinfo=timezone.utc)
                    .astimezone(__import__("zoneinfo").ZoneInfo("Asia/Ho_Chi_Minh")).date())
        self.assertEqual(result["status"],"measured")
        self.assertEqual(result["decision"],"return_balanced")
    def test_noncausal_result_never_guarantees_growth(self):
        sprint={"baseline_day":"2026-11-04",
         "latest_observation":{"proxy_new_followers_per_profile_view":.00221}}
        r=measure(sprint,ROWS,datetime(2026,11,7,2,tzinfo=timezone.utc).date())
        self.assertEqual(r["status"],"waiting_new_data")
    def test_run_updates_actual_future_editorial_policy_not_posts(self):
        db=MagicMock()
        def f(method,path,*,params=None,payload=None,prefer=None):
            if path=="/growth_metricool_daily": return ROWS
            if path=="/enna_growth_sprints" and method=="GET": return []
            if path=="/enna_learning_policy" and method=="GET": return [{"preferred_format":"balanced","version":1}]
            if path=="/enna_growth_sprints" and method=="POST": return [{"sprint_key":"follow-value-2026-11-05"}]
            if path=="/enna_learning_policy" and method=="PATCH":
                self.assertEqual(payload["preferred_format"],"practical")
                return [{"preferred_format":"practical","version":2}]
            if path=="/enna_growth_sprints" and method=="PATCH": return [{"status":"running"}]
            if path=="/enna_desk_owners":return []
            return []
        db.request.side_effect=f
        result=run(db,now=NOW)
        self.assertEqual(result["status"],"experiment_started")
        self.assertTrue(result["policy_changed"])
        posts=[x for x in db.request.call_args_list if x.args[1]=="/threads_posts"]
        self.assertEqual(posts,[])

if __name__=="__main__":unittest.main()
