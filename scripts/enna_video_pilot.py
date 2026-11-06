"""Enna short-video preproduction: validated, original, review-only drafts.

Input: config/enna_video_revenue_pilot_2026_11_06.json.
Output: episode-specific shotlist JSON + Vietnamese SRT + privacy-safe metrics schema.
No external services, video claims, social writes, affiliate links or spending.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT = PROJECT / "config/enna_video_revenue_pilot_2026_11_06.json"
SAFE_ID = re.compile(r"^[a-z][a-z0-9_]{2,35}$")
ALLOWED_MODES = {"scene_doodle", "clean_chat", "practical_ui_tip"}
REQUIRED_GATES = (
    "manual_visual_review", "verify_readable_vietnamese",
    "brand_reference_comparison", "original_sound_or_license",
    "verify_actual_post_id_after_publish", "any_paid_link_requires_full_separate_approval"
)


def validate_plan(document):
    if not isinstance(document, dict) or document.get("owner_approval_required") is not True:
        raise ValueError("owner-review-gate-missing")
    if document.get("commercial_links_allowed") is not False:
        raise ValueError("commercial-links-must-remain-disabled")
    if document.get("phase") != "research_original_video_drafts_only":
        raise ValueError("not-a-draft-only-plan")
    release = document.get("release_gates")
    if not isinstance(release, dict) or any(release.get(k) is not True for k in REQUIRED_GATES):
        raise ValueError("mandatory-video-release-gate-missing")
    spec = document.get("video_spec") or {}
    if (spec.get("width"), spec.get("height")) != (1080, 1920):
        raise ValueError("video-must-be-vertical-9x16")
    if spec.get("sound") != "none_original_silent_preview":
        raise ValueError("unapproved-audio")
    episodes = document.get("experiments")
    if not isinstance(episodes, list) or len(episodes) != 3:
        raise ValueError("exactly-three-original-pilots-required")
    identifiers = set()
    for episode in episodes:
        key = episode.get("id")
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or key in identifiers:
            raise ValueError("invalid-or-duplicate-episode-id")
        identifiers.add(key)
        if (episode.get("mode") not in ALLOWED_MODES or
            episode.get("commercial") is not False or
            not episode.get("title") or not episode.get("hook") or
            not episode.get("cta")):
            raise ValueError("bad-creative-or-commercial-gate")
        beats = episode.get("beats")
        if not isinstance(beats, list) or not 3 <= len(beats) <= 9:
            raise ValueError("bad-shot-count")
        expected = 0
        for beat in beats:
            start, end, text = beat.get("start"), beat.get("end"), beat.get("text")
            if (type(start) is not int or type(end) is not int or start != expected
                or not start < end <= 20 or not isinstance(text, str)
                or not text.strip() or len(text) > 150
                or "http://" in text.lower() or "https://" in text.lower()):
                raise ValueError("non-contiguous-or-unsafe-shot")
            expected = end
        if expected != spec.get("video_duration_seconds"):
            raise ValueError("incomplete-timeline")
    return episodes


def timestamp(seconds):
    return f"00:00:{seconds:02d},000"


def episode_files(episode):
    scenes = []
    subtitles = []
    for index, beat in enumerate(episode["beats"], 1):
        scenes.append({
            "shot": index, "seconds": [beat["start"], beat["end"]],
            "visual_mode": episode["mode"],
            "original_required": True,
            "onscreen_text": beat["text"],
            "publish_approved": False
        })
        subtitles.extend((str(index),
                          f'{timestamp(beat["start"])} --> {timestamp(beat["end"])}',
                          beat["text"].replace("\n", " "), ""))
    srt = "\n".join(subtitles).strip() + "\n"
    manifest = {
        "episode_id": episode["id"],
        "title": episode["title"],
        "target_platforms": episode["target_platforms"],
        "hook": episode["hook"],
        "cta": episode["cta"],
        "scenes": scenes,
        "status": "storyboard_requires_visual_review",
        "actual_video_rendered": False,
        "actually_published": False,
        "commercial": False,
        "soundtrack_source": "none",
        "approved_assets": [],
        "metrics_to_capture": [
            "published_post_id", "published_time", "views_24h",
            "average_watch_time_if_supported", "shares_if_supported",
            "saves_if_supported", "profile_visits_time_window",
            "verified_link_visits", "verified_orders"
        ],
    }
    return manifest, srt


def export(plan_path=DEFAULT, out_dir=None):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    episodes = validate_plan(plan)
    out_dir = Path(out_dir or PROJECT / "video-pilot-drafts")
    out_dir.mkdir(parents=True, exist_ok=True)
    for episode in episodes:
        manifest, srt = episode_files(episode)
        (out_dir / f'{episode["id"]}.storyboard.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / f'{episode["id"]}.srt').write_text(srt, encoding="utf-8")
    result = {
        "episodes": len(episodes), "storyboards": len(episodes),
        "video_files": 0, "social_posts": 0,
        "affiliate_links": 0, "requires_visual_approval": True,
        "out": str(out_dir)
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, default=PROJECT / "video-pilot-drafts")
    args = parser.parse_args()
    print(json.dumps(export(args.plan, args.output), ensure_ascii=False))
