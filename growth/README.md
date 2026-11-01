# Autonomous One v1.7 — Growth Radar cho Threads

## Mục tiêu
Tăng trưởng kênh **Đồ Hay Đi Làm** bằng nội dung gốc hữu ích, chủ đề thật sự đang được quan tâm và sự tham gia thảo luận **minh bạch**. Không tự tạo tài khoản giả, không tự bình luận hàng loạt, không mua tương tác, không dùng tin nóng nhạy cảm để câu kéo.

## Các tính năng đã triển khai

- `growth/sources.py`: đọc RSS công khai của [Google Trends Việt Nam](https://trends.google.com/trending?geo=VN) và một số truy vấn tin tức chủ đề hẹp qua Google News RSS, mỗi nguồn giới hạn bản ghi và thời gian chờ
- `growth/scoring.py`: phân loại chủ đề công sở, đi công tác, tổ chức đồ dùng; kiểm tra thời gian và loại bỏ các chủ đề nhạy cảm, ngoài lĩnh vực
- `growth/generator.py`: sử dụng Groq tạo **1 ý tưởng nội dung tiếng Việt** mỗi lần quét có nguồn phù hợp; không chép bài nguồn, không bịa trải nghiệm hay doanh số
- `growth/conversations.py`: bộ tìm kiếm các cuộc thảo luận Threads qua **API chính thức của Meta**, chỉ hoạt động sau khi có quyền `threads_keyword_search` và được bật rõ ràng
- `growth/optimizer.py`: chỉ tính gợi ý dựa trên số liệu Metricool thực khi có ít nhất 7 ngày quan sát và 5 bài đã xuất bản
- `growth/report.py`: tình trạng hoạt động và hạn mức, không in bản nháp riêng tư vào log GitHub công khai
- `.github/workflows/growth-radar.yml`: chạy 09:15 và 17:15 **giờ Việt Nam**, hoặc từ issue `growth:` của chủ repo. Hệ thống không chi tiền và không đăng nội dung công khai

## Trạng thái dữ liệu
Supabase:
- `growth_signals`: liên kết nguồn, nhan đề, thời gian, điểm liên quan, trạng thái
- `growth_opportunities`: góc nội dung và đề xuất phản hồi, luôn ở `needs_review`; hết hạn sau 72 giờ
- `growth_runs`: nhật ký các lượt quét, nguồn đã đọc, số bản nháp
- `growth_metricool_daily`: chỗ lưu số liệu thực từ Metricool (không được tự điền 0 khi Metricool chưa có dữ liệu)
- `growth_review_dashboard`: view nội bộ, không cấp quyền cho anonymous hoặc authenticated

### Quy tắc tương tác có trách nhiệm
1. Không đăng hoặc trả lời công khai từ bộ Growth Radar hiện tại. AI chỉ chuẩn bị nội dung.
2. Chỉ phản hồi bài Threads thực sự liên quan; dùng tên và danh tính thương hiệu thật. Không sử dụng nhiều tài khoản để tạo sự ủng hộ giả.
3. Không nhắn tin riêng hàng loạt, không gắn đường dẫn mua hàng vào bình luận để kéo lưu lượng, không đưa thông tin sai lệch để gây tranh cãi.
4. Trước khi bật tự động trả lời trong tương lai, cần Meta OAuth có đúng các quyền, giới hạn lượt và bảo đảm API cho phép; không dùng phương pháp cào giao diện.
5. Google Trends và Google News là **tín hiệu tìm kiếm/tin tức**, không phải bằng chứng chủ đề đang hot trên Threads. Chỉ có Threads keyword search hợp lệ mới xác nhận được hội thoại từ chính nền tảng.
6. Mọi lời khẳng định về sản phẩm, giá hay xu hướng vẫn phải được xác minh; nội dung hiện tại là bản nháp nghiên cứu.

## Cách kiểm tra
- [GitHub Actions — Growth Radar](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/workflows/growth-radar.yml)
- [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor): `growth_signals`, `growth_opportunities`, `growth_runs`
- Xem bản nháp trong `growth_review_dashboard`; không lặp lịch 15 bài hiện có của Metricool

## Điều kiện để đọc hội thoại Threads trực tiếp
Sau khi chủ sở hữu tạo Meta Developer App cho Threads và cấp phép `threads_keyword_search`:
- Lưu token trong GitHub Actions Secret `THREADS_DISCOVERY_ACCESS_TOKEN`, không đưa token vào mã nguồn hay issue
- Đặt Secret `THREADS_DISCOVERY_ENABLED=true` để Agent chỉ **tìm kiếm**, không phản hồi
- Kiểm tra phương án định danh, giới hạn và điều khoản Meta trước khi bật tự trả lời thật

## Giới hạn hiện tại
- Metricool có kết nối chat và đang quản lý lịch xuất bản 15 bài, nhưng **Metricool API server-to-server yêu cầu gói Advanced/Custom** theo tài liệu hiện tại. Với gói Free, GitHub không tự gửi thêm nội dung sang Metricool qua API thương mại.
- Khả năng phân tích Metricool đang thực hiện từ kết nối trong ChatGPT; chưa có cơ chế đồng bộ số liệu tự động vào Supabase bằng quyền máy chủ. Khi chưa đủ mẫu, `growth/optimizer.py` sẽ báo thiếu dữ liệu thay vì tự đưa quyết định.
- Không có bằng chứng hoa hồng Shopee hay doanh thu Affiliate. Tăng trưởng kênh và doanh thu là hai thước đo khác nhau.

## Tài liệu chính thức
- [Meta — Threads best practices](https://about.fb.com/news/2024/10/find-your-community-with-new-threads-educational-insights/)
- [Meta — Threads keyword search](https://www.postman.com/meta/threads/request/34203612-b3b2c12a-7ce6-4d86-a3c6-6d31e3b66ea1)
- [Meta — replies](https://www.postman.com/meta/threads/request/34203612-7abb4419-a216-4e06-8027-f9f4fcf8bee9)
- [Google Trends — RSS export](https://support.google.com/trends/answer/3076011?hl=vi)
- [Metricool — API plans](https://help.metricool.com/mcp-vs-api-access-what-is-the-difference-5y3ib)
