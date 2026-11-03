"""Produce static original Enna meme cards from the repo's own mascot SVG.

Image assets have no fabricated social metrics or unowned photos.
Generated deterministically; rendered PNGs are deployed by GitHub Pages.
"""
from io import BytesIO
from pathlib import Path
import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs"/"enna"/"media"
OUT.mkdir(parents=True,exist_ok=True)
W,H=1080,1350
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REGULAR="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else REGULAR,size)

def center(draw,text,y,fnt,color):
    box=draw.textbbox((0,0),text,font=fnt)
    x=(W-(box[2]-box[0]))//2
    draw.text((x,y),text,fill=color,font=fnt,stroke_width=0)

def rounded(draw,xy,fill,r=40,outline=None,width=1):
    draw.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)

def make(name,theme,lines,large_label,small_lines,svg="enna-work.svg"):
    bg,accent,ink,panel=theme
    im=Image.new("RGB",(W,H),bg)
    d=ImageDraw.Draw(im)
    # Subtle graphic details: original shapes, no brand marks from other pages.
    d.ellipse((800,-190,1240,250),fill=panel)
    d.ellipse((-140,960,200,1300),fill=panel)
    rounded(d,(52,44,1028,1306),fill="#FFFDF8",r=70,outline="#E6D9EA",width=5)
    rounded(d,(98,90,530,156),fill=accent,r=28)
    d.text((133,108),"ĐỒ HAY ĐI LÀM",font=font(27,True),fill="#FFFFFF")
    rounded(d,(690,90,982,156),fill="#F1E7FF",r=28)
    d.text((719,107),"ENNA  /  CÔNG SỞ",font=font(23,True),fill=ink)
    for i,line in enumerate(lines):
        center(d,line,205+i*97,font(68 if len(line)>17 else 83,True),ink)
    rounded(d,(165,410,915,558),fill=panel,r=38)
    center(d,large_label,448,font(57,True),accent)
    # Use the existing original Enna character owned by this repo.
    data=cairosvg.svg2png(url=str(ROOT/"docs"/"enna"/svg),output_width=950,output_height=784)
    art=Image.open(BytesIO(data)).convert("RGBA")
    art.thumbnail((900,695),Image.Resampling.LANCZOS)
    # Gentle translucent shadow below the illustration.
    d.ellipse((230,1105,850,1148),fill="#F1EDF2")
    x=(W-art.width)//2
    im.paste(art,(x,532),art)
    rounded(d,(130,1120,950,1270),fill="#F5F0FB",r=36)
    for i,line in enumerate(small_lines):
        center(d,line,1146+i*47,font(28 if len(line)>39 else 33,True),ink)
    dest=OUT/name
    im.save(dest,"PNG",optimize=True)
    print(name,dest.stat().st_size)

def main():
    make("enna-hop-15-phut.png",
         ("#F6EEFF","#8754BD","#352146","#EEE0FF"),
         ["HỌP 15 PHÚT"],"01:18 SAU…",
         ["Họp để chốt việc.", "Hay để chốt thêm một cuộc họp?"],svg="enna-thinking.svg")
    make("enna-file-final.png",
         ("#FFF2E1","#E17A50","#3F2C46","#FFE7D8"),
         ["TỆP CHỐT CUỐI"],"final_final_2_v3",
         ["Ai giữ bản cuối thật sự?", "Đồng nghiệp đang cần gấp."],svg="enna-work.svg")
    make("enna-ban-gon.png",
         ("#E9FAEE","#43866A","#243C38","#D8F5E0"),
         ["BÀN GỌN 10/10"],"TÌM BÚT: 0/10",
         ["Bàn làm việc đẹp quá.", "Cây bút không tìm thấy."],svg="enna-thinking.svg")
    make("enna-thu-bay-nao-truc.png",
         ("#F0ECFF","#7662AD","#332C4B","#E9E2FF"),
         ["THỨ BẢY RỒI"],"NÃO: CHƯA TAN",
         ["Công ty đã hết ca.", "Não tự mở một ca mới."],svg="enna-thinking.svg")
    make("enna-chu-nhat.png",
         ("#FFF0E6","#C97E78","#4D303E","#FFE2D6"),
         ["TỐI CHỦ NHẬT"],"MAI TÍNH NHA",
         ["Thứ Hai chưa tới.", "Đừng giao việc sớm cho não."],svg="enna-work.svg")
    make("enna-deadline.png",
         ("#E8F7FF","#4389B7","#273C52","#D5EFFC"),
         ["DEADLINE"],"LẠI NHÂN ĐÔI",
         ["Một việc chưa xong.", "Ba việc mới tới."],svg="enna-thinking.svg")

if __name__=="__main__":main()
