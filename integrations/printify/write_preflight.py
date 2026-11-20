#!/usr/bin/env python3
"""Preflight Printify *write* credential, but only make GET requests."""
import os
import sys
from collections import Counter
from audit import choose_shop, get_json, fetch_products

def main():
    token = os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("WRITE_TOKEN_SECRET_MISSING")
        return 2
    shops = get_json("/shops.json", token)
    shop = choose_shop(shops, os.getenv("PRINTIFY_SHOP_ID"), "Pie & Po")
    products = fetch_products(shop["id"], token)
    kinds = Counter((p.get("blueprint_id"),p.get("print_provider_id")) for p in products)
    print("WRITE_TOKEN_READ_PREFLIGHT_OK shop_id=%s products=%d" % (shop["id"], len(products)))
    print("Blueprints/providers:", dict(kinds))
    for p in products:
        variants = [v for v in p.get("variants",[]) if v.get("is_enabled")]
        prices = [int(v.get("price") or 0) for v in variants]
        costs = [int(v.get("cost") or 0) for v in variants]
        backgrounds = sorted(set(a.get("background") for a in p.get("print_areas",[]) if a.get("background")))
        art = sum(len(pl.get("images",[])) for a in p.get("print_areas",[]) for pl in a.get("placeholders",[]))
        print("source_id=%s blueprint=%s provider=%s enabled=%d printed_bg=%s art_layers=%d min_price_cents=%s max_cost_cents=%s visible=%s" % (
            p.get("id"),p.get("blueprint_id"),p.get("print_provider_id"),len(variants),
            "|".join(backgrounds),art,min(prices) if prices else "none",max(costs) if costs else "none",p.get("visible")))
    print("No products modified. GET-only calls.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Do not print secrets nor raw server responses.
        print("PREFLIGHT_FAILED type=%s" % type(exc).__name__, file=sys.stderr)
        sys.exit(1)
