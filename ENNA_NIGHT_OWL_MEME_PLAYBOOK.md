# ENNA — Công sở sau 0 giờ & Hài vô tri có hình (03–09/11/2026)

## Vì sao thử nghiệm

Người dùng đề xuất tuyến dành cho người thức khuya, kiểu kể đời thường, thỉnh thoảng "vô tri" vui vẻ và có ảnh, không phải mỗi post đều dài hay cần câu hỏi. Meta Threads creator insights từng ghi nhận nội dung hài có thể thu hút xem, và bài ảnh kèm văn bản ngắn tạo ngữ cảnh thường có lợi thế hơn ảnh không có ngữ cảnh. Đây là giả thuyết cần thử nghiệm với tài khoản @dohay_dilam, KHÔNG là dự báo kết quả.

Nguồn: https://about.fb.com/news/2024/10/find-your-community-with-new-threads-educational-insights/

## Thực tế đã triển khai

- 26 bài Metricool có từ trước vẫn được giữ nguyên.
- 4 bài **Công sở sau 0 giờ** mới có trạng thái PENDING trên Metricool, autoPublish bật:
  - 04/11 00:50: não tự tổ chức họp sau khi tắt máy
  - 05/11 01:05: nhân viên làm ca đêm, "bữa tối" lúc 7 giờ sáng
  - 07/11 00:55: mười hai cửa sổ trong đầu không đóng
  - 09/11 01:10: lập kế hoạch ngủ sớm lúc hơn 1 giờ sáng
- Đã đồng bộ cả 4 lịch đêm vào Supabase với trạng thái scheduled_external, không gọi PENDING là đã xuất bản.
- Có 4 bài **Meta-native Topic Tag** đang ở hàng đợi, KHÔNG phải đăng Community:
  - 03/11 15:00: Công sở (cuộc họp kéo dài)
  - 05/11 15:00: Góc làm việc (bàn làm việc gọn/hiệu quả)
  - 06/11 15:00: Đời sống đi làm (ước mơ chiều thứ Sáu)
  - 08/11 15:00: Góc làm việc (hộp đựng đẹp và cây bút thất lạc)
- Khi số liệu còn ít, giữ giới hạn khoảng cách ít nhất 90 phút và tối đa 5 bài được đặt/đăng mỗi ngày (bao gồm lịch từ Metricool và Meta). Không tự nâng hạn mức vì mong muốn tăng follower.

**Giới hạn kỹ thuật cần công khai:** Luồng Meta-native hiện vẫn có chốt ngừng tự đăng từ 22:15 đến 08:00. Các bài đêm đang dùng tính năng tự xuất bản của Metricool, không đi vòng qua chốt này. Metricool chưa được xác minh hỗ trợ native topic_tag; không tuyên bố bài đêm đã có Topic gốc. Chỉ khi Meta trả về post ID và bản ghi tag yêu cầu mới đánh dấu bài có Topic gốc đã gửi.

## Các dạng nội dung (thay vì 1 giọng cho cả tuần)

1. **Hồ sơ công sở:** nhân vật, hội thoại, nút thắt, hai góc nhìn hợp lý.
2. **Mẹo nhỏ làm được:** một việc có thể thử ngay, không công thức vạn năng.
3. **Công sở sau 0 giờ:** tâm trạng muộn, người làm ca đêm, cảm giác thường gặp; không cổ súy thiếu ngủ hay ép làm việc 24/7.
4. **Hài vô tri có hình:** caption rất ngắn và hình tự thân có tình huống; đôi khi không cần câu hỏi, không cần CTA.
5. **Một câu thả nhẹ:** câu quan sát hài hước đơn giản, không chêm nhiều emoji và không ép tranh luận.

## Sáu ý tưởng ảnh meme NGUYÊN BẢN (chưa sản xuất ảnh / chưa đăng)

| Mã | Brief ảnh mới | Caption minh họa | Cảm xúc |
|---|---|---|---|
| V01 | Cừu Enna phong cách pixel nằm trên gối; trên đầu là 8 cửa sổ suy nghĩ rối rắm | “Ngủ thì buồn ngủ. Não thì đang tổng kết KPI quý 3/2019.” | Vô tri, dễ đồng cảm |
| V02 | Một con chuột máy tính đeo balô đứng trước cửa văn phòng, mệt mỏi | “Chuột đã xin nghỉ, người thì vẫn đang kéo file.” | Hài vật dụng |
| V03 | Đồng hồ treo tường vẽ theo kiểu hài: kim phút chạy vài vòng, lời thoại “Họp 5 phút” | “Đơn vị đo thời gian của công ty mình: phút họp.” | Quan sát công sở |
| V04 | Ly cà phê và cốc nước nhìn nhau, màn hình máy tính phía sau hiện thứ Sáu | “Thứ Sáu 16:59, cà phê cũng không dám đi về trước.” | Đi làm, tự trào |
| V05 | Bức ảnh dàn dựng với sáu chiếc hộp đựng đồ được xếp đẹp, cây bút duy nhất nằm ngoài cùng | “Gọn rồi. Mỗi lần tìm bút cần thêm một cuộc điều tra.” | Hài đồ dùng |
| V06 | Hình pixel hai khung: 22:00 một nhân viên đóng máy; 00:40 bóng não ngồi họp một mình | “Máy tính: đã tắt. Cuộc họp trong đầu: mới bắt đầu.” | Cú đêm |

Nguyên tắc sản xuất: minh họa/ảnh chụp/ảnh AI nguyên bản, không sao chép ảnh tham khảo hoặc logo/người thật. Mỗi ảnh nên có alt text và caption cho ngữ cảnh. Kiểm tra bản quyền và kích thước trước khi đưa lên hosting có HTTPS công khai. Không sử dụng text-only post để mô tả một tấm ảnh không thực sự tồn tại.

## Đo thực tế

- So sánh 4 post đêm với các bài ban ngày ở cùng tuần dựa trên bài có ID Meta và insights thật; thiếu dữ liệu thì ghi **chưa biết**.
- Tách ý tưởng ảnh V01–V06 là **brief chờ tài sản ảnh**, KHÔNG hạch toán như đã đăng.
- Theo dõi số lượt xem, phản hồi có ý nghĩa, tăng follower thật; không giả định giờ đêm chắc chắn tốt hơn giờ ngày.
- Chỉ tăng/tái sử dụng định dạng thắng khi có đủ bằng chứng, không tự tạo spam hay bình luận giả.

Tài liệu và hạng mục này không khẳng định Meta Community API hoặc khả năng đăng thẳng vào Community.
