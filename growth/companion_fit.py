"""Context-first fit for a post explicitly chosen by the Enna owner.

No keyword-based prerequisite: a useful/relevant/clever contribution can fit a
work-and-life brand even without 'công sở', 'Excel' or 'đi làm'. Only enforce
concrete content and safety rules here; Enna's AI may independently decline.
"""
import re
from growth.scoring import normalize, HIGH_RISK

# The existing high-risk categories are kept; user choice does not mean every
# conversation should receive a brand reply.
PRIVATE_PATTERNS = (
    r"https?://|www[.]",
    r"\b\d{9,12}\b",
    r"\b(?:otp|m[aâ]t kh[aẩ]u|c[aă]n c[ướ]c|cmnd|"
    r"s[ốo] t[aà]i kho[aả]n|đ[iị]a ch[ỉi] nh[aà])\b",
)
PROMO_PATTERNS = (
    "nhan tin de nhan qua", "mua ngay", "follow cheo", "trao doi follow",
    "tang follow", "tao tai khoan gia", "kiem tien cap toc",
)
EXPLICIT_HARM = (
    "kieu dam", "bao hanh", "phan biet chung toc", "khoi dau danh nhau",
    "lo thong tin rieng", "tin gia", "tin don", "de doa",
)

# Advisory signals only; not publication criteria.
ANGLE_SIGNALS = {
    "hài hước & đời thường": (
        "hai", "buon cuoi", "tro dua", "troll", "cuoi", "vo tri", "ban be",
        "o nha", "meo", "cho", "thu cung", "an uong", "ca phe",
        "ngu nuong", "le hoi", "di choi", "hen ho", "tinh ban",
    ),
    "góc nhìn & trò chuyện": (
        "cau chuyen", "quan diem", "thoi quen", "trai nghiem", "suy nghi",
        "cam xuc", "dieu minh", "neu ban", "ban nghi", "theo ban",
    ),
    "công cụ & kỹ năng": (
        "excel", "sheets", "cong cu", "phan mem", "meo", "hoc hoi",
        "thu thuat", "ai", "ky nang", "lam viec", "cong so",
    ),
}


def assess_selected(text):
    if not isinstance(text, str):
        return {"state": "rejected", "reason": "missing_text"}
    body = text.strip()
    if not 30 <= len(body) <= 1800:
        return {"state": "rejected", "reason": "insufficient_or_excessive_context"}
    folded = normalize(body)
    if len(folded.split()) < 7:
        return {"state": "rejected", "reason": "too_little_readable_context"}
    if any(re.search(p, body, re.IGNORECASE) for p in PRIVATE_PATTERNS):
        return {"state": "rejected", "reason": "possible_sensitive_or_link"}
    if any(term in folded for term in HIGH_RISK):
        return {"state": "rejected", "reason": "sensitive_or_controversial"}
    if any(term in folded for term in PROMO_PATTERNS + EXPLICIT_HARM):
        return {"state": "rejected", "reason": "spam_or_harm"}
    angles = tuple(name for name, terms in ANGLE_SIGNALS.items()
                   if any(term in folded for term in terms))
    return {
        "state": "candidate",
        "niche": angles[0] if angles else "xu hướng & đời sống",
        "angles": angles or ("ý kiến ngắn & trò chuyện tự nhiên",),
        "risk_flags": [],
        "human_selected": True,
        "viral_metrics_verified": False,
    }
