"""Original, deliberately scruffy office meme doodles drawn with Pillow.

Coffee and fake chat use hand-drawn characters and wobbly marker shapes as the
primary scene. The licensed photo is kept only as a *tiny* scrapbook sticker.
Cat/reaction photographs are NEVER passed into this module.

All characters and dialogue are fictional. No AI image generation or external
assets. Stroke jitter is deterministic for reproducible hashes.
"""
from math import sin, cos, pi
from random import Random
import hashlib

from PIL import Image, ImageDraw, ImageOps

WIDTH, HEIGHT = 1080, 1350
BLACK = "#222024"
RED = "#F94357"
YELLOW = "#FFDE55"
BLUE = "#A2DCFF"
GREEN = "#ACF2A6"
PINK = "#FFB7D9"
PAPER = "#FFFCF3"


def _wiggle(draw, pts, color=BLACK, width=6, seed=1, tremble=5):
    rng=Random(seed)
    output=[]
    for a,b in zip(pts,pts[1:]):
        dist=max(2,int(((b[0]-a[0])**2+(b[1]-a[1])**2)**.5/14))
        for k in range(dist):
            t=k/dist
            output.append((round(a[0]+(b[0]-a[0])*t+rng.uniform(-tremble,tremble)),
                           round(a[1]+(b[1]-a[1])*t+rng.uniform(-tremble,tremble))))
    output.append(pts[-1])
    draw.line(output,fill=color,width=width,joint="curve")


def _box(draw,x1,y1,x2,y2,fill=None,outline=BLACK,seed=6,stroke=6):
    if fill:
        draw.rounded_rectangle((x1+3,y1+3,x2-3,y2-3),radius=19,fill=fill)
    pts=[(x1,y1+8),(x1+12,y1),(x2-13,y1),(x2,y1+8),
         (x2,y2-12),(x2-12,y2),(x1+8,y2),(x1,y2-9),(x1,y1+8)]
    _wiggle(draw,pts,outline,stroke,seed)


def _circle(draw,x,y,r,seed=8,color=BLACK,fill=None,w=6):
    if fill:
        draw.ellipse((x-r+4,y-r+4,x+r-4,y+r-4),fill=fill)
    rng=Random(seed)
    pts=[(round(x+(r+rng.randint(-4,4))*cos(i*2*pi/50)),
          round(y+(r+rng.randint(-4,4))*sin(i*2*pi/50))) for i in range(51)]
    draw.line(pts,fill=color,width=w,joint="curve")


def _sunburst(draw,x,y,color=RED,seed=9,n=8):
    for j in range(n):
        theta=2*pi*j/n
        a=(int(x+42*cos(theta)),int(y+42*sin(theta)))
        b=(int(x+77*cos(theta)),int(y+77*sin(theta)))
        _wiggle(draw,[a,b],color,7,seed+j,2)


def _grid(draw,step=53):
    for x in range(0,WIDTH,step):
        draw.line((x,0,x,HEIGHT),fill="#E7ECF2",width=2)
    for y in range(0,HEIGHT,step):
        draw.line((0,y,WIDTH,y),fill="#E7ECF2",width=2)


def _smile(draw,x,y,look="happy",seed=1,scale=1):
    r=int(66*scale)
    _circle(draw,x,y,r,seed,color=BLACK,fill=YELLOW,w=6)
    eye=int(13*scale)
    for dx in (-25,25):
        if look=="dead":
            _wiggle(draw,[(x+dx-eye,y-eye),(x+dx+eye,y+eye)],BLACK,5,seed+dx)
            _wiggle(draw,[(x+dx+eye,y-eye),(x+dx-eye,y+eye)],BLACK,5,seed-dx)
        else:
            draw.ellipse((x+dx-6,y-17,x+dx+6,y-5),fill=BLACK)
    if look=="shocked":
        draw.ellipse((x-12,y+8,x+12,y+33),outline=BLACK,width=6)
    elif look=="dead":
        _wiggle(draw,[(x-22,y+29),(x+22,y+29)],BLACK,5,seed+38,2)
    else:
        _wiggle(draw,[(x-24,y+13),(x,y+27),(x+24,y+13)],BLACK,5,seed+39,3)


