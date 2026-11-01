"""Honest metrics readout: no optimization on missing or tiny samples."""
from statistics import median

MIN_DAYS = 7


def analyze(rows):
    """Rows come ONLY from provider-reported metrics; never invent impressions."""
    if len(rows) < MIN_DAYS:
        return {
            "status": "insufficient_observations",
            "observed_days": len(rows),
            "recommendation": "Giữ lịch hiện tại; chưa có đủ dữ liệu thực để đổi chiến lược.",
        }
    valid = [r for r in rows if
             isinstance(r.get("post_views"), int) and
             isinstance(r.get("interactions"), int) and
             isinstance(r.get("published_posts"), int)]
    if len(valid) < MIN_DAYS or sum(r["published_posts"] for r in valid) < 5:
        return {
            "status": "insufficient_observations",
            "observed_days": len(valid),
            "recommendation": "Chưa có ít nhất 5 bài đăng với dữ liệu đo lường.",
        }
    view_days = [r["post_views"] for r in valid]
    views = sum(view_days)
    interactions = sum(r["interactions"] for r in valid)
    followers = [r["followers"] for r in valid if isinstance(r.get("followers"), int)]
    # Ratio is observed only, not conversion, sales or platform algorithm score.
    return {
        "status": "baseline_available",
        "observed_days": len(valid),
        "published_posts": sum(r["published_posts"] for r in valid),
        "median_daily_views": median(view_days),
        "interaction_per_view": round(interactions / views, 4) if views else None,
        "first_last_followers": [followers[0], followers[-1]]
                                if len(followers) >= 2 else None,
        "recommendation": (
            "Thử nghiệm từng thay đổi nhỏ về chủ đề hoặc giờ đăng; "
            "so sánh ít nhất 7 ngày và không coi tương tác là doanh thu."
        ),
    }
