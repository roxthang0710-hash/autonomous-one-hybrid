#!/usr/bin/env python3
"""Check whether Printify preview images visibly contain the selected print color."""
import io
import os
import sys
import urllib.parse
import urllib.request
from PIL import Image
from audit import get_json, choose_shop

PILOT_ID = "6b007b36d5e992fad203b1a7"
TARGET = (235,195,208)  # Blush Pink #EBC3D0

def evaluate_image(url, target=TARGET):
    p=urllib.parse.urlparse(url)
    if p.scheme!="https" or p.hostname!="images.printify.com":
        return None
    req=urllib.request.Request(url,headers={"User-Agent":"EnnaQA/1.0"})
    with urllib.request.urlopen(req,timeout=30) as f:
        b=f.read(7_000_000)
    img=Image.open(io.BytesIO(b)).convert("RGB")
    img.thumbnail((360,360))
    pixels=list(img.getdata())
    if not pixels: return None
    def close(c,limit):
        return sum(1 for px in pixels if sum((px[i]-c[i])**2 for i in range(3)) < limit*limit)/len(pixels)
    return {"width":img.width,"height":img.height,"near30":round(close(target,30),4),
            "near65":round(close(target,65),4),"near95":round(close(target,95),4)}

def main():
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token: return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    product=get_json("/shops/%s/products/%s.json"%(shop["id"],PILOT_ID),token)
    if product.get("blueprint_id")!=421:
        print("Wrong blueprint for pilot")
        return 1
    scores=[]
    for i,img in enumerate(product.get("images",[])[:12]):
        try: result=evaluate_image(img.get("src",""))
        except Exception as e:
            print("IMAGE_QA_ERROR index=%d type=%s"%(i,type(e).__name__))
            continue
        if result is not None:
            scores.append(result)
            print("MOCKUP color=Blush_Pink image=%d ratio30=%s ratio65=%s ratio95=%s size=%dx%d"%(
                i,result["near30"],result["near65"],result["near95"],result["width"],result["height"]))
    if not scores:
        print("NO_VALID_MOCKUPS")
        return 1
    print("MAX_NEAR30",max(x["near30"] for x in scores),"MAX_NEAR65",max(x["near65"] for x in scores))
    print("QA_RESULT", "VISIBLE_COLOR" if max(x["near30"] for x in scores)>0.015 else "COLOR_NOT_VERIFIED")
    return 0 if max(x["near30"] for x in scores)>0.015 else 1

if __name__=="__main__":
    sys.exit(main())
