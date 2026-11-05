"""Source-checked original AI-for-office content lane for Đồ Hay Đi Làm.

Each entry is ONE real office task + a transferable copyable prompt + one
comic moment for the owner-approved Người Tròn illustration identity.

The AI does not gain access to mail/files/accounts unless the user provides
content or explicitly connects an eligible app. Never invent outcomes or
claim AI work was carried out when only a prompt was drafted.
"""
from copy import deepcopy

SERIES = "AI — Đồng nghiệp thứ hai"
STYLE = "dohay_roundhead_doodle_v4"

OPENAI_PROMPT = "https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt"
OPENAI_GOOD = "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model-like-gpt-4"
MS_PROMPT = "https://learn.microsoft.com/en-us/training/modules/write-effective-prompts-do-more-prompting/"
OPENAI_DATA = "https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt"

# Simple evergreen workflows, not promises of native features of a specific plan.
# Copy-and-customize examples use invented, anonymized scenarios only.
AI_IDEAS = (
    {
        "key":"ai_prompt_4_elements", "lane":"prompt", "title":"Prompt tốt có bốn mảnh ghép",
        "hook":"Đừng bảo AI: 'LÀM GIÚP TUI' rồi trách nó đoán sai.",
        "task":"Biến một lời nhờ chung chung thành mục tiêu, bối cảnh, nguồn dữ liệu, cách trình bày.",
        "copy_prompt":"Tôi cần [kết quả]. Bối cảnh: [người đọc/mục đích]. Chỉ dùng thông tin tôi cung cấp bên dưới: [dữ liệu đã ẩn danh]. Trả lời dạng [bảng/5 ý], giọng [ngắn gọn]. Nếu thiếu dữ liệu, hỏi trước.",
        "visual":"Người Tròn cầm tờ giấy ghi LÀM GIÙM trước mặt AI mặt ngơ; bốn mẩu giấy tên Mục tiêu/Bối cảnh/Dữ liệu/Đầu ra bay vào biến thành câu lệnh cụ thể.",
        "risk":"Không nhét dữ liệu nội bộ hoặc hồ sơ cá nhân chưa được phép; AI cần thông tin đầu vào cụ thể.",
        "source":MS_PROMPT,
    },
    {
        "key":"ai_email_3_tones", "lane":"email", "title":"Một email, ba giọng điệu",
        "hook":"Tui định nhắn 'EM GỬI RỒI MÀ' nhưng còn cần đi làm ngày mai.",
        "task":"Viết lại email nhắc đồng nghiệp theo ba mức độ thân thiện, trung tính, trang trọng.",
        "copy_prompt":"Viết lại thông báo: 'Mình đã gửi tài liệu hôm qua'. Tạo 3 phiên bản: thân thiện, trung tính, lịch sự. Mỗi bản tối đa 45 từ, không tự thêm lời hứa hay thời hạn mới.",
        "visual":"Người Tròn cầm email bốc khói, ba bong bóng câu chữ với ba nét mặt từ cáu đến bình tĩnh, KHÔNG dựng giao diện email thật.",
        "risk":"Đọc lại tên người nhận, deadline, thông tin thực tế trước khi gửi.",
        "source":OPENAI_PROMPT,
    },
    {
        "key":"ai_meeting_actions", "lane":"second_brain", "title":"Họp xong phải biết ai làm gì",
        "hook":"HỌP 60 PHÚT, VIỆC VỀ TAY AI? MỘT MÀN SƯƠNG MÙ.",
        "task":"Rút quyết định, việc cần làm, phụ trách và hạn hoàn thành từ ghi chú đã ẩn danh.",
        "copy_prompt":"Từ ghi chú họp bên dưới (đã ẩn danh), tạo bảng: Quyết định | Việc tiếp theo | Phụ trách | Hạn chót | Chưa rõ. Chỗ nào không có dữ liệu thì ghi 'Chưa xác nhận', tuyệt đối không đoán tên hoặc deadline.",
        "visual":"Người Tròn giữa đám giấy họp xoay tít; một bảng việc làm có bốn cột và các dấu hỏi được đánh dấu CHƯA RÕ.",
        "risk":"Không đưa biên bản mật lên công cụ chưa được doanh nghiệp phê duyệt; con người chốt quyết định.",
        "source":MS_PROMPT,
    },
    {
        "key":"ai_daily_priorities", "lane":"second_brain", "title":"AI giúp xếp thứ tự việc, không làm sếp thứ hai",
        "hook":"TO-DO 18 MÓN. NÃO TUI TỰ THOÁT ỨNG DỤNG.",
        "task":"Tách danh sách việc giả định thành ưu tiên, việc phụ thuộc và câu hỏi xác nhận.",
        "copy_prompt":"Đây là danh sách việc đã loại dữ liệu riêng tư: [việc + hạn + tác động]. Sắp xếp 3 việc nên xử lý trước, giải thích ngắn vì sao. Chỉ ra việc thiếu hạn hoặc người phê duyệt. Đừng tự đoán mức độ khẩn.",
        "visual":"Người Tròn bị 18 tờ việc đuổi theo, AI đưa kính lúp và 3 tờ giấy ưu tiên, không hóa thân thành robot làm mọi thứ.",
        "risk":"AI chỉ gợi ý thứ tự; người dùng phải xác nhận mức ưu tiên với người giao việc.",
        "source":OPENAI_GOOD,
    },
    {
        "key":"ai_excel_formula_explain", "lane":"excel", "title":"Excel có công thức dài như sớ? Nhờ AI giải thích",
        "hook":"MỞ FILE CŨ. CÔNG THỨC NHÌN TUI NHƯ NGƯỜI LẠ.",
        "task":"Giải thích công thức Excel mẫu từng bước bằng tiếng Việt đơn giản.",
        "copy_prompt":"Giải thích công thức Excel này theo từng bước: =IF(A2>10,\"Đủ\",\"Thiếu\"). Cho 2 ví dụ đầu vào và kết quả; đừng thay công thức. Nêu tình huống có thể cho kết quả không như mong muốn.",
        "visual":"Người Tròn hoảng hốt trước con rắn ký tự =IF(...), AI cầm bút bảng phân tách thành từng đoạn dễ đọc.",
        "risk":"Đây chỉ là công thức ví dụ; kiểm thử lại trên dữ liệu thực và phiên bản Excel sử dụng.",
        "source":OPENAI_GOOD,
    },
    {
        "key":"ai_excel_data_check", "lane":"excel", "title":"AI giúp soi bảng dữ liệu trước khi báo cáo",
        "hook":"SỐ LIỆU ĐẸP QUÁ. ĐẸP KIỂU NÀO CŨNG ĐÁNG LO.",
        "task":"Soát lỗi dữ liệu theo quy tắc từ bảng giả lập đã ẩn danh; không giao AI quyền quyết định số liệu.",
        "copy_prompt":"Dữ liệu sau đã được thay bằng ví dụ giả: [dán 8 dòng]. Hãy chỉ ra giá trị trống, ngày sai định dạng, khả năng trùng và các ngoại lệ. Không tự sửa dữ liệu; lập bảng vị trí lỗi và cách kiểm tra trong Excel.",
        "visual":"Người Tròn mang kính soi bảng tính, các ô nghi vấn chui lên giơ tay; điểm chốt là KIỂM LẠI CHỨ KHÔNG TỰ SỬA.",
        "risk":"Không cung cấp dữ liệu khách hàng, số định danh hoặc dữ liệu nội bộ chưa được phép.",
        "source":MS_PROMPT,
    },
    {
        "key":"ai_ppt_outline", "lane":"powerpoint", "title":"Từ ghi chú rối thành dàn ý 5 slide",
        "hook":"SẾP: SLIDE ÍT CHỮ THÔI. GHI CHÚ: 17 TRANG.",
        "task":"Tạo dàn ý PowerPoint có thông điệp chính cho từng slide từ dữ liệu đã chuẩn bị.",
        "copy_prompt":"Đối tượng nghe là [nhóm người]. Mục tiêu: [quyết định cần chốt]. Dựa CHỈ trên ghi chú sau: [đã ẩn danh], đề xuất dàn ý 5 slide. Mỗi slide: 1 thông điệp chính, tối đa 3 ý, gợi ý hình. Đánh dấu thông tin còn thiếu.",
        "visual":"Người Tròn ôm cuộn giấy khổng lồ cạnh năm trang giấy nhỏ theo một mạch câu chuyện, bố cục không phải poster năm ô đều nhau.",
        "risk":"Không tự bịa số liệu, biểu đồ hoặc nguồn để slide 'thuyết phục' hơn.",
        "source":MS_PROMPT,
    },
    {
        "key":"ai_prompt_questions_first", "lane":"prompt", "title":"Mẹo mạnh nhất: bắt AI hỏi lại trước khi làm",
        "hook":"AI ĐOÁN TỪ A TỚI Z. TUI CHỈ CẦN NÓ HỎI A LÀ GÌ.",
        "task":"Yêu cầu AI hỏi các thông tin thiếu trước khi tạo sản phẩm hoàn chỉnh.",
        "copy_prompt":"Trước khi thực hiện, hãy hỏi tôi tối đa 3 câu quan trọng nhất để làm rõ mục tiêu, đối tượng và tiêu chí hoàn thành. Khi tôi trả lời xong mới tạo bản nháp đầu tiên.",
        "visual":"Người Tròn đưa đề bài hai chữ LÀM ĐI; AI cầm ba dấu hỏi bự, người tròn thở phào.",
        "risk":"Không biến ba câu hỏi thành lời hứa AI hiểu hết bối cảnh nếu chưa cung cấp dữ liệu.",
        "source":OPENAI_PROMPT,
    },
    {
        "key":"ai_prompt_3_tricks", "lane":"three_tips", "title":"3 mẹo dùng AI đỡ nhận đáp án chung chung",
        "hook":"NÓ VIẾT ĐÚNG NGỮ PHÁP. NHƯNG CHẲNG TRÚNG VIỆC.",
        "task":"Dạy ba thói quen: nêu đích, cho ví dụ, yêu cầu tự kiểm.",
        "copy_prompt":"Hãy giúp tôi [mục tiêu]. Đây là một ví dụ đầu ra tôi thích: [mẫu ngắn]. Tạo 2 phiên bản khác nhau, nêu điểm mạnh/yếu từng bản và đánh dấu chỗ cần tôi xác minh.",
        "visual":"Người Tròn cầm ba món đồ giả lập: kính ngắm Mục tiêu, tờ mẫu Ví dụ và kính lúp Tự kiểm; đặt trong tình huống chứ không phải ba khung giống nhau.",
        "risk":"Các mẹo cải thiện hướng dẫn, không bảo đảm kết quả đúng 100%.",
        "source":OPENAI_PROMPT,
    },
    {
        "key":"ai_prompt_example_output", "lane":"prompt", "title":"Muốn đúng định dạng? Cho AI một mẫu",
        "hook":"TUI MUỐN BẢNG. AI VIẾT THƠ. CẢ HAI ĐỀU RẤT NỖ LỰC.",
        "task":"Dùng ví dụ đầu ra để ràng buộc bảng kết quả nhất quán.",
        "copy_prompt":"Chuyển thông tin tôi cung cấp thành bảng gồm: Việc | Phụ trách | Hạn | Trạng thái. Ví dụ 1 dòng: 'Chuẩn bị slide | A | Thứ Sáu | Đang làm'. Không thêm cột khác; thiếu thông tin thì ghi 'Chưa rõ'.",
        "visual":"Người Tròn bị mưa chữ thơ rơi vào đầu, bên cạnh là tấm bảng mẫu viết tay đúng bốn cột.",
        "risk":"Định dạng ổn không đồng nghĩa dữ liệu chính xác; kiểm tra bản gốc.",
        "source":OPENAI_GOOD,
    },
    {
        "key":"ai_email_followup", "lane":"email", "title":"Nhắc deadline mà không thành 'sếp phụ'",
        "hook":"NHẮC VIỆC LẦN 3. VẪN MUỐN GIỮ TÌNH ĐỒNG NGHIỆP.",
        "task":"Viết thư nhắc việc lịch sự từ thông tin rõ ràng không tự tạo deadline.",
        "copy_prompt":"Viết tin nhắn nhắc tiến độ cho đồng nghiệp theo kiểu lịch sự, không gây áp lực. Sự thật đã xác nhận: [tên việc], [hạn], [cần người kia phản hồi điều gì]. Tối đa 60 từ, không tự thêm lời đe dọa hay lịch hẹn.",
        "visual":"Người Tròn đè bàn phím cáu giận, AI khoác cho câu chữ chiếc áo mềm mại; giữ biểu cảm hài.",
        "risk":"Dùng nội dung đã ẩn danh, xác nhận người nhận và thời hạn.",
        "source":OPENAI_PROMPT,
    },
    {
        "key":"ai_counterargument", "lane":"quality", "title":"Thay vì khen ý tưởng, nhờ AI đóng vai phản biện",
        "hook":"Ý TƯỞNG CỦA TUI HAY LẮM. AI: 'CHO XIN BẰNG CHỨNG?'",
        "task":"Đưa ra phản biện thực tế trước khi trình đề xuất.",
        "copy_prompt":"Đóng vai đồng nghiệp phản biện tích cực đề xuất sau: [mô tả không mật]. Chỉ ra 3 giả định chưa được kiểm chứng, 2 rủi ro và 1 cách thử nhỏ. Tránh khen xã giao; tách rõ suy luận và dữ kiện.",
        "visual":"Người Tròn đứng trên sân khấu thuyết trình, gương mặt tự tin; phía dưới AI giơ kính lúp to bằng người, tình huống đối lập.",
        "risk":"Đây là góp ý giả định, không thay việc hỏi người có chuyên môn.",
        "source":OPENAI_GOOD,
    },
    {
        "key":"ai_rewrite_plain", "lane":"writing", "title":"Viết lại thông báo bớt 'văn phòng phẩm'",
        "hook":"THÔNG BÁO DÀI 5 DÒNG. Ý CHÍNH: ĐỔI GIỜ HỌP.",
        "task":"Làm gọn thông báo mà giữ toàn bộ dữ kiện cốt lõi.",
        "copy_prompt":"Viết lại thông báo sau cho rõ ràng, gần gũi, tối đa 50 từ. Giữ nguyên tất cả ngày giờ, địa điểm, việc phải làm. Nếu thông tin mâu thuẫn hoặc thiếu, hãy báo trước khi viết: [thông báo đã ẩn danh].",
        "visual":"Người Tròn bị cuộn giấy thông báo quấn như bánh tráng, bản ngắn hiện ra sau chiếc kéo; không biểu diễn AI tự hành động.",
        "risk":"Không để AI làm mất thông tin quan trọng khi rút gọn.",
        "source":OPENAI_PROMPT,
    },
    {
        "key":"ai_source_checker", "lane":"quality", "title":"AI nói chắc như đinh đóng cột thì kiểm gì?",
        "hook":"AI: 'CHẮC 100%'. TUI: 'NGUỒN ĐÂU ANH?'",
        "task":"Nhận diện dữ kiện thiếu nguồn và kế hoạch xác minh trước khi dùng.",
        "copy_prompt":"Xem bản thảo sau và đánh dấu: dữ kiện có nguồn trong tài liệu, nhận định suy luận, dữ kiện chưa được kiểm chứng. Lập danh sách những điều tôi cần kiểm tra từ nguồn gốc. Không bịa liên kết hoặc trích dẫn.",
        "visual":"Người Tròn đội mũ thám tử cầm kính lúp soi tờ giấy ghi 100%, bên dưới là dấu hỏi lớn.",
        "risk":"Không coi AI là nguồn kiểm chứng độc lập cho chính câu trả lời của nó.",
        "source":OPENAI_GOOD,
    },
    {
        "key":"ai_privacy_3_no", "lane":"three_tips", "title":"3 thứ đừng quăng bừa vào AI công khai",
        "hook":"CHỤP HẾT HỒ SƠ KHÁCH GỬI AI? THÔI ĐỪNG.",
        "task":"Nhắc người đi làm phân loại thông tin trước khi sử dụng công cụ AI.",
        "copy_prompt":"Tôi định dùng AI cho [tác vụ]. Hãy giúp tôi lập checklist thông tin cần xóa hoặc thay bằng dữ liệu giả trước khi gửi: dữ liệu cá nhân, thông tin nội bộ, mật khẩu/mã truy cập. Nếu thiếu chính sách công ty, nhắc tôi hỏi bộ phận phụ trách.",
        "visual":"Người Tròn bê một thùng hồ sơ có ba ổ khóa; AI chỉ vào bảng CHECK QUYỀN TRƯỚC, không phải ảnh cảnh báo doanh nghiệp quá nghiêm.",
        "risk":"Không chia sẻ mật khẩu/OTP, dữ liệu khách hàng và tài liệu nội bộ khi chưa được phép.",
        "source":OPENAI_DATA,
    },
    {
        "key":"ai_three_roles", "lane":"second_brain", "title":"3 vai AI có thể làm đồng nghiệp thứ hai",
        "hook":"AI KHÔNG PHẢI NGƯỜI LÀM HỘ TẤT CẢ. NÓ LÀ BAN HỘI ĐỒNG NHỎ.",
        "task":"Dùng AI lần lượt để phát ý tưởng, phản biện và tự kiểm checklist đầu ra.",
        "copy_prompt":"Với tình huống [mô tả], lần lượt giúp tôi: (1) nêu 3 phương án; (2) chỉ ra 2 điểm yếu của từng phương án; (3) lập checklist 5 điểm để tôi tự đánh giá trước khi quyết định. Không tự khẳng định phương án nào chắc chắn thành công.",
        "visual":"Một Người Tròn đứng trước ba phiên bản nhỏ của chính mình: sáng tạo, khó tính, cầm checklist; nhân vật vẫn nhận diện nhất quán.",
        "risk":"Không xem AI như một người thật có quyền quyết định, phê duyệt hoặc truy cập tự động.",
        "source":MS_PROMPT,
    },
)

