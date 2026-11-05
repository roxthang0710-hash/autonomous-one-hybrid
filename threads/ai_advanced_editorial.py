"""Stage-2 practical, multi-step AI office lessons.

Unlike Stage-1 copyable micro-prompts, every topic specifies actual inputs,
intermediate artifacts, a human review gate and explicit failure conditions.
Not auto-published: stage advancement requires verified training evidence.
"""
from threads.ai_workmate_editorial import STYLE, SERIES

ADVANCED = (
  {
    "key":"ai_l2_meeting_to_action","name":"Họp → bảng việc → tin nhắn chốt",
    "lane":"meeting","inputs":"ghi chú họp giả lập có người và deadline rõ hoặc còn trống",
    "steps":("trích quyết định khác với ý kiến", "lập bảng việc/người/hạn/chưa rõ",
             "viết 1 tin nhắn xác nhận việc thiếu thông tin"),
    "deliverable":"bảng hành động và câu hỏi xác nhận",
    "verify":"mỗi tên, hạn và quyết định phải kiểm tra ngược với nguồn; không bịa người phụ trách",
    "image":"Người Tròn bị bão giấy họp đẩy đi, từng tờ tự xếp thành hàng, ô trống giơ dấu hỏi",
  },
  {
    "key":"ai_l2_excel_test_formula","name":"Excel → giải thích → 3 ca kiểm thử",
    "lane":"excel","inputs":"công thức mẫu + đầu vào mẫu không nhạy cảm",
    "steps":("giải thích từng phần công thức", "tạo 3 ca dữ liệu và kết quả dự kiến",
             "chỉ ra lỗi có thể xảy ra và cách kiểm trên Excel"),
    "deliverable":"bảng ca kiểm thử đầu vào/đầu ra kỳ vọng",
    "verify":"tự chạy các ca trong Excel; AI không phải bộ tính kiểm chứng công thức",
    "image":"Người Tròn đối đầu con rắn công thức, chia thành các đoạn rồi thử ba chiếc máy tính mini",
  },
  {
    "key":"ai_l2_excel_anomaly","name":"Báo cáo → tìm bất thường → đối chiếu gốc",
    "lane":"excel","inputs":"tám dòng dữ liệu giả, quy tắc về cột và giá trị",
    "steps":("xác định quy tắc kiểm tra", "phát hiện các dòng nghi vấn",
             "lập danh sách soát lại trước khi chỉnh dữ liệu"),
    "deliverable":"bảng nghi vấn có vị trí và cách xác thực",
    "verify":"không tự sửa, không gọi sự khác biệt là sai khi thiếu quy tắc",
    "image":"Người Tròn đeo kính thám tử soi một bảng tính có dấu hỏi thò ra từ các ô nghi vấn",
  },
  {
    "key":"ai_l2_ppt_storyline","name":"PowerPoint → câu chuyện 5 slide → phản biện",
    "lane":"powerpoint","inputs":"mục tiêu thuyết trình, người nghe và ghi chú đã ẩn danh",
    "steps":("chốt một quyết định cần dẫn tới", "xây 5 thông điệp slide",
             "tự phản biện logic, dữ liệu thiếu và lời mời hành động"),
    "deliverable":"dàn ý 5 slide với thông điệp, gợi ý hình và chỗ cần nguồn",
    "verify":"không tự tạo biểu đồ hay số không có trong ghi chú",
    "image":"Người Tròn ôm cuộn giấy 17 trang, rút ra 5 lá bài như người diễn xiếc đang tập slide",
  },
  {
    "key":"ai_l2_email_sequence","name":"Email → nháp → rủi ro → bản gửi duyệt",
    "lane":"communication","inputs":"mục đích, người nhận giả định, các sự kiện đã xác nhận",
    "steps":("viết nháp ngắn", "soát giọng điệu, deadline, lời hứa",
             "tạo bản cuối có chỗ người dùng cần xác nhận"),
    "deliverable":"email nháp + checklist xác minh",
    "verify":"người dùng tự kiểm người nhận và nội dung trước khi tự gửi",
    "image":"Người Tròn muốn bấm nút GỬI thật to nhưng AI đưa kính lúp và bản checklist",
  },
  {
    "key":"ai_l2_weekly_report","name":"Báo cáo tuần → dữ kiện → tóm tắt có nguồn",
    "lane":"reporting","inputs":"bốn số liệu mẫu, mục tiêu tuần và ghi chú thành tựu đã cho",
    "steps":("tách thành tựu/khó khăn và số liệu", "tạo tóm tắt 120 từ",
             "liệt kê dữ kiện chưa có nguồn và câu hỏi gửi người phụ trách"),
    "deliverable":"báo cáo tuần ngắn + bảng bằng chứng",
    "verify":"không tự tính tỷ lệ tăng trưởng khi thiếu kỳ đối chiếu",
    "image":"Người Tròn đội nón bảo hộ leo lên ngọn núi báo cáo, cắm từng lá cờ nguồn gốc số liệu",
  },
  {
    "key":"ai_l2_prompt_debug","name":"Prompt chưa ra kết quả → chẩn đoán → thử lại",
    "lane":"prompt","inputs":"prompt cũ và kết quả mẫu sai/thiếu, cả hai đã ẩn danh",
    "steps":("tìm điểm mơ hồ, thiếu bối cảnh hoặc đầu ra", "viết prompt cải tiến",
             "tạo bộ 3 tiêu chí so sánh kết quả trước/sau"),
    "deliverable":"prompt v2 + 3 tiêu chí định lượng/định tính",
    "verify":"không khẳng định prompt mới hiệu quả hơn nếu chưa thử lại",
    "image":"Người Tròn sửa một máy in toàn dấu chấm hỏi bằng băng keo MỤC TIÊU/BỐI CẢNH/KIỂM",
  },
  {
    "key":"ai_l2_agent_readiness","name":"Một việc lặp → đặc tả AI Agent có duyệt",
    "lane":"agent_design","inputs":"quy trình thật thường lặp lại, dữ liệu được phép, ai phê duyệt",
    "steps":("vẽ các bước nhận việc, làm nháp, kiểm, xin duyệt",
             "giới hạn công cụ/dữ liệu/số lần gọi", "thiết kế trường hợp thất bại và nút dừng"),
    "deliverable":"bản thiết kế agent 1 tác vụ + bảng quyền cần/không cần",
    "verify":"chưa triển khai quyền gửi mail/đăng bài, không sao chép Enna gốc",
    "image":"Người Tròn điều khiển dây chuyền giấy tờ, mỗi chặng có một cái phanh lớn màu đỏ",
  },
)

