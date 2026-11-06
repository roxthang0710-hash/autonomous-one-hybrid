"""E2: one goal-driven, evidence-backed action per unattended worker cycle.

Inputs are previous official Meta observations and prior verified outcomes.
A pure selection policy chooses ONE allowlisted authorized read-only recovery.
Execution is followed by independent Supabase proof readback and private audit.
No arbitrary LLM-provided code, public social actions, money or rights changes.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from agent import Database
from growth.agent_decision_policy import choose
from growth.autonomy_controller import aware_time, fresh_official_snapshot
from growth.account_followers import collect as official_followers
from growth.official_threads_observations import collect as official_posts

BRAND="do_hay_di_lam"
TABLE="/enna_agent_goal_runs"
PERMISSIONS=frozenset({"threads_read","threads_insights"})
RETRY_WINDOW=timedelta(hours=24)


def run_key(now):
    now=aware_time(now)
    return "enna-e2:"+now.strftime("%Y%m%d")+":"+str(now.hour//2)


def _recent_official(rows, field, now):
    if not isinstance(rows,list):
        raise RuntimeError("source_evidence_not_available")
    valid=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("source")!="meta_official":
            continue
        try:at=aware_time(row[field])
        except (KeyError,ValueError,TypeError,OverflowError):continue
        if timedelta(minutes=-2)<=now-at<=timedelta(days=45):
            valid.append(at)
    return max(valid) if valid else None


def build_proposals(followers, feeds, history, now):
    if not all(isinstance(x,list) for x in (followers,feeds,history)):
        raise RuntimeError("agent_observations_unavailable")
    candidates=[]
    configs=(
      ("refresh_official_meta_feed","publishing_reliability",
       "threads_read",feeds,"last_observed_at",88,93),
      ("refresh_official_followers","audience_growth",
       "threads_insights",followers,"measured_at",65,74),
    )
    for action,goal,permission,rows,key,impact,urgency in configs:
        observed=_recent_official(rows,key,now)
        if observed is None:
            continue
        recent=[x for x in history
          if isinstance(x,dict) and x.get("selected_action")==action
          and x.get("status") in ("blocked","unverified")]
        recent.sort(key=lambda x:str(x.get("finished_at") or ""),reverse=True)
        last=None
        errors=0
        for previous in recent:
            try:dt=aware_time(previous.get("finished_at"))
            except (ValueError,TypeError,OverflowError):continue
            if timedelta(0)<=now-dt<=RETRY_WINDOW:
                errors+=1
                if last is None:last=dt
        candidates.append({
          "key":action,"action":action,"goal":goal,"source":"meta_official",
          "observed_at":observed.isoformat(),
          "impact":impact,"urgency":urgency,"effort":12,
          "recent_failures":min(20,errors),
          **({"last_failed_at":last.isoformat()} if last else {}),
        })
    return candidates


def read_sources(db):
    followers=db.request("GET","/enna_threads_account_snapshots",params={
        "select":"source,measured_at,followers",
        "brand_key":"eq."+BRAND,"order":"measured_at.desc","limit":"6"})
    feed=db.request("GET","/enna_official_threads_observations",params={
        "select":"source,last_observed_at",
        "brand_key":"eq."+BRAND,"order":"last_observed_at.desc","limit":"6"})
    history=db.request("GET",TABLE,params={
        "select":"selected_action,status,finished_at",
        "brand_key":"eq."+BRAND,"order":"started_at.desc","limit":"25"})
    return followers,feed,history


def save_and_verify(db,key,action,result,now):
    """Only a proven readback may yield 'verified'."""
    state=result["status"]
    payload={
      "status":state,
      "selected_action":action["action"] if action else None,
      "selected_goal":action["goal"] if action else None,
      "chosen_verifier":action["expected_verification"] if action else None,
      "source":"meta_official" if action else None,
      "observed_at":result.get("observed_at"),
      "result_code":result["result_code"],
      "candidates":result["candidates"],
      "verified_at":result.get("verified_at"),
      "finished_at":now.isoformat(),
      "external_social_writes":0,
      "money_spent_vnd":0,
    }
    saved=db.request("PATCH",TABLE,params={
        "run_key":"eq."+key,"brand_key":"eq."+BRAND,
        "status":"eq.running"},
        payload=payload,prefer="return=representation")
    if not isinstance(saved,list) or len(saved)!=1:
        raise RuntimeError("agent_cycle_result_write_unverified")
    readback=db.request("GET",TABLE,params={
        "select":"run_key,status,selected_action,verified_at,result_code,candidates,"
                 "external_social_writes,money_spent_vnd",
        "run_key":"eq."+key,"limit":"1"})
    if not isinstance(readback,list) or len(readback)!=1:
        raise RuntimeError("agent_cycle_result_readback_unavailable")
    row=readback[0]
    if (row.get("run_key")!=key or row.get("status")!=state
        or row.get("result_code")!=payload["result_code"]
        or row.get("selected_action")!=payload["selected_action"]
        or row.get("external_social_writes")!=0
        or row.get("money_spent_vnd")!=0
        or (state=="verified")!=(row.get("verified_at") is not None)):
        raise RuntimeError("agent_cycle_result_readback_mismatch")
    return {"status":state,"result_code":payload["result_code"],
            "action":payload["selected_action"],"verified":state=="verified",
            "candidates":payload["candidates"],
            "external_social_writes":0,"money_spent_vnd":0}


def run(db=None, *, now=None, refresh_feed=None, refresh_followers=None):
    db=db or Database()
    now=aware_time(now or datetime.now(timezone.utc))
    key=run_key(now)
    claimed=db.request("POST",TABLE,params={"on_conflict":"run_key"},
        payload={"run_key":key,"brand_key":BRAND,"status":"running",
                 "result_code":"started"},
        prefer="resolution=ignore-duplicates,return=representation")
    if not isinstance(claimed,list):
        raise RuntimeError("agent_cycle_claim_unavailable")
    if not claimed:
        return {"status":"already_processed","run_key":key,
                "external_social_writes":0}
    followers,feed,history=read_sources(db)
    proposals=build_proposals(followers,feed,history,now)
    decision=choose(proposals,now=now,permissions=PERMISSIONS)
    selected=decision["selected"]
    if not selected:
        result={"status":"no_safe_action","result_code":"no_eligible_verified_action",
                "candidates":len(proposals),"observed_at":None}
        return {**save_and_verify(db,key,None,result,now),"run_key":key}

    action=selected["action"]
    evidence=next(x for x in proposals if x["action"]==action)
    result={"status":"blocked","result_code":"provider_or_permission_blocked",
            "candidates":len(proposals),"observed_at":evidence["observed_at"]}
    fn=(refresh_feed or official_posts) if action=="refresh_official_meta_feed" else (
        refresh_followers or official_followers)
    try:
        provider=fn(db=db,now=now)
        succeeded=(provider.get("state")=="verified_official_feed" and
                   type(provider.get("verified_count")) is int and provider["verified_count"]>0) if action=="refresh_official_meta_feed" else (
            provider.get("status")=="saved_official_snapshot" and
            type(provider.get("followers")) is int)
        if succeeded:
            refreshed=db.request("GET",
                "/enna_official_threads_observations" if action=="refresh_official_meta_feed"
                else "/enna_threads_account_snapshots",
                params={
                    "select":("source,last_observed_at" if action=="refresh_official_meta_feed"
                              else "source,measured_at,followers"),
                    "brand_key":"eq."+BRAND,
                    "order":("last_observed_at.desc" if action=="refresh_official_meta_feed"
                             else "measured_at.desc"),"limit":"5"})
            recent=_recent_official(refreshed,
                "last_observed_at" if action=="refresh_official_meta_feed"
                else "measured_at",now)
            if recent and now-timedelta(minutes=5)<=recent<=now+timedelta(minutes=2):
                result.update({"status":"verified","result_code":"official_provider_readback_verified",
                     "verified_at":now.isoformat()})
            else:
                result.update({"status":"unverified","result_code":"provider_saved_but_source_readback_missing"})
        else:
            code=provider.get("state") or provider.get("status")
            known={"awaiting_official_oauth","missing_threads_manage_insights_or_unavailable",
                   "provider_error","provider_unavailable","identity_mismatch",
                   "meta_owner_oauth_unavailable","identity_unavailable","empty_observation_sample",
                   "readback_unverified","readback_unavailable","missing_provider_metric",
                   "snapshot_write_unverified"}
            result["result_code"]=code if code in known else "provider_result_unverified"
    except (ValueError,TypeError,KeyError,RuntimeError):
        result.update({"status":"unverified","result_code":"provider_attempt_unverified"})
    return {**save_and_verify(db,key,selected,result,now),"run_key":key}


if __name__=="__main__":
    try:
        result=run()
        print("ENNA_AGENT_GOAL_CYCLE="+json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        print("ENNA_AGENT_GOAL_CYCLE="+json.dumps({
            "status":"unavailable","error_class":type(exc).__name__,
            "external_social_writes":0},ensure_ascii=False))
        raise SystemExit(1)
