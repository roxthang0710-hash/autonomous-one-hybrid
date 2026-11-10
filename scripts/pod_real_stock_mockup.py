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
