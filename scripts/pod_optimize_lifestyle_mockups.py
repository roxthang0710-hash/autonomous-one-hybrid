"""Optimize approved conceptual lifestyle mockups for the POD storefront.

Inputs are original PNG archives stored in this repo and Google Drive.
Outputs are compressed WebP for fast global delivery from GitHub raw.
No generated imagery, no changes to product design or customer data.
"""
from pathlib import Path
from PIL import Image, ImageOps
from hashlib import sha256
from json import dumps
src=Path("docs/pod/mockups/originals")
out=Path("docs/pod/mockups/web")
out.mkdir(parents=True,exist_ok=True)
mapping={
    "tote-still-making-progress.png":"hero-tote-still-making-progress.webp",
    "mug-master-of-the-tiny-gaps.png":"mug-master-of-the-tiny-gaps.webp",
    "notebook-future-me.png":"notebook-future-me.webp",
    "sticker-protect-the-flow.png":"sticker-protect-the-flow.webp",
}
manifest={}
for original,dest in mapping.items():
    image=Image.open(src/original)
    image=ImageOps.exif_transpose(image).convert("RGB")
    native=image.size
    # Header stays 1536 px wide; all other images ~1150 px for product grids.
    limit=1536 if original.startswith("tote-") else 1152
    image.thumbnail((limit,1200),Image.Resampling.LANCZOS)
    p=out/dest
    image.save(p,format="WEBP",quality=83,method=6)
    assert p.stat().st_size>10000 and p.stat().st_size<600000
    manifest[dest]={
       "original":original,"native_pixels":list(native),
       "web_pixels":list(image.size),"web_bytes":p.stat().st_size,
       "sha256":sha256(p.read_bytes()).hexdigest(),
       "classification":"conceptual product-in-context mockup; not customer photo"
    }
    print(f"OK {dest}: {native} -> {image.size}, {p.stat().st_size} bytes",flush=True)
(out/"manifest.json").write_text(dumps(manifest,indent=2),encoding="utf-8")
