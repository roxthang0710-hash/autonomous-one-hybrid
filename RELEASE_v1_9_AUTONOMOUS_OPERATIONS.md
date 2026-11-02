# Autonomous One v1.9 — Vận hành Threads và chuẩn bị Shopee Affiliate

**Xác minh:** 02/11/2026 · giờ Việt Nam  
**Thương hiệu:** Đồ Hay Đi Làm · Threads `@dohay_dilam`  
**GitHub:** `roxthang0710-hash/autonomous-one-hybrid` · **Supabase:** `gjdvdohylvsauphhkutw`

## Đã xác minh trực tiếp

- Owner OAuth kết nối đúng tài khoản Threads, `authorized=true`, `auto_publish_enabled=true`, 1 token Meta dài hạn còn hiệu lực trong Supabase Vault. Không in token hoặc App Secret.
- Đã so khớp trực tiếp Metricool Brand 7803567: **15 bài Threads ở trạng thái PENDING, autoPublish=true, ngày 03–17/11/2026 lúc 09:30 Asia/Saigon**. `PENDING` chưa phải bài đã đăng.
- Sau khi sửa lịch, Agent tự lập **2 bài mới**, hiện `queued` và bắt đầu **18/11/2026 09:30 giờ VN**. Github Actions được lên lịch **09:45 hằng ngày (best effort)**, nên giờ thực tế có thể trễ hơn giờ `scheduled_at`. Không đăng trùng Metricool.
- [Threads Nurture run 41422313540](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41422313540): **SUCCESS** gồm kiểm thử, sinh bản nháp, kiểm tra token, an toàn lịch và báo cáo readiness. Kết quả `publisher=no_due_post`, `posted=0`, `queued=2`, `scheduled_external=15`; `warnings=[]`.
- [Growth Radar run 41421857399](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41421857399): **SUCCESS**, 75 tín hiệu từ RSS công khai, shortlist 14, lưu 1 bản nháp mới, tổng 3 bản nháp nghiên cứu. Không truy cập xu hướng thực từ Threads do chưa cấp quyền tìm kiếm; `threads_discovery=not_authorized`, `growth engagement=not_authorized`.
- [Tests 41422196276](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41422196276): **SUCCESS**. Kiểm thử bộ lọc, xử lý bản nháp AI không an toàn, không đăng trùng ngày Metricool, báo cáo readiness, giới hạn đăng và bảo mật.

## Nâng cấp triển khai

1. `growth/runner.py`: một bản nháp Groq bị bộ lọc loại bỏ không còn làm cả workflow thất bại. Agent thử tối đa 3 nguồn đã qua kiểm duyệt, không lưu/đăng nội dung lỗi. Lỗi API/auth/database thật vẫn phát hiện, không che giấu.
2. `threads/content.py`: khởi tạo lịch 14 bài không bao giờ bắt đầu trước khi hết lịch đã đặt tại Metricool. Các bài trùng nội dung đã đặt lịch sẽ được bỏ qua (idempotent); Agent tự viết bản nháp độc lập khi backlog ít.
3. `threads/readiness.py`: kiểm tra trạng thái OAuth, số bài đã/đợi đăng, nguy cơ trùng lịch, token gần hạn, số liệu thật; phân biệt **đã đặt lịch ≠ đã xuất bản ≠ có doanh thu**.
4. `.github/workflows/threads-nurture.yml`: chạy báo cáo readiness trong mỗi chu kỳ mà không công khai token.

## Quy tắc vận hành

- **Meta OAuth:** token được lưu mã hóa. Chỉ token tài khoản đúng `@dohay_dilam` mới được sử dụng, việc đăng có bộ lọc bài viết và tránh đăng lại khi kết quả Meta không chắc chắn.
- **Xu hướng:** Google News/Trends công khai là gợi ý chủ đề, không được giả vờ đã trải nghiệm sản phẩm, lấy tin chưa xác minh làm sự thật hoặc tạo tương tác ảo.
- **Phản hồi Threads:** mặc định **chưa được cấp quyền** mở rộng, không tự bình luận/seeding. Nếu chủ tài khoản chủ động cấp quyền sau, cơ chế vẫn giới hạn tối đa 1 phản hồi chính đáng/ngày.
- **Shopee Affiliate:** tài khoản kênh chưa được xác nhận đủ điều kiện/duyệt; chưa có liên kết tiếp thị và chưa ghi nhận doanh thu. Không tự chế ngưỡng theo dõi, thời gian hoạt động hoặc hoa hồng. Khi kênh được chấp thuận và hệ thống được cấp quyền hợp lệ, mới triển khai xuất bản thương mại có ghi rõ quan hệ tiếp thị.
- **Theo dõi kết quả:** chỉ lưu dữ liệu Meta thật hoặc Metricool được xác minh; không coi bài PENDING là đã xuất bản và không coi lượt tương tác là đơn hàng.
- **Chi phí:** không tạo chiến dịch quảng cáo trả phí, mua follow, dùng danh tính giả hoặc thực hiện thanh toán.

## Lượt kiểm tra tiếp theo

Threads Nurture: lịch GitHub 09:45 giờ Việt Nam hằng ngày. Growth Radar: 09:15 và 17:15 giờ Việt Nam hằng ngày. Affiliate Research: thứ Ba và thứ Sáu lúc 09:30 giờ Việt Nam. Lịch GitHub Actions là best-effort, có thể trễ.

**Lưu ý:** Các dòng ghi “scheduled” hay “queued” mô tả lịch đã cấu hình, không phải cam kết đã chạy tương lai. Mọi lần triển khai tiếp theo cần dựa trên log và trạng thái Meta/Supabase thật.
