#!/usr/bin/env python3
"""Enna POD: read-only Printify audit. No edits, orders, publishing, or charges."""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

API = "https://api.printify.com/v1"

class PrintifyError(RuntimeError):
    pass

def get_json(path, token, opener=urllib.request.urlopen):
    if not path.startswith("/") or ".." in path or "//" in path:
        raise ValueError("Unsafe API path")
    req = urllib.request.Request(API + path, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json", "User-Agent": "Enna-Printify-Audit/1.0"})
    for i in range(4):
        try:
            with opener(req, timeout=35) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429 and i < 3:
                try:
                    pause = max(1.0, min(float(error.headers.get("Retry-After", "")), 20.0))
                except ValueError:
                    pause = 2 ** i
                time.sleep(pause)
                continue
            raise PrintifyError("Printify API HTTP %s (path %s)" % (error.code, path)) from None
        except urllib.error.URLError as error:
            raise PrintifyError("Printify unavailable: %s" % error.reason) from None
    raise PrintifyError("Rate-limit retry exhausted")

def choose_shop(shops, shop_id, hint):
    if shop_id:
        found = [s for s in shops if str(s.get("id")) == str(shop_id)]
        if len(found) == 1:
            return found[0]
        raise PrintifyError("PRINTIFY_SHOP_ID does not match an accessible shop")
    found = [s for s in shops if hint.casefold() in str(s.get("title", "")).casefold()]
    if len(found) == 1:
        return found[0]
    if len(shops) == 1 and str(shops[0].get("sales_channel", "")).lower() == "shopify":
        return shops[0]
    raise PrintifyError("Shop ambiguous. Supply exact PRINTIFY_SHOP_ID.")

def fetch_products(shop_id, token, fetch=get_json):
    output = []
    for page in range(1, 101):
        data = fetch("/shops/%d/products.json?limit=100&page=%d" % (int(shop_id), page), token)
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            raise PrintifyError("Unexpected product-page format")
        output.extend(data["data"])
        last_page = data.get("last_page")
        if (last_page is not None and page >= int(last_page)) or (last_page is None and len(data["data"]) < 100):
            return output
    raise PrintifyError("Product pagination safety limit hit")

def summarize_product(product):
    color_map = {}
    for option in product.get("options", []):
        if option.get("type", "").casefold() == "color" or "color" in option.get("name", "").casefold():
            for v in option.get("values", []):
                color_map[str(v["id"])] = str(v.get("title", v["id"]))
    enabled = [v for v in product.get("variants", []) if v.get("is_enabled")]
    enabled_ids = {str(x) for v in enabled for x in v.get("options", [])}
    colors = sorted({title for key, title in color_map.items() if key in enabled_ids})
    warnings = []
    if color_map and len(colors) < 2:
        warnings.append("single-color-manufacturer-variant")
    if not color_map:
        warnings.append("no-color-option-check-printed-background")
    if not enabled:
        warnings.append("no-enabled-variants")
    if not product.get("print_areas"):
        warnings.append("no-print-areas")
    return {
        "product_id": str(product.get("id", "")),
        "name": product.get("title", ""),
        "visible": bool(product.get("visible")),
        "blueprint_id": product.get("blueprint_id"),
        "print_provider_id": product.get("print_provider_id"),
        "enabled_variants": len(enabled),
        "manufacturer_colors": colors,
        "printed_backgrounds": sorted({
            a["background"] for a in product.get("print_areas", []) if a.get("background")
        }),
        "warnings": warnings,
    }

def audit(token, shop_id=None, hint="Pie & Po", include_unpublished=False, fetch=get_json):
    shops = fetch("/shops.json", token)
    if not isinstance(shops, list):
        raise PrintifyError("Unexpected shop-list format")
    shop = choose_shop(shops, shop_id, hint)
    products = [summarize_product(p) for p in fetch_products(shop["id"], token, fetch)]
    if not include_unpublished:
        products = [p for p in products if p["visible"]]
    warning_counts = Counter(w for p in products for w in p["warnings"])
    return {
        "shop": {"id": shop["id"], "title": shop.get("title"), "channel": shop.get("sales_channel")},
        "product_count": len(products),
        "warning_counts": dict(warning_counts),
        "products": products,
        "note": "Color is often printed artwork on phone cases, not a manufacturer variant. This script is read-only.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shop-id", default=os.getenv("PRINTIFY_SHOP_ID"))
    parser.add_argument("--shop-hint", default="Pie & Po")
    parser.add_argument("--include-unpublished", action="store_true")
    parser.add_argument("--output", help="Private local JSON report, never commit")
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()
    token = os.getenv("PRINTIFY_API_TOKEN")
    if not token:
        print("Missing GitHub Actions secret PRINTIFY_API_TOKEN. No work performed.", file=sys.stderr)
        return 2
    try:
        report = audit(token, args.shop_id, args.shop_hint, args.include_unpublished)
    except (PrintifyError, ValueError) as error:
        print("Audit stopped safely: " + str(error), file=sys.stderr)
        return 1
    counts = report["warning_counts"]
    print("Connected to Printify (READ ONLY)")
    print("Products checked:", report["product_count"])
    print("One manufacturer color:", counts.get("single-color-manufacturer-variant", 0))
    print("No manufacturer color selector:", counts.get("no-color-option-check-printed-background", 0))
    print("No products or orders changed.")
    if args.output:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if args.github_summary and path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("## Pie & Po — Printify read-only color audit\n")
            f.write("- Products checked: **%d**\n" % report["product_count"])
            f.write("- One manufacturer color: **%d**\n" % counts.get("single-color-manufacturer-variant", 0))
            f.write("- No manufacturer color selector: **%d**\n" % counts.get("no-color-option-check-printed-background", 0))
            f.write("- No publish, price, SKU or order changes\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
