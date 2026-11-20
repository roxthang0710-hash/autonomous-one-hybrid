#!/usr/bin/env python3
"""Publish verified Printify colorway products to connected Shopify in safe batches."""
import json,os,sys,time,urllib.request,urllib.error
from audit import get_json,choose_shop,fetch_products
from stage_colorways import PHONE_CASE_SOURCES, PHONE_COLORS, PAL

API="https://api.printify.com/v1"
USA_FIRST_SHIPPING_CENTS={421:499,269:499,1273:599}
BATCH_SIZE=5

def verify(p, original):
    title=p.get("title","")
    if " — Colorway: " not in title:return False
    root,color=title.rsplit(" — Colorway: ",1)
    if color not in PHONE_COLORS or color not in PAL:return False
    if root!=original.get("title"):return False
    if p.get("blueprint_id")!=original.get("blueprint_id") or p.get("print_provider_id")!=original.get("print_provider_id"):return False
    bgs={a.get("background") for a in p.get("print_areas",[])}
    if bgs!={PAL[color]}:return False
    orig_art={x["id"] for a in original.get("print_areas",[]) for placeholder in a.get("placeholders",[]) for x in placeholder.get("images",[])}
    new_art={x["id"] for a in p.get("print_areas",[]) for placeholder in a.get("placeholders",[]) for x in placeholder.get("images",[])}
    if orig_art != new_art:return False
    variants=[v for v in p.get("variants",[]) if v.get("is_enabled")]
    if len(variants)!=len([v for v in original.get("variants",[]) if v.get("is_enabled")]):return False
    if len(p.get("images",[]))<4:return False
    ship=USA_FIRST_SHIPPING_CENTS.get(p["blueprint_id"])
    if ship is None:return False
    if min(int(v["price"])-int(v["cost"])-ship for v in variants)<500:return False
    if "PRINTED background color" not in p.get("description",""):return False
    return True

def send(shop_id,product_id,token):
    body=json.dumps({"title":True,"description":True,"images":True,"variants":True,"tags":True,"keyFeatures":True,"shipping_template":True}).encode()
    req=urllib.request.Request(API+"/shops/%s/products/%s/publish.json"%(shop_id,product_id),data=body,method="POST",headers={
        "Authorization":"Bearer "+token,"Accept":"application/json","Content-Type":"application/json","User-Agent":"Enna-PiePo-BatchPublish/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            return response.status
    except urllib.error.HTTPError as error:
        print("API_REJECTED product_id=%s status=%d"%(product_id,error.code))
        return error.code

def main():
    if os.getenv("ENNA_APPROVE_COLORWAY_PUBLISH")!="YES":
        print("Publishing is disabled")
        return 2
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    if "shopify" not in str(shop.get("sales_channel","")).casefold():
        print("Wrong linked sales channel")
        return 1
    shop_id=shop["id"]
    allp=fetch_products(shop_id,token)
    by_id={p["id"]:p for p in allp}
    sources={by_id[pid]["title"]:by_id[pid] for pid in PHONE_CASE_SOURCES}
    expected_titles={name+" — Colorway: "+color for name in sources for color in PHONE_COLORS}
    target=[p for p in allp if p.get("title") in expected_titles]
    if len(target)!=len(expected_titles):
        print("BLOCKED_NOT_ALL_DRAFTS_FOUND",len(target),len(expected_titles));return 1
    for p in target:
        name=p["title"].rsplit(" — Colorway: ",1)[0]
        if not verify(p,sources[name]):
            print("BLOCKED_QA_FAIL",p["id"]);return 1
    notyet=[p for p in target if not p.get("external") and not p.get("is_locked")]
    print("COLORWAY_PUBLISH_PREFLIGHT_OK total=%d already_or_locked=%d ready=%d"%(
        len(target),len(target)-len(notyet),len(notyet)))
    accepted=0
    failed=0
    for start in range(0,len(notyet),BATCH_SIZE):
        batch=notyet[start:start+BATCH_SIZE]
        ids=[]
        for p in batch:
            product_id=p["id"]
            st=send(shop_id,product_id,token)
            if st>=200 and st<300:
                ids.append(product_id);accepted+=1
                print("QUEUED_PUBLISH",product_id,"status",st)
            else:
                failed+=1
                print("PUBLISH_API_ERROR",product_id,st)
                break
            time.sleep(0.5)
        for attempt in range(10):
            pending=[]
            for pid in ids:
                latest=get_json("/shops/%s/products/%s.json"%(shop_id,pid),token)
                if not latest.get("external"):pending.append(pid)
            print("BATCH_SYNC_POLL",start//BATCH_SIZE+1,"attempt",attempt+1,"synced",len(ids)-len(pending),"pending",len(pending))
            if not pending:break
            time.sleep(5)
        if failed or pending:
            print("STOPPED_AFTER_BATCH_FOR_SAFE_RETRY submitted=%d failed=%d pending=%d"%(accepted,failed,len(pending)))
            break
    refreshed=fetch_products(shop_id,token)
    bytitle={p.get("title"):p for p in refreshed}
    synched=sum(bool(bytitle.get(name,{}).get("external")) for name in expected_titles)
    print("FINAL_PRINTIFY_SYNCED=%d EXPECTED=%d PUBLISH_SUBMISSIONS_THIS_RUN=%d FAILED=%d"%(
        synched,len(expected_titles),accepted,failed))
    print("No order submission, no source product modification.")
    return 0 if failed==0 and synched==len(expected_titles) else 1

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("SAFE_PUBLISH_ERROR type=%s"%type(exc).__name__,file=sys.stderr)
        sys.exit(1)
