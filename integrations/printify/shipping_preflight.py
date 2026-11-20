#!/usr/bin/env python3
"""Read-only US shipping cost and contribution safety check per Printify product type."""
import os,sys
from collections import defaultdict
from audit import get_json, choose_shop, fetch_products
def main():
    token=os.getenv("PRINTIFY_API_TOKEN")
    if not token: return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    prods=fetch_products(shop["id"],token)
    grouped=defaultdict(list)
    for p in prods:
        if "Colorway:" in p.get("title",""):continue
        grouped[(p["blueprint_id"],p["print_provider_id"])].append(p)
    for (blueprint,provider),items in sorted(grouped.items()):
        try:
            ship=get_json("/catalog/blueprints/%s/print_providers/%s/shipping.json"%(blueprint,provider),token)
        except Exception as ex:
            print("SHIPPING_UNAVAILABLE blueprint=%d provider=%d type=%s"%(blueprint,provider,type(ex).__name__))
            continue
        profiles=ship.get("profiles",[]) if isinstance(ship,dict) else ship
        if not isinstance(profiles,list): profiles=[]
        us=[]
        for p in profiles:
            if "US" in (p.get("countries") or []):
                unit=(p.get("first_item") or {}).get("cost")
                if unit is not None: us.append(int(unit))
        prows=[v for item in items for v in item.get("variants",[]) if v.get("is_enabled")]
        if not prows: continue
        lowprice=min(int(v["price"]) for v in prows)
        highcost=max(int(v.get("cost",0)) for v in prows)
        worstship=max(us) if us else None
        # Conservative estimate if seller absorbs 100% of US shipping.
        # Shopify payment fees/tax are NOT verified and excluded from this estimate.
        gross_before_fees=lowprice-highcost-worstship if worstship is not None else None
        print("COST_CHECK blueprint=%d provider=%d product_count=%d min_retail_cents=%d max_production_cents=%d us_first_shipping_cents=%s shipping_included_contribution_before_fees_cents=%s"%(
            blueprint,provider,len(items),lowprice,highcost,worstship,gross_before_fees))
    return 0
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("COST_PREFLIGHT_ERROR type=%s"%type(exc).__name__,file=sys.stderr)
        sys.exit(1)
