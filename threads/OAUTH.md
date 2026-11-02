> **Khắc phục lỗi localhost:3000 / otp_expired (02/11/2026):** Ngoài Redirect URLs, bắt buộc đổi **Authentication → URL Configuration → Site URL** từ `http://localhost:3000` thành `https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/`, bấm **Save changes**. Nhật ký Supabase cho thấy liên kết đầu tiên đã đăng nhập thành công nhưng đưa về localhost, các lần mở lại gây lỗi mã một lần không tồn tại. Sau khi sửa Site URL, hãy yêu cầu email mới và bấm **một lần** vào liên kết mới nhất. Không gửi các URL chứa token cho người khác.

> **Cập nhật 02/11/2026 — không còn yêu cầu mật khẩu quản trị:** Supabase Auth dự án này bật đăng nhập email nhưng **chưa bật Google provider**. Trang GitHub Pages đã thay form nhập mật khẩu bằng **liên kết đăng nhập một lần gửi đến email** đã có trong `Authentication → Users`; backend kiểm tra danh sách `agent_reviewers` trước khi cho cấp Meta OAuth. Không tự tạo thêm người dùng. Mã JWT từ email link nằm trong bộ nhớ trình duyệt và được xóa khỏi URL ngay khi xác thực. Sau khi mở email link và được xác minh, form nhập Threads App ID/Secret mới xuất hiện.
>
> **Cấu hình URL bắt buộc một lần:** tại [Supabase Authentication → URL Configuration](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/auth/url-configuration), thêm `https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/` vào **Redirect URLs → Add URL**, và nhấn Save. Đây là URL đăng nhập email, **khác** Callback URL trong Meta Developers; không thay đổi Meta callback cũ.
>
> [Mở giao diện đăng nhập không mật khẩu](https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/).

