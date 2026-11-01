"""Private-data-safe GitHub Actions summary; full records stay in Supabase."""
import os
from agent import Database

PROJECT_EDITOR = "https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor"
RUNS_LINK = "https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions"


def report(db):
    rows = db.request("GET", "/agent_review_dashboard", params={
        "select": "approval_status,review_score,verdict,experiments,observed_signals",
        "order": "created_at.desc", "limit": "200",
    })
    runs = db.request("GET", "/agent_runs", params={
        "select": "status", "order": "started_at.desc", "limit": "50",
    })
    pending = sum(1 for x in rows if x["approval_status"] == "pending")
    approved = sum(1 for x in rows if x["approval_status"] == "approved")
    completed = sum(1 for x in runs if x["status"] == "success")
    failed = sum(1 for x in runs if x["status"] == "failed")
    under_review = sum(1 for x in rows if x["verdict"] == "review")
    documented_experiments = sum(int(x["experiments"]) for x in rows)
    signals = sum(int(x["observed_signals"]) for x in rows)
    # Do not include titles, business plans or financial details in a public repo summary.
    return (
        "## Autonomous One — Báo cáo sau chu kỳ\n\n"
        "| Chỉ số | Kết quả |\n|---|---:|\n"
        f"| Đề xuất đang lưu | {len(rows)} |\n"
        f"| Chờ chủ sở hữu duyệt | {pending} |\n"
        f"| Đã duyệt về mặt ý tưởng | {approved} |\n"
        f"| Đủ tiêu chí để xem xét (không phải dự báo lợi nhuận) | {under_review} |\n"
        f"| Thử nghiệm có dữ liệu | {documented_experiments} |\n"
        f"| Tín hiệu thực tế do chủ sở hữu ghi nhận | {signals} |\n"
        f"| Chu kỳ thành công (50 gần nhất) | {completed} |\n"
        f"| Chu kỳ lỗi (50 gần nhất) | {failed} |\n\n"
        f"Để xem nội dung và quyết định, mở [Supabase Table Editor]({PROJECT_EDITOR}) "
        "và chọn bảng `agent_review_dashboard`, `agent_proposals`, "
        "`agent_evaluations` hoặc `agent_experiments`.\n\n"
        "**Quyền hạn:** Các đề xuất không kích hoạt hành động công khai, giao dịch "
        "hay thay đổi mã nguồn. Các chỉ số trên không chứng minh có doanh thu.\n"
    )


if __name__ == "__main__":
    content = report(Database())
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)
