"""Build a truly offline DOHAYDILAM preview: images embedded as data URLs.
No external fonts, JS, tracking, unverified reviews, or AI-generated people.
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from io import BytesIO
from html import escape
import requests, base64, re
ROOT=Path("docs/pod")
ROOT.mkdir(parents=True,exist_ok=True)
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0","Accept":"image/jpeg,image/png,image/webp,*/*"})
cdn="https://cdn.fourthwall.com/customizations/sh_57a327d5-739d-483f-8764-df47410eb057/"
shop="https://dohaydilam-shop.fourthwall.com"
assets={
 "hero":"https://images.pexels.com/photos/10752096/pexels-photo-10752096.jpeg?auto=compress&cs=tinysrgb&w=1200&fm=jpg",
 "mug":cdn+"0310d641-c7ce-419e-acd5-06efa44684f2.webp",
 "note":cdn+"d56fe486-857e-4abb-9098-a5b7a5e9a0f6.webp",
 "tote":cdn+"054e722d-4a14-40f7-ae74-9a52348e586c.webp",
 "sticker":cdn+"5b73d33a-b59c-4dba-944b-c96996699830.webp",
 "model":str(ROOT/"v4_mug_stock_mockup_office.jpg"),
}
def encode_image(key,url,max_w=1200):
    try:
        blob=Path(url).read_bytes() if not url.startswith("http") else session.get(url,timeout=35).content
        im=Image.open(BytesIO(blob))
        im=ImageOps.exif_transpose(im).convert("RGB")
        if im.width>max_w: im.thumbnail((max_w,1400),Image.Resampling.LANCZOS)
        out=BytesIO()
        im.save(out,format="JPEG",quality=76,progressive=True,optimize=True)
        content=out.getvalue()
        print("OK",key,"bytes",len(content),"size",im.size)
        return "data:image/jpeg;base64,"+base64.b64encode(content).decode("ascii")
    except Exception as e:
        print("FAILED",key,repr(e))
        if key!="hero":
            return encode_image("emergency_"+key,assets["hero"],max_w)
        raise
data={key:encode_image(key,url,1150 if key in ("hero","model") else 480) for key,url in assets.items()}
products=[
("mug","Coffee mugs","Master of the Tiny Gaps","19.95","master-of-the-tiny-gaps-11oz-office-coffee-mug-2"),
("note","Notebooks","Future Me Appreciates Present Me","21.95","future-me-appreciates-present-me-spiral-ruled-notebook"),
("tote","Tote bags","Still Making Progress","29.95","still-making-progress-organic-cotton-office-tote"),
("sticker","Stickers","Protect the Flow","7.95","protect-the-flow-die-cut-vinyl-workday-sticker")]
cards="".join(f'<a class="product" href="{shop}/products/{slug}"><div class="product-img"><img src="{data[key]}" alt="{escape(title)} · actual Fourthwall listing image" width="480" height="480" loading="lazy"></div><div class="product-info"><span><small>{escape(category)}</small><strong>{escape(title)}</strong></span><b>${price}</b></div></a>' for key,category,title,price,slug in products)
categories=[
("Mugs","coffee-break-mugs"),("Notebooks","workday-notebooks"),("Totes","everyday-office-totes"),
("Stickers","laptop-desk-stickers"),("Wall art","workday-wall-art")]
nav="".join(f'<a href="{shop}/collections/{slug}">{escape(title)} <span>↗</span></a>' for title,slug in categories)
html=f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DOHAYDILAM · V4.2 working offline preview</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#fdfcf9;font:14px/1.5 Arial,Helvetica,sans-serif;color:#222323}}
a{{color:inherit;text-decoration:none}} img{{display:block;max-width:100%}}
.top{{background:#28302e;color:#fff;text-align:center;padding:10px 16px;font-size:11px;letter-spacing:.05em}}
.bar{{max-width:1280px;min-height:69px;margin:auto;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px}}
.logo{{font-size:24px;font-weight:800;letter-spacing:-.05em}}
.bar nav{{display:flex;gap:25px;font-size:13px;font-weight:600}} .bar a:hover,.cats a:hover{{text-decoration:underline}}
.notice{{background:#eeebe3;border-block:1px solid #dedbd4;padding:8px 24px;font-size:11px;text-align:center;color:#5d5a53}}
.wrap{{max-width:1280px;margin:auto;padding:0 28px}}
.overline{{font-size:10px;letter-spacing:.12em;font-weight:700;text-transform:uppercase;color:#615f58;margin:20px 0 12px}}
.hero{{display:grid;grid-template-columns:1.12fr .88fr;min-height:485px;background:#f0eee8}}
.hero-photo{{overflow:hidden;min-height:440px}}
.hero-photo img{{width:100%;height:100%;object-fit:cover;object-position:center 44%}}
.hero-text{{display:flex;flex-direction:column;align-items:start;justify-content:center;padding:clamp(24px,5vw,69px)}}
.hero h1{{font-size:clamp(36px,4.5vw,62px);line-height:1.06;letter-spacing:-.056em;font-weight:600;margin:0 0 21px}}
.hero p:not(.overline){{font-size:16px;line-height:1.55;color:#4b4945;margin:0 0 25px;max-width:365px}}
.action{{display:inline-flex;justify-content:space-between;gap:50px;background:#222323;color:#fff;padding:15px 18px;font-weight:700}}
.secondary{{border-bottom:1px solid #3e3e3e;margin-top:17px;font-size:13px}}
.cats{{display:grid;grid-template-columns:120px repeat(5,1fr);border-bottom:1px solid #d4d0c8;margin:35px auto 0}}
.cats label{{align-self:center;font-size:11px;text-transform:uppercase;color:#666159;font-weight:700}}
.cats a{{border-left:1px solid #d4d0c8;padding:18px 11px;display:flex;justify-content:space-between;gap:8px;font-size:13px;font-weight:700}}
.prod-section{{padding:58px 0 74px}}
.section-head{{display:flex;justify-content:space-between;align-items:end;margin-bottom:25px}}
.section-head h2{{font-size:clamp(29px,3vw,46px);letter-spacing:-.05em;line-height:1.15;margin:0}}
.section-head>a{{font-size:13px;border-bottom:1px solid #555;padding-bottom:3px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}}
.product{{min-width:0}}
.product-img{{background:#f0efe9;aspect-ratio:1/1;overflow:hidden}}
.product-img img{{width:100%;height:100%;object-fit:contain}}
.product-info{{display:flex;justify-content:space-between;gap:15px;padding-top:12px;font-size:13px}}
.product-info span{{display:flex;flex-direction:column;gap:5px}}
.product-info small{{font-size:11px;color:#77716a}}
.product-info strong{{font-size:13px;line-height:1.3}}
.product-info b{{white-space:nowrap}}
.editorial{{display:grid;grid-template-columns:1.04fr .96fr;background:#f1eee8}}
.editorial-photo{{position:relative;min-height:380px}}
.editorial-photo img{{width:100%;height:100%;max-height:550px;object-fit:cover;object-position:center 45%}}
.caption{{position:absolute;bottom:10px;left:12px;background:#fcfbf8e8;font-size:10px;padding:7px 9px;max-width:80%}}
.editorial-copy{{padding:45px clamp(25px,5vw,65px);display:flex;flex-direction:column;justify-content:center;align-items:flex-start}}
.editorial-copy h2{{font-size:clamp(30px,3.3vw,44px);letter-spacing:-.05em;line-height:1.13;margin:10px 0 14px}}
.editorial-copy>p:not(.overline){{color:#5c5652;margin:0 0 22px}}
.mug-link{{display:flex;align-items:center;border-top:1px solid #cfcac2;gap:16px;padding-top:18px}}
.mug-link img{{width:90px;height:90px;object-fit:contain;background:white}}
.mug-link span{{display:flex;flex-direction:column;gap:5px}}
.mug-link a{{text-decoration:underline}}
.under{{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:56px 0}}
.under h2{{font-size:clamp(34px,4vw,54px);margin:0}}
.under p{{margin:12px 0 20px;color:#5d5853}}
.under a{{font-weight:700;text-decoration:underline}}
.under img{{width:180px}}
.foot{{background:#efede8;padding:24px;font-size:11px;text-align:center;color:#555}}
@media(max-width:800px){{.bar{{padding:13px 16px}} .bar nav{{gap:14px}}.wrap{{padding:0 16px}} .hero{{grid-template-columns:1fr}} .hero-photo{{height:365px;min-height:0}}.hero-text{{padding:27px 21px}}.hero h1{{font-size:39px}} .cats{{display:flex;overflow-x:auto;margin-top:25px}}.cats label{{display:none}} .cats a{{flex:0 0 auto;white-space:nowrap}} .grid{{grid-template-columns:repeat(2,minmax(0,1fr));gap:23px 12px}} .editorial{{grid-template-columns:1fr}} .editorial-photo{{min-height:0;height:320px}} .editorial-copy{{padding:29px 22px}}}}
@media(max-width:480px){{.logo{{font-size:20px}} .bar nav a:first-child{{display:none}} .bar nav{{gap:12px;font-size:11px}}.hero-photo{{height:260px}} .hero h1{{font-size:35px}} .product-info{{display:block}} .product-info b{{display:block;margin-top:4px}} .under img{{width:100px}} .under{{padding:30px 0}}}}
</style></head>
<body>
<div class="top">Workday objects, made to order — preview with original photography</div>
<header class="bar"><a class="logo" href="{shop}">dohaydilam</a><nav><a href="{shop}">Home</a><a href="{shop}/collections/start-here-workday-gift-picks">Start Here</a><a href="{shop}/collections/office-gifts-under-20">Under $20</a></nav></header>
<div class="notice">All photos embedded in this HTML. Preview works offline. Stock photos show models, not actual customers.</div>
<main><div class="wrap"><p class="overline">DOHAYDILAM / WORKDAY GOODS</p>
<section class="hero"><div class="hero-photo"><img src="{data['hero']}" alt="Authentic Pexels stock photograph of a person carrying a blank tote on the street; not an exact product mockup"></div>
<div class="hero-text"><p class="overline">A LITTLE SOMETHING FOR THE WORKDAY</p><h1>Good things for ordinary workdays.</h1><p>Mugs, notebooks, tote bags and the little things that make your desk feel like yours.</p>
<a class="action" href="{shop}/collections/start-here-workday-gift-picks">Explore the shop <span>↗</span></a>
<a class="secondary" href="{shop}/collections/office-gifts-under-20">Gifts under $20 ↗</a></div></section>
<nav class="cats"><label>Shop by type</label>{nav}</nav>
<section class="prod-section"><div class="section-head"><div><p class="overline">FROM THE SHOP</p><h2>Made for the workday.</h2></div>
<a href="{shop}/collections/workday-objects-series-01">View all ↗</a></div><div class="grid">{cards}</div></section></div>
<section class="editorial"><div class="editorial-photo"><img src="{data['model']}" alt="A real stock photo model with the true Fourthwall mug print composited onto the mug"><span class="caption">Pexels stock photograph · Product art digitally composited</span></div>
<div class="editorial-copy"><p class="overline">COFFEE BETWEEN MEETINGS</p><h2>The small breaks count, too.</h2><p>An ordinary office moment and a mug that remembers those five-minute gaps. Photographic mockup; see the real listing for the exact print.</p>
<div class="mug-link"><a href="{shop}/products/master-of-the-tiny-gaps-11oz-office-coffee-mug-2"><img src="{data['mug']}" alt="Actual Fourthwall 11 oz mug listing photo"></a>
<span><strong>Master of the Tiny Gaps</strong><b>$19.95 USD</b><a href="{shop}/products/master-of-the-tiny-gaps-11oz-office-coffee-mug-2">See mug ↗</a></span></div></div></section>
<div class="wrap"><section class="under"><div><p class="overline">SMALL GIFTS, REAL USE</p><h2>Under $20.</h2><p>A few small finds for the desk, coffee break and everyday office life.</p><a href="{shop}/collections/office-gifts-under-20">Browse gifts under $20 ↗</a></div><a href="{shop}/products/protect-the-flow-die-cut-vinyl-workday-sticker"><img src="{data['sticker']}" alt="Real Fourthwall Protect the Flow sticker"></a></section></div></main>
<footer class="foot">DOHAYDILAM · Prices in USD · Shipping/taxes at checkout · This is an offline layout preview, not the live checkout.</footer>
</body></html>'''
assert html.count("data:image/jpeg;base64,")>=6
assert 'src="https:' not in html, "Preview contains remote image source"
out=ROOT/"DOHAYDILAM_V4_2_OFFLINE_PREVIEW.html"
out.write_text(html,encoding="utf-8")
print("SAVED",out,"bytes",out.stat().st_size,"embedded images",html.count("data:image/jpeg;base64,"))
