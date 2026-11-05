"""Evidence-gated 3-level AI editorial progression for dohay_dilam.

The readiness check is deliberately conservative. A queued/scheduled/used plan
does NOT count as published or a real-life workflow success. Stage-3 community
growth can be tested separately with the safe public clone, but training
progression must be supported by independently verified evidence.
"""
from datetime import date
from urllib.parse import urlparse

from threads.ai_advanced_editorial import ADVANCED, briefs as advanced_briefs

BASE_SERIES="AI — Đồng nghiệp thứ hai"
VALID_NETWORKS={"threads","facebook","instagram"}
KNOWN_POST_HOSTS={"www.threads.com","threads.com","www.instagram.com","instagram.com",
                  "www.facebook.com","facebook.com","m.facebook.com"}

def _verified_post(row, level):
    if not isinstance(row,dict) or row.get("level") != level:
        return False
    if row.get("status")!="published" or row.get("provider_verified") is not True:
        return False
    if row.get("platform") not in VALID_NETWORKS:
        return False
    url=str(row.get("permalink") or "")
    p=urlparse(url)
    if p.scheme!="https" or p.hostname not in KNOWN_POST_HOSTS:
        return False
    try:
        date.fromisoformat(str(row.get("published_local_day") or ""))
    except ValueError:
        return False
    return bool(p.path and p.path!="/")

def evaluate_progress(posts, applied_workflows=()):
    if not isinstance(posts,(list,tuple)) or not isinstance(applied_workflows,(list,tuple)):
        raise ValueError("Evidence must be collections")
    basic={r["permalink"]:r for r in posts if _verified_post(r,1)}
    advanced={r["permalink"]:r for r in posts if _verified_post(r,2)}
    days1={r["published_local_day"] for r in basic.values()}
    topics1={str(r.get("lesson_key") or "") for r in basic.values() if r.get("lesson_key")}
    # A level-1 publishing batch of at least 6 actual posts over at least 4
    # days, from 3 distinct lessons. No assertion about virality.
    level2_ready=len(basic)>=6 and len(days1)>=4 and len(topics1)>=3
    # Real-use cases must be de-identified and explicitly human-confirmed.
    cases={str(r.get("case_id")):r for r in applied_workflows
           if isinstance(r,dict) and r.get("human_verified") is True
           and r.get("safe_to_share") is True
           and r.get("outcome_checked") is True
           and r.get("case_id")}
    lanes={str(r.get("lane")) for r in cases.values() if r.get("lane")}
    level3_ready=level2_ready and len(advanced)>=4 and len(cases)>=3 and len(lanes)>=2
    return {
       "current_teaching_level":3 if level3_ready else (2 if level2_ready else 1),
       "level_2_ready":level2_ready,
       "level_3_ready":level3_ready,
       "verified_level_1_posts":len(basic),
       "verified_level_1_days":len(days1),
       "distinct_level_1_lessons":len(topics1),
       "verified_level_2_posts":len(advanced),
       "human_checked_safe_workflows":len(cases),
       "distinct_workflow_lanes":len(lanes),
       "next_step":(
          "invite_to_public_enna_clone_starter" if level3_ready
          else "publish_and_verify_level_2_workflows" if level2_ready
          else "publish_6_basic_ai_lessons_on_4_days_with_3_distinct_topics"
       ),
       "no_autopublish":True,
    }

def stage_two_briefs_if_ready(progress):
    if progress.get("level_2_ready") is not True:
        return tuple()
    return advanced_briefs()

def public_clone_enabled():
    """Public educational clone is opt-in regardless of editorial stage."""
    return {"demo_site":"docs/enna/clone/index.html",
            "local_agent":"starter/enna-clone/agent.py",
            "uses_original_enna_tokens":False,
            "has_autonomous_social_actions":False,
            "server_side_secret_required_in_browser":False}