def validate():
    assert len(ADVANCED) >= 8
    assert len({x["key"] for x in ADVANCED}) == len(ADVANCED)
    assert len({x["lane"] for x in ADVANCED}) >= 5
    for a in ADVANCED:
        assert len(a["steps"]) >= 3
        assert all(a[k] for k in ("name","inputs","deliverable","verify","image"))
        assert "Người Tròn" in a["image"]
    return True

def as_editorial_brief(x):
    if x["key"] not in {a["key"] for a in ADVANCED}:
        raise ValueError("Unknown advanced lesson")
    steps="; ".join(f"{i+1}. {step}" for i,step in enumerate(x["steps"]))
    return {
       "key":x["key"],"pillar":"work","series":"AI — Đồng nghiệp thứ hai · Tầng 2",
       "visual_style_id":STYLE,"ai_level":2,"source":"docs/enna/ai/index.html",
       "prompt":(
           "Bài AI ứng dụng NÂNG CAO nhưng vẫn dễ hiểu, không phải mẹo 1 dòng. "
           "Tác vụ: "+x["name"]+". Đầu vào: "+x["inputs"]+
           ". Các bước: "+steps+". Kết quả thực tế: "+x["deliverable"]+
           ". Kiểm tra bắt buộc: "+x["verify"]+
           ". Minh họa Người Tròn có hành động hài riêng: "+x["image"]+
           ". Không tự nhận đã chạy thật hoặc đã xử lý tài liệu người dùng. "
           "Nêu prompt ví dụ ngắn và điều kiện phải xin duyệt trước hành động."
       ),
    }

def briefs():
    validate()
    return tuple(as_editorial_brief(a) for a in ADVANCED)
