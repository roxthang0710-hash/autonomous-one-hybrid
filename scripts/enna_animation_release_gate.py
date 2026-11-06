"""Enna Animation release-quality gate: fail closed for unverified AI video.

Does not generate video or change provider accounts. Uses actual media probe
facts and owner review, never invented engagement or quality scores.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = BASE / "config" / "enna_animation_flow_first_2026_11_07.json"


def review_episode(metadata: dict, policy: dict) -> dict:
    reasons = []
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be a dict")
    gate = policy["release_gate"]
    production = policy["production"]
    series = policy["series"]
    line = metadata.get("series_id")
    characters = {x["id"]: x for x in series.values()}
    if line not in characters or characters[line]["status"] != "owner_approved":
        reasons.append("unapproved_character_series")
    if metadata.get("reference_canva_asset") != characters.get(line, {}).get("reference_canva_asset"):
        reasons.append("reference_character_mismatch")

    provider = metadata.get("generator")
    if provider != production["default_generator"] and not metadata.get("fallback_explicitly_owner_approved", False):
        reasons.append("fallback_generator_not_approved")

    if not metadata.get("mp4_file_verified", False):
        reasons.append("no_verified_mp4")
    w, h = metadata.get("width"), metadata.get("height")
    if not (isinstance(w, int) and isinstance(h, int) and w >= gate["min_width"] and h >= gate["min_height"]
            and abs(w / h - 9 / 16) <= .006):
        reasons.append("not_portrait_9_16")
    d = metadata.get("duration_seconds")
    if not isinstance(d, (float, int)) or not gate["min_duration_seconds"] <= d <= gate["max_duration_seconds"]:
        reasons.append("bad_short_duration")

    for key, reason in (
        ("character_consistency_verified", "character_drift_unchecked"),
        ("articulated_motion_verified", "slide_motion_or_unverified"),
        ("story_setup_action_payoff_verified", "missing_comedic_payoff"),
        ("rights_verified", "rights_unverified"),
        ("original_copy_check_passed", "copy_check_missing"),
        ("owner_visual_approved", "owner_visual_approval_missing"),
    ):
        if metadata.get(key) is not True:
            reasons.append(reason)
    if production["free_only"] and metadata.get("new_spend", 0) != 0:
        reasons.append("unauthorized_spend")
    if metadata.get("published", False):
        reasons.append("already_published_or_unsafe_status")

    return {"release_ready": not reasons, "reasons": reasons, "production_stage": "approved_asset" if not reasons else "draft_only"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Enna animated episode for owner-review-only archive")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    report = review_episode(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.policy.read_text(encoding="utf-8")),
    )
    print(json.dumps(report, ensure_ascii=False))
    if not report["release_ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
