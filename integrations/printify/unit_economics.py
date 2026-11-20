#!/usr/bin/env python3
"""Read-only Printify price-vs-production margin QA; Shopify checkout shipping & fees excluded."""
import os
import sys
from collections import defaultdict
from audit import get_json,fetch_products,choose_shop

SHOP=29780383
def main():
    token=os.getenv("PRINTIFY_API_TOKEN")
    if not token:
        return 2
    shop=choose_shop(get_json("/shops.json",token),os.getenv("PRINTIFY_SHOP_ID"),"Pie & Po")
    if int(shop["id"])!=SHOP:
        print("WRONG_SHOP");return 1
    products=fetch_products(SHOP,token)
    groups=defaultdict(list)
    invalid=[]
    negative=[]
    for p in products:
        for v in p.get("variants",[]):
            if not v.get("is_enabled"):
                continue
            try:
                cost=int(v["cost"]); price=int(v["price"])
            except (KeyError,ValueError,TypeError):
                invalid.append((p["id"],v.get("id"),"unknown-cost"))
                continue
            if not 0<cost<=price*3 or price<=0:
                invalid.append((p["id"],v.get("id"),"suspicious-price-cost"))
                continue
            contribution=price-cost
            groups[(p.get("blueprint_id"),p.get("print_provider_id"))].append(contribution)
            if contribution<=0:
                negative.append((p["id"],v.get("id"),contribution))
    print("PRINTIFY_PRICE_AUDIT products=%d families=%d incomplete_variant_costs=%d non_positive_margin_variants=%d" %(
          len(products),len(groups),len(invalid),len(negative)))
    for (blueprint,provider), margins in sorted(groups.items()):
        vals=sorted(margins)
        print("UNIT_ECONOMICS blueprint=%s provider=%s enabled_variants=%d min_before_shipping_and_fees=%.2f p10=%.2f median=%.2f max=%.2f" %(
            blueprint,provider,len(vals),vals[0]/100,vals[max(0,int(len(vals)*.1))]/100,vals[len(vals)//2]/100,vals[-1]/100))
    if invalid or negative:
        print("FLAGGED variants with missing, suspect, or non-positive cost margin; do not change prices automatically.")
        return 1
    print("VALIDATE: no model is sold below Printify production cost before shipping, fees or tax.")
    return 0
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as ex:
        print("UNIT_ECONOMICS_ABORTED",type(ex).__name__)
        sys.exit(1)
