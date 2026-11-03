# Enna v2.19 — Tự chủ cộng đồng và phòng thử nghiệm tư liệu (03/11/2026)

## Mục tiêu và những gì đang chặn
Chủ kênh đã cấp quyền OAuth cho Threads @dohay_dilam, cờ `threads_vault_credentials.enable_replies=true`. Tuy nhiên hai lượt Growth Radar gần nhất lưu `own_posts_only_possible_app_review`: Meta Keyword Search đang có dấu hiệu chưa có cấp truy cập nâng cao tới bài công khai của người khác. Quyền tài khoản người dùng **khác** quyền phê duyệt ứng dụng từ Meta. Không cào HTML, không tạo tài khoản giả và không vượt App Review. Chủ sở hữu cần kiểm tra ứng dụng Threads tại https://developers.facebook.com/apps/ và App Review/Permissions cho `threads_keyword_search`, `threads_read_replies`, `threads_manage_replies`. Không tự ghi nhận đã duyệt nếu chưa có chứng cứ từ Meta.

Kiểm toán trước thay đổi: 0 bình luận tự động, 0 cơ hội bình luận trong hàng đợi; 6 bài có Meta ID xác nhận, 8 bài AI queued. Sau thay đổi SQL vẫn là 0 bình luận, 0 tư liệu/ảnh đã lưu: CHƯA chứng minh workflow mới đã thực thi.

## Ba dây chuyền độc lập
1. **Growth Radar** (`.github/workflows/growth-radar.yml`): 09:15,14:15,19:15 VN (best effort). Tìm thảo luận công khai thông qua API Meta được cấp phép, lọc chủ đề công sở/Excel/mẹo phần mềm, soạn phản hồi có ích. Khi Meta Search không trả được bài công khai, dừng tự động, không giả vờ đã tương tác. Giới hạn theo tác giả và tối đa 3 bình luận/ngày.
2. **Community Care** (job `community` trong `.github/workflows/enna-community-media.yml`): 09:40,14:40,19:40 VN; gọi `growth/community_care.py`. Đọc câu hỏi mới dưới bài chính chủ qua API Meta, chọn câu hỏi an toàn và thật, tạo câu trả lời đúng ngữ cảnh bằng Groq, lọc spam/sự thật, đọc lại bình luận trước khi gửi. Atomic RPC `enna_claim_own_reply` xác nhận token OAuth, chính bài thuộc kênh, chỉ 1 phản hồi/ngày riêng nhánh này, tổng 3/ngày chia chung nhánh Growth Radar, cooldown 7 ngày theo tác giả băm. Không lặp gửi khi kết quả mơ hồ; trạng thái `uncertain` cần đối soát. Nếu không có câu hỏi hoặc Meta thiếu scope thì không bình luận.
3. **Media Scout & Original Meme Lab** (job `visual`, cùng mốc giờ): `growth/media_scout.py`, `growth/meme_ideas.py`, `growth/meme_renderer.py`. Tạo meme gốc bằng chữ và hình khối, không copy khung mẫu meme nổi tiếng/nhân vật có bản quyền. AI tự đặt góc mới nhưng chỉ giữ khi không trùng lặp và không vi phạm mẫu cấm. Render PNG bằng Pillow, tải lên Supabase Storage bucket public `enna-original-media`; định danh trong `enna_media_ideas`. Có thể đọc phân tích hiệu quả Threads, nhưng CHỈ ưu tiên tuyến sau 7 ngày và đủ mẫu. Chuẩn bị storyboard video nguyên bản. Thu thập nguồn tham khảo qua Wikimedia Commons API với dấu hiệu CC0/Public Domain; Pexels API chỉ khi **đã có** PEXELS_API_KEY. Pexels thông báo tạm dừng cấp API key mới vào 03/11/2026: không yêu cầu người sở hữu tạo key mới, không cào Pexels.

