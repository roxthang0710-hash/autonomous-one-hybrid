"""Safe live Threads profile audit: only read official Meta profile, alert owner.

This module never edits a third-party profile; Meta's supported owner
profile access is read-only here. Produces a specific owner action, and
does not confuse Supabase channel metadata with actual public biography.
"""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

from agent import Database
from threads.credentials import load_credentials, verify_identity
from threads.publisher import thread_request

VN=ZoneInfo("Asia/Ho_Chi_Minh")
USERNAME="dohay_dilam"
BIO=("Mẹo Windows, Excel & chuyện công sở bớt mệt 🫠\n"
     "Mẹo nhỏ dùng được ngay, không lý thuyết dài dòng.\n"
     "Bộ mẫu miễn phí ở liên kết bên dưới 👇")
LINK="https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/links/"


def profile_gap(text):
    """A checked biography may be good already; don't force a rewrite."""
    if not isinstance(text,str):
        return "unverifiable"
    value=text.casefold()
    helpful=any(v in value for v in ("mẹo","phím tắt","excel","windows"))
    promise=any(v in value for v in ("theo dõi","mỗi ngày","bộ mẫu","miễn phí","dùng ngay"))
    return "healthy_copy" if helpful and promise else "needs_value_proposition"


def notify_owner(db, status, *, day):
    owners=db.request("GET","/enna_desk_owners",params={"select":"user_id","limit":"5"})
    if not isinstance(owners,list) or not owners:return 0
    if status=="healthy_copy":
        title="Enna đã kiểm tra hồ sơ Threads: có lợi ích theo dõi"
        details="Bio công khai đã nêu được giá trị của kênh và có lý do trở lại. Không tự thay đổi hồ sơ."
        action="Giữ thông điệp hiện tại và đo follower mới sau khi người xem vào hồ sơ."
        severity="info"
    elif status=="needs_value_proposition":
        title="Enna phát hiện bio Threads chưa rõ lý do theo dõi"
        details="Enna đã cải tiến trang bio và chuẩn bị mẫu bio ngắn trong Enna Desk. Bio hiện tại chưa thể hiện rõ lợi ích theo dõi."
        action="Chọn Sao chép bio mới ở Enna Desk, dán trong Chỉnh sửa hồ sơ Threads và thêm liên kết trang bio Enna."
        severity="warning"
    else:
        title="Enna chưa đọc được bio Threads qua quyền hiện tại"
        details="Không có đủ bằng chứng từ Meta để xác minh nội dung bio công khai. Enna không tự đoán hoặc ghi đè."
        action="Mở Enna Desk xem mẫu bio, kiểm tra trực tiếp mục Chỉnh sửa hồ sơ Threads; chỉ cấp thêm quyền nếu Meta thông báo quyền cụ thể."
        severity="warning"
    rows=[{"owner_id":o["user_id"],"source_key":"profile-audit:"+day+":"+status,
           "category":"growth","severity":severity,"title":title,
           "details":details,"suggested_action":action} for o in owners]
    written=db.request("POST","/enna_desk_notifications",
        params={"on_conflict":"owner_id,source_key"},
        payload=rows,prefer="resolution=ignore-duplicates,return=representation")
    return len(written) if isinstance(written,list) else 0


def audit(db=None, *, now=None, read=thread_request, credentials=load_credentials):
    db=db or Database()
    now=now or datetime.now(timezone.utc)
    day=now.astimezone(VN).date().isoformat()
    cred=credentials(db,refresh=False)
    if not cred:
        notify_owner(db,"unverifiable",day=day)
        return {"status":"needs_official_oauth","bio_verified":False}
    token,expected=cred
    try:
        name,uid=verify_identity(token,expected,read=read)
        if name!=USERNAME or not uid:
            return {"status":"identity_mismatch","bio_verified":False}
        result=read("GET","/me",token,
             params={"fields":"id,username,threads_biography"})
        if str(result.get("id"))!=str(uid) or str(result.get("username","")).casefold()!=USERNAME:
            return {"status":"identity_mismatch","bio_verified":False}
        bio=result.get("threads_biography")
        status=profile_gap(bio)
    except (requests.RequestException,ValueError,KeyError,TypeError):
        status="unverifiable"
    notify_owner(db,status,day=day)
    return {"status":status,"bio_verified":status!="unverifiable",
            "owner_action_required":status!="healthy_copy",
            "recommended_bio_copy_ready":True}


if __name__=="__main__":
    try:
        print("Enna profile conversion audit:",json.dumps(audit(),ensure_ascii=False))
    except Exception as exc:
        print("Enna profile audit failed:",type(exc).__name__)
        raise
