"""Autonomous One brand voice for legitimate public Threads conversations.

Owner-approved: warm Vietnamese, quick wit and *moderate* youth slang.
The brand speaks as a brand, not as a fake customer or a fabricated user.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from growth.scoring import normalize, classify

VOICE_RULES = (
    "Bạn đang viết thay mặt tài khoản thương hiệu công khai Đồ Hay Đi Làm. "
    "Giọng trẻ trung, thông minh, vui tự nhiên; có thể dùng một tiếng lóng "
    "phổ biến hợp ngữ cảnh như 'vibe', 'toang', 'rén', 'xỉu', 'xin vía', "
    "'hết cứu', 'đỉnh', nhưng KHÔNG nhét từ lóng chỉ để bắt trend. "
    "Một câu đùa duyên tối đa, có ý kiến cụ thể hoặc mẹo hữu ích. "
    "Không mở đầu bằng 'Đồ Hay Đi Làm xin chào', không làm thơ rập khuôn, "
    "không 'tấu hài' quá trớn, không spam emoji hoặc hashtag. "
    "Viết bình luận liên quan CHÍNH XÁC đến nội dung bài gốc, "
    "thường 80–250 ký tự, tối đa 380, có thể dùng 0–1 emoji. "
    "Không yêu cầu người khác theo dõi, bấm thích, chia sẻ, nhắn tin riêng "
    "hoặc truy cập link. Không công kích chủ bài, đùa cợt nhạy cảm, "
    "kéo bè phái, gây tranh cãi để tăng reach, hay giả làm người đã mua "
    "hoặc trải nghiệm sản phẩm. "
    "Không tự nhận là đồng nghiệp, khách hàng hay cá nhân ngoài đời. "
    "Nếu chủ đề không đủ liên quan hoặc thiếu dữ kiện, tốt nhất không bình luận."
)

SLANG_TERMS = (
    "toang", "rén", "xỉu", "hết cứu", "xin vía", "vibe", "đỉnh",
    "căng", "lụi tim", "cứu", "khét", "cơm áo gạo tiền",
)
DISALLOWED_REPLY_PATTERN = (
    "theo dõi", "follow mình", "ghé trang", "inbox", "ib mình",
    "link bio", "bấm vào", "truy cập", "chia sẻ giúp", "tag bạn",
    "đỉnh quá bạn ơi", "hay quá ạ", "mình bán", "bên mình bán",
)
# Not an endorsement of slang in every reply.
MAX_EMOJI_CHARS = 2


def suitable_reply(reply, original, prior_texts=()):
    """Deterministic second-stage checks; model output is NEVER a safe default."""
    if not isinstance(reply, str) or not isinstance(original, str):
        return False
    text = reply.strip()
    if not 60 <= len(text) <= 380:
        return False
    folded = normalize(text)
    original_norm = normalize(original)
    if not original_norm or classify(original)["state"] != "candidate":
        return False
    if any(normalize(x) in folded for x in DISALLOWED_REPLY_PATTERN):
        return False
    if text.count("#") or text.count("@") > 0 or text.count("!") > 2:
        return False
    # Emoji are optional; don't penalize Unicode Vietnamese letters.
    emoticons = sum(1 for ch in text if ord(ch) >= 0x1F000)
    if emoticons > MAX_EMOJI_CHARS:
        return False
    if sum(1 for slang in SLANG_TERMS if normalize(slang) in folded) > 2:
        return False
    original_terms = set(original_norm.split()) - {
        "cu", "co", "nhung", "voi", "mot", "ban", "minh", "cua", "cho",
        "la", "va", "thi", "duoc", "chua", "cach", "lam", "neu", "khong",
        "khi", "trong", "noi", "nay", "do", "nhieu", "hay", "se", "ve",
    }
    reply_terms = set(folded.split())
    # A reply should refer to a concrete topic from the actual post, not
    # a generic one-line joke that works below every trending thread.
    if len(original_terms & reply_terms) < 2:
        return False
    for previous in prior_texts:
        if (isinstance(previous, str) and
            SequenceMatcher(None, folded, normalize(previous)).ratio() > .82):
            return False
    return True
