"""A2.2: match Metricool stable UUIDs to independently verified Meta IDs.

Bootstrap from one owner-authorized Metricool connector snapshot (NOT a live
Metricool API inside GitHub). Future unattended six-hour runs consume the
latest official Meta evidence and reconcile exact permalink / tightly unique
caption-hash-and-time matches. No new social posts or remote planner edits.

Only an exact permalink from both providers may repair the legacy Threads
ledger; hash/time links remain explicitly lower-confidence bridge evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from agent import Database

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT/"config/enna_metricool_threads_observation_2026_11_06.json"
COPY=ROOT/"config/enna_metricool_copy_refresh_2026_11_06.json"
BRAND="do_hay_di_lam"
TABLE="/enna_metricool_threads_links"
UUID=re.compile(r"^-?[0-9]{5,25}$")
POSTID=re.compile(r"^[0-9]{5,30}$")
SLUG=re.compile(r"^/@dohay_dilam/post/([a-zA-Z0-9_-]{8,50})/?$")
DAY_SECS=timedelta(minutes=10)


def date(value):
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-required")
    return dt.astimezone(timezone.utc)


def canonical(url):
    """Whitelist official own-account post links, never arbitrary redirects."""
    if not isinstance(url,str) or len(url)>450:
        return None
    try:
        u=urlsplit(url)
    except ValueError:
        return None
    if (u.scheme!="https" or u.hostname not in
        {"threads.com","www.threads.com","threads.net","www.threads.net"}
        or u.username or u.password or u.port or u.fragment):
        return None
    match=SLUG.fullmatch(u.path)
    return match.group(1) if match else None


def make_seed(snapshot, editorial):
    if snapshot.get("brand_key")!=BRAND or snapshot.get("provider_source")!="metricool_owner_connector_snapshot":
        raise ValueError("invalid-source")
    if snapshot.get("metricool_brand_id")!="7803567" or snapshot.get("timezone")!="Asia/Saigon":
        raise ValueError("wrong-brand-or-timezone")
    observed=date(snapshot["observed_at_utc"])
    contents={x["metricool_uuid"]:x["revised_text"] for x in editorial["items"]}
    posts=snapshot.get("posts")
    if not isinstance(posts,list) or not posts or len(posts)>120:
        raise ValueError("invalid-post-count")
    seen=set()
    rows=[]
    for p in posts:
        uuid=p.get("metricool_uuid")
        postid=str(p.get("metricool_post_id") or "")
        st=p.get("provider_status")
        if (not isinstance(uuid,str) or not UUID.fullmatch(uuid)
            or not POSTID.fullmatch(postid) or uuid in seen
            or st not in {"PENDING","PUBLISHED"}):
            raise ValueError("bad-post-uuid-status")
        seen.add(uuid)
        local=datetime.fromisoformat(p["scheduled_local"])
        if local.tzinfo is not None:
            raise ValueError("local-schedule-must-have-explicit-context")
        scheduled=local.replace(tzinfo=timezone(timedelta(hours=7))).astimezone(timezone.utc)
        if abs((observed-scheduled).days)>50:
            raise ValueError("out-of-range-snapshot")
        permalink=p.get("provider_permalink")
        if st=="PUBLISHED" and not canonical(permalink):
            raise ValueError("published-without-valid-permalink")
        if st=="PENDING" and permalink:
            raise ValueError("unexpected-pending-permalink")
        caption=contents.get(uuid)
        if st=="PENDING" and (not isinstance(caption,str) or len(caption)<15):
            raise ValueError("pending-caption-missing-from-approved-copy")
        rows.append({
            "brand_key":BRAND, "metricool_uuid":uuid,
            "metricool_post_id":postid,
            "scheduled_at":scheduled.isoformat(),
            "provider_status_last_seen":st,
            "provider_permalink":permalink,
            "expected_text_sha256":hashlib.sha256(caption.encode("utf-8")).hexdigest()
                if caption else None,
            "provider_observed_at":observed.isoformat(),
            "provider_source":"metricool_owner_connector_snapshot",
        })
    return rows


def seed(db=None, *, snapshot_path=SNAPSHOT, editorial_path=COPY):
    db=db or Database()
    snapshot=json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    editorial=json.loads(Path(editorial_path).read_text(encoding="utf-8"))
    records=make_seed(snapshot,editorial)
    result=db.request("POST",TABLE,params={"on_conflict":"brand_key,metricool_uuid"},
        payload=records, prefer="resolution=ignore-duplicates,return=representation")
    if not isinstance(result,list):
        raise RuntimeError("provider-snapshot-write-unverified")
    readback=db.request("GET",TABLE,params={
        "select":"metricool_uuid,metricool_post_id,scheduled_at,provider_source,"
                 "provider_permalink,expected_text_sha256",
        "brand_key":"eq."+BRAND,"limit":"120"})
    if not isinstance(readback,list):
        raise RuntimeError("provider-snapshot-readback-unavailable")
    lookup={x["metricool_uuid"]:x for x in readback}
    for row in records:
        saved=lookup.get(row["metricool_uuid"])
        if (not saved or saved.get("metricool_post_id")!=row["metricool_post_id"]
            or date(saved.get("scheduled_at"))!=date(row["scheduled_at"])
            or saved.get("provider_source")!="metricool_owner_connector_snapshot"
            or saved.get("provider_permalink")!=row["provider_permalink"]
            or saved.get("expected_text_sha256")!=row["expected_text_sha256"]):
            raise RuntimeError("provider-snapshot-readback-mismatch")
    return {"state":"bootstrap_verified","snapshot_rows":len(records),
            "inserted_now":len(result),
            "pending":sum(x["provider_status_last_seen"]=="PENDING" for x in records),
            "published":sum(x["provider_status_last_seen"]=="PUBLISHED" for x in records),
            "social_writes":0}


def match_pairs(bridge, official, *, now):
    """Bipartite uniqueness: one UUID ↔ one Meta ID, never time-only."""
    now=date(now)
    candidates=[]
    occupied={str(x.get("meta_post_id")) for x in bridge if x.get("meta_post_id")}
    official_by_url={}
    for post in official:
        mid=str(post.get("meta_post_id") or "")
        if not POSTID.fullmatch(mid) or post.get("source")!="meta_official":
            continue
        slug=canonical(post.get("permalink"))
        if slug:
            official_by_url.setdefault(slug,[]).append(post)
    for row in bridge:
        if row.get("meta_post_id") or row.get("brand_key")!=BRAND:
            continue
        if row.get("provider_status_last_seen") not in {"PUBLISHED","PENDING"}:
            continue
        uuid=row.get("metricool_uuid")
        if not isinstance(uuid,str) or not UUID.fullmatch(uuid):
            continue
        slug=canonical(row.get("provider_permalink"))
        proposed=[]
        if slug:
            for post in official_by_url.get(slug,[]):
                proposed.append((post,"exact_verified_permalink"))
        else:
            expected=row.get("expected_text_sha256")
            try: due=date(row["scheduled_at"])
            except (ValueError,TypeError,KeyError):continue
            if (not expected or not re.fullmatch("[0-9a-f]{64}",str(expected))
                or due>now):
                continue
            for post in official:
                if post.get("source")!="meta_official" or post.get("text_sha256")!=expected:
                    continue
                try:at=date(post["published_at"])
                except (KeyError,ValueError,TypeError):continue
                if abs(at-due)<=DAY_SECS:
                    proposed.append((post,"unique_caption_hash_and_time"))
        for post,basis in proposed:
            mid=str(post.get("meta_post_id") or "")
            if mid in occupied or not POSTID.fullmatch(mid):
                continue
            try:at=date(post["published_at"])
            except (KeyError,ValueError,TypeError):continue
            candidates.append({"metricool_uuid":uuid,"meta_post_id":mid,
                               "meta_published_at":at.isoformat(),
                               "match_basis":basis,
                               "permalink":post.get("permalink")})
    per_uuid=Counter(x["metricool_uuid"] for x in candidates)
    per_id=Counter(x["meta_post_id"] for x in candidates)
    return [x for x in candidates
            if per_uuid[x["metricool_uuid"]]==1 and per_id[x["meta_post_id"]]==1]


def _repair_legacy(db, *, matched, bridge_row, now):
    """Only provider + official exact permalink may update old internal status."""
    if matched["match_basis"]!="exact_verified_permalink":
        return "not_applicable"
    links=db.request("GET","/threads_metricool_schedule",params={
        "select":"post_id,metricool_uuid,provider",
        "metricool_uuid":"eq."+matched["metricool_uuid"],"provider":"eq.threads",
        "limit":"2"})
    if not isinstance(links,list) or len(links)!=1:
        return "no_unique_internal_schedule"
    post_id=links[0].get("post_id")
    if not post_id:
        return "no_ledger_post_id"
    existing=db.request("GET","/threads_posts",params={
        "select":"id,status,platform_post_id",
        "id":"eq."+post_id,"limit":"1"})
    if not isinstance(existing,list) or len(existing)!=1:
        return "ledger_unavailable"
    row=existing[0]
    if row.get("status")=="posted":
        return "already_posted" if str(row.get("platform_post_id"))==matched["meta_post_id"] else "existing_conflicting_meta_id"
    if row.get("status")!="scheduled_external" or row.get("platform_post_id"):
        return "unsafe_ledger_state"
    upd=db.request("PATCH","/threads_posts",params={
        "id":"eq."+post_id,"status":"eq.scheduled_external",
        "platform_post_id":"is.null"},
        payload={"status":"posted","platform_post_id":matched["meta_post_id"],
          "permalink":matched["permalink"],
          "published_at":matched["meta_published_at"],
          "updated_at":now.isoformat()},
        prefer="return=representation")
    if not isinstance(upd,list) or len(upd)!=1:
        return "ledger_write_unverified"
    check=db.request("GET","/threads_posts",params={
        "select":"id,status,platform_post_id,permalink",
        "id":"eq."+post_id,"limit":"1"})
    if (not isinstance(check,list) or len(check)!=1
        or check[0].get("status")!="posted"
        or str(check[0].get("platform_post_id"))!=matched["meta_post_id"]
        or canonical(check[0].get("permalink"))!=canonical(matched["permalink"])):
        return "ledger_readback_unverified"
    return "ledger_repaired_verified"


def overdue_diagnostics(bridge, official, *, now):
    """Only fresh owner-Meta checks can justify an unverified-post alert.

    This does NOT say the post failed or that reposting is safe. Meta results
    can be paginated and the saved Metricool status may be stale.
    """
    now=date(now)
    timestamps=[]
    for item in official:
        if item.get("source")!="meta_official":
            continue
        try:timestamps.append(date(item["last_observed_at"]))
        except (KeyError,ValueError,TypeError):continue
    if not timestamps or now-max(timestamps)>timedelta(minutes=20):
        return []
    alerts=[]
    for row in bridge:
        if row.get("brand_key")!=BRAND or row.get("meta_post_id"):
            continue
        if row.get("provider_status_last_seen")!="PENDING":
            continue
        try:due=date(row["scheduled_at"])
        except (KeyError,ValueError,TypeError):continue
        lag=now-due
        if lag<timedelta(hours=2) or lag>timedelta(days=7):
            continue
        uuid=str(row.get("metricool_uuid") or "")
        if not UUID.fullmatch(uuid):
            continue
        digest=row.get("expected_text_sha256")
        possible=[]
        for item in official:
            if item.get("source")!="meta_official" or item.get("text_sha256")!=digest or not digest:
                continue
            try:when=date(item["published_at"])
            except (KeyError,ValueError,TypeError):continue
            if abs(when-due)<=timedelta(hours=6):
                possible.append(item)
        if possible:
            reason="ambiguous_or_shifted_official_post"
            description=("Meta có bài tương tự nhưng thời điểm hoặc độ duy nhất không đủ "
                         "để xác nhận chính xác. Không ghi nhận hay đăng lại tự động.")
        else:
            reason="not_identified_in_recent_official_sample"
            description=("Không tìm thấy bằng chứng khớp trong mẫu Meta đã đọc. "
                         "Mẫu Meta có thể phân trang; đây KHÔNG phải bằng chứng bài chưa đăng.")
        alerts.append({
            "metricool_uuid":uuid,"reason":reason,
            "details":("Bài Threads đến hạn "+due.isoformat()+
                ", lịch Metricool chỉ là bản chụp trước đó. "+description),
            "action":("Kiểm tra permalink và trạng thái thật trên Metricool, "
                "đọc lại Meta bài chính chủ; không tự đăng bù cho đến khi xác định chắc chắn."),
            "due":due.isoformat(),
        })
    return sorted(alerts,key=lambda x:x["due"])[:3]


def notify_overdue(db, incidents):
    if not incidents:
        return 0
    owners=db.request("GET","/enna_desk_owners",params={
        "select":"user_id","limit":"5"})
    if not isinstance(owners,list):
        raise RuntimeError("unverified-owner-registry")
    if not owners:
        return 0
    notices=[{
        "owner_id":person["user_id"],
        "source_key":"a22-metricool-unmatched:"+x["metricool_uuid"],
        "category":"publisher","severity":"warning",
        "title":"Enna: Threads đến hạn nhưng chưa đối soát được",
        "details":x["details"],
        "suggested_action":x["action"],
    } for person in owners for x in incidents]
    result=db.request("POST","/enna_desk_notifications",
        params={"on_conflict":"owner_id,source_key"},
        payload=notices,
        prefer="resolution=ignore-duplicates,return=representation")
    if not isinstance(result,list):
        raise RuntimeError("unverified-private-owner-notification")
    return len(result)


def reconcile(db=None, *, now=None):
    db=db or Database()
    now=date(now or datetime.now(timezone.utc))
    bridge=db.request("GET",TABLE,params={
        "select":"brand_key,metricool_uuid,metricool_post_id,provider_status_last_seen,"
                 "scheduled_at,provider_permalink,expected_text_sha256,meta_post_id",
        "brand_key":"eq."+BRAND,"limit":"120"})
    official=db.request("GET","/enna_official_threads_observations",params={
        "select":"meta_post_id,published_at,permalink,text_sha256,source,last_observed_at",
        "brand_key":"eq."+BRAND,"order":"published_at.desc","limit":"120"})
    if not isinstance(bridge,list) or not isinstance(official,list):
        raise RuntimeError("required-provider-evidence-unavailable")
    proposed=match_pairs(bridge,official,now=now)
    saved=[]
    legacy={}
    by_uuid={x["metricool_uuid"]:x for x in bridge}
    for item in proposed:
        key=item["metricool_uuid"]
        record=db.request("PATCH",TABLE,params={
            "brand_key":"eq."+BRAND,"metricool_uuid":"eq."+key,
            "meta_post_id":"is.null"},
            payload={"meta_post_id":item["meta_post_id"],
                     "meta_published_at":item["meta_published_at"],
                     "match_basis":item["match_basis"],
                     "verified_at":now.isoformat(),
                     "updated_at":now.isoformat()},
            prefer="return=representation")
        if not isinstance(record,list) or len(record)!=1:
            continue
        verify=db.request("GET",TABLE,params={
            "select":"meta_post_id,meta_published_at,match_basis",
            "brand_key":"eq."+BRAND,"metricool_uuid":"eq."+key,"limit":"1"})
        if (not isinstance(verify,list) or len(verify)!=1
            or str(verify[0].get("meta_post_id"))!=item["meta_post_id"]
            or verify[0].get("match_basis")!=item["match_basis"]
            or date(verify[0].get("meta_published_at"))!=date(item["meta_published_at"])):
            raise RuntimeError("bridge-write-readback-unverified")
        saved.append(item)
        if item["match_basis"]=="exact_verified_permalink":
            legacy[key]=_repair_legacy(db,matched=item,bridge_row=by_uuid[key],now=now)
    diagnostics=overdue_diagnostics(bridge,official,now=now)
    alerts_saved=notify_overdue(db,diagnostics)
    return {"state":"verified" if saved else "no_new_matches",
        "metricool_snapshot_rows":len(bridge),
        "official_meta_observations":len(official),
        "candidate_links":len(proposed),
        "linked_verified":len(saved),
        "exact_permalink_matches":sum(x["match_basis"]=="exact_verified_permalink" for x in saved),
        "hash_time_matches":sum(x["match_basis"]=="unique_caption_hash_and_time" for x in saved),
        "legacy_ledger_repaired":sum(s=="ledger_repaired_verified" for s in legacy.values()),
        "legacy_other_states":dict(Counter(legacy.values())),
        "due_unmatched_needing_review":len(diagnostics),
        "new_private_review_alerts":alerts_saved,
        "metricool_api_called":False,
        "social_posts_created":0,
        "safe_to_auto_retry_failed_posts":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",action="store_true")
    args=p.parse_args()
    try:
        if args.seed:
            print("ENNA_METRICOOL_BRIDGE_SEED="+json.dumps(seed(),ensure_ascii=False))
        print("ENNA_METRICOOL_BRIDGE="+json.dumps(reconcile(),ensure_ascii=False))
    except Exception as exc:
        print("ENNA_METRICOOL_BRIDGE="+json.dumps({
            "state":"unavailable","error_class":type(exc).__name__,
            "social_posts_created":0},ensure_ascii=False))
        raise SystemExit(1)
