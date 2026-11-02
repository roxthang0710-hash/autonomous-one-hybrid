"""Read-only storytelling-vs-other Threads insight analysis.

Never attributes follower growth causally to a single post. Missing insights
remain missing, not zero. Uses only our own verified Meta post IDs and metrics.
"""
import json
from datetime import datetime, timedelta, timezone
from statistics import median
from agent import Database

def classify_format(text):
    return "story" if isinstance(text,str) and "Tình huống giả định" in text else "other"

def assess(rows, metrics, *, now=None):
    now = now or datetime.now(timezone.utc)
    latest = {}
    for item in metrics:
        if not isinstance(item,dict) or not item.get("post_id"):
            continue
        at = item.get("collected_at")
        try:
            ts = datetime.fromisoformat(str(at).replace("Z","+00:00"))
            if not ts.tzinfo: continue
        except (ValueError,TypeError): continue
        key=item["post_id"]
        if key not in latest or ts > latest[key][0]:
            latest[key]=(ts,item)
    seen={"story":[],"other":[]}
    for p in rows:
        if p.get("status")!="posted" or not p.get("platform_post_id"):
            continue
        try:
            ts=datetime.fromisoformat(str(p.get("published_at")).replace("Z","+00:00"))
            if not ts.tzinfo or not timedelta(hours=24) <= now-ts:
                continue
        except (TypeError,ValueError): continue
        matching=latest.get(p.get("id"))
        if not matching: continue
        m=matching[1]
        views=m.get("views"); replies=m.get("replies")
        if type(views) is not int or type(replies) is not int or views<=0 or replies<0:
            continue
        seen[classify_format(p.get("text_content"))].append((views,replies))

    output={"status":"insufficient_evidence",
            "group_stats":{group:{"measured_posts":len(vals),
                "median_views":median([v for v,_ in vals]) if vals else None,
                "replies_per_1000_views":round(1000*sum(r for _,r in vals)/sum(v for v,_ in vals),2) if vals else None
            } for group,vals in seen.items()},
            "note":"Xu hướng tương tác quan sát được; không chứng minh nội dung gây tăng follower."}
    if min(len(seen["story"]),len(seen["other"]))>=3:
        output["status"]="comparison_ready"
        sr=output["group_stats"]["story"]["replies_per_1000_views"]
        other=output["group_stats"]["other"]["replies_per_1000_views"]
        output["higher_reply_density"]="story" if sr>other else "other" if other>sr else "tie"
    return output

def snapshot(db=None, *, now=None):
    db=db or Database()
    posts=db.request("GET","/threads_posts",params={
        "select":"id,status,text_content,platform_post_id,published_at",
        "order":"published_at.desc","limit":"120",
    })
    metrics=db.request("GET","/threads_metrics",params={
        "select":"post_id,views,replies,collected_at",
        "order":"collected_at.desc","limit":"350",
    })
    return assess(posts,metrics,now=now)

if __name__=="__main__":
    try:
        print("Enna storytelling evidence:",json.dumps(snapshot(),ensure_ascii=False))
    except Exception as exc:
        print("Enna storytelling evidence:",json.dumps({
            "status":"source_unavailable","error_class":type(exc).__name__}))
