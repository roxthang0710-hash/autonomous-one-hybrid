# Autonomous One v1.6 — Threads Nurture & official Meta API

**Trạng thái thực tế:** đã triển khai hệ thống lập lịch/viết nội dung và thử nghiệm GitHub Actions + Supabase. **Chưa tạo tài khoản Threads thật, chưa được Meta OAuth ủy quyền, chưa đăng bài, chưa có doanh thu.** Các bước xác minh danh tính, chấp thuận điều khoản và cấp phép OAuth chỉ được thực hiện bởi người sở hữu tài khoản.

## Thương hiệu soạn sẵn

- Tên hiển thị: **Đồ Hay Đi Làm**
- Ngách: mẹo công sở, sắp xếp không gian làm việc, đồ dùng phục vụ đi làm và công tác
- Tiểu sử gợi ý: "Mẹo nhỏ cho dân văn phòng và những chuyến công tác gọn nhẹ. Gợi ý hữu ích, không giả vờ từng sử dụng sản phẩm."
- Gợi ý tên người dùng, **chưa đăng ký hoặc kiểm tra có sẵn**: `dohaydilam`, `gocdohaydilam`, `dohaydilam.vn`
- Không sử dụng tên, logo Shopee hoặc tuyên bố là tài khoản chính thức của Shopee.
- Trong giai đoạn đầu chỉ đăng nội dung gốc hữu ích, **không có link tiếp thị**.

## Đã tự động hóa trên Cloud

1. GitHub Actions: [Autonomous One — Threads Nurture](../.github/workflows/threads-nurture.yml), chạy **09:45 sáng hằng ngày theo giờ Việt Nam** (cron có thể trễ).
2. [`threads/planner.py`](planner.py): lập lịch 14 bài hữu ích, đa dạng chủ đề, mỗi ngày một bài (không mua bán, không giả vờ trải nghiệm).
3. [`threads/content.py`](content.py): tự lưu lịch vào Supabase, chặn trùng lặp, giữ hàng đợi tối thiểu 6 bài và sử dụng Groq để tạo bài tiếp theo.
4. [`threads/publisher.py`](publisher.py): sau khi kết nối được tài khoản Threads thật, dùng **Threads API chính thức của Meta** để đăng mỗi lần tối đa 1 bài đã đạt kiểm tra; không tự đăng lại khi kết quả chưa rõ.
5. [`threads/insights.py`](insights.py): đọc số liệu thật từ Threads API nếu tài khoản đã cấp quyền insights. Thiếu chỉ số thì không tự coi là 0.
6. Supabase: `threads_channels`, `threads_posts`, `threads_publish_attempts`, `threads_metrics`. Các bảng có RLS, máy chủ nắm quyền ghi.

## Cấp quyền lần đầu — không thể bỏ qua bước xác thực của nền tảng

### 1. Tạo tài khoản chủ sở hữu

