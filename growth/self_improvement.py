"""Enna controlled editorial self-improvement: evidence, decisions, rollback.

Never edits source code, model weights, permissions or existing Metricool posts.
Only official Meta-verified published posts qualify for strategy changes.
"""
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from agent import Database
from growth.story_insights import assess

BRAND = "do_hay_di_lam"
COOLDOWN = timedelta(hours=48)
MIN_POSTS = 3
ADVANTAGE = 1.35


def decide(measurement, current="balanced", *, now=None, last_changed=None):
    now = now or datetime.now(timezone.utc)
    groups = measurement.get("group_stats") or {}
    s, p = groups.get("story") or {}, groups.get("other") or {}
    sample = {"story_posts":s.get("measured_posts",0),
              "practical_posts":p.get("measured_posts",0),
              "story_replies_per_1000":s.get("replies_per_1000_views"),
              "practical_replies_per_1000":p.get("replies_per_1000_views"),
              "story_median_views":s.get("median_views"),
              "practical_median_views":p.get("median_views")}
    if (measurement.get("status")!="comparison_ready"
        or sample["story_posts"]<MIN_POSTS or sample["practical_posts"]<MIN_POSTS):
        return "insufficient_evidence", current, sample
    if last_changed:
        try:
            t=datetime.fromisoformat(str(last_changed).replace("Z","+00:00"))
            if t.tzinfo is None or now-t<COOLDOWN:
                return "hold",current,{**sample,"reason":"cooldown"}
        except (ValueError,TypeError,OverflowError):
            return "hold",current,{**sample,"reason":"invalid_timestamp"}
    sv,pv=sample["story_median_views"],sample["practical_median_views"]
    sr,pr=sample["story_replies_per_1000"],sample["practical_replies_per_1000"]
    if any(type(x) not in (int,float) or x<0 for x in (sv,pv,sr,pr)) or not (sv and pv):
        return "insufficient_evidence",current,sample
    story=sr>=max(.5,pr*ADVANTAGE) and sv>=pv*.75
    practical=pr>=max(.5,sr*ADVANTAGE) and pv>=sv*.75
    if story==practical:
        return "hold",current,{**sample,"reason":"mixed_evidence"}
    winning="story" if story else "practical"
    if current==winning:
        return "hold",current,{**sample,"reason":"no_change"}
    if current!="balanced":
        return "rollback_balanced","balanced",{**sample,"reason":"reversal"}
    return ("promote_story" if story else "promote_practical"),winning,sample


def run(db=None, *, now=None):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    day=now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    current_rows=db.request("GET","/enna_learning_policy",params={
        "select":"preferred_format,applied_at,version",
        "brand_key":"eq."+BRAND,"limit":"1"})
    if not isinstance(current_rows,list) or not current_rows:
        return "policy_unavailable"
    policy=current_rows[0]; current=policy["preferred_format"]
    previous=db.request("GET","/enna_learning_decisions",params={
        "select":"decision","brand_key":"eq."+BRAND,
        "evaluated_on":"eq."+day,"limit":"1"})
    if previous: return "already_evaluated_today"
    posts=db.request("GET","/threads_posts",params={
        "select":"id,status,text_content,platform_post_id,published_at",
        "status":"eq.posted","order":"published_at.desc","limit":"120"})
    metrics=db.request("GET","/threads_metrics",params={
        "select":"post_id,views,replies,collected_at",
        "order":"collected_at.desc","limit":"350"})
    if not isinstance(posts,list) or not isinstance(metrics,list):
        return "source_unavailable"
    result=assess(posts,metrics,now=now)
    action,next_style,evidence=decide(result,current,now=now,
                                     last_changed=policy.get("applied_at"))
    saved=db.request("POST","/enna_learning_decisions",
        params={"on_conflict":"brand_key,evaluated_on"},
        payload={"brand_key":BRAND,"evaluated_on":day,
                 "evaluated_at":now.isoformat(),"decision":action,
                 "reason":evidence.get("reason") or result.get("note",""),
                 "evidence":evidence},
        prefer="resolution=ignore-duplicates,return=representation")
    if not saved:
        return "already_evaluated_today"
    if current==next_style:
        return action
    changed=db.request("PATCH","/enna_learning_policy",
        params={"brand_key":"eq."+BRAND,
                "preferred_format":"eq."+current,
                "version":"eq."+str(policy.get("version",1))},
        payload={"preferred_format":next_style,
                 "version":int(policy.get("version",1))+1,
                 "applied_at":now.isoformat(),"evidence":evidence},
        prefer="return=representation")
    return action if changed else "policy_changed_concurrently"


if __name__=="__main__":
    try:
        print("Enna controlled learning:",json.dumps({"result":run()},ensure_ascii=False))
    except Exception as e:
        print("Enna controlled learning:",json.dumps({
            "result":"source_unavailable","error_class":type(e).__name__}))