## Xuất bản meme gốc, không tự đăng lại bên ngoài
Các trường mới `threads_posts.media_url/media_alt_text/media_idea_id` chỉ cho phép URL PNG gốc thuộc chính Supabase Storage và `editorial_series=visual_meme`, ràng buộc DB chống chèn URL lạ. `threads/content.py` đính kèm meme **chỉ khi** lượt biên tập mới cần bổ sung hàng đợi, khoảng mỗi 5 bài mới và ảnh đã lưu thành công `status=ready`; không đụng lịch Metricool hay 8 bài queued hiện có. `threads/publisher.py` xác minh quyền sở hữu nguồn và gọi Meta chính thức `media_type=IMAGE` + `image_url` + `alt_text` theo hai bước. Không có hình ảnh/video của bên khác nào tự động được phát hành. Video hiện là *kịch bản*, chưa phải tệp MP4 hoặc bài đã đăng.

## Bảo mật và kiểm tra
- Supabase migrations: `sql/v2_19_enna_community_media.sql`, `sql/v2_19b_shared_reply_budget.sql`, `sql/v2_19c_original_meme_post_columns.sql`. Raw tables `enna_community_attempts` và `enna_media_ideas` bật RLS, chỉ worker service-role đọc/ghi, RPC claim chỉ service-role được gọi. Token thực vẫn trong Vault, GitHub secrets. Bucket public chỉ có bản gốc không chứa bí mật.
- Public Edge Function `enna-public-status` ACTIVE phiên bản 15 chỉ trả aggregate trạng thái Community/Visual Lab, không tiết lộ câu hỏi, tác giả, đường dẫn tài liệu nháp. Dashboard công khai `docs/enna/index.html` bổ sung số lần bình luận đã xác nhận, số meme sẵn sàng, storyboard video, tư liệu cần xem quyền và mốc lịch.
- Đã thêm bộ kiểm thử thuần logic `tests/test_community_media.py`; mỗi job kiểm thử toàn repo trước hành động. **Chưa có bằng chứng CI mới đã PASS, chưa xác minh lần đầu Meta reply hay PNG xuất hiện công khai, chưa chứng minh workflow mới chạy theo lịch.** Không công bố là đã tương tác hoặc đã đăng meme trước khi có hàng `posted`/Meta post ID tương ứng.
- Nếu quyền Meta `threads_keyword_search` bị hạn chế, kênh vẫn có thể chăm sóc câu hỏi dưới nội dung chính chủ **nếu** `threads_read_replies` và `threads_manage_replies` hoạt động; nếu không, báo cần quyền, không vượt rào.
- GitHub schedule best effort, không phải tiến trình máy tính chạy 24/7, và avatar chuyển động không bằng chứng agent hoạt động.

## Kiểm tra sau lượt tự chạy đầu tiên
Mở https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/workflows/enna-community-media.yml , xem jobs `community` và `visual`: test PASS; kết quả scan phân biệt số 0; `enna_activity_events` xuất hiện `community_started`, `media_started`, `community_checked`, `media_checked`. Trong Supabase `enna_media_ideas`, ảnh gốc nếu upload thành công sẽ có `source_url` và `status=ready`; nếu không có link thì vẫn `research`, không tuyên bố hoàn tất. Bình luận xác nhận chỉ khi `enna_community_attempts.status=posted`.
Ngoài ra cần Meta App Review để Enna có thể tự tìm và bình luận có kiểm soát ở bài **bên ngoài**. Thông tin kiểm chứng từ người dùng không phải phê duyệt nâng cao.

## Nguồn chính chủ
- Meta API trả lời bình luận: https://www.postman.com/meta/threads/request/34203612-7abb4419-a216-4e06-8027-f9f4fcf8bee9
- Meta API ảnh/video: https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- Pexels API https://www.pexels.com/api/ , giấy phép https://www.pexels.com/license/
- Wikimedia Commons https://commons.wikimedia.org/wiki/Commons:Commons_API
