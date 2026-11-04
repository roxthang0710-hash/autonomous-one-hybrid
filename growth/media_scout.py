"""Source-verified media scouting and original visual R&D for Enna.

Runs unattended from GitHub Actions. Generates original meme cards when enabled
and discovers public-domain image references. Any third-party photo or video
is research-only until a human verifies visual content, privacy and rights.
Never auto-download/repost social videos, copyrighted memes or music.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlparse
from io import BytesIO
from PIL import Image, UnidentifiedImageError

import requests

from agent import Database
from growth.meme_renderer import make_card

BRAND="do_hay_di_lam"
VN=ZoneInfo("Asia/Ho_Chi_Minh")
BUCKET="enna-original-media"
PUBLIC_BASE="https://gjdvdohylvsauphhkutw.supabase.co/storage/v1/object/public/"+BUCKET+"/"
MAX_READY_ORIGINAL=7
MAX_RESEARCH=40
MAX_ARCHIVE_BYTES=5*1024*1024
ARCHIVE_MIME={"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}

# All text and visual elements are original; no copied viral templates.
MEME_CONCEPTS=(
 ("deadline_calendar","Đồng hồ ở công ty có hai múi giờ.","Bình thường và còn 5 phút nữa tới hạn.", "work"),
 ("meeting_notes","Họp xong mọi người đều gật đầu.","Đến lúc làm mới hỏi: ủa ai nhận việc?", "conversation"),
 ("file_final","Tên tệp là BẢN CUỐI.","Trong thư mục có thêm 13 bản cuối khác.", "work"),
 ("office_keyboard","Tay đang gõ báo cáo rất chăm.","Não thì vẫn đang mở 37 tab.", "work"),
 ("excel_filter","Bảng tính này ai cũng được sửa.","Và mỗi người có một định nghĩa về xong.", "organize"),
 ("urgent_message","Tin nhắn có đúng một chữ: GẤP.","Deadline cụ thể lại là một bí ẩn.", "conversation"),
 ("monday_todo","Danh sách việc hôm nay có 19 dòng.","Việc đầu tiên: tìm xem nên làm dòng nào.", "work"),
 ("browser_tabs","Mở thêm một tab để tập trung.","Đã 28 tab, vẫn chưa tìm thấy sự tập trung.", "organize"),
 ("lunch_break","Nghỉ trưa 60 phút.","Mất 45 phút để chọn món ăn.", "conversation"),
 ("screenshot","Chụp ảnh màn hình để gửi một ô.","Vô tình gửi luôn 23 tab trên trình duyệt.", "work"),
)
VIDEO_STORYBOARDS=(
 ("file_name_story","Khi bạn nhận thư mục có 20 tệp 'cuối cùng'","video_storyboard","organize",
  "Video gốc 15 giây quay màn hình dữ liệu giả: tên tệp lộn xộn → demo PowerRename → thư mục dễ tìm. Không dùng tệp khách hàng thật."),
 ("meeting_story","Một cuộc họp không có ai nhận việc","video_storyboard","conversation",
  "Tiểu phẩm do Enna tự dựng: ba khung chat giả lập về người phụ trách, hạn chót và bảng chốt việc. Nhạc tự sáng tác hoặc không nhạc."),
 ("tab_story","28 tab trình duyệt và một ngày công sở","video_storyboard","work",
  "Video gốc 12–18 giây: quay màn hình tab giả lập, hiển thị mẹo nhóm tab và cách đóng tab thừa. Không sử dụng giao diện chứa dữ liệu cá nhân."),
)

# Search only safe scenes without identifiable people, logos or celebrity references.
COMMONS_QUERIES=("funny cat expression", "confused animal expression", "sleepy cat face", "surprised dog expression", "funny office illustration", "public domain cartoon reaction")
PEXELS_QUERIES=("desk workspace stationery","minimal keyboard on desk","notebook planning closeup")


def make_key(provider, identifier):
    return hashlib.sha256((provider+":"+str(identifier)).encode("utf-8")).hexdigest()[:30]


def allowed_source_url(url, provider):
    if not isinstance(url,str) or not url.startswith("https://"):
        return False
    from urllib.parse import urlparse
    host=urlparse(url).hostname
    return host in ({"commons.wikimedia.org"} if provider=="wikimedia_commons"
                    else {"www.pexels.com","pexels.com"} if provider=="pexels"
                    else set())


def allowed_commons_binary(url):
    """Only HTTPS Wikimedia-hosted image objects: never fetch arbitrary result URLs."""
    if not isinstance(url,str): return False
    parsed=urlparse(url)
    return (parsed.scheme=="https" and parsed.hostname=="upload.wikimedia.org"
            and parsed.port in (None,443) and parsed.username is None
            and parsed.password is None and parsed.path.startswith("/wikipedia/commons/")
            and not parsed.query and not parsed.fragment)


def archive_commons_image(item, *, get=requests.get, post=requests.post):
    """Archive CC0/PD candidate bytes under /reference; never a published meme."""
    if item.get("source_provider")!="wikimedia_commons" or item.get("status")!="needs_review":
        return None
    if item.get("license_code") not in ("cc0","cc0 1.0","public domain","public domain mark 1.0"):
        return None
    evidence=item.get("evidence") or {}
    url=evidence.get("original_image_url")
    mime=evidence.get("mime")
    if not allowed_commons_binary(url) or mime not in ARCHIVE_MIME: return None
    response=get(url,timeout=20,stream=True,allow_redirects=False,
                 headers={"User-Agent":"EnnaContentScout/1.1 (public-domain archival)"})
    if response.status_code!=200: return None
    try:
        content=bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            content.extend(chunk)
            if len(content)>MAX_ARCHIVE_BYTES:return None
        with Image.open(BytesIO(content)) as im:
            im.verify()
        with Image.open(BytesIO(content)) as im:
            if im.width<180 or im.height<180 or im.width*im.height>20000000:
                return None
            actual={"PNG":"image/png","JPEG":"image/jpeg","WEBP":"image/webp"}.get(im.format)
            if actual!=mime:return None
        object_path="reference/"+item["idea_key"]+"."+ARCHIVE_MIME[mime]
        host=os.getenv("SUPABASE_URL","").rstrip("/")
        secret=os.getenv("DB_SERVICE_KEY","")
        if not host.startswith("https://") or not secret:return None
        headers={"apikey":secret,"Content-Type":mime,"x-upsert":"false"}
        if not secret.startswith("sb_secret_"):headers["Authorization"]="Bearer "+secret
        result=post(host+"/storage/v1/object/"+BUCKET+"/"+object_path,
                    data=bytes(content),headers=headers,timeout=20)
        if result.status_code not in (200,201):return None
        return PUBLIC_BASE+object_path
    except (requests.RequestException,OSError,ValueError,UnidentifiedImageError):
        return None
    finally:
        response.close()


def inspect_commons(payload, query):
    """Only sufficiently explicit public-domain labels. All still need review."""
    items=(payload.get("query") or {}).get("pages") or {}
    suggestions=[]
    for p in items.values():
        if not isinstance(p,dict): continue
        info=(p.get("imageinfo") or [{}])[0]
        meta=info.get("extmetadata") or {}
        def clean(k):
            raw=meta.get(k,{})
            return str(raw.get("value") or "") if isinstance(raw,dict) else ""
        short=clean("LicenseShortName").strip().casefold()
        if short not in ("cc0","cc0 1.0","public domain","public domain mark 1.0"):
            continue
        name=str(p.get("title") or "")
        if not name.startswith("File:") or any(x in name.casefold() for x in
                ("person","portrait","celebrity","brand","logo","face")):
            continue
        url="https://commons.wikimedia.org/wiki/"+quote(name.replace(" ","_"),safe=":_()-.")
        if not allowed_source_url(url,"wikimedia_commons"):continue
        mime=str(info.get("mime") or "")
        if mime not in ARCHIVE_MIME: continue
        original_url=str(info.get("url") or "")
        if not allowed_commons_binary(original_url): continue
        suggestions.append({
            "idea_key":"commons-"+make_key("commons",name),
            "media_type":"licensed_meme_source",
            "title":("Meme nguồn mở: "+name[5:])[:140],
            "creative_brief":"Nguồn biểu cảm/tình huống để sáng tác meme công sở tiếng Việt. Duyệt trực quan, tác giả, logo, nhân vật và quyền liên quan trước khi dùng.",
            "hook_text":"Chọn tình huống công sở phù hợp; viết lời vui ngắn, không sao chép câu cửa miệng có bản quyền.",
            "source_provider":"wikimedia_commons","source_url":url,
            "creator_credit":clean("Artist")[:200] or "Xem thông tin tác giả tại Wikimedia Commons",
            "license_code":short[:50],"license_url":clean("LicenseUrl")[:500] or None,
            "rights_status":"review_required","status":"needs_review",
            "pillar":"organize",
            "evidence":{"query":query,"api":"commons_api","license_metadata":"checked","original_image_url":original_url,"mime":mime,"not_auto_publishable":True},
        })
    return suggestions


def commons_candidates(query, *, fetch=requests.get):
    try:
        resp=fetch("https://commons.wikimedia.org/w/api.php",
            headers={"User-Agent":"EnnaContentScout/1.0 (original media research; account: @dohay_dilam)"},
            params={"action":"query","format":"json","generator":"search",
               "gsrsearch":query,"gsrnamespace":6,"gsrlimit":12,
               "prop":"imageinfo","iiprop":"url|extmetadata|mime"},
            timeout=15)
        resp.raise_for_status()
        return inspect_commons(resp.json(),query)[:2]
    except (requests.RequestException,ValueError,KeyError,TypeError):
        return []


def pexels_candidates(query, key, *, fetch=requests.get):
    """Optional API; no key -> no access and never attempt scraping."""
    if not key: return []
    collected=[]
    for media,endpoint,label in (
        ("photo","https://api.pexels.com/v1/search","photos"),
        ("video","https://api.pexels.com/v1/videos/search","videos"),
    ):
        try:
            response=fetch(endpoint,headers={"Authorization":key},
                params={"query":query,"per_page":3,"orientation":"portrait"},
                timeout=15)
            if response.status_code in (401,403,429):
                break
            response.raise_for_status()
            candidates=response.json().get(label) or []
        except (requests.RequestException,ValueError,KeyError,TypeError):
            continue
        for item in candidates[:2]:
            ident=item.get("id")
            url=item.get("url")
            if not ident or not allowed_source_url(url,"pexels"):continue
            user=item.get("user") if isinstance(item.get("user"),dict) else {}
            credit=str(item.get("photographer") or user.get("name") or "Pexels")
            collected.append({
                "idea_key":"pexels-"+make_key("pexels",str(ident)),
                "media_type":"licensed_photo" if media=="photo" else "licensed_video",
                "title":"Tư liệu văn phòng: "+query,
                "creative_brief":"Đánh giá chất lượng và độ phù hợp; không hàm ý người/nhãn hàng trong ảnh bảo trợ Đồ Hay Đi Làm.",
                "hook_text":"Có thể chuyển thành bài chia sẻ mẹo công việc, cần kiểm tra quyền hình ảnh.",
                "source_provider":"pexels","source_url":url,
                "creator_credit":credit[:200],
                "license_code":"Pexels License",
                "license_url":"https://www.pexels.com/license/",
                "rights_status":"review_required","status":"needs_review",
                "pillar":"organize",
                "evidence":{"query":query,"api":"pexels","not_auto_publishable":True},
            })
    return collected


def upload_original_png(path,png, *, post=requests.post):
    """Service-role-only upload. Public URL contains only our own original pixels."""
    host=os.getenv("SUPABASE_URL","").rstrip("/")
    key=os.getenv("DB_SERVICE_KEY","")
    if not host.startswith("https://") or not key:
        raise RuntimeError("Backend storage credentials unavailable")
    headers={"apikey":key,"Content-Type":"image/png","x-upsert":"false"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"]="Bearer "+key
    response=post(host+"/storage/v1/object/"+BUCKET+"/"+path,
                  data=png,headers=headers,timeout=20)
    if response.status_code == 409:
        # A prior upload may have succeeded before its database update failed.
        # Confirm the exact public object exists without repeating the write.
        probe=requests.head(PUBLIC_BASE+path,timeout=10)
        if probe.status_code == 200 and probe.headers.get("Content-Type","").startswith("image/png"):
            return PUBLIC_BASE+path
    if response.status_code not in (200,201):
        # Never accept an ambiguous timeout as proof of upload.
        raise RuntimeError("Original meme upload was not confirmed")
    return PUBLIC_BASE+path


def insert_idea(db,row):
    result=db.request("POST","/enna_media_ideas",
        params={"on_conflict":"idea_key"},payload=row,
        prefer="resolution=ignore-duplicates,return=representation")
    return bool(result)


def run(db=None, *, now=None, enable_public_assets=None):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    today=now.astimezone(VN).date()
    existing=db.request("GET","/enna_media_ideas",params={
        "select":"id,idea_key,status,media_type,created_at,title,creative_brief,hook_text,pillar,source_url,source_provider,license_code,evidence",
        "order":"created_at.desc","limit":"140"})
    if not isinstance(existing,list):
        raise RuntimeError("Media idea source unavailable")
    existing_keys={x.get("idea_key") for x in existing}
    ready=sum(x.get("status")=="ready" and x.get("media_type")=="original_meme" for x in existing)
    def same_vn_date(row):
        try:
            at=datetime.fromisoformat(str(row.get("created_at") or "").replace("Z","+00:00"))
            return at.tzinfo is not None and at.astimezone(VN).date()==today
        except (TypeError,ValueError,OverflowError):
            return False
    created_today=sum(same_vn_date(x) for x in existing)
    original_today=sum(same_vn_date(x) and x.get("media_type")=="original_meme" for x in existing)
    new_original=0
    metrics_state={"status":"collecting_evidence","preferred_pillar":None,"observed_posts":0}
    try:
        from growth.editorial_autopilot import editorial_evidence
        published=db.request("GET","/threads_posts",params={
            "select":"id,pillar,status,published_at,platform_post_id",
            "status":"eq.posted","order":"published_at.desc","limit":"120"})
        measured=db.request("GET","/threads_metrics",params={
            "select":"post_id,views,likes,replies,collected_at",
            "order":"collected_at.desc","limit":"350"})
        if isinstance(published,list) and isinstance(measured,list):
            metrics_state=editorial_evidence(published,measured,now=now)
    except Exception:
        metrics_state={"status":"source_unavailable","preferred_pillar":None,"observed_posts":0}
    favored=metrics_state.get("preferred_pillar") if metrics_state.get("status")=="provider_evidence" else None

    # Recover a previously created original image when Storage was unavailable.
    if enable_public_assets is True or (enable_public_assets is None and
                                       os.getenv("ENNA_ORIGINAL_MEDIA_ENABLED","false")=="true"):
        recovery=next((x for x in reversed(existing)
                       if x.get("media_type")=="original_meme"
                       and x.get("status")=="research"
                       and not x.get("source_url")
                       and x.get("idea_key","").startswith("original-")),None)
        if recovery:
            try:
                png=make_card(recovery["title"],recovery["hook_text"])
                url=upload_original_png("meme/"+recovery["idea_key"]+".png",png)
                db.request("PATCH","/enna_media_ideas",params={
                    "id":"eq."+str(recovery["id"]),
                    "status":"eq.research"},payload={"status":"ready",
                    "source_url":url,
                    "evidence":{"created_from":"original_text_and_shapes",
                                "image_uploaded":True,
                                "recovered_after_storage_failure":True}},
                    prefer="return=minimal")
            except Exception:
                pass

    # Typography-only cards are a rare fallback, not the main visual library.\n    if ready<MAX_READY_ORIGINAL and original_today<1 and today.toordinal()%3==0:
        from growth.meme_ideas import generate as invent
        past=[x.get("creative_brief") for x in existing
              if x.get("media_type")=="original_meme" and x.get("creative_brief")]
        # Fresh AI concepts are optional; original evergreen concepts are the fallback.
        candidate=invent(past, favored=favored)
        choice=None
        if candidate:
            code,head,punch,pillar=candidate
            choice=("original-"+code,head,punch,pillar)
        else:
            for idx in range(len(MEME_CONCEPTS)):
                code,head,punch,pillar=MEME_CONCEPTS[(today.toordinal()+idx)%len(MEME_CONCEPTS)]
                if "original-"+code not in existing_keys:
                    choice=("original-"+code,head,punch,pillar)
                    break
        if choice:
            key,head,punch,pillar=choice
            if key not in existing_keys:
                use_upload=(enable_public_assets is True or
                            (enable_public_assets is None and
                             os.getenv("ENNA_ORIGINAL_MEDIA_ENABLED","false")=="true"))
                source_url=None
                if use_upload:
                    try:
                        source_url=upload_original_png("meme/"+key+".png",
                                                       make_card(head,punch))
                    except Exception:
                        source_url=None
                row={"brand_key":BRAND,"idea_key":key,"media_type":"original_meme",
                     "title":head,"creative_brief":head+" / "+punch,
                     "hook_text":punch,"source_provider":"original",
                     "source_url":source_url,"creator_credit":"Enna · Đồ Hay Đi Làm",
                     "license_code":"original","license_url":None,
                     "rights_status":"original",
                     "status":"ready" if source_url else "research",
                     "pillar":pillar,
                     "evidence":{"created_from":"original_text_and_shapes",
                       "image_uploaded":bool(source_url),
                       "performance_evidence":metrics_state.get("status"),
                       "performance_favored_pillar":favored,
                       "no_external_templates":True}}
                if insert_idea(db,row):
                    new_original+=1
    new_storyboard=0
    if created_today < 3:
        for key,title,media,pillar,brief in VIDEO_STORYBOARDS:
            idea_key="storyboard-"+key
            if idea_key in existing_keys: continue
            row={"brand_key":BRAND,"idea_key":idea_key,
                 "media_type":media,"title":title,"creative_brief":brief,
                 "hook_text":title,"source_provider":"original","source_url":None,
                 "creator_credit":"Enna · Đồ Hay Đi Làm",
                 "license_code":"original","rights_status":"original",
                 "status":"research","pillar":pillar,
                 "evidence":{"not_yet_rendered":True,"original_storyboard":True}}
            if insert_idea(db,row):new_storyboard+=1
            break
    research_count=sum(x.get("status")=="needs_review" for x in existing)
    new_sources=0
    archived_sources=0
    # Backfill already catalogued licensed references before scouting more.
    for older in existing:
        if archived_sources>=2:break
        evidence=older.get("evidence") or {}
        if (older.get("media_type")!="licensed_meme_source"
            or evidence.get("archive_url") or older.get("status")!="needs_review"):
            continue
        archived_url=archive_commons_image(older)
        if not archived_url:continue
        db.request("PATCH","/enna_media_ideas",
                   params={"id":"eq."+str(older["id"]),"status":"eq.needs_review"},
                   payload={"evidence":{**evidence,"archive_url":archived_url,
                       "archived_for_review":True,"not_auto_publishable":True}},
                   prefer="return=minimal")
        archived_sources+=1
    if research_count<MAX_RESEARCH:
        query=COMMONS_QUERIES[today.toordinal()%len(COMMONS_QUERIES)]
        for item in commons_candidates(query):
            archived_url=archive_commons_image(item) if archived_sources<2 else None
            if archived_url:
                item["evidence"]={**item["evidence"],"archive_url":archived_url,
                                  "archived_for_review":True,"not_auto_publishable":True}
            if insert_idea(db,{"brand_key":BRAND,**item}):
                new_sources+=1
                archived_sources+=int(bool(archived_url))
        key=os.getenv("PEXELS_API_KEY","").strip()
        if key:
            for item in pexels_candidates(PEXELS_QUERIES[today.toordinal()%len(PEXELS_QUERIES)],key):
                if insert_idea(db,{"brand_key":BRAND,**item}):
                    new_sources+=1
    return {"original_concepts_new":new_original,
        "video_storyboards_new":new_storyboard,
        "rights_review_sources_new":new_sources,
        "licensed_meme_sources_archived":archived_sources,
        "media_asset_upload_enabled":os.getenv("ENNA_ORIGINAL_MEDIA_ENABLED","false")=="true" if enable_public_assets is None else enable_public_assets,
        "external_sources_are_not_published":True}


if __name__=="__main__":
    try:
        result=run()
        print("Enna media scout:",json.dumps(result,ensure_ascii=False))
        from growth.activity_log import emit
        run_id=os.getenv("GITHUB_RUN_ID","")
        if run_id.isdecimal():
            code="media_concept_prepared" if (result["original_concepts_new"] or result["video_storyboards_new"] or result["rights_review_sources_new"]) else "media_no_new"
            try:
                emit(Database(),"editor",
                    "success" if code=="media_concept_prepared" else "skipped",
                    code,run_id=run_id)
            except Exception:
                pass
    except Exception as exc:
        print("Enna media scouting unavailable:",type(exc).__name__)
        raise SystemExit(1)
