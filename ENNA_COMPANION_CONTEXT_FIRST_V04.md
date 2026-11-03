# Enna Companion v0.4 — Mở rộng tương tác vượt khỏi từ khóa công sở

**Ngày cập nhật:** 04/11/2026 (giờ Việt Nam).

## Phản hồi người dùng và nguyên nhân

Ảnh chụp Enna Companion v0.3 hiển thị `Bài chưa đủ tín hiệu về chủ đề đi làm, công sở hoặc công cụ.` dù chủ kênh đã chọn bài. Đó là lỗi sản phẩm: người dùng chọn nội dung nổi bật từ đời sống, giải trí, câu chuyện thú vị, thú cưng, bạn bè hoặc meme không nhất thiết chứa từ khóa công sở. V0.3 có cùng rào cản ở ba tầng: `background.js TOPIC`, `panel.js classify()` và `growth/companion_selected_reply.py` dùng `growth.scoring.classify()`; sâu hơn `growth.voice.suitable_reply()` kiểm tra phân loại tương tự.

## Thiết kế mới

- Chủ kênh bấm `✳ Gửi Enna` trên đúng một bài Threads. Không cần từ khóa công sở/phần mềm/Excel; trích đoạn 50–1100 ký tự, permalink chuẩn Threads.
- **Enna đánh giá NGỮ CẢNH**, không đánh giá theo từ khóa: độ thú vị/khả năng góp ý thật sự, giọng thương hiệu phù hợp, độ an toàn, tính nguyên bản, không spam, không chèn lời kêu gọi theo dõi. *Người dùng chọn bài* là tín hiệu quan tâm thủ công, KHÔNG phải bằng chứng bài thực sự viral hoặc có bao nhiêu tương tác.
- Tầng backend `growth/companion_fit.py` nhận diện góc hài hước/đời thường, góc nhìn/trò chuyện, công cụ/kỹ năng chỉ để tham khảo; chưa thấy góc nào vẫn có thể là candidate nếu ngữ cảnh đủ rõ và an toàn. Từ chối chủ đề nhạy cảm, nguy hiểm, lừa đảo, URL chưa rõ, thông tin riêng tư.
- `growth/companion_editor.py` có quyết định AI `should_reply`, `post_text`, `content_angle`, `reason`. Khi không có phản hồi duyên/giúp ích, Enna chủ động **không đăng** nhưng có thể đưa ý tưởng nội dung gốc. Không ép bài về công sở, không giả danh tác giả/đã trải nghiệm.
- `growth/companion_selected_reply.py` xử lý AI decision, kiểm tra chống phản hồi chung chung với `suitable_reply(..., require_niche=False)`; các worker khác giữ nguyên `require_niche=True`. **Meta GET xác minh mục tiêu, Supabase atomic daily cap và API chính thức giữ nguyên.** Nếu Meta chưa đọc được bài ngoài app scope, chỉ trả bản nháp ở Issue. Không dùng DOM bot để tự click bình luận.
- `tests/test_companion_selected_reply.py` mở rộng kiểm thử: bài đời thường về chú chó/cà phê được xét, nội dung nhạy cảm bị từ chối, AI có quyền quyết định không bình luận; test mã và nháp không có quyền Meta. Unit tests mới đã lưu trên GitHub, GitHub CI **chưa xác nhận PASS**.

## Chrome v0.4

- Gói: `enna_companion_chrome_v0.4.zip` do ChatGPT tạo trong cuộc trò chuyện ngày 04/11/2026, đã xuất hiện ở `/mnt/data` trong cuộc hội thoại đó. **Đường dẫn sandbox không tồn tại vĩnh viễn trong các phiên khác.**
- Thư mục trong gói: `enna_companion_extension_v04/` chứa `manifest.json`, `content.js`, `content.css`, `background.js`, `panel.js`, `panel.html`, `panel.css`, `test_local.js`, `README.md`. Không có khóa bí mật.
- Chỉnh `background.js` bỏ yêu cầu `TOPIC.test(text)`, vẫn kiểm tra URL Threads chính xác, giới hạn độ dài và thông tin nhạy cảm; `panel.js` bỏ `if (!classify(text).length) ... return`, biến bộ nhóm từ khóa thành **gợi ý góc nội dung** chứ không phải điều kiện cần. Các yêu cầu soạn nháp cũng không ép liên hệ dân văn phòng.
- JavaScript `node --check` PASS toàn bộ mã nguồn; `node test_local.js` PASS cho cả bài Excel lẫn bài đời thường thú cưng không có từ khóa công sở; kiểm tra trang giả, đoạn quá ngắn, chuyển tiếng Việt Base64URL và ZIP integrity PASS. Chưa kiểm thử trên DOM Chrome/Threads thực tế.
- Cài nâng cấp: vào `chrome://extensions` tắt/gỡ phiên bản 0.3 để khỏi trùng nút, giải nén ZIP v0.4, `Load unpacked` thư mục có manifest, tải lại Threads. Vẫn cần bấm **Submit new issue** ở GitHub vì không giữ token GitHub trong extension.
- **Nguồn mã v0.4 hiện nằm trong ZIP được tạo bởi phiên làm việc này, chưa commit nguyên bộ tệp extension vào GitHub.** Nếu muốn bảo trì độc lập lâu dài, cần lưu mã nguồn extension vào GitHub sau khi tiếp nhận ZIP. Backend Python đã commit trên GitHub.

## Không thay đổi giới hạn quyền Meta

Không có xác nhận quyền đọc/bình luận tự động bài của tài khoản khác. Owner selection và shortcode ID không thể thay thế cấp quyền App Review. Chỉ đánh dấu `posted` khi Meta trả mã phản hồi; không đăng lại nếu trạng thái `uncertain`. Không tự đọc video/meme chỉ bằng văn bản; phải thông báo giới hạn dữ liệu đầu vào.

## Đo hiệu quả sau thử nghiệm

Theo dõi riêng: số bài owner chọn → số bị từ chối vì rủi ro → số Enna cho rằng đáng góp ý → số bản nháp do thiếu Meta scope → số bình luận Meta xác nhận → phản hồi thực sau bình luận. Tránh kết luận đã tăng follower hoặc tăng reach chỉ từ số bình luận gửi.
