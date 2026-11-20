#!/usr/bin/env python3
"""Verify a Printify colorway draft exists without editing or publishing anything."""
import os
import sys
from audit import fetch_products, get_json

SHOP=29780383
EXPECTED_SOURCE="6afb5733141ec60788085f34"
EXPECTED_TITLE_PREFIX="[ENNA QA DRAFT - DO NOT PUBLISH]"
EXPECTED_BG="#F2E9D9"

def main():
    token=os.getenv("PRINTIFY_API_TOKEN")
    if not token:
        print("READ SECRET MISSING")
        return 2
    p=get_json(f"/shops/{SHOP}/products/{EXPECTED_SOURCE}.json",token)
    originals={int(v["id"]):int(v["price"]) for v in p.get("variants",[]) if v.get("is_enabled")}
    products=fetch_products(SHOP,token)
    drafts=[x for x in products if str(x.get("title","")).startswith(EXPECTED_TITLE_PREFIX) and "Cream" in str(x.get("title",""))]
    print("ALL_PRODUCTS:",len(products),"CREAM_DRAFTS:",len(drafts))
    if len(drafts)!=1:
        print("EXPECTED ONE DRAFT; found",len(drafts))
        return 1
    d=drafts[0]
    print("DRAFT_ID:",d.get("id"))
    print("DRAFT_VISIBLE:",d.get("visible"))
    print("DRAFT_EXTERNAL_LINK:",bool(d.get("external")))
    print("SOURCE_ID_UNCHANGED:",p.get("id")==EXPECTED_SOURCE)
    actual={int(v["id"]):int(v["price"]) for v in d.get("variants",[]) if v.get("is_enabled")}
    backgrounds={a.get("background") for a in d.get("print_areas",[])}
    print("PRICE_VARIANTS_EQUAL:",actual==originals)
    print("BACKGROUNDS:",sorted(str(x) for x in backgrounds))
    print("MOCKUP_COUNT:",len(d.get("images") or []))
    if actual!=originals or backgrounds!={EXPECTED_BG} or bool(d.get("external")):
        print("QA FAILED: mismatch or unexpectedly linked")
        return 1
    print("DRAFT_QA_PASS: no Shopify publishing link")
    return 0

if __name__ == "__main__":
    sys.exit(main())
