"""Verified evergreen workplace-tech briefs for organic Enna Threads content.

Research checked 2026-11-03 against first-party documentation.
Use only as prompts for NEW posts after the existing Metricool and Enna queue.
These are not reviews, recommendations to purchase, affiliate offers, or claims
that Enna personally used the tools. Re-check source when revising a feature.
"""

TECH_BRIEFS = (
    {
        "key": "windows_clipboard",
        "series": "Mẹo máy tính 30 giây",
        "pillar": "work",
        "prompt": (
            "Mẹo Windows 11: Win + V mở lịch sử bảng tạm; lần đầu có thể cần bật."
            " Viết một mẹo về việc tìm lại đoạn vừa sao chép, KHÔNG khuyên lưu"
            " mật khẩu, mã OTP hay thông tin nhạy cảm trong bảng tạm."
        ),
        "source": "https://support.microsoft.com/vi-vn/windows/apps/using-the-clipboard",
    },
    {
        "key": "windows_snip",
        "series": "Mẹo máy tính 30 giây",
        "pillar": "work",
        "prompt": (
            "Windows 11: Win + Shift + S mở công cụ chụp vùng màn hình."
            " Công cụ Cắt có thể nhận dạng văn bản trong ảnh qua Text actions."
            " Viết một mẹo cho người hay nhận tài liệu qua ảnh; tránh khẳng"
            " định nhận dạng văn bản luôn chính xác."
        ),
        "source": "https://support.microsoft.com/vi-vn/windows/apps/use-snipping-tool-to-capture-screenshots",
    },
    {
        "key": "powertoys_rename",
        "series": "Phần mềm hay, đi làm đỡ cực",
        "pillar": "organize",
        "prompt": (
            "Microsoft PowerToys PowerRename: đổi tên hàng loạt tệp bằng"
            " tìm/thay thế, xem trước kết quả trước khi áp dụng."
            " Nêu tình huống thư mục có nhiều phiên bản tệp lộn xộn;"
            " ghi rõ cần cài PowerToys trước, không phải tính năng mặc định."
        ),
        "source": "https://learn.microsoft.com/windows/powertoys/powerrename",
    },
    {
        "key": "powertoys_fancyzones",
        "series": "Phần mềm hay, đi làm đỡ cực",
        "pillar": "work",
        "prompt": (
            "Microsoft PowerToys FancyZones: cho phép tạo vùng bố trí"
            " cửa sổ trên màn hình Windows. Viết tình huống đối chiếu"
            " tài liệu và bảng tính cạnh nhau. Ghi rõ đây là tiện ích"
            " phải cài, không hứa tăng năng suất bằng con số."
        ),
        "source": "https://learn.microsoft.com/en-us/windows/powertoys/fancyzones",
    },
    {
        "key": "sheets_filter_view",
        "series": "Bớt khổ với bảng tính",
        "pillar": "work",
        "prompt": (
            "Google Sheets: chế độ xem bộ lọc giúp mỗi người lọc/sắp xếp"
            " dữ liệu theo góc nhìn riêng mà không thay đổi cách xem của"
            " đồng nghiệp. Viết tình huống hai người cùng xem danh sách."
            " Tính năng trên máy tính, không suy diễn cho mọi thiết bị."
        ),
        "source": "https://support.google.com/docs/answer/3540681?hl=en",
    },
    {
        "key": "sheets_dropdown",
        "series": "Bớt khổ với bảng tính",
        "pillar": "organize",
        "prompt": (
            "Google Sheets: Insert > Dropdown hoặc Data > Data validation"
            " tạo ô chọn trạng thái như Chờ làm / Đang làm / Hoàn thành."
            " Viết mẹo tránh nhập lung tung nhiều cách ghi cùng trạng thái;"
            " không tuyên bố tự động đồng bộ với mọi hệ thống khác."
        ),
        "source": "https://support.google.com/docs/answer/186103?hl=en",
    },
    {
        "key": "microsoft_todo",
        "series": "Quy trình nhỏ, hiệu quả lớn",
        "pillar": "work",
        "prompt": (
            "Microsoft To Do: mục My Day giúp chọn công việc trong ngày,"
            " việc chưa xong vẫn được giữ trong Tasks và có thể được gợi ý"
            " lại hôm sau. Viết mẹo chọn ba việc quan trọng thay vì"
            " ôm mọi nhiệm vụ. Không hứa việc sẽ được tự động hoàn thành."
        ),
        "source": "https://support.microsoft.com/en-us/todo/plan-and-connect-with-microsoft-to-do",
    },
    {
        "key": "powertoys_text_extract",
        "series": "Phần mềm hay, đi làm đỡ cực",
        "pillar": "work",
        "prompt": (
            "PowerToys Text Extractor có thể sao chép văn bản hiển thị"
            " trên màn hình bằng Win + Shift + T khi tiện ích được bật."
            " Kết quả OCR có thể sai, cần đọc lại, và cần gói ngôn ngữ"
            " phù hợp. Tập trung vào tình huống hình ảnh chứa nội dung."
        ),
        "source": "https://learn.microsoft.com/windows/powertoys/text-extractor",
    },
    {
        "key": "ai_safe_prompt",
        "series": "AI làm trợ lý, không làm hộ suy nghĩ",
        "pillar": "conversation",
        "prompt": (
            "Mẹo viết yêu cầu AI: nói rõ mục tiêu, định dạng, đối tượng,"
            " hạn chế và yêu cầu AI chỉ ra phần chưa chắc chắn."
            " Ví dụ nhờ gợi ý dàn ý email bàn giao từ dữ liệu đã ẩn danh."
            " Không khuyên tải hồ sơ khách hàng, hợp đồng mật hay dữ liệu"
            " nội bộ lên dịch vụ AI công khai."
        ),
        "source": "https://www.cisa.gov/secure-our-world",
    },
    {
        "key": "enna_mini_meeting",
        "series": "Enna Mini – Công cụ nhà làm",
        "pillar": "organize",
        "prompt": (
            "Enna Mini (bản thử miễn phí của Đồ Hay Đi Làm) có mẫu chốt"
            " việc sau cuộc họp với bốn trường: việc, người phụ trách,"
            " hạn chót và điều cần xác nhận; có nút sao chép và xuất CSV."
            " Viết tình huống hài nhẹ về họp xong không ai biết ai làm,"
            " không gắn liên kết, không nói ứng dụng có tính năng chưa có."
        ),
        "source": "docs/enna/kit/index.html",
    },
)