def validate_ideas(ideas=AI_IDEAS):
    if len(ideas) < 14:
        raise ValueError("too_few_ai_series_ideas")
    keys = [a["key"] for a in ideas]
    if len(keys)!=len(set(keys)):
        raise ValueError("duplicate_ai_idea_keys")
    if len({a["lane"] for a in ideas}) < 6:
        raise ValueError("ai_series_lacks_format_diversity")
    if len({a["visual"] for a in ideas})!=len(ideas):
        raise ValueError("repeated_ai_doodle_concept")
    for row in ideas:
        if any(not row.get(k) for k in ("key","lane","title","hook","task",
                                        "copy_prompt","visual","risk","source")):
            raise ValueError("missing_ai_idea_attribute")
        if not row["source"].startswith(("https://help.openai.com/",
                                          "https://learn.microsoft.com/")):
            raise ValueError("unverified_ai_idea_source")
        if len(row["copy_prompt"]) < 95:
            raise ValueError("ai_prompt_example_too_thin")
    return True

def as_tech_brief(idea):
    """Safe entry for Enna's automatic content planner; no external posting."""
    if idea["key"] not in {row["key"] for row in AI_IDEAS}:
        raise ValueError("unknown_ai_idea")
    return {
        "key":idea["key"], "pillar":"work", "series":SERIES,
        "app":"ai", "category":"ai_"+idea["lane"],
        "source":idea["source"], "visual_style_id":STYLE,
        "prompt":(
            "Tuyến AI — Đồng nghiệp thứ hai. MỘT tình huống: "+
            idea["task"]+". Hook: "+idea["hook"]+
            " Đưa một prompt mẫu ngắn, dùng được ngay, dựa trên: "+
            idea["copy_prompt"]+" Lưu ý: "+idea["risk"]+
            " Viết tiếng Việt tự nhiên, hài nhẹ, một vấn đề/bài. "
            "Không bịa số liệu, trải nghiệm đã thử, quyền đọc tệp/email, "
            "tự động thực hiện tác vụ hay độ chính xác tuyệt đối. "
            "Nhắc người đọc kiểm tra lại kết quả. "
            "Minh họa Người Tròn vẽ tay, tình huống riêng: "+
            idea["visual"]+
            " Không dùng poster ba ô lặp lại. Không tự đăng."
        ),
        "example_prompt":idea["copy_prompt"],
        "visual_scene":idea["visual"],
        "editorial_lane":idea["lane"],
    }

def ai_briefs():
    validate_ideas()
    return tuple(as_tech_brief(idea) for idea in AI_IDEAS)
