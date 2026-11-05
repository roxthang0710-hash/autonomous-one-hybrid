"""Microsoft-source-checked keyboard shortcut library for Đồ Hay Đi Làm.

Diversity comes from NEW use cases and shortcut combinations, not from
rewording the same Win+V/Win+L/closed-tab post. All platform and feature
limitations must be disclosed when relevant.

Do not attach visual assets or publish any post from this module.
"""
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

MS_WINDOWS="https://support.microsoft.com/vi-vn/accessibility/windows/keyboard-shortcuts-in-windows"
MS_INPUT="https://support.microsoft.com/en-us/accessibility/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc"
MS_EXCEL="https://support.microsoft.com/vi-vn/accessibility/excel/keyboard-shortcuts-in-excel"
MS_PPT_CREATE="https://support.microsoft.com/en-us/accessibility/powerpoint/use-keyboard-shortcuts-to-create-powerpoint-presentations"
MS_PPT_PRESENT="https://support.microsoft.com/en-us/accessibility/powerpoint/use-keyboard-shortcuts-to-deliver-powerpoint-presentations"

def item(key,app,category,shortcut,effect,scene,limit="",source=None):
    return {
        "key":key,"app":app,"category":category,"shortcut":shortcut,
        "effect":effect,"scene":scene,"limit":limit,
        "source":source or (MS_WINDOWS if app=="windows" else
                            MS_EXCEL if app=="excel" else MS_PPT_CREATE),
    }

WINDOWS_IDEAS=(
  item("win_snap","windows","window_layout","Win + Z","mở bố cục Snap Layouts","Làm báo cáo cần đặt Excel và tài liệu cạnh nhau","Windows 11; tính năng/bố cục tùy cửa sổ"),
  item("win_switch","windows","multitask","Alt + Tab","chuyển nhanh giữa các cửa sổ","Sếp gọi đúng lúc mở mười cửa sổ"),
  item("win_desktop_new","windows","virtual_desktops","Win + Ctrl + D","tạo màn hình nền ảo mới","Muốn tách khu vực họp và khu vực làm việc","Màn hình nền ảo không phải màn hình vật lý"),
  item("win_desktop_switch","windows","virtual_desktops","Win + Ctrl + ←","chuyển sang màn hình nền ảo bên trái","Quên tài liệu đang ở desktop ảo nào","Chỉ dùng khi có nhiều màn hình nền ảo"),
  item("win_secondary_display","windows","display","Win + Shift + →","chuyển cửa sổ sang màn hình tiếp theo","Mang laptop đi họp với hai màn hình","Cần nhiều màn hình; chọn trái hoặc phải cho phù hợp"),
  item("win_project","windows","display","Win + P","chọn chế độ trình chiếu/màn hình","Cắm máy chiếu xong chỉ thấy hình trên laptop","Một số chế độ cần màn hình thứ hai"),
  item("win_rename","windows","file_explorer","F2","đổi tên tệp được chọn","Khách gửi 17 tệp tên final"),
  item("win_folder","windows","file_explorer","Ctrl + Shift + N","tạo thư mục mới trong File Explorer","Tài liệu nằm như đống mì trong Downloads"),
  item("win_preview","windows","file_explorer","Alt + P","bật/tắt ngăn xem trước trong File Explorer","Chọn ảnh trong thư mục mà chưa muốn mở từng tệp","Bản xem trước tùy loại tệp và cấu hình"),
  item("win_path","windows","file_explorer","Alt + D","chọn thanh địa chỉ trong File Explorer","Đồng nghiệp gửi đường dẫn thư mục dài như sớ"),
  item("win_properties","windows","file_explorer","Alt + Enter","mở Thuộc tính của tệp hoặc thư mục đã chọn","Không biết tệp nào quá nặng để gửi mail"),
  item("win_voice","windows","input","Win + H","mở nhập liệu bằng giọng nói","Họp xong cần ghi nhanh ý tưởng trước khi quên","Cần microphone, kết nối internet và ngôn ngữ được hỗ trợ",MS_INPUT),
  item("win_emoji","windows","input","Win + .","mở bảng emoji và ký hiệu","Trả lời đồng nghiệp mà mãi không tìm thấy emoji phù hợp"),
  item("win_language","windows","input","Win + Space","chuyển ngôn ngữ hoặc bố trí bàn phím","Đang nhập tiếng Việt thì bàn phím chuyển layout","Cần cài nhiều ngôn ngữ hoặc bố trí bàn phím"),
  item("win_taskview","windows","multitask","Win + Tab","mở Task View","Mười ứng dụng mở cùng lúc, tìm hoài không thấy Excel"),
  item("win_focus","windows","window_layout","Win + Home","thu nhỏ các cửa sổ khác, giữ cửa sổ hiện tại","Desktop như chợ đầu mối mỗi khi sếp vào"),
  item("win_settings","windows","system","Win + I","mở Cài đặt Windows","Tìm phần cài đặt Bluetooth trong lúc họp"),
  item("win_magnifier","windows","accessibility","Win + +","mở Kính lúp của Windows","Đọc bảng tính trên màn hình nhỏ","Đây là phím Windows cùng phím dấu cộng"),
  item("win_run","windows","system","Win + R","mở hộp thoại Run","Muốn mở công cụ Windows theo tên thay vì dò menu","Không chạy lệnh lạ lấy từ bình luận"),
)

