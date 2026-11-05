"""Enna photo-based workplace memes: 3 CC0 photos, 3 layouts, drafts ONLY."""
import argparse,hashlib,io,json,re
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps
API="https://commons.wikimedia.org/w/api.php"
UA={"User-Agent":"EnnaPhotoLab/0.1 (license verification; github.com/roxthang0710-hash/autonomous-one-hybrid)"}
SRC=[
 ("cat","File:Cat Sleeping on Keyboard.jpg","Panini!"),
 ("keyboard","File:Keyboard close-up.jpg","Jiafei Slay Queen"),
 ("tray","File:Lack of paper documents.jpg","Ірина Бучнєва")]
IDEAS=[
 ("kiem-tra-tien-do","chat",["cat"],"PHÒNG KIỂM TRA TIẾN ĐỘ ĐÃ VÀO CA.","Mới 9 giờ mà đã có người nằm chặn bàn phím."),
 ("luu-file-lan-thu-17","editorial",["keyboard"],"“FILE ĐÃ LƯU CHƯA EM?”","Tôi: bấm Ctrl + S lần thứ 17 để chắc ăn."),
 ("chuyen-doi-so","split",["keyboard","tray"],"8:30 — “TỪ NAY MÌNH SỐ HÓA!”","16:59 — MÁY IN: “GIẤY ĐÂU RỒI?”")]
def trusted(url):
 p=urlparse(str(url))
 return p.scheme=="https" and p.hostname in ("upload.wikimedia.org","thumb.wikimedia.org") and p.path.startswith("/wikipedia/commons/") and (not p.query or p.hostname=="thumb.wikimedia.org") and not p.fragment and not p.username and not p.password
def cc0(info):
 if not isinstance(info,dict) or info.get("mime") not in ("image/jpeg","image/png"):return False
 ext=info.get("extmetadata") or {}
 name=str((ext.get("LicenseShortName") or {}).get("value") or "").lower()
 link=str((ext.get("LicenseUrl") or {}).get("value") or "").lower()
 return "cc0" in name or "cc-zero" in name or "creativecommons.org/publicdomain/zero/1.0" in link
def fetch_photo(item,req=requests):
 sid,title,author=item
 res=req.get(API,params={"action":"query","format":"json","titles":title,"prop":"imageinfo",
   "iiprop":"url|size|mime|extmetadata","iiurlwidth":1600},headers=UA,timeout=20)
 res.raise_for_status()
 pages=(res.json().get("query") or {}).get("pages") or {}
 if len(pages)!=1:raise ValueError("ambiguous-Commons-metadata")
 page=next(iter(pages.values()))
 if page.get("title")!=title:raise ValueError("wrong-Commons-file")
 info=(page.get("imageinfo") or [None])[0]
 if not cc0(info):raise ValueError("license-not-verified-CC0")
 url=info.get("thumburl") or info.get("url")
 if not trusted(url):
  p=urlparse(str(url))
  raise ValueError("unsafe-media-url scheme="+p.scheme+" host="+str(p.hostname)+" path_prefix="+p.path[:45]+" query_present="+str(bool(p.query)))
 reply=req.get(url,headers=UA,timeout=25,stream=True)
 reply.raise_for_status()
 if urlparse(reply.url).hostname not in ("upload.wikimedia.org","thumb.wikimedia.org"):raise ValueError("offsite-redirect")
 data=bytearray()
 for chunk in reply.iter_content(chunk_size=65536):
  data.extend(chunk)
  if len(data)>8500000:raise ValueError("oversized-photo")
 with Image.open(io.BytesIO(data)) as inp:
  if inp.format not in ("JPEG","PNG") or min(inp.size)<550 or inp.width*inp.height>30000000:raise ValueError("invalid-image")
  im=ImageOps.exif_transpose(inp).convert("RGB")
 return im,{"file":title,"photographer":author,"license":"CC0 1.0",
  "source_page":"https://commons.wikimedia.org/wiki/"+title.replace(" ","_"),
  "photo_sha256":hashlib.sha256(data).hexdigest()}
