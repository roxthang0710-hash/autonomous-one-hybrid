"""Read-only monitor for Enna photo-first Metricool rollout.

Supabase stores the *last known Metricool state*, not real-time publication.
A due PENDING post remains unverified; no Meta or Metricool POST is ever sent.
"""
import json
from datetime import datetime, timedelta, timezone
from agent import Database

BRAND = "do_hay_di_lam"
ACCEPTED = ("PENDING", "POSTED", "ERROR", "FAILED", "UNKNOWN")

def parse_date(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Datetime must include a timezone")
    return parsed

def inspect(rows, *, now=None):
    now = now or datetime.now(timezone.utc)
    output = []
    for row in rows:
        try:
            scheduled = parse_date(row["scheduled_at"])
            status = row["provider_status"]
            media = row["media_keys"]
            count = row["media_count"]
            network = row["platform"]
            identifier = row["metricool_uuid"]
        except (KeyError, ValueError, TypeError):
            continue
        if status == "POSTED" and row.get("verified_publication_id") and row.get("published_at"):
            outcome = "verified_published"
        elif status in ("ERROR", "FAILED"):
            outcome = "provider_error_not_retried"
        elif status not in ACCEPTED or not isinstance(media, list) or len(media)!=count:
            outcome = "invalid_snapshot"
        elif status == "PENDING" and scheduled + timedelta(minutes=90) < now:
            outcome = "due_not_verified"
        elif status == "PENDING":
            outcome = "pending_scheduled_only"
        else:
            outcome = "not_verified"
        output.append({"provider":network,"uuid":identifier,"due":scheduled.isoformat(),
                       "format":row.get("format_key"),"media_count":count,"outcome":outcome})
    return output

def run(db=None, *, now=None):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    data = db.request("GET","/enna_visual_rollouts",params={
      "select":"platform,metricool_uuid,scheduled_at,format_key,media_keys,media_count,provider_status,verified_publication_id,published_at",
      "brand_key":"eq."+BRAND,"order":"scheduled_at.asc","limit":"100"
    })
    if not isinstance(data,list):
        raise RuntimeError("Visual rollout ledger unavailable")
    results = inspect(data,now=now)
    alertable = [r for r in results if r["outcome"] in ("due_not_verified","provider_error_not_retried","invalid_snapshot")]
    if alertable:
        owners=db.request("GET","/enna_desk_owners",params={"select":"user_id","limit":"5"})
        if isinstance(owners,list) and owners:
            alerts=[]
            for owner in owners:
                for item in alertable[:8]:
                    alerts.append({
                      "owner_id":owner["user_id"],
                      "source_key":"visual-v2:"+item["uuid"]+":"+item["outcome"],
                      "category":"media","severity":"warning",
                      "title":"Enna Visual: bài chưa xác minh",
                      "details":"Kênh "+item["provider"]+", giờ dự kiến "+item["due"]+
                        ", dạng "+str(item["format"])+". Trạng thái "+item["outcome"]+
                        " dựa trên bản ghi nội bộ, không phải xác nhận xuất bản trực tiếp.",
                      "suggested_action":"Đối chiếu bản ghi Metricool và bài thực trên kênh; không tự đăng lại hoặc tính là đã xuất bản."
                    })
            db.request("POST","/enna_desk_notifications",
                params={"on_conflict":"owner_id,source_key"},
                payload=alerts,prefer="resolution=ignore-duplicates,return=representation")
    return {"rollout_slots":len(results),"pending":sum(x["outcome"]=="pending_scheduled_only" for x in results),
            "verified_published":sum(x["outcome"]=="verified_published" for x in results),
            "attention":len(alertable),"source":"stored_metricool_confirmation_not_live",
            "no_external_social_actions":True}

if __name__=="__main__":
    print("Enna visual rollout:",json.dumps(run(),ensure_ascii=False))
