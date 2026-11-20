#!/usr/bin/env python3
"""Enna Printify: safe, idempotent colored-background draft creator. NEVER publishes."""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from audit import get_json, choose_shop, fetch_products

API = "https://api.printify.com/v1"
PAL = {"Blush Pink": "#EBC3D0", "Sage Green": "#B5C8BA", "Sky Blue": "#BDD8EF", "Lavender": "#D4CAE5", "Cream": "#EFE5D7"}
# Pilot first: exactly one approved source, one color, unpublished.
PILOT = [("6afb5733141ec60788085f34", "Blush Pink")]
# Nine smartphone case models; AirPods white plastic cases require separate QA.
PHONE_CASE_SOURCES = [
    "6afb5733141ec60788085f34", "6afb579f2bd121e7b20aa7e3",
    "6afb57a4a4a5022c1007ae4d", "6afb57aaa44fa49e570d0843",
    "6afbd25f5d3c51e94d0c6ba2", "6afbd26a63e250153506caee",
    "6afbd26d1e97b3cc9303ef04", "6afbd2702be6156d0902c8e1",
    "6afbe2194770279e860d077d",
]
PHONE_COLORS = ["Blush Pink","Cream","Sage Green","Sky Blue"]
PHONE_BATCH = [(source,color) for source in PHONE_CASE_SOURCES for color in PHONE_COLORS]

def build_payload(source, color):
    if color not in PAL:
        raise ValueError("Color not in tested pastel palette")
    enabled = [v for v in source.get("variants", []) if v.get("is_enabled") and v.get("is_available", True)]
    if not enabled:
        raise ValueError("No enabled/available source variants")
    allowed_ids = {int(v["id"]) for v in enabled}
    if min(int(v["price"]) - int(v.get("cost", v["price"])) for v in enabled) < 800:
        raise ValueError("Insufficient pre-shipping price minus production cost")
    areas = []
    for area in source.get("print_areas", []):
        related = [int(i) for i in area.get("variant_ids", []) if int(i) in allowed_ids]
        if not related:
            continue
        placeholders = []
        for p in area.get("placeholders", []):
            images = []
            for img in p.get("images", []):
                if not img.get("id"):
                    raise ValueError("Print layer lacks library image ID")
                art = {k: img[k] for k in ("id", "x", "y", "scale", "angle") if k in img}
                if "pattern" in img:
                    art["pattern"] = img["pattern"]
                images.append(art)
            if not images:
                raise ValueError("Cannot create blank print-area")
            placeholder = {"position": p["position"], "images": images}
            if p.get("decoration_method"):
                placeholder["decoration_method"] = p["decoration_method"]
            placeholders.append(placeholder)
        if not placeholders:
            raise ValueError("Print area lacks placeholders")
        areas.append({"variant_ids": related, "placeholders": placeholders, "background": PAL[color]})
    covered = {vid for a in areas for vid in a["variant_ids"]}
    if covered != allowed_ids:
        raise ValueError("Print areas do not cover every selected variant")
    title = str(source["title"]).split(" — Colorway:")[0] + " — Colorway: " + color
    description = str(source.get("description") or "")
    description += "<p>Colorway: " + color + ". This is a PRINTED background color; the underlying case material may be a different color. View mockups before purchasing.</p>"
    payload = {
        "title": title,
        "description": description,
        "blueprint_id": int(source["blueprint_id"]),
        "print_provider_id": int(source["print_provider_id"]),
        "variants": [{"id": int(v["id"]), "price": int(v["price"]), "is_enabled": True} for v in enabled],
        "print_areas": areas,
        "tags": list(dict.fromkeys([*(source.get("tags") or []), "Pie & Po", "printed colorway", color]))[:10],
    }
    return payload

