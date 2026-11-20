#!/usr/bin/env python3
"""Visual color coverage heuristic for one unpublished AirPods QA draft (read-only)."""
import os
import sys
from audit import get_json
from pilot_mockup_qa import evaluate_image

SHOP=29780383
SOURCE="6afb5760a4a5022c1007adfb"
DRAFT="6b0094d87f5076e0c30c96b3"
TARGET=(235, 195, 208)  # Blush Pink

def sample(product):
    imgs=product.get("images") or []
    selected=[img for img in imgs if str(img.get("position","")).lower()=="front"]
    if not selected:
        selected=imgs
    scores=[]
    for image in selected[:8]:
        try:
            result=evaluate_image(image.get("src",""),TARGET)
            if result: scores.append(result)
        except Exception as exc:
            print("MOCKUP_SKIPPED",type(exc).__name__)
    print("MOCKUP_COUNT",len(imgs),"FRONT_SAMPLED",len(scores))
    return scores

def main():
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("MISSING_TOKEN")
        return 2
    original=get_json(f"/shops/{SHOP}/products/{SOURCE}.json",token)
    variant=get_json(f"/shops/{SHOP}/products/{DRAFT}.json",token)
    if variant.get("blueprint_id")!=original.get("blueprint_id") or variant.get("print_provider_id")!=original.get("print_provider_id"):
        print("SOURCE_MISMATCH")
        return 1
    if {a.get("background") for a in variant.get("print_areas",[])}!={"#EBC3D0"}:
        print("WRONG_BACKGROUND")
        return 1
    old=sample(original)
    new=sample(variant)
    if not old or not new:
        print("AIRPODS_IMAGE_QA_UNAVAILABLE")
        return 1
    base=max(x["near30"] for x in old)
    pink=max(x["near30"] for x in new)
    print("AIRPODS_PINK_BASELINE",base,"DRAFT",pink,"INCREASE",round(pink-base,4))
    if pink<0.018 or pink-base<0.005:
        print("AIRPODS_COLOR_NOT_VISIBLY_VERIFIED")
        return 1
    print("AIRPODS_FRONT_PRINTED_PINK_VERIFIED")
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as exc:
        print("AIRPODS_QA_ERROR",type(exc).__name__)
        sys.exit(1)
