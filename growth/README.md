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
1. Theo cấu hình hiện tại, Growth Radar chỉ lưu bản nháp. Bộ phản hồi riêng chỉ được kích hoạt bằng Meta OAuth có đủ quyền và công tắc rõ ràng của chủ sở hữu; mặc định tắt.
2. Chỉ phản hồi bài Threads thực sự liên quan; dùng tên và danh tính thương hiệu thật. Không sử dụng nhiều tài khoản để tạo sự ủng hộ giả.
3. Không nhắn tin riêng hàng loạt, không gắn đường dẫn mua hàng vào bình luận để kéo lưu lượng, không đưa thông tin sai lệch để gây tranh cãi.
4. Trước khi bật tự động trả lời trong tương lai, cần Meta OAuth có đúng các quyền, giới hạn lượt và bảo đảm API cho phép; không dùng phương pháp cào giao diện.
5. Nếu sau này cho phép phản hồi, hệ thống sử dụng **một tài khoản thương hiệu thật**, tối đa 1 lần phản hồi/ngày, chỉ trên bài liên quan còn hiệu lực; ghi nhật ký để tránh phản hồi lại khi kết quả không rõ.
6. Google Trends và Google News là **tín hiệu tìm kiếm/tin tức**, không phải bằng chứng chủ đề đang hot trên Threads. Chỉ có Threads keyword search hợp lệ mới xác nhận được hội thoại từ chính nền tảng.
7. Mọi lời khẳng định về sản phẩm, giá hay xu hướng vẫn phải được xác minh; nội dung hiện tại là bản nháp nghiên cứu.

## Cách kiểm tra
- [GitHub Actions — Growth Radar](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/workflows/growth-radar.yml)
- [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor): `growth_signals`, `growth_opportunities`, `growth_runs`
- Xem bản nháp trong `growth_review_dashboard`; không lặp lịch 15 bài hiện có của Metricool

## Điều kiện để đọc hội thoại Threads trực tiếp
Sau khi chủ sở hữu tạo Meta Developer App cho Threads và cấp phép `threads_keyword_search`:
- Lưu token trong GitHub Actions Secret `THREADS_DISCOVERY_ACCESS_TOKEN`, không đưa token vào mã nguồn hay issue
- Đặt Secret `THREADS_DISCOVERY_ENABLED=true` để Agent chỉ **tìm kiếm**, không phản hồi
- Kiểm tra phương án định danh, giới hạn và điều khoản Meta trước khi bật tự trả lời thật

## Bộ phản hồi tự động — chưa kích hoạt

Mã `growth/engage.py` đã có sẵn luồng chính thức của Meta để tạo phản hồi hữu ích, không gắn liên kết, không giả danh khách hàng. **Không hoạt động trong dự án hiện tại** vì chưa có Meta Threads OAuth token và quyền `threads_keyword_search` / `threads_content_publish` / `threads_manage_replies`. Metricool đã kết nối không mặc nhiên cấp những quyền đó cho GitHub Actions.

Nếu chủ sở hữu muốn **tự nguyện** bật phản hồi tự động trong tương lai, sau khi xác minh các quyền API và kiểm tra chính sách nền tảng:
- Secret `THREADS_DISCOVERY_ENABLED=true`
- Secret `THREADS_DISCOVERY_ACCESS_TOKEN` là token chính thức dùng tìm kiếm
- Secret `THREADS_ENGAGE_ACCESS_TOKEN` là token Meta đủ quyền gửi phản hồi
- Secret `THREADS_EXPECTED_USERNAME=dohay_dilam`
- Secret `THREADS_AUTO_ENGAGE_ENABLED=true` là công tắc đồng ý gửi phản hồi từ thương hiệu

Không lưu token trong issue, file hoặc nội dung chat. Sau khi kết nối, worker xác minh tài khoản Meta `/me`, giới hạn 1 phản hồi/ngày, chỉ trả lời bài đã tìm qua API, chất lượng và liên quan cao, không bình luận kèm liên kết hay mua hàng. Nếu lỗi gửi bài không rõ kết quả, worker không thử lại tự động. Chưa kiểm thử gửi phản hồi lên nền tảng thật, chỉ kiểm thử bằng API giả lập.

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
