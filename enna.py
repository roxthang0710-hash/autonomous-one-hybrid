"""Enna: truthful, read-only operations controller for the existing agent.

Stable infrastructure remains Autonomous One: GitHub repository, database IDs,
Meta account and GitHub Actions trigger names do NOT change with the persona.
Never include access tokens, post content, emails or credentials in logs.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from agent import Database
from growth.report import snapshot as growth_snapshot
from threads.readiness import snapshot as threads_snapshot

AGENT_NAME = "Enna"
BRAND_NAME = "Đồ Hay Đi Làm"
VN = ZoneInfo("Asia/Ho_Chi_Minh")
UNKNOWN_SEARCH = {
    "empty_keyword_results",
    "own_posts_only_possible_app_review",
    "no_relevant_recent_public_posts",
    "source_unavailable",
    "not_authorized",
}


def _instant(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def health(db=None, *, now=None):
    """Read only verified backend facts, never infer followers or earnings."""
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    threads = threads_snapshot(db=db, now=now)
    growth = growth_snapshot(db)
    recent = db.request("GET", "/growth_runs", params={
        "select": "status,started_at,finished_at,source_summary",
        "order": "started_at.desc", "limit": "1",
    })
    latest = recent[0] if recent else {}
    discovery = (latest.get("source_summary") or {}).get("threads")
    started = _instant(latest.get("started_at"))
    lag = (now - started) if started and started <= now else None

    findings = []
    if threads.get("status") != "connected":
        findings.append("threads_connection_needs_attention")
    findings.extend(threads.get("warnings", []))
    if lag is None or lag > timedelta(hours=36):
        findings.append("growth_radar_not_recently_verified")
    if latest.get("status") == "failed":
        findings.append("growth_radar_latest_run_failed")
    if discovery in UNKNOWN_SEARCH:
        findings.append("public_threads_discovery_not_confirmed")

    posting = threads.get("threads_posts", {})
    policy = growth.get("engagement_policy", {})
    result = {
        "agent": AGENT_NAME,
        "brand": BRAND_NAME,
        "state": (
            "attention" if threads.get("status") != "connected" or
            "growth_radar_latest_run_failed" in findings else
            "operating_with_limits" if findings else "operating"
        ),
        "threads": {
            "connected": threads.get("status") == "connected",
            "metricool_reserved": posting.get("scheduled_external", 0),
            "ai_queued": posting.get("queued", 0),
            "ai_confirmed_posted": posting.get("posted", 0),
            "next_ai_day_vn": threads.get("next_queued_local_date"),
        },
        "growth": {
            "last_run_status": latest.get("status") or "unknown",
            "discovery": discovery or "unknown",
            "drafts_needing_review": growth.get("drafts_needing_review", 0),
            "real_insights": growth.get("metricool_performance", {}).get("status")
                             if isinstance(growth.get("metricool_performance"), dict)
                             else "unknown",
        },
        "comments": {
            "owner_opted_in": policy.get("reply_mode") == "owner_authorized",
            "daily_max_vn": policy.get("daily_maximum_vietnam", 3),
            "today_attempts": policy.get("today_attempted", 0),
            "today_confirmed": policy.get("today_confirmed", 0),
        },
        "affiliate": {
            "shopee_approved": (
                threads.get("shopee_affiliate", {}).get("channel_approval")
                == "approved_by_owner_record"
            ),
            "revenue_verified": False,
        },
        "findings": sorted(set(findings)),
        "as_of_vietnam": now.astimezone(VN).isoformat(timespec="minutes"),
    }
    return result


def summary(report):
    """GitHub Markdown summary; content and secrets never enter this report."""
    t, g, c = report["threads"], report["growth"], report["comments"]
    lines = [
        "## Enna — Nhật ký vận hành",
        "",
        "| Chỉ số thực tế | Trạng thái |",
        "|---|---|",
        f"| Sức khỏe | {report['state']} |",
        f"| Threads kết nối | {'Có' if t['connected'] else 'Không'} |",
        f"| Metricool đã đặt lịch | {t['metricool_reserved']} |",
        f"| Bài AI chờ đăng | {t['ai_queued']} |",
        f"| Bài AI đã xác nhận đăng | {t['ai_confirmed_posted']} |",
        f"| Ngày đăng AI tiếp theo (VN) | {t['next_ai_day_vn'] or '—'} |",
        f"| Radar gần nhất | {g['last_run_status']} |",
        f"| Tìm kiếm bài công khai | {g['discovery']} |",
        f"| Bình luận xác nhận hôm nay | {c['today_confirmed']} / {c['daily_max_vn']} |",
        f"| Shopee Affiliate được duyệt | {'Có' if report['affiliate']['shopee_approved'] else 'Chưa xác minh'} |",
        "",
        "Những chỉ số đang lên lịch không phải kết quả đã xuất bản."
        " Quyền OAuth không đồng nghĩa Meta đã duyệt App Review."
        " Chưa có bằng chứng về doanh thu affiliate.",
    ]
    if report["findings"]:
        lines.extend(["", "Vấn đề cần theo dõi: " + ", ".join(report["findings"])])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    state = health()
    print(json.dumps(state, ensure_ascii=False))
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write("\n" + summary(state))
