"""Curated Vietnam publisher programs; terms must be rechecked by an owner.

These are program leads, not contracts or earning claims. Only official sources.
"""
from datetime import date

SOURCES_CHECKED = date(2026, 11, 2)

# Niche is a research hypothesis, NOT a product recommendation.
NICHES = (
    "phụ kiện du lịch thiết thực cho người đi công tác",
    "dụng cụ sắp xếp hành lý cho chuyến đi ngắn",
    "đồ dùng hỗ trợ làm việc và học tập tại nhà",
    "phụ kiện tối ưu góc làm việc nhỏ",
)

PROGRAM_WEIGHTS = {
    # The numbers below measure research accessibility only, not conversion.
    "shopee_koc": {"organic_fit": 20, "eligibility_friction": 6},
    "accesstrade": {"organic_fit": 16, "eligibility_friction": 9},
    "tiktok_shop": {"organic_fit": 16, "eligibility_friction": 16},
}


def score_lead(program):
    """Research priority, not profit potential. Bound to 0..100."""
    code = program.get("code", "")
    weights = PROGRAM_WEIGHTS.get(code, {"organic_fit": 0, "eligibility_friction": 30})
    score = 35 + weights["organic_fit"] - weights["eligibility_friction"]
    if program.get("evidence_url", "").startswith("https://"):
        score += 10
    if program.get("official_url", "").startswith("https://"):
        score += 10
    if program.get("review_status") == "active":
        score += 10
    # Verified commissions are deliberately not a factor until independently substantiated.
    return max(0, min(100, score))


def select_lead(programs, prior_runs):
    """Pick supported program with fewest finished successful runs."""
    counts = {row["code"]: 0 for row in programs if row.get("code") in PROGRAM_WEIGHTS}
    for run in prior_runs:
        code = run.get("program_code")
        if code in counts and run.get("status") == "success":
            counts[code] += 1
    choices = [
        p for p in programs
        if p.get("code") in counts and p.get("review_status") != "inactive"
    ]
    if not choices:
        raise RuntimeError("No active public affiliate program leads")
    return min(choices, key=lambda p: (counts[p["code"]], -score_lead(p), p["code"]))


def choose_niche(prior_runs, niches=NICHES):
    """Cycle through hypotheses; no implicit product or commission data."""
    count = len([row for row in prior_runs if row.get("status") == "success"])
    return niches[count % len(niches)]
