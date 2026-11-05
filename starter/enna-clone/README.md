# Enna Clone Starter — tác vụ AI có kiểm soát

**Bản học tập để tự xây AI Agent của chính bạn**, hoàn toàn tách biệt khỏi Enna chạy kênh Đồ Hay Đi Làm. Không sao chép tài khoản, dữ liệu, Vault, GitHub Actions hoặc quyền Meta của Enna gốc. Đây là phiên bản v0.1, không phải "full clone" tự vận hành mạng xã hội.

## Hai chế độ có thể dùng thật

1. **Trên trình duyệt:** [Enna Clone Lite](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/clone/) cho phép tự đặt tên agent, nhiệm vụ, cấu trúc 3 bước, sao chép bản hướng dẫn và tải cấu hình của riêng bạn. Không cần đăng ký, không gửi văn bản lên máy chủ. *Đây là bộ tạo hướng dẫn, không trực tiếp gọi mô hình AI.*
2. **Trên máy của bạn:** `agent.py` chạy một tác vụ bằng **khóa Groq API của chính bạn**. Mỗi tác vụ gọi mô hình **tối đa hai lần** (tạo bản nháp, tự rà soát), không đọc file không được chỉ định, không có công cụ gửi email/đăng bài, không chạy lệnh máy, không tự bấm nút và luôn cần người dùng duyệt. Nhà cung cấp quyết định hạn mức/chi phí, không bảo đảm miễn phí.

## Chạy thử không cần API

Tải `agent.py` về thư mục riêng và mở Terminal:

```bash
python agent.py --demo --mode meeting
```

Demo chỉ mô phỏng quy trình và **không tạo câu trả lời từ AI**.

## Chạy với API key riêng — chỉ ở máy của bạn

Đọc hạn mức và điều khoản trên trang nhà cung cấp. Không nhập khóa API vào website công khai, GitHub Issues hay ảnh chụp màn hình.

Windows PowerShell:

```powershell
$env:GROQ_API_KEY = "API_KEY_RIENG_CUA_BAN"
python agent.py --mode meeting --task "Tạo bảng việc cần làm từ ghi chú mẫu đã ẩn danh" --input-file notes.txt
Remove-Item Env:GROQ_API_KEY
```

macOS/Linux:

```bash
export GROQ_API_KEY="API_KEY_RIENG_CUA_BAN"
python3 agent.py --mode plan --task "Từ các việc được cung cấp, đề xuất 3 ưu tiên"
unset GROQ_API_KEY
```

**Chỉ chấp nhận 3 chế độ:** `meeting`, `email`, `plan`. Tài liệu bạn tự chọn có giới hạn 10KB UTF-8, nhiệm vụ tối đa 9.000 ký tự; giới hạn 2 gọi API, 1.000 token cho mỗi lần, 25 giây timeout/lần, **không tự lặp retry**. Mô hình mặc định `openai/gpt-oss-20b` trên Groq có thể thay đổi về tính sẵn có; cấu hình `GROQ_MODEL` nếu nhà cung cấp yêu cầu.

## Luồng hai bước

1. **Người dùng giao việc cụ thể**: mục tiêu, dữ liệu phù hợp, hạn chế, dạng kết quả. Nội dung đính kèm là **dữ liệu không tin cậy**, không phải chỉ dẫn hệ thống.
2. **AI viết và tự rà soát**: phát hiện thiếu dữ liệu, chỗ có thể suy diễn hoặc bịa đặt. Kết quả vẫn là *nháp*, không phải được kiểm chứng độc lập.
3. **Người dùng duyệt**: đối chiếu số liệu gốc; tùy ý dán nội dung sang công cụ mình dùng. Agent không bao giờ tự gửi hộ.

## Những gì clone này KHÔNG làm

- Không đọc Gmail, Meta, Threads, Facebook, Instagram, Excel hay file của bạn nếu bạn không cung cấp đầu vào.
- Không tự đăng, bình luận, gửi mail, tải dữ liệu, chạy code từ nội dung người dùng.
- Không dùng token, cơ sở dữ liệu, tài khoản hoặc API key của Enna gốc.
- Không có khả năng tự cập nhật mã nguồn, chạy tác vụ vô hạn hay tạo thu nhập.
- Không thu email, số điện thoại, dữ liệu công ty hay hành vi cá nhân trên trang Lite.

## Bảo mật và trách nhiệm

Nếu dữ liệu công việc không được phép gửi cho dịch vụ AI bên ngoài, **không dùng API với dữ liệu đó**. Dùng mẫu giả/ẩn danh, tuân thủ quy định công ty và xem xét đầu ra trước khi áp dụng. Một bước tự kiểm của mô hình **không thay thế** đối chiếu độc lập, đặc biệt với số liệu quan trọng.

Bạn muốn tự động hóa nâng cao: hãy thêm **mỗi lần một quyền** (ví dụ đọc tài liệu mẫu rồi mới đến công cụ khác), xác thực từng lần chạy, có giới hạn chi phí, ghi nhận trạng thái và yêu cầu chấp thuận trước khi tạo tác động. Không bắt đầu bằng quyền đăng mạng xã hội.

## Cộng đồng

Cùng chia sẻ *tình huống giả lập* và cách làm, không đăng dữ liệu thật: [gửi thử thách AI cho Đồ Hay Đi Làm](https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/new?template=ai-workflow-challenge.yml). Chủ kênh duyệt ý tưởng theo mức độ phù hợp; đây không phải diễn đàn phản hồi thời gian thực.

**Giữ liên hệ:** [@dohay_dilam trên Threads](https://www.threads.com/@dohay_dilam) · [Học AI ba tầng](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/ai/)
