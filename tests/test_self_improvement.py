import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from growth.self_improvement import decide, run
NOW=datetime(2026,11,8,10,tzinfo=timezone.utc)

def report(story_rate=5,practical_rate=2,story_views=500,other_views=400):
    return {"status":"comparison_ready","group_stats":{
        "story":{"measured_posts":4,"replies_per_1000_views":story_rate,
                 "median_views":story_views},
        "other":{"measured_posts":5,"replies_per_1000_views":practical_rate,
                 "median_views":other_views}}}

class ImprovementTests(unittest.TestCase):
    def test_no_data_means_no_policy_change(self):
        action,style,_=decide({"status":"insufficient_evidence",
                              "group_stats":{}},now=NOW)
        self.assertEqual((action,style),("insufficient_evidence","balanced"))
    def test_stories_win_with_actual_evidence(self):
        action,style,sample=decide(report(),now=NOW)
        self.assertEqual((action,style),("promote_story","story"))
        self.assertEqual(sample["story_posts"],4)
    def test_rollback_before_switching_to_opposite(self):
        action,style,_=decide(report(story_rate=2,practical_rate=6),
                              current="story",now=NOW,
                              last_changed=(NOW-timedelta(days=4)).isoformat())
        self.assertEqual((action,style),("rollback_balanced","balanced"))
    def test_cooldown_and_close_evidence_hold(self):
        self.assertEqual(decide(report(),now=NOW,current="practical",
                         last_changed=(NOW-timedelta(hours=8)).isoformat())[0],"hold")
        self.assertEqual(decide(report(story_rate=2.2,practical_rate=2.1),
                         now=NOW)[0],"hold")
    def test_reach_tradeoff_rejects_shiny_reply_ratio(self):
        self.assertEqual(decide(report(story_rate=12,practical_rate=2,
                                       story_views=100,other_views=1200),now=NOW)[0],"hold")
    def test_deduplicated_daily_decision_and_no_fabricated_posts(self):
        db=MagicMock()
        db.request.side_effect=[
            [{"preferred_format":"balanced",
              "version":1,"applied_at":(NOW-timedelta(days=4)).isoformat()}],
            [],
            [],
            [],
            [{"brand_key":"do_hay_di_lam"}]
        ]
        result=run(db,now=NOW)
        self.assertEqual(result,"insufficient_evidence")
        calls=[x for x in db.request.call_args_list if x.args[0]=="PATCH"]
        self.assertEqual(calls,[])
        log=db.request.call_args
        self.assertEqual(log.kwargs["payload"]["decision"],"insufficient_evidence")

if __name__=="__main__":unittest.main()
