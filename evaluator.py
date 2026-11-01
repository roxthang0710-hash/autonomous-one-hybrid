"""Deterministic proposal screening. Score measures completeness, NOT profit probability."""
from difflib import SequenceMatcher
import re

VERSION = "rubric-v1.1"


def _normalize(value):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(value).lower())).strip()


def _text(proposal, name):
    return str(proposal.get(name) or "").strip()


def evaluate_proposal(proposal, sources, recent_titles=()):
    """Produce explainable 0–100 screening score; never authorize an action."""
    metric = _text(proposal, "success_metric")
    experiment = _text(proposal, "zero_cost_experiment")
    title = _text(proposal, "title")
    risks = proposal.get("risks")
    risks = risks if isinstance(risks, list) else []
    sources = sources if isinstance(sources, list) else []

    budget = proposal.get("estimated_cost_vnd")
    zero_cost_points = 20 if type(budget) is int and budget == 0 else 0
    metric_points = 20 if len(metric) >= 30 and re.search(r"\d", metric) else (
        10 if len(metric) >= 25 else 0
    )
    source_points = min(20, 5 * len(sources))
    plan_points = 20 if len(experiment) >= 80 else (10 if len(experiment) >= 40 else 0)
    risk_points = 20 if len(risks) >= 2 else (10 if len(risks) == 1 else 0)

    rubric = {
        "zero_cost": {"points": zero_cost_points, "maximum": 20,
                      "note": "No money is authorized by this score."},
        "measurable_goal": {"points": metric_points, "maximum": 20,
                            "note": "A numerical target is only a proposed metric."},
        "public_research_leads": {"points": source_points, "maximum": 20,
                                  "note": "Public search hits do not prove demand."},
        "experiment_detail": {"points": plan_points, "maximum": 20,
                              "note": "Length is a proxy for specificity."},
        "risk_disclosure": {"points": risk_points, "maximum": 20,
                            "note": "Count of stated risks, not their severity."},
    }
    base = sum(item["points"] for item in rubric.values())
    duplicate = False
    normalized_title = _normalize(title)
    if normalized_title and len(normalized_title) >= 12:
        duplicate = any(
            SequenceMatcher(None, normalized_title, _normalize(old)).ratio() >= 0.84
            for old in list(recent_titles)[:40]
            if old
        )
    score = max(0, base - (35 if duplicate else 0))
    verdict = "review" if score >= 70 else ("revise" if score >= 40 else "hold")
    findings = [
        "Điểm chỉ đánh giá mức độ hoàn chỉnh của đề xuất; không dự báo doanh thu.",
        "Dữ liệu tìm kiếm công khai chưa xác minh được nhu cầu khách hàng.",
        "Mọi hoạt động bên ngoài hoặc chi tiền đều cần chủ sở hữu phê duyệt.",
    ]
    if duplicate:
        findings.append("Ý tưởng tương tự một đề xuất trước đây, cần làm rõ điểm mới.")
    if not sources:
        findings.append("Chưa có tín hiệu nghiên cứu từ nguồn công khai.")
    if metric_points < 20:
        findings.append("Cần mục tiêu đo lường định lượng cụ thể hơn.")
    if zero_cost_points != 20:
        findings.append("Không đáp ứng điều kiện thử nghiệm 0 đồng.")
    return {
        "score": score, "verdict": verdict, "rubric": rubric,
        "findings": findings, "evidence_status": "unvalidated",
        "evaluator_version": VERSION,
    }