- Tạo tài khoản Threads chính chủ tại [Threads](https://www.threads.com/) hoặc ứng dụng Threads, theo các phương thức đăng nhập nền tảng cho phép. Nếu cần liên kết Instagram, hoàn thành liên kết.
- Xác minh email/số điện thoại, chấp thuận điều khoản, thiết lập hồ sơ thương hiệu và chọn tên người dùng **thật sự khả dụng**.
- Không dùng bot vượt CAPTCHA, không dùng danh tính giả, không gửi mật khẩu hay OTP cho Agent.
- Thông tin tên người dùng hiển thị sẽ được ghi vào `threads_channels` **chỉ sau khi OAuth chứng thực**.

### 2. Cấp quyền Threads API cho hệ thống

Theo [Meta Threads API](https://www.postman.com/meta/threads/collection/dht3nzz/threads-api):
- Tạo ứng dụng trong [Meta for Developers](https://developers.facebook.com/apps/) với **Threads use case**.
- Tài khoản chủ sở hữu chấp thuận OAuth, bao gồm `threads_basic`, `threads_content_publish` và, nếu muốn đọc số liệu, `threads_manage_insights`.
- Lấy Threads User Access Token theo hướng dẫn Meta và kiểm tra quyền/hạn sử dụng. Token có thể hết hạn hoặc bị thu hồi.
- **Chỉ lưu token trong GitHub Actions Secrets**, tuyệt đối không đưa vào issue, file, log hoặc tin nhắn.
- Cấp quyền cho đúng tài khoản sở hữu kênh; worker sẽ tự kiểm tra `GET /me?fields=id,username`.

### 3. Kích hoạt một lần trong GitHub Secrets

Mở [Repository secrets](https://github.com/roxthang0710-hash/autonomous-one-hybrid/settings/secrets/actions) và tạo:

| Tên secret | Mô tả |
|---|---|
| `THREADS_ACCESS_TOKEN` | Token cấp phép chính thức, không nhập vào trò chuyện |
| `THREADS_EXPECTED_USERNAME` | Tên người dùng Threads đã tạo, không có @ |
| `THREADS_PUBLISH_ENABLED` | `true` chỉ khi chủ sở hữu đồng ý bắt đầu đăng tự động |

Ba secret Supabase/Groq cũ vẫn giữ nguyên. **Không có đủ cả token, username và switch thì mọi thao tác xuất bản đều bị bỏ qua.** Nếu token sai kênh, ứng dụng từ chối đăng.

Khi kết nối chính xác lần đầu, server tự kích hoạt `threads_channels` và **dời toàn bộ lịch nuôi kênh sang ngày hôm sau lúc 09:30**. Không tự đăng dồn các bài cũ.

### 4. Xác nhận

- [GitHub Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions): chọn workflow Threads Nurture, bấm **Run workflow → publish**. Nếu chưa tới giờ, không đăng bài.
- Hoặc chờ lịch chạy tự động 09:45 mỗi ngày; Meta có thể áp dụng giới hạn tốc độ hoặc quyền ứng dụng.
- Kiểm tra `threads_posts.status='posted'` + `platform_post_id`; nếu lỗi bất định `status='uncertain'`, hệ thống **không tự đăng lại** để tránh trùng nội dung.
- Ghi nhận tương tác từ Threads API nếu được cấp scope. Không tự chế số liệu.

## Shopee Affiliate — điều kiện chưa hoàn thành

- Shopee hướng dẫn đăng ký tại [affiliate.shopee.vn](https://affiliate.shopee.vn/), chọn Blogger / Social Media, cung cấp kênh có thật.
- Theo [điều khoản Shopee](https://help.shopee.vn/portal/10/article/122944), Shopee quyết định cuối cùng việc duyệt KOC; **không có bằng chứng rằng Threads được chấp thuận như kênh đăng ký riêng**.
- Nếu Shopee chỉ chấp nhận Facebook Fanpage hoặc Instagram trong hồ sơ, xây một hồ sơ Instagram thật và liên kết cùng hệ sinh thái Threads, nhưng chưa khẳng định được duyệt.
- Sau khi kênh đã hoạt động có nội dung thật, kiểm tra quy định Shopee hiện hành rồi mới nộp.
- Không tự tạo link giả, không gắn link tiếp thị lên kênh chưa được Shopee duyệt, không dự báo ngày được duyệt hay doanh thu.

## Trường hợp cần ngừng tự động hóa

- Bị nền tảng yêu cầu xác minh, OAuth hết hạn, thay đổi quyền Meta, người dùng tắt switch: **ngừng đăng**.
- POST đến Threads API trả lỗi hoặc timeout: trạng thái `uncertain`; **không thử lại cho đến khi đối soát**.
- Nội dung có link thương mại, giá chưa kiểm chứng, giả trải nghiệm hoặc kêu gọi mua gấp: **từ chối đưa vào hàng đăng tự động**.
- Nội dung chỉ mang tính hữu ích; không tự trả lời người lạ, gắn thẻ hàng loạt hoặc spam.

## Lưu ý

Cấu hình trong Supabase là *hồ sơ thương hiệu nội bộ*, không phải tài khoản Threads đã được đăng ký ngoài đời. Mọi lời nói rằng đã tự đăng ký hoặc đã công khai bài đều cần bằng chứng từ Meta API.
