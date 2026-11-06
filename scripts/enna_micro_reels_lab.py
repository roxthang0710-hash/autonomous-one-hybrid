"""E5: original 6–10s workplace micro-Reel storyboard and evidence lab.

This DOES NOT generate video, claim viewing the reference Reel, call paid
models, or publish to any social network. It validates short-form production
plans and optionally evaluates OWN Instagram Reel metrics after publication.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
DEFAULT=PROJECT/"config/enna_micro_reels_lab_2026_11_06.json"
ID=re.compile(r"^[a-z][a-z0-9_]{4,48}$")
FORBIDDEN=("http://","https://","www.","@threesingsters","#viral","#fyp")
METRIC_NAMES=("views","reach","shares","likes","comments","saves","avg_watch_seconds","retention_percent")


def validate(plan):
    """Reject unclear source attribution, brand risk or a too-long storyboard."""
    if not isinstance(plan,dict) or plan.get("phase")!="research_original_micro_reel_prototypes_no_render_or_publish":
        raise ValueError("wrong_plan_phase")
    source=plan.get("reference") or {}
    if (source.get("video_playback_verified") is not False
        or source.get("duration_verified") is not False
        or source.get("shots_verified") is not False
        or source.get("no_copying_original_scenes_or_audio") is not True):
        raise ValueError("reference_is_not_frame_by_frame_verified")
    spec=plan.get("production_spec") or {}
    if ((spec.get("width"),spec.get("height"),spec.get("fps"))!=(1080,1920,30)
         or spec.get("aspect_ratio")!="9:16"
         or spec.get("intro_logo") is not False
         or spec.get("outro_logo") is not False):
        raise ValueError("wrong_vertical_micro_video_format")
    release=plan.get("release_gates") or {}
    if (any(release.get(k) is not True for k in (
       "owned_or_licensed_assets","original_story_and_prop",
       "human_visual_humor_review","audio_rights_verified",
       "confirm_actual_mp4_before_publication","keep_social_post_manual_approval"
    )) or release.get("disable_commercial_links") is not True):
        raise ValueError("unsafe_release_gates")
    status=plan.get("status") or {}
    if (status.get("mp4_rendered") is not False or
        status.get("published") is not False or
        status.get("claim_of_viral_probability") is not False):
        raise ValueError("unverified_media_completion_claim")
    clips=plan.get("variants")
    if not isinstance(clips,list) or len(clips)!=3:
        raise ValueError("exactly_three_production_prototypes")
    seen=set()
    for clip in clips:
        key=clip.get("id")
        if not isinstance(key,str) or not ID.fullmatch(key) or key in seen:
            raise ValueError("duplicate_or_invalid_id")
        seen.add(key)
        d=clip.get("duration_ms")
        if type(d) is not int or not 6000<=d<=10000:
            raise ValueError("unsupported_short_duration")
        if clip.get("performers",9)>2 or clip.get("locations",9)!=1:
            raise ValueError("too_many_locations_or_performers")
        if clip.get("follow_cta")!="none_in_video":
            raise ValueError("no_interrupting_follow_cta")
        if not clip.get("ending_loop") or len(clip["ending_loop"])<20:
            raise ValueError("missing_loop_plan")
        caption=clip.get("caption")
        if not isinstance(caption,str) or not 8<=len(caption)<=110:
            raise ValueError("bad_caption")
        overlays=clip.get("overlays")
        if not isinstance(overlays,list) or len(overlays)>2:
            raise ValueError("excessive_text_overlay")
        for item in overlays:
            start,end,txt=item.get("at_ms"),item.get("until_ms"),item.get("text")
            if (type(start) is not int or type(end) is not int
               or not 0<=start<end<=d
               or not isinstance(txt,str) or len(txt)>52):
                raise ValueError("bad_overlay")
        beats=clip.get("beats")
        if not isinstance(beats,list) or not 3<=len(beats)<=5:
            raise ValueError("nonminimal_or_missing_beats")
        cursor=0
        for beat in beats:
            start,end=beat.get("start_ms"),beat.get("end_ms")
            action=beat.get("scene")
            if (type(start) is not int or type(end) is not int or
                start!=cursor or not start<end<=d):
                raise ValueError("noncontiguous_shot_timeline")
            if not isinstance(action,str) or not 20<=len(action)<=350:
                raise ValueError("bad_visual_action")
            if not isinstance(beat.get("sound"),str) or not beat["sound"]:
                raise ValueError("missing_sound_rights_plan")
            onscreen=beat.get("text")
            if not isinstance(onscreen,str) or len(onscreen)>52:
                raise ValueError("excessive_script_text")
            cursor=end
        if cursor!=d or len(clip.get("asset_needs",[]))<2:
            raise ValueError("incomplete_storyboard_or_assets")
        combined=" ".join(str(s) for s in (caption,*(
            b["text"] for b in beats),*(o["text"] for o in overlays))).casefold()
        if any(t in combined for t in FORBIDDEN):
            raise ValueError("unlicensed_reference_or_promotional_link")
    return clips


def _rate(metrics, numerator, reach):
    value=metrics.get(numerator)
    if value is None or reach is None or reach<=0:
        return None
    return round(value/reach,6)


def evaluate(metrics, duration_ms):
    """No invented engagement. One Reel with limited reach is not a winner."""
    if not isinstance(metrics,dict):
        raise ValueError("metrics_must_be_dict")
    if type(duration_ms) is not int or duration_ms<=0:
        raise ValueError("invalid_duration")
    for k in METRIC_NAMES:
        v=metrics.get(k)
        if v is not None and (type(v) not in (int,float) or
                             not math.isfinite(v) or v<0):
            raise ValueError("invalid_metric:"+k)
    reach=metrics.get("reach")
    avg=metrics.get("avg_watch_seconds")
    return {
      "reel_id":metrics.get("reel_id") or None,
      "reach":reach,
      "views":metrics.get("views"),
      "shares_per_reach":_rate(metrics,"shares",reach),
      "likes_per_reach":_rate(metrics,"likes",reach),
      "comments_per_reach":_rate(metrics,"comments",reach),
      "saves_per_reach":_rate(metrics,"saves",reach),
      "average_watch_to_duration":round(avg/(duration_ms/1000),4)
           if avg is not None else None,
      "retention_reported_by_provider":metrics.get("retention_percent"),
      "interpretation":"exploratory_only" if not isinstance(reach,(int,float))
             or reach<100 else "directional_review_only_not_causal_proof",
      "metric_absence_is_not_zero":True,
      "video_success_claim":False if not metrics.get("verified_published_post_id") else None,
    }


def export(plan_path=DEFAULT,output_dir=None):
    data=json.loads(Path(plan_path).read_text(encoding="utf-8"))
    clips=validate(data)
    out=Path(output_dir or PROJECT/"micro-reels-review-only")
    out.mkdir(parents=True,exist_ok=True)
    for clip in clips:
        manifest={
          "id":clip["id"],
          "duration_ms":clip["duration_ms"],
          "camera_shotlist":clip["beats"],
          "overlays":clip["overlays"],
          "props":clip["asset_needs"],
          "caption":clip["caption"],
          "why_someone_might_share":clip["share_trigger"],
          "loop_plan":clip["ending_loop"],
          "publish_approved":False,
          "media_rendered":False,
          "provider_post_id":None,
        }
        (out/(clip["id"]+".storyboard.json")).write_text(
          json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={
      "review_only_storyboards":len(clips),
      "actual_mp4_files":0,"publications":0,"new_spend":0,
      "reference_video_full_playback_verified":False,
      "metrics_24h_72h_not_yet_collected":True,
    }
    (out/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,default=DEFAULT)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    print("ENNA_MICRO_REELS_LAB="+json.dumps(export(args.plan,args.output),ensure_ascii=False))
