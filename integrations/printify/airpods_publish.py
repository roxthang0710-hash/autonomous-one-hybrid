#!/usr/bin/env python3
"""Safely publish only the 16 pre-QA'd AirPods FRONT printed colorway products to Shopify."""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from audit import fetch_products, get_json, choose_shop
from airpods_batch import SHOP, SOURCE_IDS, COLORS
from stage_colorways import PAL

API="https://api.printify.com/v1"
LIMIT=4

def preflight(token):
    shops=get_json("/shops.json",token)
    shop=choose_shop(shops,os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    if int(shop["id"])!=SHOP or "shopify" not in str(shop.get("sales_channel","")).casefold():
        raise ValueError("Not the expected Shopify-linked Printify shop")
    products=fetch_products(SHOP,token)
    titles={}
    for p in products:
        titles.setdefault(str(p.get("title","")),[]).append(p)
    sources=[get_json("/shops/%s/products/%s.json"%(SHOP,pid),token) for pid in SOURCE_IDS]
    checked=[]
    for source in sources:
        src_art={str(i["id"]) for a in source.get("print_areas",[]) for ph in a.get("placeholders",[]) for i in ph.get("images",[])}
        originals={int(v["id"]):int(v["price"]) for v in source.get("variants",[]) if v.get("is_enabled")}
        for color in COLORS:
            title=source["title"]+" — Colorway: "+color
            matches=titles.get(title,[])
            if len(matches)!=1:
                raise ValueError("Missing or duplicated AirPods colorway "+color)
            p=matches[0]
            bgs={x.get("background") for x in p.get("print_areas",[])}
            art={str(i["id"]) for a in p.get("print_areas",[]) for ph in a.get("placeholders",[]) for i in ph.get("images",[])}
            enabled={int(v["id"]):int(v["price"]) for v in p.get("variants",[]) if v.get("is_enabled")}
            costs=[int(v["price"])-int(v.get("cost",v["price"])) for v in p.get("variants",[]) if v.get("is_enabled")]
            description=p.get("description","")
            disclosed="physical AirPods case and unprinted back/sides remain" in description or "supplier's physical AirPods case remains white" in description
            if (p.get("blueprint_id"),p.get("print_provider_id"))!=(1505,23) or bgs!={PAL[color]} or src_art!=art or enabled!=originals or len(enabled)!=7 or not disclosed or not p.get("images") or min(costs)<800:
                raise ValueError("AirPods product did not pass manufacturing preflight: "+color)
            checked.append(p)
    if len(checked)!=16:
        raise ValueError("Expected 16 products")
    return checked

def publish_one(token,pid):
    body=json.dumps({"title":True,"description":True,"images":True,"variants":True,"tags":True,"keyFeatures":True,"shipping_template":True}).encode()
    req=urllib.request.Request(f"{API}/shops/{SHOP}/products/{pid}/publish.json",data=body,method="POST",headers={
        "Authorization":"Bearer "+token,"Accept":"application/json","Content-Type":"application/json",
        "User-Agent":"Enna-AirPods-Colorway-Publish/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            return response.status
    except urllib.error.HTTPError as error:
        print("PRINTIFY_PUBLISH_REJECTED",pid,error.code)
        return error.code

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:return 2
    targets=preflight(token)
    linked=sum(bool(x.get("external")) for x in targets)
    print("AIRPODS_PUBLISH_PREFLIGHT_OK count=16 already_linked=%d pending=%d"%(linked,16-linked))
    if not args.apply:
        print("DRY_RUN_NO_PUBLISH")
        return 0
    if os.getenv("ENNA_APPROVE_AIRPODS_PUBLISH")!="YES":
        print("PUBLISH_GUARD_MISSING")
        return 2
    from airpods_batch_qa import main as live_color_qa
    if live_color_qa()!=0:
        print("PUBLISH_BLOCKED_LIVE_QA_FAILED")
        return 1
    pending=[x for x in targets if not x.get("external")]
    if any(p.get("is_locked") for p in pending):
        print("PUBLISH_BLOCKED_LOCKED_UNLINKED_DRAFT")
        return 1
    sent=0
    for off in range(0,len(pending),LIMIT):
        batch=pending[off:off+LIMIT]
        ids=[]
        for item in batch:
            pid=item["id"]
            status=publish_one(token,pid)
            if status<200 or status>=300:
                print("PUBLISH_STOPPED_BAD_STATUS",pid,status)
                return 1
            ids.append(pid)
            sent+=1
            print("AIRPODS_PUBLISH_ACCEPTED",pid,"http",status)
            time.sleep(0.5)
        for retry in range(12):
            current=[get_json(f"/shops/{SHOP}/products/{pid}.json",token) for pid in ids]
            outstanding=[p.get("id") for p in current if not p.get("external")]
            if not outstanding:break
            time.sleep(5)
        print("AIRPODS_SYNC_BATCH",off//LIMIT+1,"count",len(ids),"outstanding",len(outstanding))
        if outstanding:
            print("PUBLISH_STOPPED_PENDING_SYNC; safe retry after checking Printify")
            return 1
    current=fetch_products(SHOP,token)
    byname={p["title"]:p for p in current}
    confirmed=sum(bool(byname.get(p["title"],{}).get("external")) for p in targets)
    print("AIRPODS_PUBLISH_FINISHED linked=%d expected=16 new_submitted=%d"%(confirmed,sent))
    print("No orders placed; physical shell remains white on unprinted areas.")
    return 0 if confirmed==16 else 1

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("AIRPODS_PUBLISH_ABORTED",type(exc).__name__,str(exc) if isinstance(exc,ValueError) else "")
        sys.exit(1)