def _photo_sticker(canvas,photo,xywh=(820,75,190,143)):
    """Small proof-of-origin inset: meme remains a drawing, not photo layout."""
    x,y,w,h=xywh
    card=Image.new("RGB",(w+20,h+31),"#FFFFFF")
    thumb=ImageOps.fit(photo.convert("RGB"),(w,h),method=Image.Resampling.LANCZOS)
    card.paste(thumb,(10,9))
    card=card.rotate(7,expand=True,fillcolor=PAPER)
    canvas.paste(card,(x,y))
    d=ImageDraw.Draw(canvas)
    d.polygon([(x+8,y-7),(x+93,y+1),(x+90,y+22),(x+12,y+15)],fill="#FFDA66")


def _scribble_arrow(d,pts,seed=0,color=RED):
    _wiggle(d,pts,color,8,seed)
    x,y=pts[-1]
    _wiggle(d,[(x-23,y-15),(x,y),(x-28,y+14)],color,8,seed+4)


def _letter(d,copy,x,y,w,size,write,fill=BLACK,max_lines=3):
    return write(d,copy,x,y,w,size,fill,max_lines=max_lines)


def _cup(draw,x,y,look="happy",seed=1,scale=1):
    """Wobbly expressive cup drawn from simple original strokes, not a stock icon."""
    w=int(330*scale)
    h=int(255*scale)
    left=x-w//2
    top=y-h//2
    base=[(left+30,top+24),(left+w-26,top+24),(left+w-55,top+h-8),
          (left+70,top+h-8),(left+30,top+24)]
    _box(draw,left+22,top+10,left+w-20,top+70,fill="#F5DFBC",seed=seed)
    _wiggle(draw,base,BLACK,9,seed+3,5)
    draw.polygon([(left+40,top+35),(left+w-40,top+35),
                  (left+w-59,top+h-15),(left+66,top+h-15)],fill="#F5DFBC")
    # Re-ink the edges after filling.
    _wiggle(draw,base,BLACK,8,seed+5,4)
    for a,b in [(0,1),(1,2)]:
        pass
    draw.ellipse((left+30,top+1,left+w-29,top+88),fill="#FFF7E9",outline=BLACK,width=8)
    draw.ellipse((left+42,top+27,left+w-41,top+76),
                 fill="#86604D",outline=BLACK,width=5)
    _wiggle(draw,[(left+w-23,top+86),(left+w+57,top+70),
                  (left+w+82,top+150),(left+w+30,top+190),
                  (left+w-47,top+160)],BLACK,8,seed+9,6)
    if look=="happy":
        for dx in (-52,54):
            draw.arc((x+dx-19,y-9,x+dx+20,y+17),180,355,fill=BLACK,width=8)
        draw.arc((x-41,y+30,x+45,y+92),0,177,fill=BLACK,width=9)
        for sx in (x-80,x+60):
            draw.ellipse((sx,y+39,sx+23,y+59),fill="#FF8F9A")
        for k in range(3):
            _wiggle(draw,[(x-84+82*k,top-15),(x-102+82*k,top-57),
                          (x-76+82*k,top-103)],BLACK,5,seed+24+k,5)
    else:
        for dx in (-49,49):
            _wiggle(draw,[(x+dx-17,y+1),(x+dx+17,y+32)],BLACK,7,seed+dx,3)
            _wiggle(draw,[(x+dx+17,y+1),(x+dx-17,y+32)],BLACK,7,seed+dx+100,3)
        draw.ellipse((x-11,y+53,x+11,y+73),fill=RED)
        _wiggle(draw,[(x-99,y+109),(x-144,y+137),(x-178,y+170)],BLACK,8,seed+39)
    return left+w,top+h