def create_product(shop, token, payload):
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(API+"/shops/%s/products.json" % int(shop), data=data, method="POST",headers={
        "Authorization": "Bearer "+token, "User-Agent": "Enna-Printify-Colorway/1.0",
        "Content-Type": "application/json","Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as error:
        # Server response might contain shop data, never echo it in public Actions.
        print("PRINTIFY_CREATE_FAILED http=%d" % error.code, file=sys.stderr)
        raise RuntimeError("Printify product creation rejected") from None

def stage(token, records, apply=False, specs=PILOT):
    shop = choose_shop(get_json("/shops.json", token), os.getenv("PRINTIFY_SHOP_ID"), "Pie & Po")
    existing = fetch_products(shop["id"], token)
    by_id = {p["id"]: p for p in existing}
    titles = {p["title"].strip().casefold():p for p in existing}
    created = []
    for source_id, color in specs:
        if source_id not in by_id:
            raise ValueError("Source product not in connected shop")
        source = by_id[source_id]
        if source["blueprint_id"] not in (421,269,1273,1505):
            raise ValueError("Unapproved product blueprint")
        payload = build_payload(source,color)
        key = payload["title"].strip().casefold()
        if key in titles:
            found = titles[key]
            if {a.get("background") for a in found.get("print_areas",[])} != {PAL[color]}:
                raise RuntimeError("Existing titled product has mismatched background")
            print("SKIPPED_EXISTING source=%s color=%s draft_id=%s visible=%s preview_count=%d" % (source_id,color,found.get("id"),found.get("visible"),len(found.get("images",[]))))
            if found.get("images"):
                print("QA_PREVIEW_URL="+str(found["images"][0].get("src","")))
            continue
        if not apply:
            print("DRY_RUN source=%s color=%s variants=%d background=%s print_areas=%d" % (
                source_id,color,len(payload["variants"]),PAL[color],len(payload["print_areas"])))
            continue
        item = create_product(shop["id"],token,payload)
        item_id = item.get("id")
        if not item_id:
            raise ValueError("Create returned no id")
        # Fresh readback from server; do not infer success from status alone.
        readback = get_json("/shops/%s/products/%s.json" % (shop["id"], item_id), token)
        bgs = {a.get("background") for a in readback.get("print_areas",[])}
        count = len([v for v in readback.get("variants",[]) if v.get("is_enabled")])
        correct = (readback.get("title") == payload["title"] and
            PAL[color] in bgs and count >= len(payload["variants"]) and
            bool(readback.get("images")) and
            all(v.get("price") for v in readback.get("variants",[]) if v.get("is_enabled")))
        print("CREATED_DRAFT id=%s source=%s color=%s verified=%s visible=%s enabled_variants=%d images=%d" % (
            item_id,source_id,color,correct,readback.get("visible"),count,len(readback.get("images",[]))))
        if readback.get("images"):
            print("QA_PREVIEW_URL="+str(readback["images"][0].get("src","")))
        created.append((item_id,correct))
        time.sleep(0.25)
        titles[key] = readback
        if not correct:
            raise RuntimeError("Created product failed readback; do not publish")
    print("TOTAL_CREATED=%d VERIFIED=%d NO_PUBLISH_CALLED" % (len(created),sum(ok for _,ok in created)))
    return int(not all(ok for _,ok in created))

def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--apply",action="store_true")
    arg.add_argument("--pilot",action="store_true")
    arg.add_argument("--all-phone-cases",action="store_true")
    ns=arg.parse_args()
    if ns.apply and os.getenv("ENNA_CONFIRM_DRAFT_CREATION") != "YES":
        print("Explicit staging guard missing",file=sys.stderr)
        return 2
    token=os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("Write token secret missing",file=sys.stderr)
        return 2
    try:
        return stage(token, records=None, apply=ns.apply, specs=PHONE_BATCH if ns.all_phone_cases else PILOT)
    except (ValueError,RuntimeError,urllib.error.URLError) as exc:
        print("STAGING_STOPPED type=%s" % type(exc).__name__, file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
