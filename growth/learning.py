"""Enna evidence loop: choose the next safe, useful action from VERIFIED records.

Read-only. Does not publish, buy, change schedules or infer profit from reach.
The public GitHub Actions summary only receives fixed, non-sensitive labels.
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

from growth.optimizer import analyze


def _valid_link(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlparse(value.strip())
        return url.scheme == "https" and bool(url.hostname) and not url.username
    except ValueError:
        return False


def _rows(db, table, columns, order, limit=100):
    value = db.request("GET", "/" + table, params={
        "select": columns, "order": order, "limit": str(limit),
    })
    if not isinstance(value, list):
        raise ValueError("Expected list response")
    return [r for r in value if isinstance(r, dict)]


def decide(evidence, *, threads_connected=True, search_confirmed=False, now=None):
    """Pure policy engine: prioritize blockers before experiments.

    Confidence is NEVER a guessed success probability.
    """
    now = now or datetime.now(timezone.utc)
    local_day = now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    # Only complete, recent local days qualify as a performance baseline.
    # Do not learn from today's partial counters or historic/stale snapshots.
    metric_rows = []
    for row in evidence.get("metricool", []):
        try:
            measured = date.fromisoformat(str(row.get("measured_on", "")))
            if local_day - timedelta(days=30) <= measured < local_day:
                metric_rows.append(row)
        except (ValueError, TypeError):
            continue
    metric = analyze(list(reversed(metric_rows)))
    affiliate_programs = evidence.get("programs", [])
    affiliate_drafts = evidence.get("affiliate_drafts", [])
    commissions = evidence.get("commissions", [])
    growth_drafts = evidence.get("growth_drafts", [])
    thread_posts = evidence.get("posts", [])
    actual_experiments = evidence.get("experiments", [])

    active = sum(p.get("review_status") == "active" for p in affiliate_programs)
    pending_affiliate = sum(x.get("review_status") == "pending" for x in affiliate_drafts)
    pending_growth = sum(x.get("status") == "needs_review" for x in growth_drafts)
    posted = sum(x.get("status") == "posted" for x in thread_posts)
    queued = sum(x.get("status") == "queued" for x in thread_posts)
    confirmed_commission = sum(
        max(0, r["confirmed_commission_vnd"])
        for r in commissions
        if isinstance(r.get("confirmed_commission_vnd"), int)
        and type(r["confirmed_commission_vnd"]) is int
        and r.get("provenance") == "provider_export"
        and _valid_link(r.get("evidence_url"))
    )
    # Owner-reported receipts / provider CSVs are not proof that a payout
    # reached a bank. We only describe this as supported commission evidence.
    unverified_commission_entries = sum(
        isinstance(r.get("confirmed_commission_vnd"), int)
        and r["confirmed_commission_vnd"] > 0
        and not (r.get("provenance") == "provider_export" and
                 _valid_link(r.get("evidence_url")))
        for r in commissions
    )
    observed_experiments = sum(
        x.get("status") in ("running", "completed", "stopped")
        for x in actual_experiments
    )

    actions = []
    def add(code, priority, label, detail, owner_required=False):
        actions.append({
            "code": code, "priority": priority, "label": label,
            "detail": detail, "owner_required": owner_required,
        })

    if not threads_connected:
        add("threads_auth", 100, "Kiểm tra kết nối Threads",
            "Khôi phục cấp quyền chính thức; không thử đăng bằng đường vòng.", True)
    if metric["status"] != "baseline_available":
        add("metrics_baseline", 95, "Bổ sung dữ liệu hiệu quả có nguồn",
            "Cần tối thiểu 7 ngày đo và 5 bài đã xuất bản; hiện không đủ "
            "mẫu để tự đổi chiến lược.", True)
    else:
        add("controlled_test", 82, "Thử một giả thuyết nội dung có đối chứng",
            "Chỉ đổi một yếu tố (chủ đề HOẶC giờ đăng), đo ít nhất 7 ngày; "
            "không lấy tương tác làm doanh thu.", False)
    if not active:
        add("affiliate_approval", 93, "Xác minh quyền tham gia Affiliate",
            "Chưa có chương trình được xác nhận active; không tạo liên kết "
            "hoa hồng hay khẳng định có thu nhập.", True)
    elif pending_affiliate:
        add("affiliate_review", 84, "Thẩm định đề xuất Affiliate",
            "Kiểm tra chứng cứ sản phẩm, điều khoản hoa hồng và kênh được "
            "phép trước bất kỳ nội dung thương mại nào.", True)
    if unverified_commission_entries:
        add("commission_evidence", 90, "Đối soát bản ghi hoa hồng",
            "Có dòng hoa hồng thiếu chứng từ xuất từ nhà cung cấp; "
            "chưa tính là hoa hồng có căn cứ.", True)
    if not search_confirmed:
        add("meta_search_review", 88, "Kiểm tra quyền tìm bài Threads công khai",
            "Tra cứu trạng thái Meta App Review; tiếp tục nguồn RSS hợp lệ, "
            "không cào giao diện để vượt hạn chế.", True)
    if pending_growth:
        add("draft_review", 70, "Rà soát bản nháp nghiên cứu",
            "Chỉ duyệt nội dung còn hạn, xác minh nguồn và giá trị cho người đọc.", True)
    if queued and not posted:
        add("publication_evidence", 65, "Đợi và xác nhận bài đăng thực",
            "Bài chờ trong hàng đợi không phải bài đã đăng; chỉ đo hiệu quả "
            "khi có ID và số liệu nền tảng.", False)
    if observed_experiments == 0:
        add("zero_cost_validation", 62, "Thiết kế thử nghiệm không chi phí",
            "Đặt giả thuyết, chỉ số đầu ra và điều kiện dừng; cần chủ sở hữu "
            "duyệt trước khi tiếp xúc khách hàng hoặc công khai.", True)

    actions.sort(key=lambda x: (-x["priority"], x["code"]))
    return {
        "phase": "evidence_learning" if metric["status"] == "baseline_available"
                 else "evidence_collection",
        "metric_status": metric["status"],
        "metric_days": metric.get("observed_days", 0),
        "posts_confirmed": posted,
        "affiliate_active_programs": active,
        "affiliate_drafts_pending": pending_affiliate,
        "growth_drafts_pending": pending_growth,
        "commission_provider_evidenced_vnd": confirmed_commission,
        "commission_needs_verification": unverified_commission_entries,
        "real_experiments_started": observed_experiments,
        "earnings_verified_as_paid": False,
        "next_actions": actions[:4],
    }


def snapshot(db, *, threads_connected=True, search_confirmed=False, now=None):
    """Reads only allowlisted columns; do not return private drafts or URLs."""
    sources = {
        "metricool": ("growth_metricool_daily",
                     "measured_on,followers,post_views,interactions,published_posts",
                     "measured_on.desc", 30),
        "programs": ("affiliate_programs", "review_status", "verified_on.desc", 30),
        "affiliate_drafts": ("affiliate_opportunities",
                             "review_status,publishing_status", "created_at.desc", 100),
        "commissions": ("affiliate_metrics",
                        "confirmed_commission_vnd,evidence_url,provenance",
                        "created_at.desc", 100),
        "growth_drafts": ("growth_opportunities",
                          "status,expires_at", "created_at.desc", 100),
        "posts": ("threads_posts", "status", "created_at.desc", 200),
        "experiments": ("agent_experiments", "status", "created_at.desc", 100),
    }
    evidence, failed = {}, []
    for name, (table, cols, order, limit) in sources.items():
        try:
            evidence[name] = _rows(db, table, cols, order, limit)
        except (ValueError, TypeError, KeyError, OSError, RuntimeError):
            evidence[name] = []
            failed.append(name)
        except Exception:
            # Some HTTP clients raise specialized request errors. Never
            # print a raw exception: it can contain credentials or paths.
            evidence[name] = []
            failed.append(name)

    result = decide(evidence, threads_connected=threads_connected,
                    search_confirmed=search_confirmed, now=now)
    if failed:
        result["status"] = "partial_source_unavailable"
        result["unavailable_sources"] = failed
        # Never present missing rows as measured zero.
        result["commission_provider_evidenced_vnd"] = None if "commissions" in failed else result["commission_provider_evidenced_vnd"]
        result["metric_status"] = "source_unavailable" if "metricool" in failed else result["metric_status"]
        result["next_actions"].insert(0, {
            "code": "repair_evidence_feed", "priority": 110,
            "label": "Kiểm tra nguồn dữ liệu",
            "detail": "Một hoặc nhiều nguồn đo lường chưa đọc được; tạm dừng tối ưu.",
            "owner_required": True,
        })
        result["next_actions"] = result["next_actions"][:4]
    else:
        result["status"] = "ok"
    return result
