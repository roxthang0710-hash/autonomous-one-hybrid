"""Index CC0-derived Enna visual drafts in the existing Supabase media library.

This stores **review-only** images. It never schedules/posts social content.
Only service-role GitHub Actions may write. The old publisher uses only
'original_meme'+'ready'; these are 'licensed_photo'+'needs_review'.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image
from agent import Database

BUCKET="enna-original-media"
BRAND="do_hay_di_lam"
MAX_ASSET_BYTES=6_000_000
EXPECTED="DRAFT_REQUIRES_HUMAN_REVIEW"

def verify_draft(file):
    file=Path(file)
    if file.suffix.lower()!=".png" or not file.is_file():
        raise ValueError("png-required")
    if not 20000<file.stat().st_size<MAX_ASSET_BYTES:
        raise ValueError("invalid-file-size")
    proof=json.loads(file.with_suffix(".rights.json").read_text(encoding="utf-8"))
    if proof.get("status")!=EXPECTED or proof.get("published") is not False:
        raise ValueError("not-a-review-only-draft")
    if proof.get("license")!="CC0 1.0" or proof.get("fictional_joke_not_factual_claim") is not True:
        raise ValueError("unverified-rights-or-factual-claim")
    source=proof.get("visual_source_page","")
    link=urlparse(source)
    if link.scheme!="https" or link.hostname!="commons.wikimedia.org" or not link.path.startswith("/wiki/File:"):
        raise ValueError("unverified-source-page")
    if not proof.get("author") or not proof.get("commons_filename","").startswith("File:"):
        raise ValueError("missing-attribution")
    raw=file.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=proof.get("image_sha256"):
        raise ValueError("image-hash-mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}",str(proof.get("source_photo_sha256",""))):
        raise ValueError("unverifiable-original-image")
    with Image.open(file) as im:
        if im.format!="PNG" or im.size!=(1080,1350):
            raise ValueError("wrong-photo-format")
    return proof,digest,raw

def storage_upload(path, data, *, post=requests.post, head=requests.head):
    host=os.environ.get("SUPABASE_URL","").rstrip("/")
    secret=os.environ.get("DB_SERVICE_KEY","")
    if not host.startswith("https://") or not secret:
        raise RuntimeError("storage-credentials-missing")
    url=host+"/storage/v1/object/"+BUCKET+"/"+path
    headers={"apikey":secret,"Content-Type":"image/png","x-upsert":"false"}
    if not secret.startswith("sb_secret_"):
        headers["Authorization"]="Bearer "+secret
    # Path includes content hash. Upsert is disabled and repeated uploads must
    # resolve through a read-only HEAD, never overwrite existing bytes.
    resp=post(url,data=data,headers=headers,timeout=25)
    public=host+"/storage/v1/object/public/"+BUCKET+"/"+path
    if resp.status_code in (200,201):
        return public
    if resp.status_code==409:
        check=head(public,timeout=12)
        if check.status_code==200 and check.headers.get("Content-Type","").startswith("image/png"):
            return public
    raise RuntimeError("storage-upload-not-confirmed")

def catalog_row(proof,digest,source_url):
    if not source_url.startswith("https://"):
        raise ValueError("untrusted-storage-link")
    return {
      "brand_key":BRAND,
      "idea_key":"visual-cc0-"+digest[:28],
      "media_type":"licensed_photo",
      "title":str(proof["headline"])[:140],
      "creative_brief":(str(proof["visual_hint"])+" / "+str(proof["punchline"]))[:1000],
      "hook_text":str(proof["punchline"])[:250],
      "source_provider":"wikimedia_commons",
      "source_url":source_url,
      "creator_credit":str(proof["author"])[:180]+" · Enna biên tập",
      "license_code":"cc0 1.0",
      "license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
      "rights_status":"review_required",
      "status":"needs_review",
      "pillar":"work",
      "evidence":{
         "not_auto_publishable":True,
         "derived_from_cc0_photo":True,
         "source_file":proof["commons_filename"],
         "source_page":proof["visual_source_page"],
         "source_image_sha256":proof["source_photo_sha256"],
         "draft_image_sha256":digest,
         "visual_layout":proof["format"],
         "copy_origin":proof["copy_origin"],
         "human_visual_approval":False,
         "not_a_real_life_claim":True
      }
    }

def publish_review_drafts(directory, *, upload=storage_upload, db=None):
    """Fail closed; storage review copies are not approved posts."""
    files=sorted(Path(directory).glob("*.png"))
    if not files or len(files)>3:
        raise ValueError("unexpected-asset-count")
    db=db or Database()
    result=[]
    for file in files:
        proof,digest,bytes_=verify_draft(file)
        path="visual-review/"+digest[:2]+"/"+digest+".png"
        url=upload(path,bytes_)
        row=catalog_row(proof,digest,url)
        db.request("POST","/enna_media_ideas",
            params={"on_conflict":"idea_key"},payload=row,
            prefer="resolution=ignore-duplicates,return=representation")
        # Read back the exact entry, including on retries after a lost response.
        stored=db.request("GET","/enna_media_ideas",params={
             "select":"idea_key,status,rights_status,source_url,media_type",
             "idea_key":"eq."+row["idea_key"],"limit":"1"})
        if not (isinstance(stored,list) and len(stored)==1
                and stored[0].get("status")=="needs_review"
                and stored[0].get("rights_status")=="review_required"
                and stored[0].get("media_type")=="licensed_photo"
                and stored[0].get("source_url")==url):
            raise RuntimeError("review-registration-not-confirmed")
        result.append({"idea_key":row["idea_key"],"status":"needs_review",
                       "source_photo":proof["commons_filename"],"image_url":url})
    return result

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--directory",default="visual-factory-drafts")
    args=a.parse_args()
    items=publish_review_drafts(args.directory)
    print(json.dumps({"registered_review_only":len(items),"social_posts":0,
                      "items":[{"idea_key":i["idea_key"],"status":i["status"]} for i in items]},
                     ensure_ascii=False))
