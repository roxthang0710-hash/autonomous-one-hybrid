# Enna Companion v0.2 — Chủ kênh chọn bài, Enna tự thẩm định và thử phản hồi

**Mốc chuẩn bị:** 03/11/2026, giờ Việt Nam.

## Quy trình triển khai

**Yêu cầu gốc của người dùng:** Khi đang lướt Threads, chọn một bài viết mình đánh giá là thú vị / đang thu hút. Tiện ích Chrome chuyển bài đó tới Enna, Enna tự xác nhận chủ đề, soạn phản hồi phù hợp và tự đăng nếu được Meta cho phép — không cần quyền `threads_keyword_search` để chủ động tìm kiếm.

**Đường truyền bản 0.2 đang dùng:** Chrome MV3 extension → biểu mẫu GitHub Issue được điền sẵn → chủ repo `roxthang0710-hash` bấm Submit new issue → GitHub Actions `enna-selected-reply.yml` → `growth/companion_selected_reply.py` → Groq soạn phản hồi → Meta Graph GET /{id} xác minh **ID, tác giả, nội dung, permalink, thời điểm** → Supabase RPC atomic claim → Meta Threads official reply API (chỉ khi đủ quyền).

Nhờ GitHub Issues, **không cần mật khẩu Supabase Auth** đã gặp khó khăn ở các cuộc trò chuyện trước; token Meta vẫn chỉ nằm trong Supabase Vault. Extension chỉ biết phần văn bản tác giả đã công khai và URL do người dùng chủ động chọn. Repository GitHub **công khai**, nên nội dung issue ở dạng Base64url **không phải mã hóa bí mật**. Không gửi dữ liệu mật.

### Tệp trong GitHub và Supabase

- `growth/companion_selected_reply.py`: biên tập 1 bài chủ repo chọn và 1 bình luận qua API Meta khi chính thức được cấp quyền. Nếu API không cho xác minh thì ghi `draft_only_meta_cannot_verify_target`, không đăng, bình luận gợi ý lại ngay trên GitHub Issue. Nếu Meta POST không phản hồi chắc chắn, ghi `uncertain`, tuyệt đối không tự lặp lại.
- `.github/workflows/enna-selected-reply.yml`: chạy khi issue với tiêu đề `enna-pick:<shortcode>` được **chính chủ sở hữu repo** mở. Kiểm tra riêng `tests/test_companion_selected_reply.py` trước hành động. Cập nhật kết quả qua GitHub Issue comment. Không nhận issue từ người lạ.
- `sql/v2_20_enna_companion_selected_replies.sql`: migration Supabase đã được áp dụng, tạo `enna_companion_attempts`, claim RPC chỉ service-role, khóa giao dịch ngăn vượt giới hạn tổng **3 bình luận/ngày**, tính chung với hai worker tương tác còn lại, kiểm tra trùng ID/bài và cooldown 7 ngày theo tác giả.
- `enna-public-status` Edge Function v16 và `docs/enna/index.html`: trả và hiển thị tổng lần thử/đăng thành công từ các bài chủ kênh tự chọn. **Không coi bản nháp như bình luận đã đăng.**
- Extension ZIP `enna_companion_chrome_v0.2.zip` được tạo tại đường dẫn sandbox của cuộc trò chuyện có tác vụ này; **chưa commit mã nguồn Chrome vào GitHub**, nên ở cuộc trò chuyện mới phải dùng bản ZIP đã tải/saved hoặc yêu cầu upload lại nếu cần chỉnh sửa. Thư mục trong ZIP `enna_companion_extension_v02/` gồm manifest.json, background.js, panel.html/js/css, README.md. Cú pháp JS/ZIP và kiểm thử giả lập GitHub URL+Base64url tiếng Việt trên máy đã PASS.

### Vì sao phải xác minh post ID qua API Meta?

Liên kết người dùng chọn có dạng `https://www.threads.com/@tacgia/post/<shortcode>`. Shortcode giải mã thành ID số bằng bảng chữ cái Base64 đặc thù. Tuy nhiên đây chỉ là **mã ứng viên**, không bảo đảm bằng ID API: trước khi bình luận thật phải GET chính thức Meta và so khớp ID, tác giả, text, URL, timestamp. Một ví dụ công khai: `DdcPsEkH3NZ` → `3989132369199067993`, chưa dùng để đăng test. Khi Meta App Review hạn chế đọc bài của tài khoản khác thì **phải dừng tự động**, ngay cả khi đã có URL/chữ chọn. Không tự click vào website hoặc dùng API nội bộ để vượt giới hạn.

### Cài đặt cho người dùng

1. Tải ZIP từ file artifact của cuộc trò chuyện, giải nén.
2. Chrome → `chrome://extensions` → Developer Mode → Load unpacked → thư mục có manifest.
3. Trên Threads, chọn một đoạn bài **công khai** 50–1800 ký tự, nhấp phải → “Chọn bài này cho Enna phân tích và phản hồi”.
4. Copy **link của chính bài** từ Threads, điền vào thanh Enna (nếu URL chưa tự nhận).
5. Bấm “Gửi bài đã chọn cho Enna (GitHub)” → đăng nhập GitHub → kiểm tra URL/body → bấm **Submit new issue**.
6. Theo dõi Issue comment, và lịch sử `https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/workflows/enna-selected-reply.yml`. Một bài chỉ 1 cơ hội; nếu Meta không xác nhận khả năng đọc sẽ trả lại bản nháp.

### Giới hạn và cách xác nhận

**Đã được xác minh:** mã nguồn GitHub đã được lưu, Supabase migration đã áp dụng, bản ghi attempts=0 lúc chuẩn bị; claim private, không cấp quyền anon/auth, cả 3 worker dùng chung số lượt/ngày; Edge trạng thái ACTIVE v16. ZIP được tạo và kiểm tra cấu trúc, JavaScript bằng `node --check`, giả lập luồng GitHub issue đã PASS.

**Chưa xác minh:** GH Actions workflow này đã chạy toàn bộ tests thành công, GitHub Issues form có chuyển chính xác trên tài khoản người dùng, Meta GET bài của tài khoản ngoài có được phép hay không, Auto Reply thực tế từ `@dohay_dilam`. Chỉ báo thành công khi `enna_companion_attempts.status=posted` có `meta_reply_id` và thấy phản hồi dưới bài. **Không tuyên bố đã đăng bình luận khi chưa có chứng cứ.**

### Tương lai

- Có thể xây quyền đăng nhập tiện ích riêng cho owner bằng Supabase Auth sau khi giải quyết được tài khoản; sẽ bỏ bước GitHub Issue và cho phép **một thao tác gửi bài** sau khi chủ kênh chọn, nhưng không thay đổi giới hạn Meta.
- Viral/trending là đánh giá thủ công của người chọn. Không giả định số lượt xem hoặc like khi không có dữ liệu chính thức.
- Bản Chrome hiện dùng menu chọn văn bản (không tự đọc DOM, cookie, tab history). Không thu thập hàng loạt từ feed.
