#!/usr/bin/env python3
"""Preflight Printify *write* credential, but only make GET requests."""
import os
import hashlib
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
    staged=[p for p in products if " — Colorway: " in str(p.get("title",""))]
    for p in staged:
        external=p.get("external")
        external_id=external.get("id") if isinstance(external,dict) else None
        digest=hashlib.sha256(str(p.get("id","")).encode("utf-8")).hexdigest()[:12]
        print("SYNC_STATUS hash=%s locked=%s external=%s visible=%s" % (
            digest,p.get("is_locked"),bool(external_id),p.get("visible")))
    print("SYNC_TOTAL staged=%d external=%d locked_unlinked=%d unlocked_unlinked=%d" % (
        len(staged),sum(bool(p.get("external",{}).get("id")) for p in staged),
        sum(bool(p.get("is_locked")) and not bool(p.get("external",{}).get("id")) for p in staged),
        sum(not bool(p.get("is_locked")) and not bool(p.get("external",{}).get("id")) for p in staged)))
    print("No products modified. GET-only calls.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Do not print secrets nor raw server responses.
        print("PREFLIGHT_FAILED type=%s" % type(exc).__name__, file=sys.stderr)
        sys.exit(1)
