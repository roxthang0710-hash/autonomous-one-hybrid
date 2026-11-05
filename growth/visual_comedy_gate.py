"""Editorial gate for a meme's comedic *structure*, not a claim that AI is funny.

Aesthetic humor is subjective. This gate only catches plain descriptions,
marketing language, copied setup, missing twist and unsafe fake testimonials.
All rendered images still require a human visual review before publication.
"""
import re
from difflib import SequenceMatcher

STALE=("hãy cùng","các bạn hãy","khám phá ngay","truyền cảm hứng",
       "năng suất làm việc","tăng hiệu quả","đừng quên","cùng nhau",
       "bạn có bao giờ","làm việc chăm chỉ","văn phòng hiện đại",
       "một ngày thú vị","những điều tuyệt vời","kỷ niệm khó quên",
       "đầy năng lượng","mang lại giá trị","tích cực mỗi ngày",
       "đúng rồi","cả team","của cả team","giúp bạn thành công")
PUNCTUATION=(":","?","!", "…","—","-")
TOOLS=("máy","họp","sếp","bàn","việc","file","tệp","cà phê","ngáp",
       "tải xuống","thư mục","lịch","laptop","màn hình","văn phòng",
       "đi làm","giờ","phút","in", "sổ", "ngủ trưa")
MACHINES={
 "time_escalation":("phút","giờ","sau","08:","09:","10:","90"),
 "outer_inner_contrast":("trong","ngoài","mặt bàn","thư mục","còn"),
 "expectation_reversal":("trừ","nhưng","còn","thiếu","hóa ra"),
 "escalating_circularity":("việc thứ","họp","giải thích","lần","chưa xong"),
 "object_personification":("máy","cà phê","tui","tôi","gọi","sửa"),
 "visual_reaction":("ngáp","mic","mặt","nhìn","tắt","phản ứng","giữ","bàn phím","con tin"),
 "role_reversal":("nhân viên","ngủ","đi làm","sớm","9 giờ","trưa"),
}
def signals(source, copy):
    if not isinstance(source,dict) or not isinstance(copy,dict):
        return {"pass":False,"score":0,"reasons":["bad-input"]}
    h=str(copy.get("headline") or "").strip()
    p=str(copy.get("punchline") or "").strip()
    combined=(h+" "+p).casefold()
    reasons=[]
    if not 9<=len(h)<=85 or not 14<=len(p)<=115:
        reasons.append("bad-length")
    if "\n" in combined or re.search(r"https?://|www\.|@[a-z0-9]+|\b\d{8,}\b",combined):
        reasons.append("unsafe-or-linebreak")
    if any(x in combined for x in STALE):
        reasons.append("generic-ad-copy")
    if re.search(r"\b(vs|team)\b",combined) or "ngừng ngơi" in combined:
        reasons.append("stilted-language-or-unwanted-english")
    if p.count(".")>1:
        reasons.append("long-explanatory-punchline")
    if any(str(x).casefold() in combined for x in source.get("not_visually_supported",[]) if isinstance(x,str)):
        reasons.append("unobserved-photo-action")
    if not any(t in combined for t in TOOLS):
        reasons.append("not-anchored-in-office-life")
    anchors=source.get("twist_anchor_any") or []
    if not isinstance(anchors,list) or not anchors:
        reasons.append("missing-source-specific-twist-anchors")
    elif not any(isinstance(a,str) and a.casefold() in p.casefold() for a in anchors):
        reasons.append("no-recognizable-payoff")
    if p.count("'")%2 or p.count('"')%2:
        reasons.append("broken-dialogue-quoting")

    if h.casefold()==p.casefold() or SequenceMatcher(None,h.casefold(),p.casefold()).ratio()>.82:
        reasons.append("repeated-setup")
    device=source.get("comic_device")
    markers=MACHINES.get(device)
    if not markers or not any(marker in combined for marker in markers):
        reasons.append("missing-comedic-mechanism")
    # A valid meme should have a setup and a different payoff. We don't claim
    # the rubric can predict human laughter or social engagement.
    scene=source.get("scene")
    if not isinstance(scene,str) or len(scene)<8:
        reasons.append("missing-visual-premise")
    count=len(reasons)
    return {"pass":count==0,"score":max(0,6-count),"reasons":reasons,
            "device":device,"human_funny_rating":None}
