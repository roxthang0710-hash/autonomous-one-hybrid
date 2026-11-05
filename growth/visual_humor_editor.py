"""Safe, optional Groq 'humor critic' for Enna photo-first draft media.

The AI can only propose Vietnamese copy for an already-licensed, captioned
photograph. Nothing here posts or approves a media asset. An AI suggestion
failing the groundedness gate is discarded in favor of the human-written copy.
"""
import json
import os
import re
from difflib import SequenceMatcher
import requests

GENERIC = ("bạn có bao giờ", "phiên bản tốt nhất", "cố gắng mỗi ngày",
           "cùng nhau lan tỏa", "hãy cùng", "truyền cảm hứng",
           "mở ra hành trình", "không thể bỏ lỡ", "bí quyết thành công",
           "tất cả chúng ta", "đồng nghiệp thân yêu",
           "thả tim", "bình luận ngay", "theo dõi ngay",
           "đừng quên", "năng suất 200%", "sống hết mình")
FORBIDDEN = ("http://", "https://", "www.", "@", "tiktok", "shopee",
             "mua ngay", "trúng thưởng", "affiliate", "người trong ảnh",
             "cô ấy trong ảnh", "anh ấy trong ảnh")
OFFICE_TERMS = ("bàn", "máy", "laptop", "cà phê", "họp", "deadline", "việc",
                "lịch", "file", "tệp", "sếp", "văn phòng", "báo cáo", "đi làm",
                "đồng nghiệp", "màn hình", "thư mục", "sổ", "nghỉ trưa",
                "bút", "tải xuống", "buổi sáng", "công ty")

def check_copy(source, suggestion):
    """Reject ungrounded, repetitive, promotional or generic AI prose."""
    if not isinstance(suggestion,dict):
        return None
    h=suggestion.get("headline")
    p=suggestion.get("punchline")
    if not isinstance(h,str) or not isinstance(p,str):
        return None
    h,p=h.strip(),p.strip()
    if (not 12<=len(h)<=66 or not 18<=len(p)<=100
            or h.count("\n") or p.count("\n")
            or len(h.split())>13 or len(p.split())>22):
        return None
    combined=(h+" "+p).casefold()
    if any(x in combined for x in GENERIC+FORBIDDEN):
        return None
    if re.search(r"[\u0000-\u001f]|\b\d{8,}\b|[<>]",combined):
        return None
    # A draft must explicitly relate to real, non-identifying office props.
    if not any(t in combined for t in OFFICE_TERMS):
        return None
    # No "same line with a different exclamation mark" masquerading as AI improvement.
    old=(source["headline"]+" "+source["punchline"]).casefold()
    if SequenceMatcher(None,combined,old).ratio()>.90:
        return None
    if SequenceMatcher(None,h.casefold(),p.casefold()).ratio()>.67:
        return None
    # Never change the original media or add characters, brand claims, URLs.
    return {"headline":h,"punchline":p}

def generate_variant(source, *, request=requests.post):
    """Try one optional official Groq API call; fallback is curated original.

    No key or failed generation -> None. Caller must keep draft in review.
    """
    secret=os.environ.get("GROQ_API_KEY","").strip()
    if not secret:
        return None
    allowed={k:source.get(k) for k in ("id","visual_hint","headline","punchline","topic")}
    prompt={
      "photo_scene_verified_by_human":allowed.get("visual_hint"),
      "source_is_photographic":True,
      "brand":"Đồ Hay Đi Làm",
      "original_caption":allowed["headline"]+" / "+allowed["punchline"],
      "task":"Viết câu hài công sở thuần Việt có một tình huống cụ thể và kết bất ngờ; dùng ảnh làm minh họa, KHÔNG nhận ảnh kể chuyện thật. Ngắn, có duyên, không nhắc AI, không dùng câu CTA, không meme có bản quyền.",
      "limits":"headline 12-66 ký tự, punchline 18-100 ký tự, không đưa nhân vật hoặc diễn biến không có trong ảnh, không nói người trong ảnh đã làm gì; tránh sáo rỗng.",
      "examples_to_avoid":[*GENERIC[:6]],
    }
    body={
      "model":os.getenv("GROQ_MODEL","openai/gpt-oss-20b"),
      "temperature":0.72,"max_completion_tokens":380,
      "response_format":{"type":"json_schema","json_schema":{
        "name":"enna_photo_humor","strict":True,
        "schema":{"type":"object","additionalProperties":False,
           "properties":{"headline":{"type":"string"},"punchline":{"type":"string"}},
           "required":["headline","punchline"]}}},
      "messages":[
        {"role":"system","content":"Bạn là biên tập viên hài hước tiếng Việt về đời sống văn phòng. Chỉ đề xuất 1 tiêu đề ngắn và 1 câu kết hóm hỉnh trong JSON. Hình ảnh là tư liệu minh họa, không phải bằng chứng sự kiện. Không bịa lời thoại của người thật hay dùng bất cứ thương hiệu nào."},
        {"role":"user","content":json.dumps(prompt,ensure_ascii=False)}
      ]}
    try:
        result=request("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":"Bearer "+secret,"Content-Type":"application/json"},
            json=body,timeout=25)
        result.raise_for_status()
        data=json.loads(result.json()["choices"][0]["message"]["content"])
    except (requests.RequestException,ValueError,KeyError,IndexError,TypeError):
        return None
    return check_copy(source,data)
