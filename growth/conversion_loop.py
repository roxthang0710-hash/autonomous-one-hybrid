"""Enna closed-loop follower-growth experiment operator.

Transitions: verified baseline -> one safe content-policy adjustment ->
observed outcome -> retain/revert. Never books or publishes an extra post,
never edits a live profile or replies to strangers, never invents lift.
"""
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from agent import Database
from threads.brand import BRAND_KEY

VN=ZoneInfo("Asia/Ho_Chi_Minh")
PROFILE_VISIT_THRESHOLD=100
BASELINE_DAYS=2
EXPERIMENT_DAYS=2

def clean_days(rows, today):
    found={}
    for r in rows or []:
        try:
            day=date.fromisoformat(str(r.get("measured_on")))
            followers=r.get("followers")
            views=r.get("profile_views")
            new=r.get("new_followers")
            if not (day<today and today-day<=timedelta(days=14) and
                    type(followers) is int and followers>=0 and
                    type(views) is int and views>=0 and
                    type(new) is int):
                continue
            found[day]=(day,followers,views,new)
        except (ValueError,TypeError,AttributeError):
            continue
    return [found[d] for d in sorted(found,reverse=True)]


def select_policy(rows,*,now=None):
    """Tiny-sample exploratory test, not an inference of actual conversion."""
    now=now or datetime.now(timezone.utc)
    today=now.astimezone(VN).date()
    samples=clean_days(rows,today)
    if len(samples)<BASELINE_DAYS or (today-samples[0][0]).days>1:
        return {"status":"insufficient_or_stale","focus":None,"days":len(samples)}
    a,b=samples[:2]
    if (a[0]-b[0]).days>2:
        return {"status":"nonconsecutive_snapshot","focus":None,"days":2}
    profile_views=a[2]+b[2]
    new_followers=a[3]+b[3]
    if profile_views<PROFILE_VISIT_THRESHOLD:
        return {"status":"small_profile_sample","focus":None,"days":2}
    # This is a proxy only: new followers can originate outside profile visits.
    indicator=max(0,new_followers)/profile_views
    return {"status":"ready","focus":"practical_follow_value" if indicator<0.01 else "balanced_recovery",
            "days":2,"latest_day":a[0].isoformat(),"baseline_followers":a[1],
            "baseline_profile_views":profile_views,
            "proxy_new_followers_per_profile_view":round(indicator,5),
            "source":"metricool_verified_aggregate_not_causal",
            "note":"New followers divided by profile views is not a verified conversion rate."}


def measure(sprint, rows, today):
    valid=clean_days(rows,today)
    baseline=date.fromisoformat(sprint["baseline_day"])
    newer=[r for r in valid if r[0]>baseline]
    if len(newer)<2:
        return {"status":"waiting_new_data","days_after_baseline":len(newer)}
    recent=newer[:2]
    views=sum(r[2] for r in recent)
    gains=sum(r[3] for r in recent)
    if views<PROFILE_VISIT_THRESHOLD:
        return {"status":"insufficient_profile_sample","days_after_baseline":len(newer)}
    after=max(0,gains)/views
    baseline_rate=(sprint.get("latest_observation") or {}).get("proxy_new_followers_per_profile_view")
    if type(baseline_rate) not in (int,float):
        return {"status":"no_baseline_proxy"}
    # Exploratory decision only; two days cannot establish causality.
    return {"status":"measured","after_proxy":round(after,5),
            "before_proxy":baseline_rate,"new_followers":gains,
            "profile_views":views,
            "decision":"retain_trial" if after>=baseline_rate and gains>0 else "return_balanced",
            "caveat":"Aggregate association, not evidence that the content-policy change caused follows."}


def measure_official(sprint, snapshots, today):
    """Fallback to same-provider follower counts; never invent profile visits."""
    valid={}
    baseline=date.fromisoformat(str(sprint["baseline_day"]))
    for r in snapshots or []:
        try:
            d=date.fromisoformat(str(r.get("local_day")))
            n=r.get("followers")
            if baseline < d <= today and type(n) is int and n>=0:
                valid[d]=n
        except (ValueError,TypeError,AttributeError):
            continue
    observed=sorted(valid.items())
    if len(observed)<2 or (observed[-1][0]-observed[0][0]).days<2:
        return {"status":"awaiting_two_day_meta_span","provider":"meta_official"}
    delta=observed[-1][1]-observed[0][1]
    return {"status":"measured","source":"meta_official",
        "first_day":observed[0][0].isoformat(),"last_day":observed[-1][0].isoformat(),
        "first_followers":observed[0][1],"last_followers":observed[-1][1],
        "observed_net_change":delta,
        "decision":"retain_trial" if delta>0 else "return_balanced",
        "caveat":"Same-provider follower change only; cannot attribute growth or loss to this trial."}


