#!/usr/bin/env python3
"""QA every staged Printify pastel phone case: real print layer, preview and price."""
import os,sys,time
from audit import get_json,choose_shop,fetch_products
from stage_colorways import PAL,PHONE_CASE_SOURCES
from pilot_mockup_qa import evaluate_image

def main():
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token: return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    all_products=fetch_products(shop["id"],token)
    byid={p["id"]:p for p in all_products}
    original={byid[pid]["title"].strip().casefold():byid[pid] for pid in PHONE_CASE_SOURCES}
    checked=0
    good=0
    issues=[]
    per_color={}
    for p in all_products:
        title=str(p.get("title",""))
        if " — Colorway: " not in title:continue
        root,color=title.rsplit(" — Colorway: ",1)
        source=original.get(root.strip().casefold())
        if source is None:continue
        checked+=1
        expected=PAL.get(color)
        source_art={str(i.get("id")) for a in source.get("print_areas",[]) for place in a.get("placeholders",[]) for i in place.get("images",[])}
        clone_art={str(i.get("id")) for a in p.get("print_areas",[]) for place in a.get("placeholders",[]) for i in place.get("images",[])}
        backgrounds={a.get("background") for a in p.get("print_areas",[])}
        variants=[v for v in p.get("variants",[]) if v.get("is_enabled")]
        is_structure_ok=bool(expected) and backgrounds=={expected} and source_art==clone_art and \
            p.get("blueprint_id")==source.get("blueprint_id") and \
            p.get("print_provider_id")==source.get("print_provider_id") and \
            len(variants)==len([v for v in source.get("variants",[]) if v.get("is_enabled")])
        ratios=[]
        for image in p.get("images",[])[:3]:
            try:
                rgb=tuple(int(expected.lstrip("#")[i:i+2],16) for i in (0,2,4))
                val=evaluate_image(image["src"],rgb)
                if val: ratios.append(val["near30"])
            except Exception:
                pass
            if ratios and max(ratios)>0.012: break
        is_color_ok=bool(ratios) and max(ratios)>0.012
        ok=is_structure_ok and is_color_ok
        good+=int(ok)
        per_color.setdefault(color,[0,0])[0]+=1
        per_color[color][1]+=int(ok)
        print("QA_COLORWAY id=%s color=%s blueprint=%s struct=%s visual=%s max30=%.4f images=%d" % (
            p["id"],color,p.get("blueprint_id"),is_structure_ok,is_color_ok,max(ratios or [0]),len(p.get("images",[]))))
        if not ok: issues.append(p["id"])
    print("QA_TOTAL=%d PASSED=%d FAILED=%d COLORS=%s" % (
        checked,good,checked-good,per_color))
    if checked != len(PHONE_CASE_SOURCES)*4 or good != checked:
        print("NOT_READY_FOR_PUBLISH count_or_qa_problem",file=sys.stderr)
        return 1
    print("ALL_COLORWAY_MOCKUPS_READY_FOR_REVIEW; NO_PUBLISH_PERFORMED")
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("QA_FAILED type=%s"%type(e).__name__,file=sys.stderr)
        sys.exit(1)
