# Enna | Tuyến nội dung Công cụ số & Mẹo đi làm — 03/11/2026

## Mục tiêu
Mở rộng **Đồ Hay Đi Làm** từ chuyện công sở + đồ dùng hữu ích thành kênh vừa vui vừa có giá trị thực hành: người xem đọc xong **làm được một việc rõ ràng**. Đây là trụ cột **chăm sóc độc giả và tăng chất lượng theo dõi tự nhiên**, chưa phải chiến dịch affiliate.

- Kênh ưu tiên: Threads `@dohay_dilam`. Có thể tái chế thành ảnh chỉ dẫn/đoạn quay màn hình trên Facebook/Instagram sau khi tự kiểm thử.
- Tệp đọc: nhân viên mới, thực tập sinh, hành chính, marketing, nhóm vận hành, người hay dùng Windows/Google Sheets.
- Cách viết: thuần Việt khi có từ thay thế tự nhiên, hài hước vừa phải, không nói quá, không câu kéo, không giả vờ đã dùng/kiểm thử công cụ.
- Công thức biên tập: **tình huống quen thuộc → đúng thao tác → kết quả có thể kỳ vọng → lưu ý giới hạn**, CTA thưa (theo dõi/lưu lại nếu phù hợp), không gắn link mua hàng.

## Sáu tuyến nội dung

| Tuyến | Độc giả cần gì | Hướng bài và ví dụ | Dạng Threads |
|---|---|---|---|
| Phần mềm hay, đi làm đỡ cực | Khắc phục thao tác lặp | PowerToys PowerRename; FancyZones; Text Extractor | Vấn đề thường gặp → giải pháp, 3–6 dòng |
| Mẹo máy tính 30 giây | Có hiệu quả ngay | Windows + V lịch sử sao chép; Windows + Shift + S chụp màn hình | Một phím tắt + lưu ý |
| Bớt khổ với bảng tính | Giảm lỗi khi nhiều người phối hợp | Google Sheets bộ lọc cá nhân, danh sách chọn trạng thái | Trước/sau, 3 bước |
| AI làm trợ lý, không làm hộ suy nghĩ | Viết yêu cầu và kiểm chứng kết quả | Đưa đầu bài ẩn danh, đòi câu trả lời có cấu trúc, xác minh dữ kiện | Mẫu câu / sai-lầm thường gặp |
| Quy trình nhỏ, hiệu quả lớn | Giảm quên deadline & họp không chốt | Microsoft To Do My Day; chốt ai làm gì khi nào; nguyên tắc 3 ưu tiên | Mẩu hội thoại + cách xử lý |
| Enna Mini – Công cụ nhà làm | Thử công cụ miễn phí, phản hồi | Ba công cụ trên trang Enna Mini, hướng dẫn đúng năng lực hiện tại | Demo ngắn, không giấu hạn chế |

## Mức ưu tiên

**Ưu tiên A (phù hợp và đã có nguồn):**
1. Win + V và bảo vệ thông tin nhạy cảm.
2. Google Sheets chế độ xem bộ lọc.
3. Google Sheets danh sách chọn trạng thái.
4. PowerRename cho nhiều tệp tên lộn xộn.
5. Windows Snipping Tool nhận dạng chữ từ hình chụp (kiểm tra phiên bản, độ chính xác).
6. Microsoft To Do My Day.

**Ưu tiên B (nội dung sâu hơn):**
7. FancyZones – bố trí cửa sổ (phải cài PowerToys).
8. PowerToys Text Extractor – đọc chữ trên ảnh (phải cài & có gói ngôn ngữ).
9. Mẫu yêu cầu AI an toàn và cách kiểm chứng.
10. Enna Mini mẫu chốt việc sau họp.

**Khảo sát trước khi làm thêm:** hướng dẫn tự động hóa bằng Google Apps Script/Microsoft Power Automate; trợ lý AI đọc hồ sơ; đánh giá gói miễn phí của các ứng dụng. Mỗi chủ đề phải kiểm tra phạm vi tính năng, chi phí và chính sách dữ liệu lại trước khi đăng.

## Cơ chế đưa vào Enna

Mã triển khai:
- `threads/tech_editorial.py`: ngân hàng 10 brief có nguồn (trong trường `source`), `choose_tech_brief(post_count)`.
- `threads/content.py`: đề xuất một chủ đề kỹ năng/công cụ ở mỗi lượt **thứ ba** khi Enna cần tạo bài mới; vẫn dùng các `pillar` hiện tại (`work`, `organize`, `conversation`) nên không thay schema CSDL.
- Không sửa `threads/planner.py` / `SEEDS`, không đưa lại bài cũ vào hàng đợi.
- Nếu Enna còn đủ hàng đợi, không phát sinh bài mới. Nếu bài mới bị phát hiện trùng hoặc không đạt bộ lọc, bộ biên tập thử chủ đề dự phòng theo hạn mức hiện có.
- **Lưu ý:** chưa tự thay đổi một bài nào đã hẹn trong Metricool; mọi lịch đăng là best effort theo workflow, không đồng nghĩa đã đăng.
- Tần suất dự kiến: khoảng 1/3 bài mới là kỹ năng/công cụ trong luồng tạo bài. Đây là mục tiêu vòng quay **không phải KPI thực hiện đã xác nhận**.

