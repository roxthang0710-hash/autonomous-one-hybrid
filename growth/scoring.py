"""Brand relevance and safety scoring. Not a viral or revenue prediction."""
import re
import unicodedata
from datetime import datetime, timezone

PILLARS = {
    "work": ("van phong", "cong so", "ban lam viec", "nang suat",
             "work from home", "remote work", "office",
             "laptop", "ban phim", "quan ly thoi gian", "ghi chu", "hoc tap"),
    "travel": ("du lich", "cong tac", "hanh ly", "vali", "may bay", "di chuyen",
               "hanh trinh", "khach san", "travel", "trip", "backpack", "packing"),
    "organize": ("sap xep", "don dep", "gon gang", "ngan nap", "toi gian",
                 "thiet bi", "do dung", "tui dung", "phu kien", "organize",
                 "organizer", "storage", "workspace", "desk setup"),
}
# Reject hot arguments about health, politics, religion, tragedy, celebrity
# harassment and finance. Not an exhaustive language moderation system.
HIGH_RISK = (
    "bau cu", "chinh phu", "thu tuong", "chu tich nuoc", "chinh tri",
    "chien tranh", "tu sat", "tu vong", "tai nan", "tham hoa", "bao luc",
    "benh", "dich benh", "thuoc chua", "giam can", "ca cuoc", "xo so",
    "forex", "crypto", "tien ao", "tin don", "scandal", "boi nho",
    "tinh duc", "khung bo", "ton giao", "ngoai tinh",
    "di lam viec o nuoc ngoai", "lao dong di nuoc ngoai",
    "xuat khau lao dong", "phap ly", "tranh chap",
)


def normalize(value):
    raw = str(value or "").casefold().replace("đ", "d")
    value = unicodedata.normalize("NFKD", raw)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value)).strip()


def classify(headline, published_at=None, now=None):
    """Conservative filter for actual headline/body, not merely feed search query."""
    text = normalize(headline)
    if any(phrase in text for phrase in HIGH_RISK):
        return {"state": "rejected", "score": 0, "niche": "none",
                "risk_flags": ["sensitive_or_controversial"], "notes": ["Not brand-safe"]}
    matches = {name: sum(phrase in text for phrase in terms)
               for name, terms in PILLARS.items()}
    primary = max(matches, key=matches.get)
    hits = matches[primary]
    if hits == 0:
        return {"state": "rejected", "score": 0, "niche": "none",
                "risk_flags": [], "notes": ["Not relevant to editorial pillars"]}
    score = min(90, 43 + min(hits, 3) * 13)
    notes = ["Source headline is a research lead, not an established claim."]
    now = now or datetime.now(timezone.utc)
    if published_at is None:
        score -= 10
        notes.append("No source publication date; freshness unverified.")
    else:
        if published_at.tzinfo is None:
            return {"state": "rejected", "score": 0, "niche": primary,
                    "risk_flags": ["naive_date"], "notes": ["Unverifiable timestamp"]}
        age = (now - published_at).total_seconds()
        if age > 96 * 3600 or age < -6 * 3600:
            return {"state": "expired", "score": 0, "niche": primary,
                    "risk_flags": ["not_fresh"], "notes": ["Source outside 96-hour window"]}
        if age <= 24 * 3600:
            score += 5
    score = max(0, min(100, score))
    return {"state": "candidate" if score >= 50 else "rejected",
            "score": score, "niche": primary, "risk_flags": [], "notes": notes}