def font(sz,bold=True):
 base="/usr/share/fonts/truetype/dejavu/DejaVuSans"
 return ImageFont.truetype(base+("-Bold" if bold else "")+".ttf",sz)
def draw_text(d,text,x,y,width,size,color="#1c1c1c",maxlines=3):
 while size>=24:
  f=font(size);lines=[];part=""
  for word in text.split():
   proposed=(part+" "+word).strip()
   if part and d.textbbox((0,0),proposed,font=f)[2]>width:
    lines.append(part);part=word
   else:part=proposed
  if part:lines.append(part)
  if len(lines)<=maxlines:break
  size-=3
 if len(lines)>maxlines:raise ValueError("caption-too-long")
 for line in lines:
  d.text((x,y),line,font=f,fill=color);y+=int(size*1.28)
def crop(photo,size):
 return ImageOps.fit(photo,size,method=Image.Resampling.LANCZOS)
def compose(style,images,head,punch):
 im=Image.new("RGB",(1080,1350),"#f7f0e6")
 if style=="chat":
  im.paste(crop(images[0],(1080,1040)),(0,0));d=ImageDraw.Draw(im)
  d.rounded_rectangle((30,30,1050,180),radius=30,fill="#fff7eb")
  draw_text(d,head,66,68,955,47,maxlines=2)
  d.rounded_rectangle((28,980,1052,1330),radius=36,fill="#1c1e1c")
  draw_text(d,punch,66,1050,936,60,color="#ffffff")
 elif style=="editorial":
  im.paste(crop(images[0],(1080,950)),(0,0));d=ImageDraw.Draw(im)
  d.rectangle((0,0,1080,245),fill="#f8df52")
  draw_text(d,"ĐỒ HAY ĐI LÀM / CHUYỆN CÔNG SỞ",47,24,960,27,maxlines=1)
  draw_text(d,head,47,105,975,68,maxlines=2)
  d.rectangle((0,945,1080,1350),fill="#f7f1e8")
  d.rectangle((47,997,60,1280),fill="#ef563e")
  draw_text(d,punch,90,1035,927,59)
 elif style=="split":
  if len(images)!=2:raise ValueError("need-two-photos")
  im.paste(crop(images[0],(1080,625)),(0,0))
  im.paste(crop(images[1],(1080,650)),(0,645));d=ImageDraw.Draw(im)
  d.rectangle((0,0,1080,173),fill="#f8df52")
  draw_text(d,head,42,55,995,53,maxlines=2)
  d.rectangle((0,625,1080,645),fill="#fff9ed")
  d.rectangle((0,1120,1080,1350),fill="#1c1e1c")
  draw_text(d,punch,42,1158,990,52,color="#ffffff",maxlines=2)
 else:raise ValueError("unknown-style")
 return im
def render(dest="photo-meme-pilot",fetch=fetch_photo):
 out=Path(dest);out.mkdir(parents=True,exist_ok=True)
 photos={s[0]:fetch(s) for s in SRC};paths=[]
 for name,style,keys,head,punch in IDEAS:
  selected=[photos[k] for k in keys]
  path=out/(name+".png");compose(style,[s[0] for s in selected],head,punch).save(path)
  rights={"status":"DRAFT_REQUIRES_HUMAN_REVIEW","published":False,
   "fictional_humor":True,"layout":style,"source_media":[s[1] for s in selected],
   "output_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
  path.with_suffix(".rights.json").write_text(json.dumps(rights,ensure_ascii=False,indent=2),encoding="utf-8")
  paths.append(str(path))
 return paths
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--render",action="store_true");p.add_argument("--output",default="photo-meme-pilot")
 args=p.parse_args()
 if not args.render:raise SystemExit("Use --render for draft-only generation.")
 print(json.dumps(render(args.output),ensure_ascii=False))
