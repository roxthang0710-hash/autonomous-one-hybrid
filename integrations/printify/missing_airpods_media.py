#!/usr/bin/env python3
"""Read-only Printify published AirPods product mockup URL report for Shopify media repair."""
import os,sys,urllib.parse
from audit import get_json

SHOP=29780383
NEEDS={
"6b009779a4ba74b1f3029202":"Cocoa Cream",
"6b00977bfa28954d210707f8":"Cocoa Sage Green",
"6b00977c35ad9f69ba0fb699":"Cocoa Sky Blue",
"6b009784bd5cf5fed70fe1de":"Christmas Blush Pink",
"6b009785fa28954d21070807":"Christmas Cream",
"6b00978856c934f3660b7821":"Christmas Sage Green",
"6b009789d5e992fad203c7fe":"Christmas Sky Blue",
}
def main():
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("MISSING_TOKEN")
        return 2
    bad=0
    for pid,label in NEEDS.items():
        p=get_json("/shops/%s/products/%s.json"%(SHOP,pid),token)
        images=[img for img in p.get("images",[]) if img.get("src")]
        favored=sorted(images,key=lambda x:(not x.get("is_default",False),str(x.get("position",""))!="front"))
        picks=favored[:2]
        if not picks:
            print("NO_IMAGES",pid,label)
            bad+=1
            continue
        for i,img in enumerate(picks):
            url=img["src"]
            u=urllib.parse.urlparse(url)
            if u.scheme!="https" or u.hostname!="images.printify.com":
                print("REJECTED_HOST",pid,u.hostname)
                bad+=1
                break
            print("PRINTIFY_MEDIA",pid,label,"sample",i,"url",url,"variant_ids",len(img.get("variant_ids",[])))
    # Last AirPods colorway's device-specific image links for two Shopify variants without mockups.
    pid="6b00977c35ad9f69ba0fb699"
    p=get_json("/shops/%s/products/%s.json"%(SHOP,pid),token)
    for v in p.get("variants",[]):
        print("SOURCE_VARIANT",v.get("id"),v.get("title"),"sku",v.get("sku"))
        candidates=[img for img in p.get("images",[]) if v.get("id") in (img.get("variant_ids") or []) and img.get("src")]
        preferred=sorted(candidates,key=lambda im: (str(im.get("position",""))!="front",not bool(im.get("is_default"))))
        if preferred:
            print("SOURCE_VARIANT_MEDIA",v.get("id"),v.get("title"),"url",preferred[0]["src"])
    return int(bad>0)
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("MEDIA_LOOKUP_ABORTED",type(e).__name__)
        sys.exit(1)
