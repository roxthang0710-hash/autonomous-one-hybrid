#!/usr/bin/env python3
"""Create only unlinked AirPods printed-FRONT background QA drafts (never publish)."""
import argparse
import copy
import os
import sys
import time
from audit import get_json, fetch_products
from stage_colorways import PAL, PHONE_COLORS, build_payload, create_product

SHOP=29780383
SOURCE_IDS=[
    "6afb5760a4a5022c1007adfb",
    "6afb57a2037a5f7652018e66",
    "6afb57a7a1efd1254e001024",
    "6afb57ada1efd1254e00102a",
]
COLORS=["Blush Pink","Cream","Sage Green","Sky Blue"]

def clean_source(source):
    if (source.get("blueprint_id"),source.get("print_provider_id"))!=(1505,23):
        raise ValueError("Unexpected AirPods blueprint or provider")
    enabled=[v for v in source.get("variants",[]) if v.get("is_enabled")]
    if len(enabled)!=7:
        raise ValueError("Incorrect AirPods size coverage")
    areas=source.get("print_areas",[])
    if len(areas)!=1:
        raise ValueError("Unexpected number of AirPods print areas")
    area=areas[0]
    fronts=[x for x in area.get("placeholders",[]) if x.get("position")=="front" and x.get("images")]
    others=[x for x in area.get("placeholders",[]) if x.get("position")!="front" and x.get("images")]
    if len(fronts)!=1 or others:
        raise ValueError("Artwork cannot be safely isolated to one front print area")
    cleaned=copy.deepcopy(source)
    cleaned["print_areas"][0]["placeholders"]=copy.deepcopy(fronts)
    return cleaned

def prepare(sources):
    outputs=[]
    for source in sources:
        safe=clean_source(source)
        for color in COLORS:
            payload=build_payload(safe,color)
            payload["description"] += (
                "<p>Only the FRONT printed artwork background has this color. "
                "The physical AirPods case and unprinted back/sides remain the original white material. "
                "Please review product mockups for coverage.</p>"
            )
            outputs.append((source["id"],color,payload))
    if len(outputs)!=16:
        raise ValueError("Missing AirPods colorway draft payloads")
    return outputs

def main():
    args=argparse.ArgumentParser()
    args.add_argument("--apply",action="store_true")
    opts=args.parse_args()
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:return 2
    shop_data=get_json("/shops.json",token)
    if not any(str(s.get("id"))==str(SHOP) for s in shop_data):
        print("WRONG_SHOP")
        return 1
    sources=[get_json("/shops/%s/products/%s.json"%(SHOP,pid),token) for pid in SOURCE_IDS]
    if [str(p.get("id")) for p in sources]!=SOURCE_IDS:
        print("SOURCE_IDS_CHANGED")
        return 1
    allplans=prepare(sources)
    print("AIRPODS_PREFLIGHT_OK sources=4 backgrounds=4 total_drafts=16 all_preserve_7_SKUS")
    if not opts.apply:
        print("READ_ONLY_PREFLIGHT_NO_CREATION")
        return 0
    if os.getenv("ENNA_APPROVE_AIRPODS_DRAFT_BATCH")!="YES":
        print("MISSING_EXPLICIT_DRAFT_GUARD")
        return 2
    existing=fetch_products(SHOP,token)
    titles={str(p.get("title","")).strip().casefold():p for p in existing}
    created=0
    skipped=0
    for source_id,color,payload in allplans:
        key=payload["title"].strip().casefold()
        if key in titles:
            current=titles[key]
            bgs={a.get("background") for a in current.get("print_areas",[])}
            if bgs!={PAL[color]} or bool(current.get("external")):
                print("CONFLICTING_EXISTING_AIRPODS_DRAFT",source_id,color)
                return 1
            skipped+=1
            print("SKIP_EXISTING",source_id,color)
            continue
        new=create_product(SHOP,token,payload)
        if not new.get("id"):
            print("CREATE_ID_MISSING",source_id,color)
            return 1
        check=get_json("/shops/%s/products/%s.json"%(SHOP,new["id"]),token)
        bgs={a.get("background") for a in check.get("print_areas",[])}
        good=check.get("title")==payload["title"] and bgs=={PAL[color]} and not check.get("external") and len([v for v in check.get("variants",[]) if v.get("is_enabled")])==7
        print("AIRPODS_CREATED id=%s source=%s color=%s basicQA=%s mockups=%d external=%s" % (
            new["id"],source_id,color,good,len(check.get("images") or []),bool(check.get("external"))))
        if not good:
            return 1
        titles[key]=check
        created+=1
        time.sleep(0.35)
    print("AIRPODS_DRAFT_BATCH_DONE created=%d existing=%d total=%d no_publish" % (created,skipped,created+skipped))
    return 0 if created+skipped==16 else 1

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("AIRPODS_BATCH_ABORTED",type(e).__name__,str(e) if isinstance(e,ValueError) else "")
        sys.exit(1)
