#!/usr/bin/env python3
"""Read-only image transparency QA for Printify artwork (never changes products)."""
import hashlib
import io
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

from PIL import Image, UnidentifiedImageError
from audit import PrintifyError, choose_shop, fetch_products, get_json

MAX_BYTES = 22 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 40_000_000


def source_urls(product):
    urls = []
    seen = set()
    for area in product.get("print_areas") or []:
        for placeholder in area.get("placeholders") or []:
            for art in placeholder.get("images") or []:
                src = art.get("src")
                if src and src not in seen:
                    seen.add(src)
                    urls.append(src)
    return urls


def permitted_source(url):
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "printify.com" or host.endswith(".printify.com")) and not parsed.username and not parsed.password


def transparency_from_bytes(raw):
    with Image.open(io.BytesIO(raw)) as image:
        if image.width * image.height > Image.MAX_IMAGE_PIXELS:
            raise ValueError("image too large")
        if image.mode in ("RGB", "L", "CMYK", "1") and "transparency" not in image.info:
            return "opaque"
        alpha = image.convert("RGBA").getchannel("A")
        amin, _ = alpha.getextrema()
        return "transparent" if amin < 255 else "opaque"


def download_status(url):
    if not permitted_source(url):
        return "external-source"
    req = urllib.request.Request(url, headers={"User-Agent": "Enna-Printify-ImageQA/1.0", "Accept": "image/*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
            if not content_type.startswith("image/"):
                return "not-an-image"
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return "image-too-large"
        return transparency_from_bytes(raw)
    except (urllib.error.URLError, TimeoutError, ValueError, UnidentifiedImageError, OSError):
        return "unavailable"


def main():
    token = os.getenv("PRINTIFY_API_TOKEN")
    if not token:
        print("Missing PRINTIFY_API_TOKEN", file=sys.stderr)
        return 2
    try:
        shops = get_json("/shops.json", token)
        shop = choose_shop(shops, os.getenv("PRINTIFY_SHOP_ID"), "Pie & Po")
        products = fetch_products(shop["id"], token)
    except (PrintifyError, ValueError, TypeError) as exc:
        print("Read-only QA stopped: " + str(exc), file=sys.stderr)
        return 1
    cache = {}
    aggregate = Counter()
    print("Printify artwork transparency QA — read only")
    print("Shop ID:", shop["id"], "products:", len(products))
    for p in products:
        urls = source_urls(p)
        states = []
        for u in urls:
            if u not in cache:
                cache[u] = download_status(u)
            states.append(cache[u])
        counts = Counter(states)
        aggregate.update(counts)
        safeid = hashlib.sha256(str(p.get("id", "")).encode("utf-8")).hexdigest()[:12]
        print(
            "ARTWORK_HASH", safeid,
            "sources", len(urls),
            "transparent", counts["transparent"],
            "opaque", counts["opaque"],
            "external", counts["external-source"],
            "unavailable", counts["unavailable"],
            "other", sum(v for k, v in counts.items() if k not in ("transparent", "opaque", "external-source", "unavailable")),
        )
    print("Unique image sources:", len(cache))
    print("Aggregate:", " ".join("%s=%d" % (k, v) for k, v in sorted(aggregate.items())))
    print("No product, artwork, order, or SKU was changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
