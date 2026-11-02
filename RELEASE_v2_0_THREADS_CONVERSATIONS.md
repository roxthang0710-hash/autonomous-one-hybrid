# Autonomous One v2.0 — Threads Conversations (Đồ Hay Đi Làm)

**Đã triển khai:** 02/11/2026 (Asia/Ho_Chi_Minh)  
**Tài khoản:** `@dohay_dilam` · **Chủ sở hữu đã đồng ý trong chat:** có  
**Meta API chưa cấp mở rộng:** `enable_replies=false` tại thời điểm triển khai. Chưa có bình luận nào được Agent gửi lên Threads.

## Mục tiêu hoạt động

Autonomous One dùng **chính danh tính thương hiệu thật** để tìm hội thoại công khai về công sở, học tập, phụ kiện, công nghệ đời sống và đồ dùng đi làm qua Threads API. Nội dung mang giọng **trẻ trung, hài hước, bắt trend vừa phải**, dùng tiếng lóng phổ biến khi tự nhiên (ví dụ "toang", "rén", "vibe", "hết cứu"), không sao chép văn mẫu.

Đây là tương tác hữu ích, **không phải tạo seeding giả**, không mua theo dõi, không lập tài khoản ảo, không phát biểu giả trải nghiệm khách hàng, không kéo bè cãi nhau, không tự động gắn link affiliate vào câu trả lời.

## Mã đã triển khai

- `growth/voice.py`: phong cách thương hiệu, chống trùng lặp, chặn bình luận chung chung/CTA theo dõi, yêu cầu liên quan ít nhất hai thông tin từ bài gốc.
- `growth/generator.py`: Groq tạo phản hồi ngữ cảnh ngắn, đôi khi chêm một cách nói dí dỏm; bỏ quy tắc ép cuối câu phải hỏi để tránh câu kéo tương tác.
- `growth/conversations.py`: Threads **keyword_search** chính thức, xoay vòng truy vấn ngành, nhận kết quả **RECENT/TOP**; chỉ chọn bài công khai mới trong 24 giờ, không chọn bài của thương hiệu và lọc tin nhạy cảm.
- `growth/runner.py`: ưu tiên một cuộc thảo luận Threads thật trong shortlist dù Google News RSS nhiều hơn; tối đa 21 ý tưởng trong 7 ngày, 5 bản nháp không phải hội thoại; từng workflow chỉ tạo tối đa một đề xuất mới.
- `growth/engage.py`: xác thực danh tính API trước khi hành động, đọc lại bài đích, kiểm tra chưa bị sửa chủ đề, kiểm duyệt và so độ giống với phản hồi trước, thực hiện yêu cầu SQL an toàn trước khi viết qua Meta. Không thử lại tự động nếu kết quả đăng không chắc chắn.
- `sql/v2_0_safe_reply_claim.sql`: RPC chỉ mở cho service_role, khóa giao dịch tránh tranh chấp, **tối đa 3 lượt gửi/ngày theo giờ Việt Nam**, không trả lời trùng bài và không tiếp cận cùng tác giả quá một lần trong 7 ngày. Chỉ chấp nhận đề xuất có bằng chứng từ Meta Threads, đạt ngưỡng liên quan và còn hiệu lực; bắt buộc Vault có `enable_replies=true` với token đúng thương hiệu.
- `.github/workflows/growth-radar.yml`: lên lịch 09:15 / 14:15 / 19:15 giờ VN; một cơ hội/phiên. **3/ngày là giới hạn trên, không phải chỉ tiêu ép đăng**.
- `growth/report.py`: báo cáo riêng trạng thái cấp quyền, số lần đã cố gắng/đã đăng trong ngày và hạn mức còn lại (số không khi chưa được cấp quyền).
- `docs/oauth/index.html`: ô đồng ý rõ ràng về quyền tìm kiếm/bình luận Meta và giới hạn 3/ngày.

## Đã kiểm thử

- GitHub Actions test Python bao gồm chặn bài không liên quan, bình luận spam, yêu cầu theo dõi, trùng bình luận, chủ đề nhạy cảm, nguồn cũ, tin người dùng đã sửa, gửi API mơ hồ, SQL từ chối, danh tính không khớp.
- SQL trên Supabase thật: đã kiểm thử với 5 đề xuất giả trong một giao dịch có **hoàn tác**, chứng minh cho phép tối đa 3 tác giả khác nhau, chặn tác giả lặp và chặn quá hạn mức. Toàn bộ cờ OAuth và bản ghi giả đã hoàn tác. Vai trò `anon` / `authenticated` không được thực thi RPC; chỉ `service_role` được.
- Không có dữ liệu người dùng thật, App Secret hay token được in ra log công khai; không gọi Meta để bình luận thật trước khi đủ quyền.

## Một hành động còn lại của chủ sở hữu: Meta OAuth / App Review

1. Mở **[Trang kết nối Threads Autonomous One](https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/)** và chọn **Tiếp tục với GitHub**. Trong biểu mẫu Meta, nhập **Threads App ID** và **Threads App Secret** vào trang HTTPS (không gửi qua ChatGPT).
2. Tích ô **“Tôi cho phép Autonomous One tự tìm và bình luận…”** (khác lần cấp OAuth trước đã để trống). Bấm **Cấp quyền tại Meta** và chấp nhận bằng tài khoản `@dohay_dilam`. Luồng sẽ yêu cầu `threads_keyword_search`, `threads_manage_replies`, `threads_read_replies` cùng các quyền cơ bản.
3. **Nếu Threads keyword_search không trả về bài công khai của người khác hoặc Meta từ chối quyền nâng cao:** mở [Meta for Developers](https://developers.facebook.com/apps/) → ứng dụng `dohaydilam` → Threads API / App Review, yêu cầu quyền cần thiết và thực hiện các hướng dẫn Meta, bao gồm video chứng minh luồng đăng nhập, tìm bài, phản hồi và kết quả trên Threads nếu Meta yêu cầu. App Review tùy trạng thái ứng dụng; chỉ người sở hữu Meta mới gửi hồ sơ phê duyệt. Việc được chấp nhận làm Tester không đồng nghĩa tất cả quyền tìm bài công khai đã được phê duyệt.

**Không cần** dùng token tự tạo, nhập vào GitHub Secrets, hay đăng nhập vào tài khoản phụ. Nếu Meta không cấp đủ quyền, chức năng tương tác sẽ **không đăng tự động**, nhưng phần đăng bài Threads hiện có tiếp tục hoạt động.

## Trạng thái thực tại thời điểm phát hành

- Threads đã kết nối, có token dài hạn trong Vault, `enable_replies=false`.
- 15 bài Metricool từ 03–17/11 đã đặt lịch riêng; các bản nháp Agent không được xếp trùng.
- **0 bình luận Threads** từ Agent (không có quyền).
- **0 doanh thu affiliate được xác nhận**, không có Shopee tracking link.
- Không cam kết lượt theo dõi, tương tác hay hiệu quả "viral"; Agent chỉ tối ưu khi có dữ liệu thật.

## Kiểm tra vận hành

- [GitHub Actions — Growth Radar](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/workflows/growth-radar.yml)
- [Supabase — Database](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor) xem `growth_signals`, `growth_opportunities`, `growth_engagement_attempts`, `threads_vault_credentials.enable_replies` (không mở giá trị token).
- [Meta Threads API — Postman chính thức](https://www.postman.com/meta/threads/collection/dht3nzz/threads-api).
