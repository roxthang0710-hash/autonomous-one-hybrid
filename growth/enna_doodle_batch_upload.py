"""Deliver strictly original Enna doodles into private review catalog + public media.

This file never creates, schedules, updates or publishes a social post.
Existing storage helpers are reused so no new auth API is introduced.
"""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

from agent import Database
from growth.visual_review_catalog import storage_upload

BRAND="do_hay_di_lam"

def verify_original(file):
    file=Path(file)
    if file.suffix!=".png" or file.name.endswith(".rights.png"):
        raise ValueError("expected-png")
    if not file.is_file() or not 15_000 < file.stat().st_size < 6_000_000:
        raise ValueError("invalid-png-size")
    meta=json.loads((file.parent/(file.name+".rights.json")).read_text(encoding="utf-8"))
    data=file.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if (meta.get("sha256")!=digest
         or meta.get("status")!="DRAFT_REQUIRES_HUMAN_REVIEW"
         or meta.get("published") is not False
         or meta.get("source")!="enna_original_drawing_no_third_party_art"
         or meta.get("ai_generated_image") is not False):
        raise ValueError("original-art-provenance-mismatch")
    if not re.fullmatch(r"[a-z0-9-]{5,60}",meta.get("id","")):
        raise ValueError("invalid-asset-id")
    with Image.open(file) as img:
        if img.size!=(1080,1350) or img.format!="PNG":
            raise ValueError("bad-media-dimensions")
    return meta,digest,data

def deliver(folder,upload=storage_upload,db=None):
    db=db or Database()
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    selected=manifest.get("items") or []
    if manifest.get("count")!=14 or len(selected)!=14:
        raise ValueError("unexpected-doodle-count")
    observed=set()
    records=[]
    for item in selected:
        fname=item["file"]
        if Path(fname).name!=fname or not fname.endswith(".png"):
            raise ValueError("unsafe-file-reference")
        proof,digest,data=verify_original(folder/fname)
        if proof["id"] in observed or proof["id"]!=item["id"]:
            raise ValueError("duplicate-asset")
        observed.add(proof["id"])
        if digest!=item["sha256"]:
            raise ValueError("manifest-sha-mismatch")
        idea_key="doodle-v31-"+proof["id"]+"-"+digest[:12]
        path="visual-original-doodle/"+digest[:2]+"/"+digest+".png"
        prior=db.request("GET","/enna_media_ideas",params={
           "select":"idea_key,source_url,status,evidence",
           "idea_key":"eq."+idea_key,"limit":"1"
        })
        if not isinstance(prior,list):
            raise RuntimeError("review-read-failed")
        if prior:
            item_db=prior[0]
            url=item_db.get("source_url","")
            if (not url.endswith("/"+path) or
                (item_db.get("evidence") or {}).get("draft_image_sha256")!=digest):
                raise RuntimeError("existing-original-conflict")
            # Reusing a previously scheduled/reviewed asset is safe, but do
            # not reset approval to needs_review on reruns.
            records.append({"id":proof["id"],"url":url,"idea_key":idea_key,
                            "status":item_db["status"],"reused":True})
            continue
        url=upload(path,data)
        row={
            "brand_key":BRAND,"idea_key":idea_key,"media_type":"original_meme",
            "title":proof["hook"],"creative_brief":proof["punch"],
            "hook_text":proof["punch"],"source_provider":"original",
            "source_url":url,"creator_credit":"Enna · Đồ Hay Đi Làm",
            "license_code":"original",
            "rights_status":"original","status":"needs_review",
            "pillar":"work",
            "evidence":{
                 "style":"original_handdrawn_doodle","art_id":proof["id"],
                 "scene":proof["scene"],"draft_image_sha256":digest,
                 "original_by_enna":True,"ai_generated_image":False,
                 "human_visual_approval":False,
                 "not_auto_publishable":True,
                 "social_post_id":None
            }
        }
        db.request("POST","/enna_media_ideas",
            params={"on_conflict":"idea_key"},payload=row,
            prefer="resolution=ignore-duplicates,return=representation")
        check=db.request("GET","/enna_media_ideas",params={
            "select":"idea_key,source_url,status,evidence",
            "idea_key":"eq."+idea_key,"limit":"1"
        })
        if not (isinstance(check,list) and len(check)==1
                and check[0].get("source_url")==url
                and check[0].get("status")=="needs_review"):
            raise RuntimeError("catalog-not-confirmed")
        records.append({"id":proof["id"],"url":url,"idea_key":idea_key,
                        "status":"needs_review","reused":False})
    target=folder/"public-media-manifest.json"
    target.write_text(json.dumps({"count":len(records),"status":"media_uploaded_social_not_scheduled",
            "items":records},ensure_ascii=False,indent=2),encoding="utf-8")
    return records

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--folder",default="enna-doodle-queue")
    args=p.parse_args()
    records=deliver(args.folder)
    print(json.dumps({"uploaded_original_media":len(records),
                      "reused_existing":sum(x["reused"] for x in records),
                      "social_posts_created":0,
                      "artifact":"public-media-manifest.json"},ensure_ascii=False))
