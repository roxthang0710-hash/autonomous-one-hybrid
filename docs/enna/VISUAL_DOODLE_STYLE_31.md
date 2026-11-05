# Enna Visual Tone 3.1 — Meme vẽ tay nguệch ngoạc

## Quyết định đã triển khai

Người dùng yêu cầu thay đổi **hình thức thể hiện** của hai mẫu (cốc cà phê và khung chat) thành nét vẽ tay ngộ nghĩnh, **không thay ảnh mèo**. Bản 3.0 trước đó chủ yếu tăng màu và vẫn mang cảm giác stock image + tiêu đề.

- **Reaction (mèo): GIỮ NGUYÊN.** Phần `reaction` của `scripts/enna_visual_factory.py` tiếp tục dựng ảnh chụp thật, không đi qua bộ vẽ tay.
- **Cà phê:** dùng minh họa cốc cà phê nét bút rung, hai trạng thái có nét mặt (vui / cạn năng lượng), bảng phác tay hai khung thời gian.
- **Chat giả lập:** khung điện thoại tự vẽ, bong bóng hội thoại méo nhẹ, nhân vật que, mũi tên nguệch ngoạc, nhãn rõ rằng đây là đoạn chat *giả lập*.
- Để lưu dấu quyền ảnh hợp lệ, ảnh CC0 vốn được Enna xác minh lại vẫn xuất hiện dưới dạng tấm ảnh scrapbook *rất nhỏ*, **không phải chủ thể chính**.
- Các mẫu `contrast` không liên quan đến cà phê tạm giữ bố cục ảnh thật để tránh vẽ nhầm nội dung; `chat` luôn dùng kiểu vẽ tay. Những mẫu khác không bị chỉnh sửa tùy tiện.

## Kỹ thuật

- `scripts/enna_doodle_composer.py`: các nét cong, đường viền méo, mặt biểu cảm, nhân vật que được dựng bằng Pillow và seed cố định; không dùng công cụ tạo hình trả phí.
- `scripts/enna_visual_factory.py`: định tuyến `render_doodle(...)`; lưu `visual_rendering=hand_drawn_doodle` hoặc `authentic_photo`, `visual_tone_version=3.1` vào file `*.rights.json`.
- `tests/test_enna_doodle_composer.py`: ảnh vẽ tay không phụ thuộc ảnh stock ở vùng trung tâm; mèo vẫn giữ vùng ảnh chụp thật.
- `.github/workflows/enna-visual-factory.yml`: kiểm thử và xuất 3 PNG theo định dạng 1080×1350; workflow chỉ tạo bản nháp, **không đăng lên Threads, Facebook hoặc Instagram**.

## Tiêu chí biên tập

Một ảnh vẽ tay phải khiến người xem thấy nhân vật hoặc tình huống hài mà không cần đọc một đoạn caption dài. Không thay ảnh mèo bằng ảnh AI. Lời thoại giả lập không được mạo nhận tin nhắn hay cá nhân có thật. Nhãn `DRAFT_REQUIRES_HUMAN_REVIEW` tiếp tục được giữ, để đánh giá chất lượng sau khi xem PNG thực tế.

Lưu ý: vẽ tay theo chương trình vẫn có thể trông gọn hơn nét bút của con người; đây là mẫu có thể tái tạo trên GitHub, không khẳng định có thể thay thế mọi minh họa do nghệ sĩ sáng tác.