## Kịch bản 4 tuần sau hàng đợi 21/11/2026

**Tuần 1 — Bàn phím và thao tác nhỏ:** Mẹo Win + V; phím chụp màn hình và nhận dạng chữ; bài trò chuyện 'cái gì làm mình mất thời gian'.
**Tuần 2 — Làm bảng tính bớt phát cáu:** Bộ lọc cá nhân Google Sheets; danh sách chọn trạng thái; câu hỏi về lỗi bàn giao dữ liệu.
**Tuần 3 — Phần mềm hỗ trợ nhiều cửa sổ/tệp:** PowerRename; FancyZones; clip quay màn hình ngắn, có kiểm thử trước.
**Tuần 4 — Quản lý việc & AI có trách nhiệm:** Microsoft To Do My Day; cách ra yêu cầu AI tốt; Enna Mini chốt việc sau họp. 

Các tuần là **định hướng tuần**, không phải cam kết ngày giờ hoặc bài đã được Metricool đặt lịch. Hãy đối chiếu lịch Metricool trước mỗi lần lên lịch thực tế.

## Chuyển đổi thành nhiều định dạng

- **Threads:** 1 chi tiết đời thường + 1 thao tác chính xác. Không nhồi 10 mẹo/bài.
- **Facebook/Instagram:** ảnh 2–4 bước, hoặc đoạn quay màn hình 15–30 giây, dùng dữ liệu mô phỏng.
- **Link Bio:** tài nguyên miễn phí Enna Mini làm điểm đến sau khi có đường dẫn hợp lệ và trải nghiệm đã được thử. Link công cụ/phần mềm nên dẫn tới nguồn chính chủ, không đến trang tải lạ.
- **Affiliate:** chỉ nghiên cứu liên quan (giá đỡ laptop, sổ...) khi được duyệt publisher, SKU và phương tiện tiếp thị. **Phần mềm miễn phí không đồng nghĩa có chương trình Affiliate**. Giữ nội dung miễn phí chiếm ưu thế.

## Kiểm duyệt trước mỗi bài

1. Nguồn chính chủ còn tồn tại và đúng khả năng công cụ.
2. Phím tắt/đường dẫn menu được kiểm tra với hệ điều hành, loại tài khoản và phiên bản.
3. Tránh lời hứa không đo được như 'giảm 80% thời gian'; tránh giả vờ Enna đã thử.
4. Không yêu cầu người đọc dán dữ liệu công ty, bảng lương, tài liệu mật hay thông tin khách hàng vào AI.
5. Không gắn liên kết rút gọn, liên kết mua hàng khi affiliate chưa được phê duyệt, phần mềm crack.
6. Không lặp bài Metricool/Supabase đã hẹn; không thay đổi bài cũ không được chủ sở hữu yêu cầu.
7. Theo dõi số liệu **thật**: lượt hiển thị, tương tác, theo dõi, lưu bài nếu nền tảng cung cấp. Không điền 0 thay cho số liệu bị thiếu.
8. Mỗi 14 ngày so sánh bài mẹo thực hành với bài tình huống/hài công sở (cùng giai đoạn, số liệu đủ mẫu) rồi điều chỉnh tần suất. Không suy luận quan hệ nhân quả từ vài bài.

## Nguồn chính chủ (kiểm tra 03/11/2026)

- Windows clipboard: https://support.microsoft.com/vi-vn/windows/apps/using-the-clipboard
- Snipping Tool: https://support.microsoft.com/vi-vn/windows/apps/use-snipping-tool-to-capture-screenshots
- Microsoft PowerToys / PowerRename: https://learn.microsoft.com/windows/powertoys/powerrename
- FancyZones: https://learn.microsoft.com/en-us/windows/powertoys/fancyzones
- PowerToys Text Extractor: https://learn.microsoft.com/windows/powertoys/text-extractor
- Google Sheets filter view: https://support.google.com/docs/answer/3540681?hl=en
- Google Sheets dropdown: https://support.google.com/docs/answer/186103?hl=en
- Microsoft To Do My Day: https://support.microsoft.com/en-us/todo/plan-and-connect-with-microsoft-to-do
- Enna Mini source: https://github.com/roxthang0710-hash/autonomous-one-hybrid/blob/main/docs/enna/kit/index.html

## Chỉ tiêu quan sát (giả thuyết, không báo là đã đạt)

- Có ít nhất 8 bản nháp hướng dẫn kỹ năng/công cụ được duyệt trước khi mở rộng.
- Tăng tỷ trọng bài mang giá trị hành động lên xấp xỉ 1/3 trong nhóm **bài mới**; không sửa backlog.
- Khi có đủ dữ liệu đo được: ưu tiên bình luận hỏi thêm cách làm, lưu/chia sẻ và theo dõi chất lượng hơn lượt xem đơn lẻ.
- Rà soát phát ngôn và nguồn tính năng mỗi 60–90 ngày.

Hồ sơ bàn giao dự án: `ENNA_PROJECT_HANDOFF.md`. Bản xem trước ý tưởng trên web: `docs/enna/content-lab/index.html` (bản nháp, không phải lịch đã đăng).
