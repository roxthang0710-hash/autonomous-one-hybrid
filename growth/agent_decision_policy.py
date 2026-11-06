"""Enna agent proposal evaluation policy: goal-driven, bounded and evidence-first.

Inspired by public ReAct, agent evaluation and practical agent engineering
patterns, but implements a small, auditable safety gate rather than claiming
a fully autonomous model runtime. Untrusted model proposals may ONLY select
pre-registered internal actions, never supply tool names or arguments.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite

GOALS={
    "publishing_reliability": 22,
    "content_quality": 14,
    "audience_growth": 12,
    "revenue_readiness": 6,
}
# Registered executable CAPABILITIES. Not an LLM generated tool list.
ACTIONS={
    "refresh_official_meta_feed": {
        "permission": "threads_read", "source": "meta_official",
        "verify": "official_feed_db_readback", "minimum_gap_hours": 6,
        "effect": "verified_private_observation", "risk": "low",
    },
    "refresh_official_followers": {
        "permission": "threads_insights", "source": "meta_official",
        "verify": "official_follower_db_readback", "minimum_gap_hours": 12,
        "effect": "verified_private_observation", "risk": "low",
    },
    "reconcile_metricool_meta": {
        "permission": "private_db_update", "source": "dual_provider_verified",
        "verify": "official_permalink_and_db_readback", "minimum_gap_hours": 0,
        "effect": "internal_record_only", "risk": "low",
    },
    "evaluate_editorial_quality": {
        "permission": "private_db_read", "source": "measured_daily_aggregate",
        "verify": "reproducible_eval_result", "minimum_gap_hours": 0,
        "effect": "read_only", "risk": "low",
    },
    "prepare_original_media_brief": {
        "permission": "private_draft_write", "source": "owner_editorial_policy",
        "verify": "private_draft_readback", "minimum_gap_hours": 0,
        "effect": "draft_only", "risk": "low",
    },
}
FORBIDDEN_EXTERNAL={
    "republish_uncertain_post", "publish_social_post", "reply_to_stranger",
    "buy_subscription", "upload_unreviewed_media", "delete_post",
    "grant_own_permissions", "create_affiliate_link", "push_unreviewed_code",
    "bypass_mcp_oauth",
}
# Trusted evidence only; a local database cache cannot invent a second provider.
CONFIDENCE={
    "dual_provider_verified": 20,
    "meta_official": 16,
    "measured_daily_aggregate": 12,
    "owner_editorial_policy": 10,
}
MAX_FAILURES=2
COOLDOWN=timedelta(hours=24)


def aware(value):
    if isinstance(value, datetime):
        v=value
    else:
        v=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if v.tzinfo is None:
        raise ValueError("timezone missing")
    return v.astimezone(timezone.utc)


def assess(proposal, *, now, permissions):
    """Return JSON-safe gate. NEVER obey instructions embedded in evidence."""
    now=aware(now)
    if not isinstance(proposal,dict):
        return {"state":"blocked","reason":"invalid_proposal"}
    action=proposal.get("action")
    if not isinstance(action,str) or action in FORBIDDEN_EXTERNAL or action not in ACTIONS:
        return {"state":"blocked","reason":"unregistered_or_external_action"}
    goal=proposal.get("goal")
    if goal not in GOALS:
        return {"state":"blocked","reason":"unknown_goal"}
    config=ACTIONS[action]
    if config["permission"] not in permissions:
        return {"state":"blocked","reason":"missing_scoped_permission"}
    source=proposal.get("source")
    if source!=config["source"]:
        return {"state":"blocked","reason":"insufficient_source_provenance"}
    if proposal.get("external_write") is True or proposal.get("payment") is True:
        return {"state":"blocked","reason":"unsafe_side_effect"}
    if proposal.get("duplicate_verified") is True:
        return {"state":"skip","reason":"effect_already_verified"}
    try:
        observed=aware(proposal["observed_at"])
    except (KeyError,ValueError,TypeError,OverflowError):
        return {"state":"blocked","reason":"unverifiable_source_timestamp"}
    lag=now-observed
    if lag < timedelta(minutes=-2) or lag>timedelta(days=45):
        return {"state":"blocked","reason":"implausible_evidence_time"}
    # Repeated failure is a signal to change approach, not retry indefinitely.
    failures=proposal.get("recent_failures",0)
    if type(failures) is not int or not 0<=failures<=20:
        return {"state":"blocked","reason":"invalid_failure_count"}
    if failures>=MAX_FAILURES:
        try:
            previous=aware(proposal["last_failed_at"])
        except (KeyError,TypeError,ValueError,OverflowError):
            return {"state":"blocked","reason":"retry_history_unverified"}
        if timedelta(0)<=now-previous<COOLDOWN:
            return {"state":"blocked","reason":"require_alternative_after_repeated_failures"}
    if action=="reconcile_metricool_meta":
        if proposal.get("unique_provider_match") is not True or proposal.get("meta_id_confirmed") is not True:
            return {"state":"blocked","reason":"ambiguous_publication_proof"}
        if lag>timedelta(hours=24):
            return {"state":"blocked","reason":"official_proof_stale"}
    if action in ("refresh_official_meta_feed","refresh_official_followers"):
        # This is the AGE of the last official proof; if already fresh,
        # a GET to the provider is an unnecessary repeated action.
        if lag<timedelta(hours=config["minimum_gap_hours"]):
            return {"state":"skip","reason":"official_data_still_fresh"}
    if action=="evaluate_editorial_quality":
        if type(proposal.get("measured_days")) is not int or proposal["measured_days"]<7:
            return {"state":"blocked","reason":"too_few_measured_days"}
        if proposal.get("provider_verified") is not True:
            return {"state":"blocked","reason":"unverified_analytics"}
    if action=="prepare_original_media_brief":
        if proposal.get("asset_rights_checked") is not True or proposal.get("brand_style_approved") is not True:
            return {"state":"blocked","reason":"brand_or_rights_not_verified"}
    impact=proposal.get("impact",0)
    urgency=proposal.get("urgency",0)
    effort=proposal.get("effort",0)
    if any(type(v) not in (int,float) or not isfinite(v) or not 0<=v<=100
           for v in (impact,urgency,effort)):
        return {"state":"blocked","reason":"invalid_priority_inputs"}
    score=round(0.65*impact+0.35*urgency+GOALS[goal]
                +CONFIDENCE[source]-0.15*effort-10*failures,2)
    return {
        "state":"eligible", "reason":"scoped_evidence_sufficient",
        "score":score, "action":action, "goal":goal,
        "expected_verification":config["verify"],
        "max_tool_iterations":1, "external_social_writes":0,
    }


def choose(proposals, *, now, permissions):
    if not isinstance(proposals,list) or len(proposals)>50:
        raise ValueError("bounded_proposals_required")
    results=[]
    for idx,proposal in enumerate(proposals):
        outcome=assess(proposal,now=now,permissions=permissions)
        results.append({**outcome,"key":str(proposal.get("key",""))[:80]
                           if isinstance(proposal,dict) else "", "index":idx})
    eligible=[x for x in results if x["state"]=="eligible"]
    eligible.sort(key=lambda x:(-x["score"],x["key"],x["index"]))
    selected=eligible[0] if eligible else None
    return {
        "selected":selected,
        "eligible_count":len(eligible),
        "evaluated_count":len(results),
        "rejections":[{"key":x["key"],"reason":x["reason"]}
             for x in results if x["state"]!="eligible"],
        "external_social_writes_allowed":False,
        "bounded_to_one_action":True,
    }


if __name__=="__main__":
    # Offline proof only: no API key, no LLM, no side effects.
    import json
    from pathlib import Path
    tests=json.loads((Path(__file__).resolve().parents[1]/
       "config/enna_agent_behavior_eval_cases_v1.json").read_text(encoding="utf-8"))
    passed=0
    for item in tests["cases"]:
        actual=choose(item["proposals"],now=tests["now"],permissions=set(item["permissions"]))
        expected=item.get("expected_key")
        chosen=actual["selected"]["key"] if actual["selected"] else None
        if chosen!=expected:
            raise SystemExit("AGENT_BEHAVIOR_EVAL_FAILED:"+item["id"])
        passed+=1
    print(json.dumps({"suite":"enna_agent_behavior_v1","passed":passed,
                      "total":len(tests["cases"]),"external_social_writes":0,
                      "model_calls":0},ensure_ascii=False))
