"""A2.1: verify REAL owner-account Threads posts independent of Metricool copy.

Reads only official Meta /me and /me/threads. Stores hashed caption evidence
plus published IDs in a private Supabase table. Does not publish, edit,
authorize channels, or infer that absent/paginated posts failed to publish.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from agent import Database
from threads.credentials import load_credentials, verify_identity
from threads.publisher import thread_request

BRAND = "do_hay_di_lam"
TABLE = "/enna_official_threads_observations"
MAX_POSTS = 60
ID_PATTERN = re.compile(r"^[0-9]{5,30}$")
SAFE_DOMAINS = {"threads.com","www.threads.com","threads.net","www.threads.net"}


def _datetime(value):
    if isinstance(value,datetime):
        dt=value
    else:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("provider time missing timezone")
    return dt.astimezone(timezone.utc)


def _permalink(value):
    if not isinstance(value,str):
        return None
    try:
        url=urlparse(value)
    except ValueError:
        return None
    if (url.scheme=="https" and url.hostname in SAFE_DOMAINS
        and url.username is None and url.password is None
        and url.path.startswith("/@dohay_dilam/post/") and len(value)<450):
        return value
    return None


def parse_posts(payload, *, now):
    """Validate all records BEFORE writing any observations."""
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list):
        raise ValueError("unexpected_official_meta_response")
    now=_datetime(now)
    out={}
    for post in payload["data"][:MAX_POSTS]:
        if not isinstance(post,dict):
            continue
        ident=str(post.get("id") or "")
        if not ID_PATTERN.fullmatch(ident) or ident in out:
            continue
        try:
            created=_datetime(post["timestamp"])
        except (KeyError,ValueError,TypeError,OverflowError):
            continue
        if not timedelta(minutes=-2)<=now-created<=timedelta(days=45):
            continue
        text=post.get("text")
        fingerprint=hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text,str) and text else None
        out[ident]={
            "brand_key": BRAND,
            "meta_post_id": ident,
            "published_at": created.isoformat(),
            "permalink": _permalink(post.get("permalink")),
            "text_sha256": fingerprint,
            "last_observed_at": now.isoformat(),
            "source": "meta_official",
        }
    return list(out.values())


def collect(db=None, *, now=None, load=load_credentials, read=None):
    db=db or Database()
    now=_datetime(now or datetime.now(timezone.utc))
    read=read or thread_request
    credentials=load(db,refresh=False)
    if not credentials:
        return {"state":"meta_owner_oauth_unavailable","verified_count":0,
                "social_posts_created":0}
    token,expected=credentials
    try:
        verified,user_id=verify_identity(token,expected,read=read)
    except (ValueError,KeyError,TypeError):
        return {"state":"identity_unavailable","verified_count":0,
                "social_posts_created":0}
    if verified!="dohay_dilam" or not user_id:
        return {"state":"identity_mismatch","verified_count":0,
                "social_posts_created":0}
    feed=read("GET","/me/threads",token,params={
        "fields":"id,text,timestamp,permalink", "limit":MAX_POSTS})
    observations=parse_posts(feed,now=now)
    if not observations:
        return {"state":"empty_observation_sample","verified_count":0,
                "sample_paginated":bool(feed.get("paging")),
                "social_posts_created":0}
    saved=db.request("POST",TABLE,params={
        "on_conflict":"brand_key,meta_post_id"
    },payload=observations,prefer="resolution=merge-duplicates,return=representation")
    if not isinstance(saved,list) or len(saved)!=len(observations):
        return {"state":"upsert_unverified","verified_count":0,
                "social_posts_created":0}
    ids=','.join(x["meta_post_id"] for x in observations)
    readback=db.request("GET",TABLE,params={
        "select":"meta_post_id,published_at,source",
        "brand_key":"eq."+BRAND,
        "meta_post_id":"in.("+ids+")",
        "limit":str(MAX_POSTS),
    })
    if not isinstance(readback,list):
        return {"state":"readback_unavailable","verified_count":0,
                "social_posts_created":0}
    actual={str(x.get("meta_post_id")):x for x in readback if isinstance(x,dict)}
    for row in observations:
        found=actual.get(row["meta_post_id"])
        if (not found or found.get("source")!="meta_official" or
            _datetime(found.get("published_at"))!=_datetime(row["published_at"])):
            return {"state":"readback_unverified","verified_count":0,
                    "social_posts_created":0}
    return {
        "state":"verified_official_feed",
        "verified_count":len(observations),
        "sample_paginated":bool(feed.get("paging")),
        "raw_post_text_logged":False,
        "social_posts_created":0,
        "provider":"meta_threads_official",
    }


if __name__=="__main__":
    try:
        print("ENNA_OFFICIAL_FEED="+json.dumps(collect(),ensure_ascii=False))
    except Exception as exc:
        print("ENNA_OFFICIAL_FEED="+json.dumps({
            "state":"unavailable","error_class":type(exc).__name__,
            "social_posts_created":0},ensure_ascii=False))
        raise SystemExit(1)
