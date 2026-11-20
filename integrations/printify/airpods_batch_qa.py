#!/usr/bin/env python3
"""Read-only structural and color-pixel QA of 16 published AirPods colorways."""
import os
import sys
from audit import get_json, fetch_products
from airpods_batch import SHOP, SOURCE_IDS, COLORS
from stage_colorways import PAL
from pilot_mockup_qa import evaluate_image

def colored_ratio(image, hex_color):
    col=tuple(int(hex_color.lstrip("#")[i:i+2],16) for i in (0,2,4))
    try:
        result=evaluate_image(image.get("src",""),col)
        return result["near30"] if result else 0
    except Exception:
        return 0

def main():
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        return 2
    sources=[get_json("/shops/%s/products/%s.json"%(SHOP,pid),token) for pid in SOURCE_IDS]
    catalog=fetch_products(SHOP,token)
    grouped={}
    for item in catalog:
        grouped.setdefault(str(item.get("title","")),[]).append(item)
    ok=0
    visual=0
    missing=[]
    failures=[]
    for source in sources:
        original_art={str(i["id"]) for a in source.get("print_areas",[]) for p in a.get("placeholders",[]) for i in p.get("images",[])}
        original_enabled={int(v["id"]):int(v["price"]) for v in source["variants"] if v.get("is_enabled")}
        for color in COLORS:
            title=source["title"]+" — Colorway: "+color
            matches=grouped.get(title,[])
            if len(matches)!=1:
                missing.append((source["id"],color,len(matches)))
                continue
            d=matches[0]
            layers={str(i["id"]) for a in d.get("print_areas",[]) for p in a.get("placeholders",[]) for i in p.get("images",[])}
            bgs={a.get("background") for a in d.get("print_areas",[])}
            enabled={int(v["id"]):int(v["price"]) for v in d.get("variants",[]) if v.get("is_enabled")}
            structure=(
                d.get("blueprint_id")==1505 and d.get("print_provider_id")==23
                and bgs=={PAL[color]} and layers==original_art
                and enabled==original_enabled and len(enabled)==7
                and bool(d.get("external")) and bool(d.get("images"))
                and ("physical AirPods case and unprinted back/sides remain" in d.get("description","") or "supplier\'s physical AirPods case remains white" in d.get("description",""))
            )
            if not structure:
                failures.append((source["id"],color,"structure"))
                continue
            ok+=1
            score=0
            for img in (d.get("images") or [])[:8]:
                score=max(score,colored_ratio(img,PAL[color]))
                if score>=0.06:
                    break
            if score>=0.06:
                visual+=1
            else:
                failures.append((source["id"],color,"color_render"))
            print("AIRPODS_COLOR_QA source=%s color=%s structural=%s score30=%.4f mockups=%d"%
                  (source["id"],color,structure,score,len(d.get("images",[]))))
    print("AIRPODS_FINAL_QA total_expected=16 structural_ok=%d visually_colorful=%d missing=%d failed=%d" %
          (ok,visual,len(missing),len(failures)))
    for item in missing: print("MISSING",*item)
    for item in failures: print("FAILED",*item)
    if len(missing)==0 and len(failures)==0 and ok==16 and visual==16:
        print("AIRPODS_PUBLISHED_ALL_PASS")
        return 0
    return 1

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as exc:
        print("AIRPODS_QA_EXCEPTION",type(exc).__name__)
        sys.exit(1)
