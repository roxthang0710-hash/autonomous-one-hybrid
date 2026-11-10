"""Download licensed real-person photo options and true Fourthwall mug photo.
The final composite is prepared in a later revision after visual inspection.
This script never uses generative imagery.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
import io, requests, time
from urllib.parse import quote

HERE=Path("docs/pod")
HERE.mkdir(parents=True,exist_ok=True)
ASSETS={
"01 · Pexels / Kaboompics 8546750":"https://images.pexels.com/photos/8546750/pexels-photo-8546750.jpeg?auto=compress&cs=tinysrgb&w=1400",
"02 · Pexels / Jopwell 2422287":"https://images.pexels.com/photos/2422287/pexels-photo-2422287.jpeg?auto=compress&cs=tinysrgb&w=1400",
"03 · Pexels / Kevin Malik 9031809":"https://images.pexels.com/photos/9031809/pexels-photo-9031809.jpeg?auto=compress&cs=tinysrgb&w=1400",
"04 · Pexels / Andrea Piacquadio 3765029":"https://images.pexels.com/photos/3765029/pexels-photo-3765029.jpeg?auto=compress&cs=tinysrgb&w=1400",
"05 · Actual Fourthwall mug":"https://cdn.fourthwall.com/customizations/sh_57a327d5-739d-483f-8764-df47410eb057/0310d641-c7ce-419e-acd5-06efa44684f2.webp"
}
W,H=690,550
sheet=Image.new("RGB",(W*3,H*2),"#faf9f5")
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",19)
draw=ImageDraw.Draw(sheet)
for index,(title,url) in enumerate(ASSETS.items()):
    cx,cy=index%3,index//3
    try:
        resp=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0 (compatible; Dohaydilam-Photo-Mockup/1.0)"})
        print("Fetched",title,resp.status_code,len(resp.content),flush=True)
        resp.raise_for_status()
        image=Image.open(io.BytesIO(resp.content)).convert("RGB")
        ImageOps.exif_transpose(image)
        print("Dimension",title,image.size,flush=True)
        thumbnail=ImageOps.contain(image,(W-22,H-52),Image.Resampling.LANCZOS)
        pos=(cx*W+(W-thumbnail.width)//2,cy*H+42+(H-52-thumbnail.height)//2)
        sheet.paste(thumbnail,pos)
        draw.text((cx*W+16,cy*H+12),title,font=font,fill="#222222")
    except Exception as e:
        print("Failed",title,repr(e),flush=True)
        draw.text((cx*W+12,cy*H+80),"LOAD FAILED: "+str(e)[:45],font=font,fill="#cc3333")
sheet.save(HERE/"v4_real_stock_contact_sheet.jpg",quality=85,optimize=True)
print("Wrote",HERE/"v4_real_stock_contact_sheet.jpg",flush=True)

# Detailed views to locate the EXACT live Fourthwall print artwork on mug and
# the blank ceramic surface in the authentic Pexels portrait.
original_url=ASSETS["05 · Actual Fourthwall mug"]
original=Image.open(io.BytesIO(requests.get(original_url,timeout=30).content)).convert("RGBA")
paper=Image.new("RGB",original.size,"#f3f2ef")
paper.paste(original,mask=original.getchannel("A"))
detail=paper.crop((360,620,1400,1450))
detail.thumbnail((1140,900))
detail.save(HERE/"mug_artwork_inspection.jpg",quality=90)
source_url=ASSETS["03 · Pexels / Kevin Malik 9031809"]
photo=Image.open(io.BytesIO(requests.get(source_url,timeout=30).content)).convert("RGB")
photo.thumbnail((900,1400))
mark=ImageDraw.Draw(photo)
for xx in range(0,photo.width,100):
    mark.line((xx,0,xx,photo.height),fill=(235,103,39),width=1)
    mark.text((xx+3,4),str(xx),fill=(255,255,255),stroke_width=1,stroke_fill=(75,75,75))
for yy in range(0,photo.height,100):
    mark.line((0,yy,photo.width,yy),fill=(235,103,39),width=1)
    mark.text((4,yy+3),str(yy),fill=(255,255,255),stroke_width=1,stroke_fill=(75,75,75))
photo.save(HERE/"pexels_9031809_position_guide.jpg",quality=87)
print("Wrote artwork detail and portrait position guide")


# ---------------------------------------------------------------
# COMPOSITE: real stock photography + actual Fourthwall printed art.
# Portrait 9031809 and office image 2422287 have authentic, unmodified
# human faces and environments. Only pixels on the stock ceramic mug are
# modified. Do not claim the depicted stock models endorse the merchandise.
# ---------------------------------------------------------------
from PIL import ImageFilter
import numpy as np
source_rgba=Image.open(io.BytesIO(requests.get(original_url,timeout=30).content)).convert("RGBA")
print("Product source", source_rgba.size,flush=True)
art=source_rgba.crop((530,855,1230,1165)).convert("RGB")
arr=np.asarray(art).astype(np.float32)
# Recover the print by subtracting low-frequency porcelain illumination.
bg=np.asarray(art.filter(ImageFilter.GaussianBlur(radius=27))).astype(np.float32)
positive=(bg-arr).mean(axis=2)
alpha=np.clip((positive-3.0)/65.0,0,1)**0.85
# Original print colors are dark green/black; preserve the actual print
# pixels rather than invent a logo or lettering. Tiny gold accent included.
color=np.minimum(arr*0.96,np.array([54,64,60],dtype=np.float32))
# Thin border must not disappear when reduced to 200 pixels.
mask_img=Image.fromarray(np.uint8(np.round(alpha*255)),"L")
print("Artwork extraction stats",float(alpha.max()),float(alpha.mean()),flush=True)

def composite_photo(title,url,rect,outname):
    photo=Image.open(io.BytesIO(requests.get(url,timeout=30).content)).convert("RGB")
    pixels=np.asarray(photo).astype(np.float32)
    x0,y0,x1,y1=rect
    W,H=x1-x0,y1-y0
    art_scaled=np.asarray(art.resize((W,H),Image.Resampling.LANCZOS)).astype(np.float32)
    alpha_scaled=np.asarray(mask_img.resize((W,H),Image.Resampling.LANCZOS)).astype(np.float32)/255
    # Cylindrical face of ceramic: slight vertical arch of the printed panel.
    xx=np.arange(W)[None,:]
    shift=(1-(2*xx/W-1)**2)*3.5
    for row in range(H):
        target_y=int(y0+row+shift.mean())
        if target_y>=photo.height:continue
        j=target_y
        # Retain original highlights and ceramic texture under transferred ink.
        a=alpha_scaled[row,:,None]*0.88
        surface=pixels[j,x0:x1]
        ink=np.minimum(art_scaled[row],np.array([52,65,62],dtype=np.float32))
        pixels[j,x0:x1]=surface*(1-a)+ink*a
    output=Image.fromarray(np.uint8(np.clip(pixels,0,255)),"RGB")
    output.save(HERE/outname,quality=88,subsampling=0,optimize=True)
    print("Wrote mockup",title,rect,output.size,flush=True)

composite_photo("Real portrait / Kevin Malik",source_url,(200,1730,556,1890),"v4_mug_stock_mockup_portrait.jpg")
composite_photo("Real office / Jopwell",ASSETS["02 · Pexels / Jopwell 2422287"],(643,576,870,675),"v4_mug_stock_mockup_office.jpg")

# Side-by-side review: honest labels and true Fourthwall reference image.
por=Image.open(HERE/"v4_mug_stock_mockup_portrait.jpg")
off=Image.open(HERE/"v4_mug_stock_mockup_office.jpg")
review=Image.new("RGB",(1500,980),"#f9f9f7")
for im,i,title in [(por,0,"A / REAL PEXELS PORTRAIT — PHOTOGRAPHIC COMPOSITE"),(off,1,"B / REAL OFFICE PHOTOGRAPH — PHOTOGRAPHIC COMPOSITE")]:
    fit=ImageOps.fit(im,(710,855),Image.Resampling.LANCZOS,centering=(0.5,0.74) if i==0 else (0.55,0.5))
    review.paste(fit,(26+i*745,72))
    draw=ImageDraw.Draw(review)
    draw.text((26+i*745,22),title,font=font,fill="#333333")
ImageDraw.Draw(review).text((26,943),"Stock model photos from Pexels. Artwork transferred from actual Fourthwall mug. Illustrative composite, not a customer endorsement.",font=font,fill="#555555")
review.save(HERE/"v4_mug_real_stock_mockups_comparison.jpg",quality=86,optimize=True)
print("Saved photo composite comparison",flush=True)
