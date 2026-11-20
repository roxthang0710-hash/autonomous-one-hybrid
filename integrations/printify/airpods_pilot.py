#!/usr/bin/env python3
"""AirPods printed-colorway preflight and ONE guarded unpublished draft."""
import os
import sys
from audit import get_json, choose_shop, fetch_products
from stage_colorways import build_payload, create_product, PAL

SOURCE_ID = "6afb5760a4a5022c1007adfb"
COLOR = "Blush Pink"
SHOP_ID = 29780383

def main():
    token = os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("MISSING_WRITE_TOKEN")
        return 2
    shop = choose_shop(get_json("/shops.json", token), os.getenv("PRINTIFY_SHOP_ID"), "Pie & Po")
    if int(shop["id"]) != SHOP_ID:
        print("WRONG_SHOP")
        return 1
    source = get_json("/shops/%s/products/%s.json" % (SHOP_ID, SOURCE_ID), token)
    if str(source.get("id")) != SOURCE_ID or (source.get("blueprint_id"), source.get("print_provider_id")) != (1505, 23):
        print("WRONG_BLUEPRINT_OR_PRODUCT")
        return 1
    for index, area in enumerate(source.get("print_areas", [])):
        print("SOURCE_AREA", index, "variant_count", len(area.get("variant_ids", [])),
              "placeholders", len(area.get("placeholders", [])),
              "layers", [len(x.get("images", [])) for x in area.get("placeholders", [])],
              "positions", [x.get("position") for x in area.get("placeholders", [])])
    payload = build_payload(source, COLOR)
    if len(payload["variants"]) != 7 or not payload.get("print_areas"):
        print("WRONG_VARIANTS_OR_PRINT_AREAS")
        return 1
    print("AIRPODS_DRAFT_PREVIEW_OK", "color", COLOR, "background", PAL[COLOR],
          "variants", len(payload["variants"]), "print_areas", len(payload["print_areas"]))
    if "--apply" not in sys.argv:
        print("DRY_RUN_ONLY")
        return 0
    if os.getenv("ENNA_CONFIRM_AIRPODS_DRAFT_CREATION") != "YES":
        print("DRAFT_CREATE_GUARD_NOT_SET")
        return 2
    existing = fetch_products(SHOP_ID, token)
    matches = [p for p in existing if str(p.get("title", "")).strip().casefold() == payload["title"].strip().casefold()]
    if len(matches) > 1:
        print("DUPLICATE_TITLE_FOUND")
        return 1
    if matches:
        item = matches[0]
        print("AIRPODS_EXISTING_DRAFT", item.get("id"))
    else:
        item = create_product(SHOP_ID, token, payload)
        print("AIRPODS_CREATED_DRAFT", item.get("id"))
    current = get_json("/shops/%s/products/%s.json" % (SHOP_ID, item["id"]), token)
    backgrounds = {a.get("background") for a in current.get("print_areas", [])}
    enabled = [v for v in current.get("variants", []) if v.get("is_enabled")]
    correct = (current.get("title") == payload["title"] and
               backgrounds == {PAL[COLOR]} and len(enabled) == len(payload["variants"]) and
               len(current.get("images", [])) >= 1 and not current.get("external"))
    print("AIRPODS_DRAFT_QA", correct, "id", current.get("id"), "mockups", len(current.get("images", [])),
          "external", bool(current.get("external")), "background", sorted(backgrounds))
    print("Never called Printify publish endpoint")
    return 0 if correct else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("AIRPODS_PILOT_ABORTED", type(exc).__name__, str(exc) if isinstance(exc, ValueError) else "")
        sys.exit(1)
