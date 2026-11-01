# Autonomous One — Threads v1.8

**Thương hiệu:** Đồ Hay Đi Làm · @dohay_dilam

## Tình trạng xác minh 02/11/2026

- Metricool đã kết nối Threads/Instagram/Facebook và xếp 15 bài Threads vào lịch ngày **03–17/11/2026, 09:30 giờ Việt Nam**.
- Dịch vụ Meta OAuth đã được triển khai và kiểm thử quyền truy cập công khai: https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth
- **Chưa có Meta OAuth token thật trong Supabase Vault** vì người sở hữu chưa chấp thuận quyền trong Meta Developer App.
- Growth Radar đã tự quét xu hướng từ RSS; các hoạt động trao đổi trực tiếp trên Threads chờ đúng quyền Meta.
- Chưa có bài được Meta API xác nhận trong ngày 02/11; trạng thái Metricool PENDING không đồng nghĩa đã đăng.

## Thiết lập một lần

Đọc [Hướng dẫn cấp quyền chi tiết](OAUTH.md). Trên trang kết nối chính thức, đăng nhập bằng tài khoản Supabase Auth đã được cấp quyền điều hành, sau đó nhập Threads App ID và App Secret từ ứng dụng Meta của bạn. Chỉ cung cấp quyền và xác minh trên giao diện HTTPS, **không nhập bất kỳ token/secret nào vào chat, issue hay source code**.

### Công tắc tự động hóa

- Việc xác nhận cấp quyền Meta cho phép AI tiếp tục tự xuất bản nội dung sau lịch Metricool; không cần bật thêm GitHub Secrets.
- Ô chọn phản hồi trên trang OAuth **mặc định tắt**. Chỉ khi chủ sở hữu tự bật ô này và được Meta chấp thuận quyền tìm kiếm/phản hồi thì Growth Agent mới được tham gia tối đa **1 cuộc thảo luận phù hợp/ngày** bằng tài khoản thương hiệu thật.
- Nếu tài khoản Meta chưa có quyền mở rộng thì cứ cấp quyền cơ bản trước; có thể cấp lại quyền để bổ sung sau.

## Hành vi tự động sau khi được cấp Meta OAuth

GitHub Actions workflow Threads Nurture chạy lúc **09:45 sáng hằng ngày theo giờ Việt Nam** (GitHub Actions cron theo cơ chế best effort).

1. Groq tạo bản nháp ngắn tiếng Việt, không link tiếp thị và không bịa trải nghiệm.
2. Bảo lưu nguyên vẹn 15 ngày đã đặt trong Metricool, với cơ chế loại trừ ngày trùng ở cấp cơ sở dữ liệu.
3. Các bài do AI tạo được đặt lịch sau ngày cuối cùng đã lên lịch Metricool. Nguồn xu hướng chỉ được chọn khi còn mới và thuộc đúng lĩnh vực.
4. Một bài cho ngày hôm sau có thể được làm mới dựa trên Growth Radar (tối đa **2 bài theo xu hướng mỗi tuần**).
5. Nếu đến giờ, Meta OAuth đang hoạt động và mọi điều kiện đạt, hệ thống gửi tối đa **1 bài đăng gốc trong mỗi lượt chạy**, nhận mã bài từ Meta trước khi đánh dấu đã đăng.
6. Nếu là bài Metricool, chỉ Meta API listing thực sự xác nhận bài có ID/timestamp mới được đổi trạng thái thành đã xuất bản; không tự bịa số liệu.
7. Đọc insights thật từ Meta, không suy diễn missing views thành 0.
8. Gia hạn Meta token dài hạn khi gần hết hạn, lưu token trong Supabase Vault; không log secret hay tự giả đăng nhập.

## Thành phần

- threads/content.py: tạo hàng đợi nội dung, lên ngày không trùng Metricool.
- threads/trends.py và threads/refresh.py: chuyển nguồn nghiên cứu phù hợp thành bài viết kịp thời.
- threads/daily.py: điều phối tạo bài, làm mới xu hướng, xuất bản, đối soát, đọc số liệu.
- threads/publisher.py: 2 bước xuất bản Meta API có xác thực đúng tài khoản.
- threads/reconcile.py: đối soát bài Metricool dựa trên bằng chứng thực tế từ Meta.
- threads/credentials.py: sử dụng Meta OAuth token dài hạn đã lưu mã hóa tại Vault, tự gia hạn; vẫn có đường legacy thông qua GitHub Secrets nhưng không bắt buộc.
- growth/runner.py và growth/engage.py: Radar và phản hồi hữu ích khi chủ sở hữu chấp thuận.
- supabase/functions/threads-oauth: trang cấp quyền và callback chính thức.
- sql/v1_8_1_threads_oauth_vault.sql: schema và RPC xác thực Vault backend-only.

## Điều không được thực hiện

- Tạo tài khoản ảo, tự làm tăng tương tác, seeding giả khách hàng, bình luận hàng loạt hoặc cố tình kích động tranh cãi.
- Cào giao diện Instagram/Threads nhằm né quyền API.
- Tự động phát sinh link Shopee không được nhà cung cấp cấp phép.
- Tự động coi kết quả mô phỏng, status PENDING hoặc bản nháp là lượt xem, đơn hàng và doanh thu thật.

## Nơi kiểm tra

- [Trang cấp quyền Threads](https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth)
- [Lịch 15 bài trên Metricool](https://app.metricool.com/planner/calendar?blogId=7803567)
- [Các lượt chạy GitHub Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions)