def notify(db, code, title, detail, action, *,severity="info"):
    owners=db.request("GET","/enna_desk_owners",params={"select":"user_id","limit":"5"})
    if not isinstance(owners,list) or not owners:
        return 0
    rows=[{"owner_id":o["user_id"],"source_key":code,
           "category":"growth","severity":severity,
           "title":title,"details":detail[:800],
           "suggested_action":action[:350]} for o in owners]
    result=db.request("POST","/enna_desk_notifications",
        params={"on_conflict":"owner_id,source_key"},payload=rows,
        prefer="resolution=ignore-duplicates,return=representation")
    return len(result)


def run(db=None,*,now=None):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    today=now.astimezone(VN).date()
    data=db.request("GET","/growth_metricool_daily",params={
        "select":"measured_on,followers,new_followers,profile_views",
        "metricool_brand_id":"eq.7803567",
        "order":"measured_on.desc","limit":"12"})
    if not isinstance(data,list):
        return {"status":"provider_metric_unavailable"}
    active=db.request("GET","/enna_growth_sprints",params={
        "select":"brand_key,sprint_key,focus,status,baseline_day,baseline_followers,latest_observation,evaluation_due,execution_proof",
        "brand_key":"eq."+BRAND_KEY,
        "order":"started_at.desc","limit":"1"})
    if not isinstance(active,list):
        return {"status":"sprint_state_unavailable"}
    if active and active[0]["status"] in ("running","measuring"):
        sprint=active[0]
        if today<date.fromisoformat(sprint["evaluation_due"]):
            return {"status":"experiment_running","sprint_key":sprint["sprint_key"]}
        outcome=measure(sprint,data,today)
        if outcome["status"]!="measured":
            official=db.request("GET","/enna_threads_account_snapshots",params={
                "select":"local_day,followers",
                "brand_key":"eq."+BRAND_KEY,
                "order":"local_day.asc","limit":"14"})
            if isinstance(official,list):
                outcome=measure_official(sprint,official,today)
        if outcome["status"]!="measured":
            # Do not invent an outcome because the provider has no new data.
            return {"status":"outcome_pending","reason":outcome["status"]}
        target="balanced" if outcome["decision"]=="return_balanced" else "practical"
        policy=db.request("GET","/enna_learning_policy",params={
            "select":"preferred_format,version","brand_key":"eq."+BRAND_KEY,"limit":"1"})
        if not isinstance(policy,list) or not policy:
            return {"status":"policy_unavailable"}
        # Policy may be changed by conservative Meta performance evaluator;
        # only revert the particular experimental value we own.
        if target=="balanced" and policy[0]["preferred_format"]=="practical":
            changed=db.request("PATCH","/enna_learning_policy",params={
                "brand_key":"eq."+BRAND_KEY,"preferred_format":"eq.practical",
                "version":"eq."+str(policy[0]["version"])},payload={
                "preferred_format":"balanced","version":policy[0]["version"]+1,
                "applied_at":now.isoformat(),"evidence":{"sprint_key":sprint["sprint_key"],
                     "experiment_outcome":outcome}},prefer="return=representation")
            if not changed:
                return {"status":"policy_changed_concurrently"}
        db.request("PATCH","/enna_growth_sprints",params={
            "brand_key":"eq."+BRAND_KEY,"sprint_key":"eq."+sprint["sprint_key"],
            "status":"in.(running,measuring)"},payload={
            "status":"completed","decision":outcome["decision"],
            "evaluated_on":today.isoformat(),"latest_observation":outcome,
            "updated_at":now.isoformat()},prefer="return=representation")
        notify(db,"sprint-evaluated:"+sprint["sprint_key"],
               "Enna đã đo và đánh giá thử nghiệm",
               "Đã có dữ liệu giai đoạn sau, nhưng không đủ để kết luận quan hệ nhân quả.",
               "Xem số liệu follower và lượt vào hồ sơ; tiếp tục hoặc đổi thử nghiệm dựa trên dữ liệu.",severity="info")
        return {"status":"experiment_evaluated","decision":outcome["decision"]}
    candidate=select_policy(data,now=now)
    if candidate["status"]!="ready":
        return {"status":"not_enough_fresh_metricool_data","reason":candidate["status"]}
    if active and active[0]["status"]=="completed" and (today-date.fromisoformat(active[0]["evaluation_due"])).days<2:
        return {"status":"cooldown"}
    policy=db.request("GET","/enna_learning_policy",params={
        "select":"preferred_format,version","brand_key":"eq."+BRAND_KEY,"limit":"1"})
    if not isinstance(policy,list) or not policy:
        return {"status":"policy_unavailable"}
    desired="practical" if candidate["focus"]=="practical_follow_value" else "balanced"
    sprint_key="follow-value-"+today.isoformat()
    prior=db.request("GET","/enna_growth_sprints",params={
        "select":"sprint_key","brand_key":"eq."+BRAND_KEY,
        "sprint_key":"eq."+sprint_key,"limit":"1"})
    if prior:
        return {"status":"already_started"}
    created=db.request("POST","/enna_growth_sprints",
        params={"on_conflict":"brand_key,sprint_key"},
        payload={"brand_key":BRAND_KEY,"sprint_key":sprint_key,
         "focus":candidate["focus"],"status":"running",
         "baseline_day":candidate["latest_day"],
         "baseline_followers":candidate["baseline_followers"],
         "baseline_profile_views":candidate["baseline_profile_views"],
         "evaluation_due":(today+timedelta(days=EXPERIMENT_DAYS)).isoformat(),
         "latest_observation":candidate,
         "execution_proof":{"policy_target":desired,"policy_applied":False},
         "decision":"awaiting_measurement"},
        prefer="resolution=ignore-duplicates,return=representation")
    if not created:
        return {"status":"already_started"}
    changed=[]
    if policy[0]["preferred_format"]!=desired:
        changed=db.request("PATCH","/enna_learning_policy",params={
            "brand_key":"eq."+BRAND_KEY,
            "version":"eq."+str(policy[0]["version"]),
            "preferred_format":"eq."+policy[0]["preferred_format"]},
            payload={"preferred_format":desired,
                     "version":policy[0]["version"]+1,
                     "applied_at":now.isoformat(),
                     "evidence":{"source":"verified_metricool_sprint",
                      "sprint_key":sprint_key,"baseline":candidate}},
            prefer="return=representation")
    applied=bool(changed) or policy[0]["preferred_format"]==desired
    db.request("PATCH","/enna_growth_sprints",params={
        "brand_key":"eq."+BRAND_KEY,"sprint_key":"eq."+sprint_key},
        payload={"execution_proof":{"policy_target":desired,
            "policy_applied":applied,
            "actual_change":bool(changed),
            "limitation":"Affects future authorized adaptive drafts only; no existing booked post changed"},
            "updated_at":now.isoformat(),
            "status":"running" if applied else "blocked"},
        prefer="return=representation")
    notify(db,"sprint-started:"+sprint_key,
           "Enna bắt đầu thử nghiệm tăng follower có đo lường",
           ("Đã áp dụng ưu tiên mẹo thực dụng cho các bản nháp tự động tiếp theo." if applied
            else "Chưa áp dụng được thay đổi, cần kiểm tra xung đột dữ liệu.")
            +" Đây không phải bằng chứng follower đã tăng.",
           "Ngoài nội dung, cần tối ưu bio/bài ghim trên Threads; quyền sửa hồ sơ chưa được Enna Desk xác minh.",
           severity="warning" if not applied else "info")
    return {"status":"experiment_started" if applied else "policy_conflict",
        "sprint_key":sprint_key,"policy_changed":bool(changed),
        "trial_focus":candidate["focus"],"evaluation_due":(today+timedelta(days=EXPERIMENT_DAYS)).isoformat()}


if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"status":"error","error_class":type(exc).__name__}))
        raise
