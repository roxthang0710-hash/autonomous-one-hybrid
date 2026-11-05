"""Enna Office Doodle Batch: original Vietnamese hand-drawn art, not stock photos.

14 unique 1080x1350 original meme drawings for existing schedule slots.
No third-party photo, AI image, external font asset or licensed template.
Drawings are review-only by default; companion uploader writes review media,
not a social post. Stable IDs and SHA256 evidence permit safe deduplication.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.enna_doodle_composer import (
    WIDTH, HEIGHT, BLACK, BLUE, GREEN, PINK, YELLOW, RED, PAPER,
    _box, _grid, _wiggle, _circle, _sunburst, _smile,
    _cup, _stick_person, _scribble_arrow
)
from scripts.enna_visual_factory import _write, _font

MEMES = [
 {"id":"keyboard-rescue","hook":"3 PHÍM TẮT CỨU NGUY","punch":"SẾP: XONG CHƯA?  TÔI: ĐANG CỨU CỬA SỔ!","scene":"keyboard","label":"MẸO CÔNG SỞ","bg":"#F8F9FF","accent":"#FFE063"},
 {"id":"twenty-urgent","hook":"20 TIN NHẮN ĐỀU BẢO: GẤP","punch":"ỦA, VẬY AI ĐƯỢC GẤP TRƯỚC?","scene":"urgent","label":"HỘI CHỨNG 9 GIỜ SÁNG","bg":"#FAF7FD","accent":"#FFB7D9"},
 {"id":"pen-missing","hook":"BÀN GỌN 10/10","punch":"CÂY BÚT ĐÃ VÀO DIỆN MẤT TÍCH.","scene":"pen","label":"DỌN DẸP CÓ GIÁ CỦA NÓ","bg":"#FBFFF7","accent":"#B9F7C9"},
 {"id":"twelve-tabs","hook":"NÃO LÚC 0:55 SÁNG","punch":"12 TAB MỞ. 1 TAB PHÁT NHẠC. 0 TAB NGỦ.","scene":"tabs","label":"CÚ ĐÊM ĐI LÀM","bg":"#F4F4FF","accent":"#CDB6FF"},
 {"id":"weekend-brain","hook":"NGƯỜI: HÔM NAY LÀ THỨ BẢY","punch":"NÃO: THỨ HAI CÒN FILE NÀO CHƯA GỬI?","scene":"weekend","label":"CÔNG SỞ TRONG ĐẦU","bg":"#FDF9F1","accent":"#F9CD5D"},
 {"id":"headphones-left","hook":"ĐI CÔNG TÁC: ĐỦ HẾT!","punch":"TAI NGHE: CHÀO, TUI Ở NHÀ NHA.","scene":"headphones","label":"HỘI NGƯỜI HAY QUÊN","bg":"#F7FCFF","accent":"#A4E0FF"},
 {"id":"sunday-outfits","hook":"CHỦ NHẬT 18:30","punch":"QUẦN ÁO THỨ HAI: CHƯA AI ĐƯỢC TUYỂN.","scene":"outfits","label":"LỄ TUYỂN DỤNG TRANG PHỤC","bg":"#FFFCF5","accent":"#FFB7D9"},
 {"id":"sunday-anxiety","hook":"CHỦ NHẬT, 19 GIỜ","punch":"NÃO ĐÃ TỰ ĐI LÀM TRƯỚC CHỦ NÓ.","scene":"anxiety","label":"ĐỪNG NHẮC THỨ HAI","bg":"#FBF8FF","accent":"#C9B5FF"},
 {"id":"desk-hoarder","hook":"DỌN BÀN XONG RỒI ĐÓ","punch":"CÒN HỘP ĐỒ TỪ NĂM NGOÁI: KHÔNG ĐƯỢC ĐỤNG.","scene":"hoarder","label":"TRƯỞNG HỘI HOÀI NIỆM","bg":"#FFFDF8","accent":"#F2CE77"},
 {"id":"meeting-fast","hook":"CÒN 10 PHÚT TRƯỚC GIỜ HỌP","punch":"MỞ 12 TAB KHÔNG PHẢI LÀ CHUẨN BỊ.","scene":"meeting","label":"MẸO NHANH ĐỠ TOANG","bg":"#F5FCF7","accent":"#C5F1BB"},
 {"id":"packing","hook":"VALI ĐI CÔNG TÁC","punch":"CUỘN, GẤP HAY NHỒI ĐẠI RỒI CẦU NGUYỆN?","scene":"packing","label":"BA HỆ NGƯỜI SOẠN ĐỒ","bg":"#F8FBFF","accent":"#A8DDFC"},
 {"id":"accessory","hook":"MUA ĐỒ CHO GÓC BÀN","punch":"DÙNG HẰNG NGÀY HAY CHỈ ĐẸP LÚC CHỤP ẢNH?","scene":"accessory","label":"VÍ TIỀN ĐANG CẦU CỨU","bg":"#FFF9F3","accent":"#FFCFAB"},
 {"id":"cable-spaghetti","hook":"MANG CÁP ĐI LÀM","punch":"CẦM 5 SỢI DÂY MÀ NHƯ BÊ 1 TÔ MÌ.","scene":"cables","label":"HỘI PHỤ KIỆN CÔNG SỞ","bg":"#FBF9FF","accent":"#D3C6FD"},
 {"id":"five-desk-items","hook":"BÀN LÀM VIỆC CHỈ ĐƯỢC 5 MÓN","punch":"MÓN THỨ 6: NHÂN PHẨM. CẦN NHẤT LUÔN.","scene":"five","label":"THỬ THÁCH DỌN BÀN","bg":"#F9FFF9","accent":"#B3F1C0"}
]

def note(draw,title,x,y,size=30,fill=BLACK,max_lines=2,width=680):
    if size<22:
        # Decorative micro-labels stay outside the guarded main-caption wrapper.
        draw.text((x,y),title,font=_font(size),fill=fill)
        return y+size
    return _write(draw,title,x,y,width,size,fill,max_lines=max_lines)

def sketch_laptop(d,cx,cy,scale=1):
    w=int(360*scale);h=int(230*scale)
    _box(d,cx-w//2,cy-h//2,cx+w//2,cy+h//2,fill="#B2DEFF",seed=13,stroke=8)
    _wiggle(d,[(cx-w//2-40,cy+h//2+26),(cx+w//2+43,cy+h//2+26)],seed=21,width=10)
    _smile(d,cx,cy,look="shocked",scale=.68)

def sketch_phone(d,x,y,seed=4):
    _box(d,x,y,x+440,y+650,fill="#FFF",seed=seed,stroke=9)
    _wiggle(d,[(x+70,y+58),(x+320,y+60)],seed=seed+2)
    d.ellipse((x+197,y+603,x+239,y+633),outline=BLACK,width=6)

def panel(d,box,fill="#FFFFFF",seed=0):
    _box(d,*box,fill=fill,seed=seed,stroke=6)

def drawing(d,scene):
    if scene=="keyboard":
        sketch_laptop(d,540,506,scale=1.65)
        for i,code in enumerate(["Win + V","Ctrl + Shift + T","Win + Shift + S"]):
            x=120+(i%2)*410;y=835+(i//2)*125
            panel(d,(x,y,x+370,y+100),fill=["#C4EFFF","#FFE6A1","#C6F5C6"][i],seed=21+i)
            note(d,code,x+19,y+23,size=26,width=330,max_lines=2)
        _sunburst(d,910,430,color=RED)
    elif scene=="urgent":
        sketch_phone(d,315,265)
        for i in range(7):
            left=360+(i%2)*76;top=338+i*69
            panel(d,(left,top,left+305,top+58),fill=("#FFA9C2" if i%2 else "#C1EEFF"),seed=i+3)
            note(d,["GẤP!!!","RẤT GẤP!","GẤP NHA","GẤP XÍU","CHỐT GẤP","CÒN 5 PHÚT","CŨNG GẤP"][i],
                 left+18,top+10,size=21,width=290,max_lines=1)
        _stick_person(d,165,905,look="shocked",seed=14)
    elif scene=="pen":
        panel(d,(145,355,916,940),fill="#FAEFE2",seed=10)
        sketch_laptop(d,445,583,scale=.9)
        _circle(d,775,694,85,fill="#F8C9D3")
        _wiggle(d,[(770,690),(720,749),(676,806)],width=9,seed=22)
        note(d,"BÚT ƠI?",648,491,size=37,width=260)
        _sunburst(d,804,396,color=RED)
    elif scene=="tabs":
        panel(d,(100,290,979,990),fill="#D9D0FF",seed=4)
        for i in range(11):
            x=142+(i%3)*271;y=357+(i//3)*138
            panel(d,(x,y,x+240,y+112),fill=("#FFFFFF" if i%3==0 else "#B9F5E5"),seed=i+34)
            note(d,["?","Zzz","CTRL+Z","MAIL","???","HỌP","BÁO CÁO","♪","SẾP","TỐI NAY","..."][i],
                 x+26,y+32,size=27,width=191,max_lines=1)
        _stick_person(d,894,977,look="shocked",seed=21)
    elif scene=="weekend":
        panel(d,(95,334,973,947),fill="#FFF0C3",seed=8)
        _stick_person(d,338,594,look="happy",seed=42)
        _wiggle(d,[(201,845),(345,824),(470,844)],seed=43,width=9)
        panel(d,(565,394,911,742),fill="#CCE0FC",seed=7)
        note(d,"THỨ HAI",606,436,size=37,width=290,max_lines=1)
        _smile(d,733,632,look="shocked",seed=39)
        _scribble_arrow(d,[(541,770),(624,804),(701,820)],seed=29)
    elif scene=="headphones":
        panel(d,(100,340,900,980),fill="#E1F1FF",seed=14)
        _wiggle(d,[(175,780),(175,480),(788,480),(788,810),(175,810)],seed=41,width=10)
        _box(d,197,532,770,786,fill="#FFF3E3",seed=33)
        note(d,"QUẦN ÁO  ✓",236,573,size=40,width=465)
        note(d,"SẠC  ✓",236,639,size=40,width=465)
        note(d,"GIẤY TỜ  ✓",236,704,size=40,width=465)
        for k in range(2):
            _circle(d,910,406+k*154,34,fill=PINK)
            _wiggle(d,[(907,436+k*154),(915,477+k*154),(889,501+k*154)],seed=k+15,width=6)
    elif scene=="outfits":
        for i in range(3):
            x=200+i*342
            panel(d,(x-150,365,x+150,950),fill=["#ECF8FF","#FDE0EB","#E2F6DE"][i],seed=i+10)
            _smile(d,x,479,look="shocked" if i==2 else "happy",seed=i+2,scale=.62)
            d.polygon([(x-90,652),(x-44,578),(x+44,578),(x+90,652),(x+57,838),(x-57,838)],
                      fill=["#C9A9FC","#FFA76F","#8BD4CB"][i],outline=BLACK)
            note(d,["GIẶT","CHƯA KHÔ","ĐỒ NGỦ"][i],x-112,869,size=22,width=225,max_lines=2)
    elif scene=="anxiety":
        panel(d,(118,325,962,942),fill="#EEE0FF",seed=22)
        _smile(d,376,643,look="dead",seed=99,scale=1.7)
        panel(d,(605,438,902,782),fill="#FFF3BE",seed=23)
        note(d,"MAI THỨ HAI",628,497,size=31,width=252,max_lines=2)
        _sunburst(d,721,748,color=RED)
    elif scene=="hoarder":
        panel(d,(100,350,969,948),fill="#E8D9C5",seed=11)
        sketch_laptop(d,387,530,scale=.83)
        for i in range(5):
            x=536+(i%2)*149;y=510+(i//2)*142
            _box(d,x,y,x+130,y+109,fill=["#FFB2CD","#C4F4C2","#BDDFFA"][i%3],seed=i+21)
        note(d,"HỘP ĐỪNG VỨT!",477,879,size=25,width=420)
        _sunburst(d,843,430,color=RED)
    elif scene=="meeting":
        panel(d,(130,316,952,973),fill="#E1F4D6",seed=17)
        for i,line in enumerate(["MỤC TIÊU","2 CÂU CẦN HỎI","1 QUYẾT ĐỊNH"]):
            x=232;y=416+i*152
            _box(d,x,y,x+76,y+78,fill="#FFFFFF",seed=i+9)
            _wiggle(d,[(x+14,y+37),(x+28,y+52),(x+61,y+17)],color="#2F8F51",width=9,seed=i+2)
            note(d,line,353,y+19,size=29,width=475,max_lines=2)
        _stick_person(d,839,881,look="happy",seed=45)
    elif scene=="packing":
        panel(d,(100,344,974,982),fill="#DAF4FE",seed=4)
        for i,title in enumerate(["CUỘN","GẤP","NHỒI"]):
            x=151+i*300
            panel(d,(x,430,x+260,859),fill=["#FFF5B9","#FFC9E2","#C3F9C9"][i],seed=i+11)
            note(d,title,x+45,455,size=33,width=200,max_lines=1)
            for k in range(4):
                if i==0:
                    _circle(d,x+125,580+k*61,27,fill="#A5CDFA",seed=k+2)
                elif i==1:
                    _box(d,x+56,560+k*55,x+196,601+k*55,fill="#FFE4B5",seed=k+3)
                else:
                    _wiggle(d,[(x+57,650+k*22),(x+126,560+k*55),(x+186,720+k*10)],
                            color=RED,width=7,seed=k+2)
    elif scene=="accessory":
        panel(d,(100,350,967,948),fill="#FFEDCA",seed=14)
        panel(d,(141,423,489,853),fill="#F4D9F1",seed=19)
        panel(d,(569,423,922,853),fill="#C7F0C0",seed=20)
        _circle(d,314,609,84,fill="#FFB8DC")
        _smile(d,314,606,look="happy",seed=30)
        sketch_laptop(d,751,635,scale=.65)
        note(d,"ĐẸP",239,760,size=35,width=160)
        note(d,"CÓ ÍCH",651,758,size=34,width=200)
    elif scene=="cables":
        panel(d,(83,323,989,998),fill="#E5D8FF",seed=15)
        for i in range(9):
            points=[(150+i*80,402),(178+(i%3)*160,518+i*12),
                    (190+i*70,680+((i*13)%200)),(220+(i%4)*173,895)]
            _wiggle(d,points,width=9,seed=25+i,color=["#F96277","#2997C8","#30A678","#8061C3"][i%4])
        note(d,"MÌ HẢ?  KHÔNG, DÂY SẠC.",190,933,size=29,width=730)
        _sunburst(d,812,437,color=RED)
    elif scene=="five":
        panel(d,(99,326,963,968),fill="#DDF8E4",seed=3)
        for i,name in enumerate(["MÁY","SỔ","BÚT","ĐT","GỐI"]):
            x=155+(i%3)*265;y=412+(i//3)*224
            panel(d,(x,y,x+221,y+173),fill=["#FFF6CC","#F7D2E4","#D2E8FF"][i%3],seed=i+10)
            _smile(d,x+109,y+86,look="happy",seed=i+13,scale=.45)
            note(d,name,x+49,y+132,size=23,width=145,max_lines=1)
        _sunburst(d,849,861,color=RED)
    else:
        raise ValueError("unknown-original-doodle-scene")

def draw_one(info):
    image=Image.new("RGB",(WIDTH,HEIGHT),info["bg"])
    d=ImageDraw.Draw(image)
    _grid(d,step=62)
    _box(d,23,23,1057,193,fill=info["accent"],seed=13,stroke=7)
    _write(d,info["hook"],57,73,955,44,BLACK,max_lines=2)
    _box(d,51,212,970,281,fill="#FFFFFF",seed=33,stroke=5)
    # Tiny decorative labels use a 21px font directly; the shared text
    # wrapper intentionally rejects sizes under 22px.
    d.text((76,231),info["label"],font=_font(21),fill=BLACK)
    drawing(d,info["scene"])
    _box(d,30,1093,1050,1310,fill=info["accent"],seed=81,stroke=8)
    _write(d,info["punch"],62,1161,963,40,BLACK,max_lines=3)
    d.text((56,1319),"ĐỒ HAY ĐI LÀM  •  TRANH VẼ HÀI HƯỚC HƯ CẤU",font=_font(14),fill="#67616C")
    return image

def generate(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    listing=[]
    for info in MEMES:
        art=draw_one(info)
        filename="enna-doodle-"+info["id"]+".png"
        file=folder/filename
        art.save(file,format="PNG",optimize=True)
        data=file.read_bytes()
        sha=hashlib.sha256(data).hexdigest()
        proof={
            "visual_version":"3.1-batch",
            "source":"enna_original_drawing_no_third_party_art",
            "style":"Vietnamese scribbly hand-drawn Gen Z workplace meme",
            "status":"DRAFT_REQUIRES_HUMAN_REVIEW",
            "published":False,
            "sha256":sha,
            "width":WIDTH,"height":HEIGHT,
            "id":info["id"],"scene":info["scene"],
            "hook":info["hook"],"punch":info["punch"],
            "ai_generated_image":False,
            "rights":"original illustrations generated by Enna Pillow line art",
            "no_social_actions":True
        }
        (folder/(filename+".rights.json")).write_text(
            json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf-8")
        listing.append({"id":info["id"],"file":filename,"sha256":sha,
                        "scene":info["scene"],"status":"needs_review"})
    (folder/"manifest.json").write_text(json.dumps(
        {"visual_version":"3.1-batch","count":len(listing),
         "social_published":0,"items":listing},ensure_ascii=False,indent=2),encoding="utf-8")
    return listing

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="enna-doodle-queue")
    args=parser.parse_args()
    items=generate(args.output)
    print(json.dumps({"generated":len(items),"status":"review_only","social_posts":0},ensure_ascii=False))
