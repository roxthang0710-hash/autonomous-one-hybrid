"""Enna photo-first 5-slide Instagram carousel.

Uses ONLY 3 previously verified CC0 photo-meme images and their rights sidecars.
Produces real PNG assets with a source manifest; never schedules or publishes.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

W,H = 1080,1350
SLIDES = [
    ("cat", "THỨ HAI CÓ 3 KIỂU NGƯỜI", "Mở máy lúc 8:00. Tinh thần lúc 8:01: còn đang tải.", "cover"),
    ("keyboard", "HỆ CTRL + S", "Chưa làm gì nhưng đã lưu file 17 lần.", "yellow"),
    ("paper", "HỆ MÁY IN GỌI TÊN", "Sếp nhắn 'in thêm giúp chị' đúng lúc bạn định uống cà phê.", "paper"),
    ("cat", "HỆ NÃO CHƯA KHỞI ĐỘNG", "10:15, người vẫn ở văn phòng. Tâm trí xin nghỉ phép.", "dark"),
    ("collage", "BẠN THUỘC HỆ NÀO?", "1. Ctrl + S   2. Máy in   3. Não cần nghỉ", "end"),
]
PHOTO_SPECS = {
    "cat":("kiem-tra-tien-do.png",(0,185,1080,975)),
    "keyboard":("luu-file-lan-thu-17.png",(0,255,1080,945)),
    "paper":("chuyen-doi-so.png",(0,651,1080,1116)),
}
GOLD="#f6e157"
INK="#1e211f"
CREAM="#f9f2e8"

def font(size, bold=True):
    name="/usr/share/fonts/truetype/dejavu/DejaVuSans"
    return ImageFont.truetype(name+("-Bold" if bold else "")+".ttf",size)

def wrap(draw, message, max_px, size, maximum=3):
    while size>=min(24,size):
        f=font(size)
        chunks=[];one=""
        for word in message.split():
            draft=(one+" "+word).strip()
            if one and draw.textbbox((0,0),draft,font=f)[2]>max_px:
                chunks.append(one);one=word
            else:one=draft
        if one:chunks.append(one)
        if len(chunks)<=maximum:return chunks,size
        size-=3
    raise ValueError("Vietnamese caption overflows layout")

def text(draw, message, *, x,y,width,size,fill,maximum=3):
    chunks,size=wrap(draw,message,width,size,maximum)
    use_font=font(size)
    for line in chunks:
        draw.text((x,y),line,font=use_font,fill=fill)
        y+=round(size*1.33)
    return y

def verified_photo(folder,key):
    stem,region=PHOTO_SPECS[key]
    photo=folder/stem
    sidecar=folder/(Path(stem).stem+".rights.json")
    info=json.loads(sidecar.read_text(encoding="utf-8"))
    if info.get("status")!="DRAFT_REQUIRES_HUMAN_REVIEW" or info.get("published") is not False:
        raise ValueError("source-approval-state-mismatch")
    if info.get("output_sha256")!=hashlib.sha256(photo.read_bytes()).hexdigest():
        raise ValueError("photo-hash-mismatch")
    if not info.get("source_media") or any(src.get("license")!="CC0 1.0" for src in info["source_media"]):
        raise ValueError("unverified-copyright")
    with Image.open(photo) as im:
        assert im.size==(W,H) and im.format=="PNG"
        return im.convert("RGB").crop(region), info["source_media"]

def make(slide_index, photos):
    key,title,subtitle,variant=SLIDES[slide_index]
    canvas=Image.new("RGB",(W,H),CREAM)
    if key=="collage":
        for idx,part in enumerate(["cat","keyboard","paper"]):
            frame=ImageOps.fit(photos[part],(360,910),method=Image.Resampling.LANCZOS)
            canvas.paste(frame,(360*idx,0))
    else:
        frame=ImageOps.fit(photos[key],(W,970),method=Image.Resampling.LANCZOS)
        canvas.paste(frame,(0,0))
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((36,38,310,95),radius=17,fill=GOLD)
    text(d,"ĐỒ HAY ĐI LÀM",x=55,y=56,width=250,size=21,fill=INK,maximum=1)
    d.rounded_rectangle((934,37,1040,95),radius=19,fill=INK)
    text(d,f"{slide_index+1}/5",x=959,y=55,width=75,size=22,fill="#ffffff",maximum=1)
    if variant=="yellow":color=GOLD;ink=INK
    elif variant=="paper":color=CREAM;ink=INK
    else:color=INK;ink="#ffffff"
    d.rectangle((0,907,W,H),fill=color)
    d.rectangle((47,950,60,1282),fill="#ef5844" if color!=GOLD else INK)
    y=text(d,title,x=94,y=946,width=915,size=52,fill=ink,maximum=2)
    text(d,subtitle,x=94,y=y+30,width=925,size=30,fill=ink,maximum=3)
    return canvas

def render(source_dir,output_dir):
    source=Path(source_dir);output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    images={}; provenance={}
    for key in PHOTO_SPECS:
        photo,sources=verified_photo(source,key)
        images[key]=photo;provenance[key]=sources
    output_files=[]
    for idx,slide in enumerate(SLIDES):
        image=make(idx,images)
        path=output/(f"thu-hai-cua-toi-{idx+1:02d}.png")
        image.save(path,optimize=True)
        if not 20000<path.stat().st_size<8_000_000:raise ValueError("invalid-slide-file")
        output_files.append(path)
    source_list=sorted({(entry["file"],entry["photographer"],entry["license"])
        for each in provenance.values() for entry in each})
    manifest={"type":"carousel","status":"DRAFT_REQUIRES_HUMAN_REVIEW",
              "published":False,"size":[W,H],
              "slides":[{"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in output_files],
              "sources":[{"file":x[0],"photographer":x[1],"license":x[2]} for x in source_list]}
    (output/"thu-hai-cua-toi.sources.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return [str(p) for p in output_files]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",default="docs/enna/media/photo-meme")
    p.add_argument("--output",default="docs/enna/media/carousel-thu-hai")
    a=p.parse_args()
    print(json.dumps(render(a.sources,a.output),ensure_ascii=False))

if __name__=="__main__":
    main()
