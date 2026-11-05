"""Enna Visual Factory: fresh licensed photographs + grounded Vietnamese jokes.

Produces *only* source-attributed drafts as GitHub Actions artifacts.  No
posting, updating schedules, database writes, payments or public uploads.
Photos are chosen from a human-curated Commons catalog; every candidate must
pass a live CC0 metadata check before the image is downloaded.
"""
import argparse
import hashlib
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from scripts.enna_photo_memes import fetch_photo
from growth.visual_comedy_gate import signals

SIZE = (1080, 1350)
MAX_PHOTOS_PER_BATCH = 3
VN = ZoneInfo("Asia/Ho_Chi_Minh")

def local_day():
    return datetime.now(VN).date()
ALLOWED_FORMATS = frozenset({"full_photo", "polaroid", "minimal", "reaction", "contrast", "chat"})
COMEDY_MECHANICS = frozenset({"time_escalation", "outer_inner_contrast", "expectation_reversal", "escalating_circularity", "object_personification", "visual_reaction", "role_reversal"})

def load_bank(path):
    """Fail closed on malformed manifests; model text cannot introduce URLs."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not 4 <= len(sources) <= 24:
        raise ValueError("visual-bank-source-count-invalid")
    ids = []
    for src in sources:
        if not isinstance(src, dict):
            raise ValueError("bad-source-record")
        ident = src.get("id")
        title = src.get("title")
        if (not isinstance(ident, str) or not ident.replace("-", "").isalnum()
                or not isinstance(title, str) or not title.startswith("File:")
                or not title.lower().endswith(".jpg")
                or src.get("format") not in ALLOWED_FORMATS
                or src.get("comic_device") not in COMEDY_MECHANICS):
            raise ValueError("source-unapproved")
        if any(not isinstance(src.get(k), str) or not 8 <= len(src[k]) <= 140
               for k in ("headline", "punchline", "visual_hint", "scene")):
            raise ValueError("missing-human-creative-brief")
        if src.get("format")=="chat" and (not isinstance(src.get("chat_lines"),list)
           or len(src["chat_lines"])!=2 or any(not isinstance(line,str) or not 16<=len(line)<=100 for line in src["chat_lines"])):
            raise ValueError("invalid-fictional-chat")
        ids.append(ident)
    if len(set(ids)) != len(ids) or len(set(s["title"] for s in sources)) != len(sources):
        raise ValueError("duplicated-source")
    return sources

def choose_batch(sources, day, count=MAX_PHOTOS_PER_BATCH):
    """Different source groups on successive days. Stable for same calendar date."""
    if count < 1 or count > MAX_PHOTOS_PER_BATCH:
        raise ValueError("unsupported-batch-size")
    count = min(len(sources), count)
    # Default batch intentionally mixes: fictional chat + expressive
    # photographic reaction + real-life visual contradiction. Prioritise the
    # reaction photo over three tasteful yet static workplace stock photos.
    if count==3:
        buckets={style:sorted((s for s in sources if s["format"]==style),
                             key=lambda item:item.get("featured_rank",99))
                 for style in ("chat","reaction","contrast")}
        if all(buckets.values()):
            return [bucket[day.toordinal()%len(bucket)]
                    for bucket in buckets.values()]
    start = (day.toordinal() * count) % len(sources)
    return [sources[(start + i) % len(sources)] for i in range(count)]

def _font(size, bold=True):
    prefix = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
    return ImageFont.truetype(prefix + ("-Bold" if bold else "") + ".ttf", size)

def _wrapped(draw, label, *, size=46, width=950, max_lines=2):
    if not isinstance(label, str):
        raise ValueError("non-string-copy")
    while size >= 22:
        font = _font(size)
        lines = []
        one = ""
        for word in label.split():
            trial = (one+" "+word).strip()
            if one and draw.textbbox((0,0),trial,font=font)[2] > width:
                lines.append(one)
                one = word
            else:
                one = trial
        if one:
            lines.append(one)
        if len(lines) <= max_lines and all(
                draw.textbbox((0,0),ln,font=font)[2]<=width for ln in lines):
            return font, lines, size
        size -= 2
    raise ValueError("copy-overflows-image")

def _write(draw, label, x, y, width, size, fill, max_lines=2):
    font, lines, size = _wrapped(draw,label,size=size,width=width,max_lines=max_lines)
    for ln in lines:
        draw.text((x,y),ln,font=font,fill=fill)
        y += int(size*1.29)
    return y

def _cover(img, area, original_photo):
    photo = ImageOps.fit(original_photo.convert("RGB"),(area[2]-area[0],area[3]-area[1]),
                         method=Image.Resampling.LANCZOS)
    img.paste(photo, (area[0],area[1]))

def compose(source, photo, copy=None):
    """Different visual grammars: image dominant; less robotic oversized copy."""
    if photo.width<850 or photo.height<560:
        raise ValueError("image-too-small")
    title = (copy or {}).get("headline") or source["headline"]
    punch = (copy or {}).get("punchline") or source["punchline"]
    if not (8<=len(title)<=85 and 12<=len(punch)<=110):
        raise ValueError("invalid-creative-length")
    layout=source["format"]
    canvas=Image.new("RGB",SIZE,"#fff8ed")
    if layout == "full_photo":
        _cover(canvas,(0,0,1080,1200),photo)
        panel = Image.new("RGBA", (1080, 300),(13,17,17,224))
        canvas.paste(panel,(0,1050),panel)
        d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((44,40,480,107),radius=23,fill="#ffdc59")
        _write(d,title,65,60,390,27,"#151515",max_lines=1)
        _write(d,punch,64,1117,945,48,"#ffffff",max_lines=3)
    elif layout == "polaroid":
        _cover(canvas,(58,70,1022,1002),photo)
        d=ImageDraw.Draw(canvas)
        d.rectangle((58,70,1022,1002),outline="#e6ddcb",width=6)
        d.rounded_rectangle((62,1042,1018,1315),radius=24,fill="#f6e5b0")
        _write(d,title,93,1067,900,42,"#1b1b1b",max_lines=2)
        _write(d,punch,93,1160,900,31,"#1b1b1b",max_lines=3)
        d.text((74,22),"ĐỒ HAY ĐI LÀM · NHẬT KÝ CÔNG SỞ",font=_font(20),fill="#39332b")
    elif layout == "minimal":
        _cover(canvas,(0,0,1080,1120),photo)
        d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((45,48,1010,163),radius=27,fill="#fff8ed")
        _write(d,title,77,85,900,48,"#191919",max_lines=1)
        d.rectangle((0,1095,1080,1350),fill="#f5db58")
        _write(d,punch,56,1147,966,45,"#1a1a1a",max_lines=3)
    elif layout == "reaction":
        # Meme-native reaction: large genuine photograph, intentionally little polish.
        _cover(canvas,(0,0,1080,1040),photo)
        d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((27,26,1053,199),radius=15,fill="#111111")
        _write(d,title,64,73,960,48,"#ffffff",max_lines=2)
        d.rectangle((0,1020,1080,1350),fill="#fff9ef")
        d.rectangle((0,1015,1080,1040),fill="#f6d542")
        _write(d,punch,55,1090,975,48,"#141414",max_lines=3)
    elif layout == "contrast":
        # Narrative jump in two labels, photo is the ironic middle beat.
        d=ImageDraw.Draw(canvas)
        d.rectangle((0,0,1080,230),fill="#161616")
        _write(d,title,57,72,965,49,"#ffffff",max_lines=2)
        _cover(canvas,(0,215,1080,1090),photo)
        d=ImageDraw.Draw(canvas)
        d.rectangle((0,1060,1080,1350),fill="#f3db51")
        _write(d,punch,53,1110,978,46,"#171717",max_lines=3)
    elif layout == "chat":
        lines=source.get("chat_lines") or []
        if len(lines)!=2:
            raise ValueError("chat-scenario-required")
        d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((34,34,1046,177),radius=24,fill="#e6eced")
        _write(d,title,55,70,961,40,"#202020",max_lines=2)
        d.text((64,188),"ĐOẠN CHAT GIẢ LẬP · KHÔNG PHẢI TIN NHẮN THẬT",
               font=_font(18),fill="#454545")
        for i,line in enumerate(lines):
            top=241+i*162
            left=52 if i==0 else 116
            right=994 if i==0 else 1030
            d.rounded_rectangle((left,top,right,top+134),radius=26,
               fill=("#e6eee1" if i==0 else "#f3dc68"))
            _write(d,line,left+28,top+23,right-left-58,31,"#202020",max_lines=3)
        _cover(canvas,(0,566,1080,1170),photo)
        d=ImageDraw.Draw(canvas)
        d.rectangle((0,1128,1080,1350),fill="#171717")
        _write(d,punch,49,1172,980,41,"#ffffff",max_lines=3)
    else:
        raise ValueError("unknown-visual-layout")
    return canvas

def render(bank, output, *, day=None, fetch=fetch_photo, rewrite=None, count=3):
    sources=load_bank(bank)
    day=day or local_day()
    selected=choose_batch(sources,day,count)
    # Only other pre-curated files may replace an unavailable photo.
    backups=[src for src in sources if src['id'] not in {x['id'] for x in selected}]
    target=Path(output)
    target.mkdir(parents=True,exist_ok=True)
    results=[]
    problems=[]
    for source in selected+backups:
        if len(results)>=count:
            break
        try:
            original, attribution = fetch((source["id"],source["title"],source["author"]))
        except (requests.RequestException,ValueError,OSError,KeyError,TypeError) as exc:
            # Never weaken rights checks or fetch a third-party site on failure.
            problems.append({"source_id":source["id"],"error_class":type(exc).__name__})
            continue
        baseline=signals(source,source)
        if not baseline["pass"]:
            problems.append({"source_id":source["id"],"error_class":"UnfunnyBaselineStructure",
                             "reasons":baseline["reasons"]})
            continue
        proposal = rewrite(source) if rewrite else None
        if proposal is not None and not isinstance(proposal,dict):
            raise ValueError("unsafe-copy-override")
        if proposal is not None and not signals(source,proposal)["pass"]:
            print("visual_factory: ai_copy_failed_comedy_structure_using_curated_copy")
            proposal=None
        try:
            artwork=compose(source,original,proposal)
        except ValueError:
            if proposal is None:
                raise
            # A generated joke can be appropriate but still impossible to fit.
            print("visual_factory: ai_copy_does_not_fit_using_curated_copy")
            proposal=None
            artwork=compose(source,original,None)
        file=target/(day.isoformat()+"-"+source["id"]+".png")
        artwork.save(file,format="PNG",optimize=True)
        if not 20000 < file.stat().st_size < 9_000_000:
            raise ValueError("invalid-render-size")
        evidence={
            "status":"DRAFT_REQUIRES_HUMAN_REVIEW",
            "published":False,
            "license_check":"Commons API verified CC0 at time of fetch",
            "visual_source_page":attribution["source_page"],
            "license":"CC0 1.0",
            "author":attribution["photographer"],
            "commons_filename":attribution["file"],
            "source_photo_sha256":attribution["photo_sha256"],
            "image_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
            "visual_hint":source["visual_hint"],
            "format":source["format"],
            "comic_device":source["comic_device"],
            "comedy_structure_gate":signals(source,proposal or source),
            "humor_rating_by_real_people":None,
            "scene":source["scene"],
            "headline":(proposal or {}).get("headline") or source["headline"],
            "punchline":(proposal or {}).get("punchline") or source["punchline"],
            "copy_origin":"guarded_ai_variant" if proposal else "human_curated",
            "fictional_joke_not_factual_claim":True,
            "next_step":"review visual fit, photo rights, copy and Vietnamese text before scheduling"
        }
        file.with_suffix(".rights.json").write_text(
             json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
        results.append(evidence|{"file":file.name})
    (target/"manifest.json").write_text(json.dumps({
        "date":day.isoformat(),"status":"DRAFT_REQUIRES_HUMAN_REVIEW",
        "no_social_actions":True,"source_count":len(results),
        "source_failures":problems,
        "results":[{"file":x["file"],"license":x["license"],"format":x["format"],
                    "copy_origin":x["copy_origin"]} for x in results]
    },ensure_ascii=False,indent=2),encoding="utf-8")
    if len(results)!=count:
        raise RuntimeError("insufficient_live_verified_cc0_sources")
    return results

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--bank",default="scripts/enna_visual_source_bank.json")
    parser.add_argument("--output",default="visual-factory-drafts")
    parser.add_argument("--date",default=None)
    parser.add_argument("--ai-copy",action="store_true")
    args=parser.parse_args()
    day=date.fromisoformat(args.date) if args.date else local_day()
    rewrite=None
    if args.ai_copy:
        from growth.visual_humor_editor import generate_variant
        rewrite=generate_variant
    items=render(args.bank,args.output,day=day,rewrite=rewrite)
    print(json.dumps({"status":"drafts_only","created":len(items),
                      "files":[s["file"] for s in items],
                      "ai_copy_used":sum(s["copy_origin"]=="guarded_ai_variant" for s in items)},
                     ensure_ascii=False))
if __name__=="__main__":
    main()
