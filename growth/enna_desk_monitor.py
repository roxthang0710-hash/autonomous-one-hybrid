"""Enna Desk autonomous read-only observability: signed-in owner alerts.

No Meta actions, publishing, replies, finance actions or OAuth changes.
Never invent counts. Every alert includes its observed evidence and next action.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from agent import Database

VN = ZoneInfo("Asia/Ho_Chi_Minh")
BRAND_GOAL = 1000


def build_notifications(owners, growth, posts, media, events, now=None):
    now = now or datetime.now(timezone.utc)
    local_today = now.astimezone(VN).date()
    day = local_today.isoformat()
    relevant = []
    verified = []
    for entry in growth:
        try:
            measured = datetime.fromisoformat(str(entry["measured_on"])).date()
            followers = entry.get("followers")
            if type(followers) is int and followers >= 0 and measured <= local_today:
                verified.append((measured, followers))
        except (ValueError, TypeError, KeyError):
            continue
    if verified:
        measured, followers = max(verified)
        gap = max(0, BRAND_GOAL - followers)
        days_old = (local_today - measured).days
        if days_old > 1:
            relevant.append(("growth", "warning", "Chỉ số follower đã quá hạn",
                f"Mốc gần nhất: {followers} follower ngày {measured.isoformat()} ({days_old} ngày trước).",
                "Đồng bộ Metricool hoặc Meta trước khi quyết định tăng số bài; không dùng con số cũ làm hiện tại."))
        if gap > 0 and local_today <= datetime(2026, 11, 7).date():
            relevant.append(("growth", "critical", "Mục tiêu 1.000 follower có nguy cơ không đạt",
                f"Mốc xác minh gần nhất: {followers}; còn thiếu {gap} follower trước ngày 07/11.",
                "Ưu tiên bài có giá trị lưu/chia sẻ, kiểm chứng Topic và đo follower mới. Không spam hay mua follow."))
    else:
        relevant.append(("growth", "warning", "Enna chưa nhận được số follower xác minh",
            "Chưa có snapshot hợp lệ trong cơ sở dữ liệu Metricool.",
            "Kiểm tra bộ đồng bộ Metricool và Meta. Không tự ghi 0 follower khi thiếu dữ liệu."))
    posted_topic = sum(p.get("status") == "posted" and bool(p.get("topic_tag_requested")) for p in posts)
    planned_topic = sum(p.get("status") == "queued" and bool(p.get("topic_tag_planned")) for p in posts)
    if planned_topic and not posted_topic:
        relevant.append(("topic", "warning", "Topic chính thức chưa có bằng chứng xuất bản",
            f"Có {planned_topic} bài lên kế hoạch Topic; không tìm thấy bài đã xác nhận Topic trong mẫu.",
            "Kiểm tra Meta ID và permalink của bài đã đăng. Hashtag trong caption không đồng nghĩa Topic liên kết."))
    ready_video = any(m.get("media_type") in ("original_video", "video")
                      and m.get("status") == "ready" and m.get("source_url") for m in media)
    if not ready_video:
        relevant.append(("media", "info", "Chưa có video hoàn chỉnh trong thư viện",
            "Kho media chỉ ghi nhận video nghiên cứu hoặc kịch bản, chưa có tệp video ready.",
            "Ưu tiên hoàn thiện 1 video nguyên bản ngắn; duyệt quyền sử dụng trước khi đăng."))
    recent_errors = []
    for e in events:
        try:
            at = datetime.fromisoformat(str(e.get("occurred_at")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if at.tzinfo and now - at < timedelta(hours=24) and e.get("status") == "failed":
            recent_errors.append(str(e.get("code") or "unknown")[:60])
    if recent_errors:
        relevant.append(("system", "warning", "Có workflow gần đây thất bại",
            "Mã lỗi quan sát được: " + ", ".join(dict.fromkeys(recent_errors[:3])) + ".",
            "Xem log GitHub Actions để xác định bước hỏng; tránh tự lặp lại Meta POST chưa chắc kết quả."))
    return [
        {"owner_id": owner["user_id"],
         "source_key": "2026-11-05-v2:" + day + ":" + category + ":" + title[:24],
         "category": category, "severity": severity, "title": title,
         "details": detail, "suggested_action": action}
        for owner in owners
        for category, severity, title, detail, action in relevant
    ]


def collect(db):
    owners = db.request("GET", "/enna_desk_owners", params={"select": "user_id", "limit": "5"})
    if not owners:
        return "no_owners"
    growth = db.request("GET", "/growth_metricool_daily", params={
        "select": "measured_on,followers", "order": "measured_on.desc", "limit": "30"})
    posts = db.request("GET", "/threads_posts", params={
        "select": "status,topic_tag_requested,topic_tag_planned",
        "order": "scheduled_at.desc", "limit": "120"})
    media = db.request("GET", "/enna_media_ideas", params={
        "select": "media_type,status,source_url", "order": "created_at.desc", "limit": "80"})
    events = db.request("GET", "/enna_activity_events", params={
        "select": "status,code,occurred_at", "order": "occurred_at.desc", "limit": "40"})
    alerts = build_notifications(owners, growth, posts, media, events)
    if not alerts:
        return "no_alerts"
    # DB unique key + on_conflict ignore provides deduplication even if runner repeats.
    saved = db.request("POST", "/enna_desk_notifications",
                       params={"on_conflict": "owner_id,source_key"},
                       payload=alerts, prefer="resolution=ignore-duplicates,return=representation")
    return f"alert_candidates={len(alerts)},new={len(saved)}"


if __name__ == "__main__":
    print("Enna proactive alerts:", collect(Database()))