def render_coffee(source,photo,write,font):
    canvas=Image.new("RGB",(WIDTH,HEIGHT),PAPER)
    d=ImageDraw.Draw(canvas)
    _grid(d)
    # Two rough storyboard panels with a strong "before / after" visual gag.
    _box(d,37,34,1043,661,fill="#FFF3A5",seed=17,stroke=8)
    _box(d,37,681,1043,1314,fill="#FFCCD9",seed=29,stroke=8)
    _letter(d,source["headline"],72,71,906,51,write,max_lines=2)
    _cup(d,543,411,look="happy",scale=.91,seed=8)
    _sunburst(d,840,354,color="#F8A208",seed=41)
    _letter(d,source["punchline"],68,726,925,45,write,max_lines=3)
    _cup(d,545,1079,look="dead",scale=.72,seed=33)
    _scribble_arrow(d,[(135,998),(181,1050),(213,1110)],seed=55,color="#FA4059")
    _sunburst(d,841,1070,color=RED,seed=63,n=6)
    _photo_sticker(canvas,photo,(830,466,130,95))
    d=ImageDraw.Draw(canvas)
    d.text((76,1320),"MINH HỌA VẼ TAY • TÌNH HUỐNG HƯ CẤU",font=font(16),fill="#53536A")
    return canvas


def _stick_person(d,x,y,look="happy",boss=False,seed=1):
    _smile(d,x,y,look,seed=seed,scale=.72)
    _wiggle(d,[(x,y+50),(x,y+127)],BLACK,7,seed+30)
    _wiggle(d,[(x,y+75),(x-43,y+100)],BLACK,7,seed+31)
    _wiggle(d,[(x,y+74),(x+43,y+96)],BLACK,7,seed+32)
    if boss:
        d.polygon([(x-38,y-54),(x-26,y-104),(x,y-77),(x+26,y-106),(x+39,y-52)],
                  fill="#FFE055",outline=BLACK)
        d.line((x-40,y-54,x+40,y-54),fill=BLACK,width=6)


def render_chat(source,photo,write,font):
    lines=source.get("chat_lines") or []
    if len(lines)!=2:
        raise ValueError("chat requires two fully fictional messages")
    canvas=Image.new("RGB",(WIDTH,HEIGHT),"#F9FDFF")
    d=ImageDraw.Draw(canvas)
    _grid(d,step=52)
    _box(d,36,32,1044,176,fill="#F6D9FB",seed=1,stroke=7)
    _letter(d,source["headline"],71,71,927,41,write,max_lines=2)
    d.text((66,186),"ĐOẠN CHAT GIẢ LẬP — KHÔNG PHẢI TIN NHẮN THẬT",
           font=font(20),fill="#4E5562")
    _box(d,46,230,1036,1085,fill="#FFFFFF",seed=16,stroke=8)
    d.rectangle((67,249,1016,308),fill="#B9DEFF")
    d.text((85,262),"nhóm: sống sót qua thứ hai (3)",font=font(27),fill=BLACK)
    # Do not make bubbles look like genuine platform screenshots.
    for idx,line in enumerate(lines):
        top=341+idx*275
        _stick_person(d,155,top+89,look=("happy" if idx==0 else "shocked"),
                      boss=(idx==1),seed=idx+7)
        _box(d,270,top,976,top+212,
             fill=(GREEN if idx==0 else BLUE),seed=29+idx*20,stroke=7)
        _letter(d,line,304,top+49,638,35,write,max_lines=3)
        _sunburst(d,909,top+28,color=RED if idx==1 else "#F8A208",seed=40+idx)
    # Hand-drawn reaction, explicitly a fake/creative exchange.
    _stick_person(d,174,919,look="shocked",seed=82)
    _scribble_arrow(d,[(236,956),(315,1043),(386,1060)],seed=74,color=RED)
    d=ImageDraw.Draw(canvas)
    _box(d,44,1109,1038,1324,fill=PINK,seed=77,stroke=8)
    _letter(d,source["punchline"],72,1167,925,43,write,max_lines=3)
    # Tiny ripped-paper proof-of-licensed-photo decoration, not the main visual.
    _photo_sticker(canvas,photo,(823,895,122,94))
    return canvas


def render_doodle(source,photo,write,font):
    """Use only for chat + coffee scenes; a cat/reaction must stay photographic."""
    if source["format"]=="chat":
        return render_chat(source,photo,write,font)
    if source["format"]=="contrast" and "cà phê" in source.get("topic","").casefold():
        return render_coffee(source,photo,write,font)
    return None
