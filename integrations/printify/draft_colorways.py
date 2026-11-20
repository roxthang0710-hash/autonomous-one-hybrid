#!/usr/bin/env python3
"""Printify colored case DRAFT creator. Creates only explicitly requested un-published Printify drafts."""
import argparse
import copy
import json
import os
import sys
import urllib.error
import urllib.request

from audit import get_json, PrintifyError

API = "https://api.printify.com/v1"
SHOP = 29780383
SOURCE = "6afb5733141ec60788085f34"
COLORS = {"cream": "#F2E9D9", "blush-pink": "#E8B9C8", "sage": "#A7B8A0", "sky-blue": "#B9D8ED", "lavender": "#C9C0DE"}

def read_source(token):
    shops = get_json("/shops.json", token)
    if not any(str(x.get("id")) == str(SHOP) for x in shops):
        raise PrintifyError("The token does not grant access to expected shop")
    p = get_json(f"/shops/{SHOP}/products/{SOURCE}.json", token)
    if str(p.get("id")) != SOURCE or p.get("blueprint_id") != 421 or p.get("print_provider_id") != 99:
        raise PrintifyError("Unexpected source blueprint/provider; refusing mutation")
    if not p.get("variants") or not p.get("print_areas"):
        raise PrintifyError("Source product missing variants / print areas")
    return p

def build_draft(source, color):
    if color not in COLORS:
        raise ValueError("Color outside approved palette")
    enabled = [v for v in source["variants"] if v.get("is_enabled")]
    vids = {int(v["id"]) for v in enabled}
    if len(vids) != 12:
        raise PrintifyError("Expected precisely 12 enabled iPhone case variants")
    areas = []
    for a in source["print_areas"]:
        associated = sorted(vids.intersection(a.get("variant_ids", [])))
        if not associated:
            continue
        placeholders = []
        for p in a.get("placeholders", []):
            images = []
            for img in p.get("images", []):
                if not img.get("id"):
                    raise PrintifyError("Image ID missing")
                images.append({k: img[k] for k in ("id", "x", "y", "scale", "angle") if k in img})
            if not images:
                raise PrintifyError("Missing printable images; cannot create colored background")
            ph = {"position": p["position"], "images": images}
            if p.get("decoration_method"):
                ph["decoration_method"] = p["decoration_method"]
            placeholders.append(ph)
        if not placeholders:
            raise PrintifyError("Empty placeholders")
        areas.append({"variant_ids": associated, "placeholders": placeholders, "background": COLORS[color]})
    if not areas:
        raise PrintifyError("No associated print areas")
    pretty = color.replace("-", " ").title()
    return {
        "title": f"[ENNA QA DRAFT - DO NOT PUBLISH] {source['title']} - {pretty}",
        "description": source.get("description") or "Phone case with Pie & Po original artwork",
        "tags": ["enna-colorway-qa", "not-for-publication", color],
        "blueprint_id": source["blueprint_id"],
        "print_provider_id": source["print_provider_id"],
        "variants": [{"id": int(v["id"]), "price": int(v["price"]), "is_enabled": True} for v in enabled],
        "print_areas": areas
    }

def post_draft(token, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{API}/shops/{SHOP}/products.json", method="POST", data=data,
        headers={"Authorization": "Bearer " + token, "User-Agent": "Enna-Printify-Draft/1.0",
                 "Content-Type": "application/json;charset=utf-8", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=55) as res:
            return json.load(res)
    except urllib.error.HTTPError as err:
        body = err.read(2048).decode("utf-8", errors="replace")
        raise PrintifyError(f"Draft creation HTTP {err.code}: {body[:500]}") from None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--color", choices=COLORS.keys(), default="cream")
    parser.add_argument("--create-draft", action="store_true")
    args = parser.parse_args()
    token = os.getenv("PRINTIFY_API_TOKEN_WRITE")
    if not token:
        print("Missing PRINTIFY_API_TOKEN_WRITE; refusing operation")
        return 2
    try:
        source = read_source(token)
        payload = build_draft(source, args.color)
        print("TOKEN VERIFIED: shop and source product readable; approved colors:", len(COLORS))
        print("Target:", args.color, "variants:", len(payload["variants"]), "print areas:", len(payload["print_areas"]))
        print("Backgrounds:", sorted({a["background"] for a in payload["print_areas"]}))
        if not args.create_draft:
            print("DRY RUN only. No product created.")
            return 0
        # A draft is created only with this explicit gate. Do not invoke the publish endpoint.
        created = post_draft(token, payload)
        id_ = str(created.get("id", ""))
        if not id_ or id_ == SOURCE:
            print("Creation response missing new product ID; review Printify manually")
            return 1
        print("DRAFT CREATED:", id_)
        print("PUBLISHED FLAG:", created.get("visible"), "EXTERNAL:", bool(created.get("external")))
        print("No publish endpoint invoked. Check draft and renderer QA before syncing.")
    except (PrintifyError, ValueError, TypeError) as ex:
        print("ABORTED:", ex)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
