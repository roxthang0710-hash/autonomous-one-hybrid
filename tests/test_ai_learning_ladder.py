"""Three-stage learning gate and static public-funnel security regression."""
from datetime import date, timedelta
from pathlib import Path
import unittest

from growth.ai_learning_ladder import (
 evaluate_progress,stage_two_briefs_if_ready,public_clone_enabled
)
from threads.ai_advanced_editorial import validate, ADVANCED

ROOT=Path(__file__).resolve().parents[1]
def post(i, level=1, published=True):
    host=("www.threads.com" if i%3==0 else
          "www.instagram.com" if i%3==1 else "www.facebook.com")
    return {
       "level":level,"status":"published" if published else "pending",
       "provider_verified":published,
       "platform":("threads" if i%3==0 else "instagram" if i%3==1 else "facebook"),
       "permalink":"https://"+host+"/p/test-"+str(i),
       "published_local_day":(date(2026,11,1)+timedelta(days=i//2)).isoformat(),
       "lesson_key":"lesson_"+str(i%4),
    }

class AILadderTests(unittest.TestCase):
    def test_no_queued_posts_or_fake_urls_count_as_learning_evidence(self):
        only=[post(i,published=False) for i in range(12)]
        self.assertEqual(evaluate_progress(only)["current_teaching_level"],1)
        bad=post(1)
        bad["permalink"]="https://fake-meta.example.com/p/fake"
        self.assertEqual(evaluate_progress([bad])["verified_level_1_posts"],0)

    def test_must_have_enough_posts_days_and_distinct_topics(self):
        posts=[post(i) for i in range(6)]
        status=evaluate_progress(posts)
        self.assertFalse(status["level_2_ready"]) # 6 posts span only 3 days
        posts.append(post(6))
        status=evaluate_progress(posts)
        self.assertTrue(status["level_2_ready"])
        self.assertEqual(status["current_teaching_level"],2)
        self.assertGreaterEqual(len(stage_two_briefs_if_ready(status)),8)

    def test_level_three_requires_applied_workflows_with_human_evidence(self):
        posts=[post(i) for i in range(8)]
        posts += [post(i+200,level=2) for i in range(4)]
        cases=[{"case_id":"test-"+str(i),"human_verified":True,
                "outcome_checked":True,"safe_to_share":True,
                "lane":"excel" if i%2 else "meeting"} for i in range(3)]
        self.assertEqual(evaluate_progress(posts,cases)["current_teaching_level"],3)
        cases[0]["safe_to_share"]=False
        self.assertFalse(evaluate_progress(posts,cases)["level_3_ready"])

    def test_stage2_has_real_outputs_and_verification(self):
        self.assertTrue(validate())
        for a in ADVANCED:
            self.assertGreaterEqual(len(a["steps"]),3)
            self.assertTrue(a["inputs"] and a["deliverable"] and a["verify"])
            self.assertIn("Người Tròn",a["image"])

    def test_clone_lite_does_not_call_remote_llm_or_embed_keys(self):
        paths=[
            ROOT/"docs/enna/clone/index.html",
            ROOT/"docs/enna/ai/index.html",
        ]
        for path in paths:
            html=path.read_text(encoding="utf-8")
            self.assertIn("<html",html)
            self.assertIn("connect-src 'none'",html)
            self.assertNotIn("GROQ_API_KEY =",html)
            self.assertNotIn("sb_secret",html)
            self.assertNotIn("fetch(",html)
            self.assertNotIn("XMLHttpRequest",html)
            self.assertIn("www.threads.com/@dohay_dilam",html)
        self.assertFalse(public_clone_enabled()["uses_original_enna_tokens"])
        self.assertFalse(public_clone_enabled()["has_autonomous_social_actions"])

    def test_link_bio_has_both_funnel_destinations(self):
        html=(ROOT/"docs/enna/links/index.html").read_text(encoding="utf-8")
        self.assertIn("../ai/?utm_source=link_bio",html)
        self.assertIn("../clone/?utm_source=link_bio",html)
        self.assertIn("affiliate",html.lower())

if __name__=="__main__":
    unittest.main()