# Mix Windows, Excel and PowerPoint rather than repeating a Windows-only tip.
# The older Win+V/Snip ideas remain documented above but are NOT proposed as
# new posts while the channel has recently exhausted those combinations.
from datetime import date
from threads.shortcut_diversity import (
    WINDOWS_IDEAS, EXCEL_IDEAS, POWERPOINT_IDEAS, make_brief,
    is_repeated, is_present,
)

_OLD_TOOL_BRIEFS = tuple(
    brief for brief in TECH_BRIEFS
    if brief["key"] not in ("windows_clipboard", "windows_snip")
)

def _balanced_briefs():
    lanes = {
      "windows": [make_brief(x) for x in WINDOWS_IDEAS],
      "excel": [make_brief(x) for x in EXCEL_IDEAS],
      "powerpoint": [make_brief(x) for x in POWERPOINT_IDEAS],
      "other": list(_OLD_TOOL_BRIEFS),
    }
    result=[]
    # Two Windows angles, one Excel, one PowerPoint and one general office tip
    # within each complete five-slot mini-cycle. No repeated key in one pool.
    pattern=("windows", "excel", "windows", "powerpoint", "other")
    while any(lanes.values()):
        for tag in pattern:
            if lanes[tag]:
                result.append(lanes[tag].pop(0))
    return tuple(result)

TECH_BRIEFS = _balanced_briefs()

def choose_tech_brief(post_count, previous_texts=(), *, today=None):
    """Provide one new well-sourced tool tip for every third editorial post.

    Never repeat the exact Windows combo seen in recent own posts or Nov 3–6
    baseline, and do not confuse Windows-wide shortcuts with Office-only keys.
    Fail closed to a non-shortcut brief instead of giving a stale recycled one.
    """
    if not isinstance(post_count,int) or isinstance(post_count,bool) or post_count<0:
        raise ValueError("post_count must be a nonnegative integer")
    if post_count%3:
        return None
    if not isinstance(previous_texts,(list,tuple)):
        raise ValueError("previous_texts must be a list or tuple")
    today=today or date.today()
    start=(post_count//3)%len(TECH_BRIEFS)
    ordered=TECH_BRIEFS[start:]+TECH_BRIEFS[:start]
    for brief in ordered:
        combo=brief.get("shortcut")
        if combo and is_repeated(combo,previous_texts,today=today):
            continue
        # A past Windows article with the same use-case headline does not
        # count as new simply because a different CTA was attached.
        category=brief.get("category")
        if category and any(
            str(brief.get("key","")).replace("_"," ") in str(t).casefold()
            for t in previous_texts[:24]
        ):
            continue
        return brief
    # No unique angle available: skip. Do not force a quota with repeats.
    return None
