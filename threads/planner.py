"""Organic Threads content calendar: 14 honest discussion posts. No affiliate links."""
import hashlib
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from threads.brand import BRAND_KEY, CONTENT_PILLARS

VN = ZoneInfo("Asia/Ho_Chi_Minh")

# Original editorial prompts: NO fabricated ownership, purchasing, product testing
# or unverifiable affiliate claims. Written without external URLs.
SEEDS = (
    ("work", "Bàn làm việc càng nhỏ, càng dễ bừa bộn. Nếu chỉ được giữ 5 món trên bàn, bạn sẽ chọn những gì? Mình đang tổng hợp các cách tối ưu góc làm việc để chia sẻ lại."),
    ("conversation", "Một mẹo làm việc tiết kiệm thời gian mà bạn ước mình biết sớm hơn là gì? Có thể là đặt tên tệp, ghi chú cuộc họp hoặc sắp xếp hộp thư."),
    ("travel", "Đi công tác hai ngày thì nên mang vali nhỏ hay balô? Có lẽ không có đáp án chung: còn tùy quần áo, thiết bị và lịch trình. Bạn thường cân nhắc điều gì đầu tiên?"),
    ("organize", "Sắp xếp dây sạc, tai nghe và bộ chuyển đổi trong túi đi làm thế nào để dễ tìm? Chia theo công dụng hay gom vào một túi riêng có khóa kéo?"),
    ("work", "Đôi khi danh sách việc cần làm dài hơn cả thời gian trong ngày. Bạn thích cách chia việc thành nhóm 15 phút hay ưu tiên đúng 3 việc quan trọng nhất?"),
    ("travel", "Checklist trước chuyến công tác ngắn: giấy tờ, lịch hẹn, thuốc cá nhân nếu cần, bộ sạc và đồ dùng thiết yếu. Bạn sẽ thêm gì để tránh quên món quan trọng?"),
    ("conversation", "Điều gì khiến một món đồ văn phòng thực sự đáng giữ lại: sử dụng thường xuyên, tiết kiệm diện tích, dễ sửa chữa hay giúp tập trung? Mỗi người chắc sẽ có tiêu chí khác."),
    ("organize", "Nếu góc làm việc luôn thiếu chỗ, thử phân loại theo tần suất sử dụng trước khi mua thêm hộp đựng. Cách này có hợp với kiểu bàn làm việc của bạn không?"),
    ("travel", "Đóng gói cho chuyến đi ngắn: cuộn quần áo, gấp phẳng hay chia túi? Ba cách có điểm mạnh khác nhau. Bạn thấy cách nào dễ lấy đồ giữa hành trình nhất?"),
    ("work", "Có một câu hỏi hay khi chọn phụ kiện làm việc: nó giải quyết vấn đề nào đang có, hay chỉ làm góc bàn trông đẹp hơn? Bạn ưu tiên công năng hay thẩm mỹ?"),
    ("conversation", "Ai từng phải mang theo quá nhiều dây cáp vì sợ thiếu khi đi làm? Nếu chọn một nguyên tắc để giảm đồ mang theo, bạn sẽ bắt đầu từ đâu?"),
    ("organize", "Một góc bàn gọn không nhất thiết phải mua thêm đồ. Thử bỏ bớt giấy tờ đã hết hạn sử dụng, gom dây và dành một khu vực cho đồ dùng hằng ngày trước đã."),
    ("travel", "Khi đặt chỗ ở cho chuyến công tác, bạn thường để ý bàn làm việc, vị trí ổ điện, độ yên tĩnh hay thời gian di chuyển? Chọn đúng ưu tiên sẽ giúp đỡ phát sinh hơn."),
    ("work", "Lúc đổi nơi làm việc trong ngày, thứ gì thật sự phải mang theo? Gợi ý là thử viết danh sách ngắn rồi rà soát sau một tuần xem món nào chưa từng sử dụng."),
)

FORBIDDEN = (
    r"https?://", r"www\.", r"shopee\.vn", r"shope\.ee", r"bit\.ly",
    r"(?i)\baffiliate\b", r"(?i)\bhoa hồng\b", r"(?i)\bmua ngay\b",
    r"(?i)\bnhắn tin riêng\b",
    r"(?i)mình đã (mua|dùng|thử|trải nghiệm)",
    r"(?i)tôi đã (mua|dùng|thử|trải nghiệm)",
)


def check_post(text):
    """Disallow links, spam patterns and unverifiable product-use testimonials."""
    if not isinstance(text, str) or not 60 <= len(text.strip()) <= 500:
        return ["invalid_length"]
    issues = []
    for pattern in FORBIDDEN:
        if re.search(pattern, text):
            issues.append("blocked_pattern")
            break
    if text.count("#") > 2 or text.count("@") > 2:
        issues.append("hashtag_or_mention_spam")
    return issues


def scheduled_start(now=None):
    now = now or datetime.now(VN)
    local = now.astimezone(VN)
    target = datetime.combine(local.date(), time(9, 30), tzinfo=VN)
    if local >= target:
        target += timedelta(days=1)
    return target


def planned_seed_rows(channel_id, start=None):
    """Deterministic, idempotent content keys; posts are never directly published."""
    start = start or scheduled_start()
    rows = []
    for index, (pillar, text) in enumerate(SEEDS):
        if pillar not in CONTENT_PILLARS:
            raise ValueError("Unsupported content pillar")
        issues = check_post(text)
        if issues:
            raise ValueError("Editorial seed failed quality gate: " + str(issues))
        key = hashlib.sha256(
            (BRAND_KEY + "\n" + pillar + "\n" + text).encode("utf-8")
        ).hexdigest()
        rows.append({
            "channel_id": channel_id,
            "content_key": key,
            "text_content": text,
            "pillar": pillar,
            "status": "queued",
            "content_type": "editorial",
            "risk_flags": [],
            "created_by": "seed",
            "scheduled_at": (start + timedelta(days=index)).isoformat(),
        })
    return rows
