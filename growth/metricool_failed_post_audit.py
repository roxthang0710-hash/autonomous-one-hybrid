"""Audit a Metricool ERROR against official live Threads posts.

This script NEVER creates or publishes a Threads post and NEVER retries a failed
container. It only resolves an exact, unique Meta-side publication match; all
non-matches remain uncertain because the API could be delayed or paginated.
"""
import json
import os
from datetime import datetime, timezone

import requests

from agent import Database
from threads.credentials import load_credentials, verify_identity
from threads.publisher import thread_request
from threads.reconcile import find_matches

BRAND="do_hay_di_lam"
MAX_LIVE_POSTS=70


def find_exact(target, live):
    matches=find_matches([target],live)
    if len(matches)!=1:
        return None
    # find_matches returns one result for a unique time-bounded exact text.
    return matches[0]


def audit(db=None, *, metricool_id=None, ledger_id=None, read=thread_request):
    db=db or Database()
    metricool_id=str(metricool_id or os.getenv("METRICOOL_ERROR_POST_ID","")).strip()
    ledger_id=str(ledger_id or os.getenv("METRICOOL_ERROR_LEDGER_ID","")).strip()
    if not metricool_id.isdecimal() or len(ledger_id)!=36:
        return {"state":"invalid_target"}
    ledger=db.request("GET","/threads_posts",params={
        "select":"id,status,scheduled_at,text_content,platform_post_id",
        "id":"eq."+ledger_id,"limit":"1"})
    if not isinstance(ledger,list) or len(ledger)!=1:
        return {"state":"ledger_missing"}
    target=ledger[0]
    if target.get("status")=="posted" and target.get("platform_post_id"):
        return {"state":"already_verified_posted"}
    if target.get("status")!="scheduled_external":
        return {"state":"unexpected_ledger_state"}
    credentials=load_credentials(db,refresh=False)
    if not credentials:
        return {"state":"meta_oauth_unavailable"}
    token,expected=credentials
    try:
        verified,uid=verify_identity(token,expected,read=read)
        if verified!="dohay_dilam" or not uid:
            return {"state":"meta_identity_mismatch"}
        feed=read("GET","/me/threads",token,params={
            "fields":"id,text,timestamp,permalink","limit":MAX_LIVE_POSTS})
    except (requests.RequestException,ValueError,TypeError):
        return {"state":"meta_read_unavailable"}
    if not isinstance(feed,dict) or not isinstance(feed.get("data"),list):
        return {"state":"meta_feed_unavailable"}
    match=find_exact(target,feed["data"])
    if match:
        now=datetime.now(timezone.utc).isoformat()
        changed=db.request("PATCH","/threads_posts",params={
            "id":"eq."+ledger_id,"status":"eq.scheduled_external"},
            payload={"status":"posted","platform_post_id":match["platform_post_id"],
                     "permalink":match.get("permalink"),
                     "published_at":match["published_at"],"updated_at":now},
            prefer="return=representation")
        if not isinstance(changed,list) or len(changed)!=1:
            return {"state":"meta_match_db_update_unverified"}
        db.request("PATCH","/enna_publication_evidence",params={
            "brand_key":"eq."+BRAND,"metricool_post_id":"eq."+metricool_id},
            payload={"meta_post_id":match["platform_post_id"],
                     "notes":"Metricool reported ERROR; exact unique match confirmed via official Meta Threads feed. No retry performed.",
                     "checked_at":now},prefer="return=representation")
        report="meta_verified_posted"
        details=("Metricool báo lỗi, nhưng đã tìm được mã bài Meta trùng khớp "
                 "duy nhất; Enna đã cập nhật nhật ký, không đăng trùng.")
        action="Không đăng lại bài này; kiểm tra tình trạng Metricool nếu còn báo lỗi."
    else:
        report="not_seen_on_meta_yet"
        details=("Meta chưa trả về bản đăng trùng nội dung và gần giờ 18:30 "
                 "trong mẫu bài mới nhất; điều này chưa chứng minh chắc chắn "
                 "Meta sẽ không xuất bản chậm.")
        action=("Đừng bấm thử đăng lại ngay. Kiểm tra trực tiếp Threads rồi "
                "mới thử lại một lần trong Metricool sau khi lỗi dịch vụ hết.")
    owners=db.request("GET","/enna_desk_owners",params={"select":"user_id","limit":"5"})
    if isinstance(owners,list) and owners:
        notice=[{"owner_id":o["user_id"],
          "source_key":"metricool-meta-audit:"+metricool_id+":"+report,
          "category":"growth","severity":"info" if match else "warning",
          "title":"Đối chiếu Meta cho bài Metricool lỗi ("+report+")",
          "details":details,"suggested_action":action} for o in owners]
        db.request("POST","/enna_desk_notifications",params={
            "on_conflict":"owner_id,source_key"},payload=notice,
            prefer="resolution=ignore-duplicates,return=representation")
    return {"state":report,"scanned_recent_own_posts":len(feed["data"]),
            "meta_match_verified":bool(match),"auto_retry_performed":False}


if __name__=="__main__":
    try:
        print("Enna Metricool failure audit:",json.dumps(audit(),ensure_ascii=False))
    except Exception as exc:
        print("Enna Metricool failure audit error:",type(exc).__name__)
        raise