EXCEL_IDEAS=(
  item("excel_table","excel","structured_data","Ctrl + T","chuyển vùng dữ liệu thành bảng có bộ lọc","Bảng doanh số dài hơn một buổi họp",source=MS_EXCEL),
  item("excel_sum","excel","formula","Alt + =","thêm công thức AutoSum","Đứng hình khi phải cộng một cột chi phí dài",source=MS_EXCEL),
  item("excel_filter","excel","analysis","Ctrl + Shift + L","bật/tắt bộ lọc cho vùng dữ liệu phù hợp","Trưởng phòng hỏi chỉ xem các đơn chưa xử lý",source=MS_EXCEL),
  item("excel_flashfill","excel","cleanup","Ctrl + E","dùng Flash Fill từ mẫu dữ liệu","Bảng tên nhân viên cần tách họ tên nhanh","Cần mẫu rõ ràng và kiểm tra lại kết quả",MS_EXCEL),
)

POWERPOINT_IDEAS=(
  item("ppt_newslide","powerpoint","slide_authoring","Ctrl + M","thêm trang chiếu mới","Đang làm deck 20 trang mà sếp bổ sung một trang nữa",source=MS_PPT_CREATE),
  item("ppt_duplicate","powerpoint","slide_authoring","Ctrl + Shift + D","nhân đôi trang chiếu được chọn","Muốn giữ bố cục slide đẹp mà không dựng lại",source=MS_PPT_CREATE),
  item("ppt_current_slide","powerpoint","presentation","Shift + F5","trình chiếu từ slide hiện tại","Đang sửa slide 17 nhưng phải thử ngay",source=MS_PPT_PRESENT),
  item("ppt_black","powerpoint","presentation","B","tạm bật màn hình đen khi đang trình chiếu","Muốn mọi người tập trung nghe câu chốt thay vì đọc slide","Chỉ áp dụng khi đang ở Slide Show",MS_PPT_PRESENT),
)

ALL_SHORTCUTS=WINDOWS_IDEAS+EXCEL_IDEAS+POWERPOINT_IDEAS

# These combos appeared in verified own posts on Nov 3/5 or already-booked Nov 6.
# Keep them out of NEW idea briefs for 30 days. No existing booking is edited.
RECENTLY_FEATURED={
   "WIN+V":date(2026,11,5),
   "WIN+SHIFT+S":date(2026,11,5),
   "CTRL+SHIFT+T":date(2026,11,5),
   "WIN+L":date(2026,11,6),
   "WIN+E":date(2026,11,6),
   "CTRL+SHIFT+ESC":date(2026,11,6),
}
COOLDOWN_DAYS=30

