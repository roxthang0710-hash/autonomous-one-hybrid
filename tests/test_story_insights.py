import unittest
from datetime import datetime, timezone, timedelta
from growth.story_insights import assess, classify_format

NOW=datetime(2026,11,12,10,tzinfo=timezone.utc)
def make_post(i,story):
    return {"id":str(i),"status":"posted","platform_post_id":"meta"+str(i),
            "published_at":(NOW-timedelta(days=2)).isoformat(),
            "text_content":"Mẩu chuyện công sở (Tình huống giả định)" if story else "Mẹo làm việc hữu ích"}
class StoryInsightsTests(unittest.TestCase):
    def test_does_not_fake_data(self):
        s=assess([make_post(1,True)],[],now=NOW)
        self.assertEqual(s["status"],"insufficient_evidence")
        self.assertIsNone(s["group_stats"]["story"]["median_views"])
    def test_require_3_observed_posts_each_before_comparison(self):
        p=[make_post(i,i<3) for i in range(6)]
        m=[{"post_id":str(i),"collected_at":NOW.isoformat(),"views":100,"replies":i+1}
           for i in range(6)]
        self.assertEqual(assess(p,m,now=NOW)["status"],"comparison_ready")
        self.assertEqual(assess(p[:5],m,now=NOW)["status"],"insufficient_evidence")
    def test_partial_metrics_not_zero_and_new_posts_ignored(self):
        posts=[make_post(1,True),make_post(2,False)]
        posts[0]["published_at"]=(NOW-timedelta(hours=1)).isoformat()
        metrics=[{"post_id":"1","collected_at":NOW.isoformat(),"views":500,"replies":15},
                 {"post_id":"2","collected_at":NOW.isoformat(),"views":None,"replies":2}]
        report=assess(posts,metrics,now=NOW)
        self.assertEqual(report["group_stats"]["story"]["measured_posts"],0)
        self.assertEqual(report["group_stats"]["other"]["measured_posts"],0)
    def test_classifies_true_fiction_label(self):
        self.assertEqual(classify_format("Tình huống giả định: chuyện công sở"),"story")
        self.assertEqual(classify_format("Mẹo văn phòng"),"other")

if __name__=="__main__": unittest.main()
