# Enna — Storytelling công sở và Topic/Community: đợt 02–09/11/2026

## Mục tiêu và điều đã triển khai

Thử nghiệm tăng người theo dõi thật bằng các câu chuyện công sở có xung đột, nhiều góc nhìn, giàu tính hội thoại — không phải kịch bản gây phẫn nộ hay câu chuyện giả mạo người thật.

Đã cập nhật **7/26 bài** được lên lịch tự xuất bản qua Metricool (một chuyện/ngày, 03–09/11), giữ nguyên UUID, ngày giờ và trạng thái chờ đăng. Cùng một nội dung đã được đồng bộ sang `threads_posts` để đối chiếu Meta sau xuất bản.

| Ngày | Giờ VN | Chủ đề tình huống | Hai phía tranh luận |
|---|---|---|---|
| 03/11 | 17:40 | Giao việc gấp lúc 17:28 | Trách nhiệm vs ranh giới giờ làm |
| 04/11 | 19:15 | Sếp công bố ý tưởng của nhân viên | Đại diện đội nhóm vs ghi công |
| 05/11 | 18:30 | Người làm nhanh bị giao thêm việc | Hiệu suất vs công bằng |
| 06/11 | 19:15 | Tin nhắn công việc lúc 22:47 | Chủ động vs quyền nghỉ ngơi |
| 07/11 | 21:30 | Không tham gia ăn tối nhóm | Hòa đồng vs đóng góp công việc |
| 08/11 | 19:15 | Bị yêu cầu hỗ trợ vào ngày nghỉ | Linh hoạt vs tôn trọng thời gian |
| 09/11 | 18:30 | Ai nên được thăng chức? | Chuyên môn vs năng lực dẫn dắt |

Mỗi bài đã được Meta/Metricool cho lịch ở trạng thái PENDING; **chưa xác nhận đăng thành công**. Không tính lịch là lượt xem hay follower.

## Hai khái niệm thường bị nhầm

**Topic Tag** là nhãn chủ đề của một bài Threads (khác với chữ # viết trong nội dung). Meta Threads official API cho phép `topic_tag` khi tạo container. `threads/publisher.py` đã hỗ trợ allowlist `Công sở`, `Góc làm việc`, `Đời sống đi làm`, `Du lịch` cho các bài đăng trực tiếp bằng Meta. Chưa có bằng chứng rằng Metricool MCP lưu hoặc xuất bản native Topic Tag; thử nghiệm gửi `topicTag` vào `threadsData` từng bị bỏ khỏi dữ liệu trả về. **Không mô tả 26 bài Metricool là bài đã có Topic Tag.**

**Community** là không gian cộng đồng Threads, người dùng có thể tham gia bằng giao diện Threads, với những chủ đề có biểu tượng Community riêng. Meta's public publishing API hiện không có tham số để chỉ định Community đích, theo thông tin hạn chế API phía Metricool. Đặt `topic_tag` không tự chứng minh một bài đã được đăng trực tiếp trong Community. Không dùng browser scraping hay tự động hoá không chính thức để giả lập tham gia cộng đồng.

Điểm nghẽn hệ thống: `claim_threads_post` trên Supabase cố ý chặn bộ đăng Meta trực tiếp vào **mọi ngày đã có lịch Metricool**, tránh xung đột/kịch bản đăng trùng. Giữ nguyên chốt bảo vệ trong chiến dịch. Khi muốn thử native Topic Tag, chọn khung ngày không được Metricool giữ chỗ, hoặc lập kế hoạch di chuyển trọn vẹn lịch ngày đó sang kênh Meta với quy trình thu hồi lịch, xác minh, rollback và kiểm thử.

## Công thức nội dung

1. **Hook**: sự kiện bất thường có thời điểm/đối thoại rõ ràng ngay hai dòng đầu.
2. **Nút thắt**: chỉ 2–4 câu gọn, một người bất đồng, có tình tiết đảo chiều.
3. **Hai quan điểm đều có lý**: không bêu xấu ngành nghề, giới, tuổi, cá nhân hoặc công ty có thật.
4. **Câu hỏi cuối mở**: khuyến khích kể trải nghiệm, không ép chỉ chọn A/B, không bảo tag bạn bè hay follow để nhận phần 2.
5. **Minh bạch**: ghi `(Tình huống giả định)` — không dùng “mình vừa gặp”, “bạn mình kể” cho sự việc AI bịa ra.

Kiểm tra việc đa dạng hoá với mẹo hữu ích và lời khuyên cụ thể; tránh một feed chỉ có tranh cãi. Không công kích nhân vật thật, thổi phồng tổn thương, câu kéo giận dữ, hay tự tạo bình luận.

## Đo lường sau đăng

Hệ thống `growth/story_insights.py` đọc duy nhất bài `status=posted` + Meta ID có thật, lấy snapshot `threads_metrics` mới nhất và chỉ dùng bài đã đủ 24 giờ với lượt xem, phản hồi hợp lệ. Phân nhóm story vs non-story bằng nhãn `(Tình huống giả định)`. Báo cáo số bài đo được, trung vị lượt xem và phản hồi trên mỗi 1.000 lượt xem, chỉ xếp hạng khi **mỗi nhóm có ít nhất 3 bài được đo**.

Đây là **tương quan nội dung với tương tác**, không suy luận nhân quả follower. Chưa đủ dữ liệu thì trả `insufficient_evidence`. Quy trình đã được gắn vào GitHub Actions `threads-nurture.yml`. KPI 1.000 follower trước 09/11 vẫn là mục tiêu thử thách, không phải kết quả dự báo.

## Nguồn chính thức

- Meta Topics: https://about.fb.com/news/2025/03/new-threads-features-more-personalized-experience-you-control/
- Meta Communities: https://about.fb.com/news/2025/10/introducing-threads-communities-find-your-people/
- Meta creator insights: https://about.fb.com/news/2024/10/find-your-community-with-new-threads-educational-insights/
- Meta Threads API: https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- Metricool limitations: https://help.metricool.com/api-limitations-per-social-network-n7zlr