> **Cập nhật khắc phục giao diện 02/11/2026:** Supabase Edge Functions trên tên miền mặc định không phục vụ HTML mà đổi thành văn bản thuần. Chúng tôi đã chuyển **giao diện bảo mật** sang **GitHub Pages** và giữ **Supabase Edge** xử lý API/callback. 
> 
> **Trang mới (chỉ dùng sau khi GitHub Pages được kích hoạt):** https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/
>
> **Thao tác quản trị một lần:** Mở https://github.com/roxthang0710-hash/autonomous-one-hybrid/settings/pages → Build and deployment → **Source: GitHub Actions**. Workflow \`.github/workflows/threads-pages.yml\` sẽ triển khai giao diện. Sau đó mở trang mới, không đăng nhập vào địa chỉ Supabase Edge cũ.
>
> **Callback URL Meta vẫn GIỮ NGUYÊN:** \`https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth/callback\`. Phản hồi callback được chuyển về GitHub Pages mà không để lộ mã ủy quyền. Kiểm thử API đã đạt 303 redirect, 204 preflight CORS đúng nguồn, 403 nguồn lạ, 401 khi chưa đăng nhập.
>
> **Kiểm thử:** https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41402063495 (API đã đạt); GitHub Pages cần chủ sở hữu bật tính năng vì workflow tạo site tự động bị GitHub từ chối \`Resource not accessible by integration\`.

# Kết nối Threads API cho Autonomous One — một lần cấp quyền

**Trạng thái tính đến 02/11/2026:** Trang OAuth đã triển khai tại
https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth .
GitHub Actions đã chạy thử các đường dẫn công khai và xác nhận: trang chính **200**, mã JavaScript **200**, yêu cầu `/start` chưa đăng nhập bị chặn **401**, callback giả bị chặn **400**. Chưa kết nối Meta thật, vì tài khoản sở hữu cần cấp quyền qua ứng dụng Meta Developers.

## Bước chủ sở hữu thực hiện một lần

1. Mở [Meta for Developers — Apps](https://developers.facebook.com/apps/). Tạo ứng dụng, chọn **Access the Threads API** hoặc **Threads API use case**.
2. Tại Threads use case → Settings, tìm **Threads App ID** và **Threads App Secret** (khác Meta App ID của những sản phẩm khác).
3. Thêm **Redirect callback URL** chính xác, không tự thêm dấu / cuối chuỗi:
   `https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth/callback`
4. Trong App Roles/Threads Tester, thêm tài khoản thật **@dohay_dilam**, sau đó chấp nhận lời mời trong Threads (Settings → Account → Website permissions → Invites). Khi app ở chế độ phát triển chỉ tài khoản có quyền tester/developer được phép thử nghiệm.
5. Mở **[trang cấp quyền Autonomous One](https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth)**. Đăng nhập **tài khoản quản trị Supabase Auth đã có quyền `agent_reviewers`** (không phải tài khoản Meta) và nhập App ID/Secret vào trang HTTPS đó, không gửi các giá trị này vào ChatGPT hay GitHub Issues.
6. Nếu đã bật quyền Threads nâng cao và muốn Agent phát hiện/tham gia thảo luận công khai, chọn ô đồng ý phản hồi **tối đa một cuộc trò chuyện phù hợp/ngày**. Nếu chưa được Meta cấp quyền `threads_keyword_search`, hãy **để ô này không chọn** để kết nối quyền đăng bài cơ bản trước.
7. Nhấn **Đăng nhập và chuyển sang cấp quyền Meta**. Bạn sẽ được chuyển đến chính cửa sổ cấp quyền Threads của Meta. Đăng nhập bằng **@dohay_dilam** và xác nhận.
8. Sau khi Meta trả về mã hợp lệ, máy chủ tự đổi mã lấy token, đổi sang token dài hạn, xác thực `/me` đúng tài khoản và lưu token vào **Supabase Vault**. Không có bước sao chép token thủ công. Bạn nhận được trang xác nhận thành công.

### Quyền được yêu cầu

Quyền tối thiểu:
- `threads_basic`: đọc định danh tài khoản để xác thực đúng chủ sở hữu.
- `threads_content_publish`: tạo và đăng nội dung thương hiệu.
- `threads_manage_insights`: đọc số liệu bài viết.

Khi chủ sở hữu chọn ô tương tác:
- `threads_read_replies`, `threads_manage_replies`, `threads_keyword_search` thêm khả năng tìm và trả lời thảo luận liên quan. Những quyền này có thể cần chọn thêm trong dashboard Meta và/hoặc xét duyệt.

**Quan trọng:** Các quyền chỉ được sử dụng nếu Meta thực sự cấp cho ứng dụng. Kết nối Metricool không tạo ra Meta Developer token, và không được coi là quyền của Autonomous One.

## Tự động hóa sau OAuth

- Bài Metricool **03–17/11/2026 lúc 09:30** vẫn thuộc Metricool.
- Supabase sắp lại lịch nội dung **bắt đầu từ ngày sau bài cuối Metricool** và tránh ngày đã có bài ở sổ lịch Metricool.
- Github Actions `threads-nurture.yml` chạy **09:45 giờ Việt Nam mỗi ngày**: AI Groq duy trì bản nháp, xuất bản tối đa 1 bài đủ điều kiện và đọc số liệu thật.
- GitHub lấy token đã mã hóa qua RPC chỉ dành cho `service_role`, không đưa token vào log. Nếu còn dưới 14 ngày sử dụng sẽ thử gia hạn qua Meta API, kiểm tra lại username và ID.
- Growth Radar vẫn chạy 2 lần/ngày. Quyền tìm bài và bình luận dùng một tài khoản thương hiệu thật, tối đa 1 phản hồi/ngày khi chủ sở hữu chủ động cho phép.
- Token hết hạn, bị thu hồi, tài khoản không trùng hoặc Meta lỗi không rõ ràng: dừng hành động; không tự đăng lại một yêu cầu chưa xác định.

## Nếu bạn muốn tự lấy token thủ công (phương án dự phòng)

Theo [bộ API chính thức của Meta](https://www.postman.com/meta/threads/collection/dht3nzz/threads-api):
1. Cửa sổ OAuth `https://threads.net/oauth/authorize` dùng Threads App ID, URI đã khai báo, quyền, `response_type=code` và state chống giả mạo.
2. Meta chuyển về callback URI với `code`; mã này dùng một lần và có thời hạn ngắn.
3. Máy chủ dùng `POST https://graph.threads.net/oauth/access_token` để đổi code lấy token ngắn hạn; bắt buộc Threads App Secret và redirect URI khớp hoàn toàn.
4. Dùng `GET https://graph.threads.net/access_token?grant_type=th_exchange_token` để lấy token dài hạn (Meta trả `expires_in`).
5. Dùng `GET https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token` trước khi hết hạn và sau khi token đủ tuổi để được làm mới.

**Không dán token hoặc App Secret vào GitHub public, chat hoặc ghi chú dùng chung.** Với dự án này dùng trang OAuth chủ sở hữu ở trên tiện hơn và an toàn hơn.

## Kiểm thử và giới hạn

- [Lượt chạy smoke test trên GitHub](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41348403916): thành công sau khi sửa đường dẫn Edge Gateway.
- Chưa thể kiểm thử **luồng cấp phép thật hoặc xuất bản thật** vì chưa có Meta App ID và quyền cấp phép từ chủ tài khoản. Mọi lời nói rằng đã có token live trước khi chủ sở hữu chấp thuận đều sai.
- Để kiểm tra cấu hình OAuth, đừng thử tạo danh tính Meta giả hoặc bypass CAPTCHA.
