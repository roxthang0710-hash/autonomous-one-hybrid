"""Official read-only Threads account follower snapshots for Enna.
No profile editing, public posts or account-metric guessing.
"""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
from agent import Database
from threads.brand import BRAND_KEY
from threads.credentials import load_credentials, verify_identity
from threads.publisher import thread_request

VN=ZoneInfo("Asia/Ho_Chi_Minh")

def parse_follower_count(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list):
        return None
    for item in payload["data"]:
        if not isinstance(item,dict) or item.get("name")!="followers_count":
            continue
        total=item.get("total_value")
        val=total.get("value") if isinstance(total,dict) else None
        if val is None and isinstance(item.get("values"),list) and item["values"]:
            value=item["values"][0]
            val=value.get("value") if isinstance(value,dict) else None
        if type(val) is int and val>=0:
            return val
    return None


def collect(db=None, *, now=None, load=load_credentials, request=thread_request):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    credential=load(db,refresh=False)
    if not credential:
        return {"status":"awaiting_official_oauth","followers":None}
    token,expected=credential
    # Identity check is read-only. Do not call authenticate(), which may
    # activate a publishing channel, from an insights-only worker.
    username,uid=verify_identity(token,expected,read=request)
    if username != "dohay_dilam" or not uid:
        return {"status":"identity_mismatch","followers":None}
    try:
        result=request("GET","/me/threads_insights",token,params={
            "metric":"followers_count"})
    except requests.HTTPError as exc:
        http=exc.response.status_code if exc.response is not None else None
        if http in (400,403):
            return {"status":"missing_threads_manage_insights_or_unavailable","followers":None}
        return {"status":"provider_error","followers":None}
    except requests.RequestException:
        return {"status":"provider_unavailable","followers":None}
    followers=parse_follower_count(result)
    if followers is None:
        return {"status":"missing_provider_metric","followers":None}
    day=now.astimezone(VN).date().isoformat()
    rows=db.request("POST","/enna_threads_account_snapshots",params={
        "on_conflict":"brand_key,local_day"},payload={
        "brand_key":BRAND_KEY,"local_day":day,"followers":followers,
        "measured_at":now.isoformat(),"source":"meta_official"
    },prefer="resolution=merge-duplicates,return=representation")
    if not rows:
        return {"status":"snapshot_write_unverified","followers":None}
    return {"status":"saved_official_snapshot","local_day":day,
            "followers":followers}


if __name__=="__main__":
    print(json.dumps(collect(),ensure_ascii=False))
