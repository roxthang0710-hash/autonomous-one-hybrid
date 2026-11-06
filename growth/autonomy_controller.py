"""A1 Enna autonomy controller: choose, act once when safe, verify.

Scope: self-refresh already-authorized, read-only Meta follower evidence when stale,
then rank last-known provider incidents and create private, deduplicated owner alerts.
Never publishes, deletes, purchases, changes OAuth/permissions, or retries writes.
The Metricool API is NOT available to this unattended GitHub worker; schedule
states come from Supabase snapshots and are ALWAYS labeled last-known.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

import requests
from agent import Database
from growth.account_followers import collect as collect_followers

BRAND = "do_hay_di_lam"
STALE_FOLLOWERS = timedelta(hours=12)
STALE_PROVIDER = timedelta(hours=24)
VALID_UUID = re.compile(r"^-?[0-9]{5,22}$")


def aware_time(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp without timezone")
    return parsed.astimezone(timezone.utc)


def fresh_official_snapshot(rows, now, max_age=STALE_FOLLOWERS):
    """No fake 0, only valid verified Meta-origin follower evidence."""
    for row in rows or []:
        try:
            at = aware_time(row["measured_at"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if (row.get("source") == "meta_official"
            and type(row.get("followers")) is int
            and row["followers"] >= 0
            and timedelta(seconds=-90) <= now-at <= max_age):
            return {"followers": row["followers"], "at": at}
    return None


def inspect_provider(rows, now):
    """Prioritized incident list; cached scheduler statuses are not live proof."""
    if not isinstance(rows, list):
        raise RuntimeError("provider_snapshot_unavailable")
    incidents = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider = row.get("provider")
        uuid = str(row.get("metricool_uuid") or "")
        if provider not in {"facebook", "instagram"} or not VALID_UUID.fullmatch(uuid):
            continue
        try:
            due = aware_time(row["scheduled_at"])
            observed = aware_time(row["checked_at"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if due < now - timedelta(days=3) or due > now + timedelta(days=3):
            continue
        age = now - observed
        state = row.get("provider_status")
        if state == "ERROR":
            code, priority, severity = "provider_error", 100, "critical"
            summary = "Bản ghi nội bộ báo ERROR, cần kiểm tra Metricool trực tiếp."
            action = "Đối soát trạng thái và bài thật trên Metricool; không tự đăng lại hoặc thay lịch khi kết quả chưa chắc chắn."
        elif state == "PENDING" and due < now - timedelta(minutes=30):
            code, priority, severity = "overdue_unverified", 95, "critical"
            summary = "Đã qua giờ hẹn nhưng bản ghi nội bộ còn PENDING; chưa xác minh bài đã đăng."
            action = "Đọc Metricool và permalink thực để đối soát; không tự xuất bản lần hai."
        elif state == "PENDING" and age > STALE_PROVIDER:
            code, priority, severity = "schedule_snapshot_stale", 70, "warning"
            summary = "Bản ghi lịch nội bộ cũ hơn 24 giờ, không có xác nhận trực tiếp từ Metricool."
            action = "Đồng bộ Metricool qua kết nối được cấp phép trước khi sửa bài hoặc quyết định tăng lịch."
        elif state == "PENDING" and provider == "instagram" and not row.get("has_media"):
            code, priority, severity = "instagram_media_missing", 85, "critical"
            summary = "Bản ghi Instagram chưa có media cần thiết để xuất bản."
            action = "Chuẩn bị hình hoặc video có quyền sử dụng và duyệt chất lượng trước giờ đăng."
        else:
            continue
        incidents.append({
            "code": code, "priority": priority, "severity": severity,
            "category": "publisher", "key": f"autonomy-v1:{code}:{provider}:{uuid}",
            "title": "Enna: " + {
                "provider_error": "lỗi lịch đăng cần đối soát",
                "overdue_unverified": "bài qua giờ chưa xác minh",
                "schedule_snapshot_stale": "lịch đăng nội bộ quá hạn",
                "instagram_media_missing": "bài Instagram thiếu media"
            }[code],
            "details": (f"Kênh {provider}, giờ hẹn {due.isoformat()}. "
                        f"{summary} Bằng chứng chỉ từ Supabase, "
                        "KHÔNG phải dữ liệu Metricool trực tiếp."),
            "suggested_action": action,
            "due": due.isoformat(),
        })
    incidents.sort(key=lambda x: (-x["priority"], x["due"], x["key"]))
    return incidents


def run(db=None, *, now=None, refresh=collect_followers):
    db = db or Database()
    now = aware_time(now or datetime.now(timezone.utc))
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")

    def snapshots():
        return db.request("GET", "/enna_threads_account_snapshots", params={
            "select": "followers,source,measured_at,local_day",
            "brand_key": "eq." + BRAND,
            "order": "measured_at.desc", "limit": "5",
        })

    initial = snapshots()
    if not isinstance(initial, list):
        raise RuntimeError("official_followers_source_unavailable")
    official = fresh_official_snapshot(initial, now)
    follower_action = "already_fresh"
    if official is None:
        # This one bounded read can actually repair stale evidence, without
        # contacting any publish endpoint or modifying account permissions.
        try:
            attempt = refresh(db=db, now=now)
            status = attempt.get("status") if isinstance(attempt, dict) else None
        except (requests.RequestException, RuntimeError, ValueError, TypeError, KeyError):
            status = "provider_unavailable"
        if status == "saved_official_snapshot":
            after = snapshots()
            if not isinstance(after, list):
                raise RuntimeError("snapshot_verification_source_unavailable")
            verified = fresh_official_snapshot(after, now)
            if verified and verified["at"] >= now - timedelta(minutes=5):
                official = verified
                follower_action = "verified_refresh"
            else:
                follower_action = "refresh_not_verified"
        else:
            follower_action = "blocked_" + (status if status in {
                "awaiting_official_oauth", "identity_mismatch",
                "missing_threads_manage_insights_or_unavailable",
                "provider_error", "provider_unavailable", "missing_provider_metric",
                "snapshot_write_unverified"
            } else "source_unavailable")

    rows = db.request("GET", "/enna_multichannel_posts", params={
        "select": "provider,metricool_uuid,scheduled_at,provider_status,checked_at,has_media",
        "brand_key": "eq." + BRAND, "order": "scheduled_at.asc", "limit": "150",
    })
    incidents = inspect_provider(rows, now)
    if follower_action.startswith("blocked_") or follower_action == "refresh_not_verified":
        incidents.append({
            "code": "official_followers_stale", "priority": 80, "severity": "warning",
            "category": "growth", "key": "autonomy-v1:official_followers_stale",
            "title": "Enna: thiếu số follower Meta mới",
            "details": ("Dữ liệu Meta Insights đã quá hạn hoặc chưa có. "
                        "Enna đã tự thử cập nhật đúng một lần nhưng chưa xác minh được "
                        "snapshot mới; không tự suy đoán follower = 0."),
            "suggested_action": ("Kiểm tra quyền Threads Insights và trạng thái OAuth chủ tài khoản; "
                                 "không cấp token công khai hoặc tăng bài do thiếu dữ liệu."),
            "due": now.isoformat(),
        })
    incidents.sort(key=lambda x: (-x["priority"], x["due"], x["key"]))
    selected = incidents[:3]

    # Alerts belong to the authorized owner; not a public Issues feed.
    notices_written = 0
    if selected:
        owners = db.request("GET", "/enna_desk_owners", params={
            "select": "user_id", "limit": "5",
        })
        if not isinstance(owners, list):
            raise RuntimeError("owner_registry_unavailable")
        if not owners:
            return {"status": "blocked_no_owner", "follower_action": follower_action,
                    "incidents": len(incidents), "selected_codes": [x["code"] for x in selected],
                    "notices_written": 0, "source": "supabase_last_known",
                    "external_posts_created": 0}
        notices = [
            {"owner_id": owner["user_id"], "source_key": issue["key"],
             "category": issue["category"], "severity": issue["severity"],
             "title": issue["title"], "details": issue["details"],
             "suggested_action": issue["suggested_action"]}
            for owner in owners for issue in selected
        ]
        stored = db.request("POST", "/enna_desk_notifications",
            params={"on_conflict": "owner_id,source_key"}, payload=notices,
            prefer="resolution=ignore-duplicates,return=representation")
        if not isinstance(stored, list):
            raise RuntimeError("incident_persistence_unverified")
        notices_written = len(stored)

    return {
        "status": "triaged" if selected else "no_incidents",
        "follower_action": follower_action,
        "official_follower_evidence": bool(official),
        "incidents": len(incidents),
        "selected_codes": [x["code"] for x in selected],
        "notices_written": notices_written,
        "source": "supabase_last_known",
        "external_posts_created": 0,
        "metadata_only": True,
    }


if __name__ == "__main__":
    # No raw response/errors (could contain secrets) ever leave this worker.
    try:
        print("ENNA_AUTONOMY_RESULT="+json.dumps(run(), ensure_ascii=False))
    except Exception as exc:
        print("ENNA_AUTONOMY_RESULT="+json.dumps({
            "status": "controller_unavailable",
            "error_class": type(exc).__name__, "external_posts_created": 0
        }, ensure_ascii=False))
        raise SystemExit(1)
