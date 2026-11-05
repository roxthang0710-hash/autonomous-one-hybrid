"""Warn owner about high-risk Threads captions before external Metricool booking.

Read-only on Meta and Metricool. Uses the latest stored scheduler copy, not
live provider status; notification does not mean publication has failed.
"""
import json
from datetime import datetime,timedelta,timezone
from agent import Database
from threads.brand import BRAND_KEY

WARN_AT=480
HARD_CAP=500
MAX_ROWS=75

def check(rows,now=None):
    now=now or datetime.now(timezone.utc)
    until=now+timedelta(days=3)
    flagged=[]
    for r in rows or []:
        if r.get("status")!="scheduled_external":continue
        try:
            at=datetime.fromisoformat(str(r.get("scheduled_at")).replace("Z","+00:00"))
        except (ValueError,TypeError,OverflowError):continue
        if at.tzinfo is None or not now-timedelta(hours=12)<=at<=until:continue
        body=r.get("text_content")
        if not isinstance(body,str):continue
        length=len(body)
        if length<WARN_AT:continue
        flagged.append({"id":r["id"],"chars":length,
          "severity":"warning" if length<=HARD_CAP else "critical",
          "due_at":at.isoformat(),
          "code":"caption_close_to_threads_limit" if length<=HARD_CAP else "caption_over_threads_limit"})
    return flagged


def run(db=None,*,now=None):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    rows=db.request("GET","/threads_posts",params={
      "select":"id,status,text_content,scheduled_at",
      "status":"eq.scheduled_external",
      "scheduled_at":"gte."+(now-timedelta(hours=12)).isoformat(),
      "order":"scheduled_at.asc","limit":MAX_ROWS})
    if not isinstance(rows,list):
        return {"state":"scheduler_snapshot_unavailable"}
    risks=check(rows,now=now)
    owners=db.request("GET","/enna_desk_owners",params={
      "select":"user_id","limit":"5"})
    if isinstance(owners,list) and owners:
        messages=[]
        for r in risks:
            for o in owners:
                messages.append({"owner_id":o["user_id"],
                  "source_key":"threads-caption-risk:"+str(r["id"]),
                  "category":"growth",
                  "severity":"warning",
                  "title":"Enna phát hiện bài Threads gần giới hạn ký tự",
                  "details":("Bản sao lịch Metricool ghi nhận một bài dài "+str(r["chars"])+
                    " ký tự; Threads giới hạn 500 ký tự qua API. "
                    "Đây là cảnh báo nguy cơ, KHÔNG phải bằng chứng đã đăng lỗi. "
                    "Mục tiêu nên dưới 450 ký tự để tránh sai khác bộ đếm."),
                  "suggested_action":"Kiểm tra và rút gọn bài trước giờ đăng tại Metricool; đừng tạo bản đăng trùng."})
        if messages:
            db.request("POST","/enna_desk_notifications",params={
               "on_conflict":"owner_id,source_key"},payload=messages,
               prefer="resolution=ignore-duplicates,return=representation")
    return {"state":"checked","risk_count":len(risks),
            "near_limit":sum(x["chars"]<=HARD_CAP for x in risks),
            "over_limit":sum(x["chars"]>HARD_CAP for x in risks),
            "basis":"stored_metricool_snapshot_only",
            "changed_scheduled_posts":False}


if __name__=="__main__":
    try:
        print("Enna Threads caption preflight:",json.dumps(run(),ensure_ascii=False))
    except Exception as exc:
        print("Enna Threads caption preflight unavailable:",type(exc).__name__)
        raise
