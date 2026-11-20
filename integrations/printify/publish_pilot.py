#!/usr/bin/env python3
"""Publish ONE vetted Printify phone-case colorway to connected Shopify. No orders."""
import json,os,sys,time,urllib.request,urllib.error
from audit import get_json,choose_shop
from stage_colorways import PAL
API="https://api.printify.com/v1"
PILOT_ID="6b007b36d5e992fad203b1a7"
EXPECTED_TITLE="Who Ate My Snack? — Phone Case | Pie & Po — Colorway: Blush Pink"

def main():
    if os.getenv("ENNA_APPROVE_ONE_PUBLISH")!="YES":
        print("Publish guard disabled")
        return 2
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("Missing write token")
        return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    channel=str(shop.get("sales_channel","")).casefold()
    if "shopify" not in channel:
        print("BLOCKED: wrong sales channel",channel)
        return 1
    shop_id=shop["id"]
    url="/shops/%s/products/%s.json"%(shop_id,PILOT_ID)
    p=get_json(url,token)
    enabled=[v for v in p.get("variants",[]) if v.get("is_enabled")]
    backgrounds={a.get("background") for a in p.get("print_areas",[])}
    if p.get("title")!=EXPECTED_TITLE or backgrounds!={PAL["Blush Pink"]} or len(enabled)!=12 or len(p.get("images",[]))<4:
        print("BLOCKED: pilot QA mismatch")
        return 1
    if any(int(v.get("price",0))-int(v.get("cost",0))<800 for v in enabled):
        print("BLOCKED: pre-shipping margin too narrow")
        return 1
    if p.get("external"):
        print("ALREADY_PUBLISHED_EXTERNAL",p.get("external",{}).get("id"))
        return 0
    if p.get("is_locked"):
        print("PUBLISH_ALREADY_IN_PROGRESS")
        return 0
    body={"title":True,"description":True,"images":True,"variants":True,"tags":True,
          "keyFeatures":True,"shipping_template":True}
    req=urllib.request.Request(API+"/shops/%s/products/%s/publish.json"%(shop_id,PILOT_ID),
         data=json.dumps(body).encode(),method="POST",
         headers={"Authorization":"Bearer "+token,"Content-Type":"application/json",
                  "Accept":"application/json","User-Agent":"Enna-Printify-PublishPilot/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            status=response.status
    except urllib.error.HTTPError as ex:
        print("PUBLISH_REJECTED_HTTP",ex.code)
        return 1
    print("PUBLISH_PILOT_REQUEST_ACCEPTED http=%d product_id=%s"%(status,PILOT_ID))
    for attempt in range(5):
        time.sleep(6)
        p=get_json(url,token)
        print("PUBLISH_CHECK attempt=%d locked=%s external=%s" % (attempt+1,p.get("is_locked"),bool(p.get("external"))))
        if p.get("external"):
            print("PUBLISH_SUCCEEDED_EXTERNAL_ID",p["external"].get("id","(missing)"))
            break
    print("No other products published; Shopify product status to be independently checked.")
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("PUBLISH_FAILED type=%s"%type(e).__name__,file=sys.stderr)
        sys.exit(1)