def canonical(combo):
    """Normalize Windows/Win, spaces and arrow glyphs for duplicate checks."""
    s=str(combo or "").upper().replace("WINDOWS","WIN").replace("CONTROL","CTRL")
    s=s.replace("→","RIGHT").replace("←","LEFT").replace("↑","UP").replace("↓","DOWN")
    s=re.sub(r"\s*\+\s*","+",s)
    return re.sub(r"\s+","",s)

def is_present(text,combo):
    # Strip spaces only inside explicit key combinations, not whole sentences.
    # Otherwise 'Win + V mở' wrongly becomes 'WIN+VMỞ' and hides duplicates.
    if not isinstance(text,str):
        return False
    clean=text.upper().replace("WINDOWS","WIN").replace("CONTROL","CTRL")
    clean=clean.replace("→","RIGHT").replace("←","LEFT").replace("↑","UP").replace("↓","DOWN")
    clean=re.sub(r"\s*\+\s*", "+", clean)
    key=canonical(combo)
    if len(key)<2:
        return False
    return re.search(r"(?<![A-Z0-9])"+re.escape(key)+r"(?![A-Z0-9])",clean) is not None

def recent_combos(posts, limit=65):
    if not isinstance(posts,(tuple,list)):
        raise ValueError("recent_posts_must_be_list")
    result=set()
    for post in posts[:limit]:
        if not isinstance(post,str):
            continue
        for row in ALL_SHORTCUTS:
            if is_present(post,row["shortcut"]):
                result.add(canonical(row["shortcut"]))
    return result

def is_repeated(shortcut, posts=(), *, today=None):
    today=today or datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date()
    key=canonical(shortcut)
    if key in recent_combos(list(posts)):
        return True
    last=RECENTLY_FEATURED.get(key)
    return bool(last and 0 <= (today-last).days < COOLDOWN_DAYS)

def make_brief(row):
    scene=row["scene"]
    caveat=(": Lưu ý "+row["limit"]+"." if row["limit"] else ".")
    return {
        "key":row["key"],"series":{
         "windows":"Phím tắt Windows: mỗi bài một tình huống",
         "excel":"Excel đỡ toang","powerpoint":"PowerPoint đỡ phèn"}[row["app"]],
        "pillar":"work","category":row["category"],
        "app":row["app"],"shortcut":row["shortcut"],
        "source":row["source"],
        "prompt":(
           "Chỉ viết về tổ hợp "+row["shortcut"]+" trong "+
           {"windows":"Windows","excel":"Excel trên Windows","powerpoint":"PowerPoint trên Windows"}[row["app"]]+
           ": "+row["effect"]+". Tình huống duy nhất: "+scene+
           caveat+" Viết tiếng Việt ngắn, vui nhẹ, đúng tác dụng. "
           "Tuyệt đối không nhắc lại tổ hợp phím cũ đã xuất bản "
           "hoặc biến một mẹo thành danh sách ba phím quen thuộc. "
           "Khi làm ảnh, dùng style Người Tròn, minh họa thao tác "
           "thật thay vì poster ba ô."
        ),
    }


def repeated_combos_in_draft(candidate, previous_texts=(), *, today=None):
    """Exact normalized shortcut overlap. Does not blacklist the broad word Windows."""
    if not isinstance(candidate,str):
        return []
    all_keys={canonical(row["shortcut"]):row["shortcut"] for row in ALL_SHORTCUTS}
    for old in RECENTLY_FEATURED:
        all_keys.setdefault(old,old)
    return sorted({
       short for token,short in all_keys.items()
       if is_present(candidate,token) and is_repeated(short,previous_texts,today=today)
    })
