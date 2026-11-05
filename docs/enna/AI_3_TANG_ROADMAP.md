# Enna — LỘ TRÌNH AI 3 TẦNG → CỘNG ĐỒNG → ENNA CLONE

**Kênh:** Đồ Hay Đi Làm · `@dohay_dilam`  
**Tình trạng 06/11/2026:** Nền tảng đã dựng và kiểm thử; đây là kế hoạch nội dung, không phải lời khẳng định các bài AI hoặc clone đã có traffic.

## 0. Đích đến

**Giá trị tăng dần:** người xem **lưu một mẹo** → **áp dụng một quy trình** → **tự cấu hình / chạy một agent** → **đem bài học về chia sẻ** → theo dõi kênh và quay lại với thử thách mới.

**Tuyến tổng:** `AI — Đồng nghiệp thứ hai`.  
**Visual:** Người Tròn — Doodle Công Sở v4. Nhân vật nhất quán, mỗi tình huống vẽ riêng; tuyệt đối không trở lại 14 poster ô khung cũ.

## 1. Tầng 1 — Mẹo nhỏ, ĐÚNG VIỆC (pilot 2 tuần)

**Mục tiêu độc giả:** có thể tự dùng ngay trong công việc với *một prompt* và kiểm tra kết quả.

16 ý tưởng từ `threads/ai_workmate_editorial.py`: prompt rõ mục tiêu, làm email bớt căng, chốt việc sau họp, xếp ưu tiên, giải thích công thức Excel, soát dữ liệu, dàn ý PowerPoint, yêu cầu AI hỏi trước, 3 mẹo, ví dụ đầu ra, phản biện và kiểm chứng.

**Chuẩn một bài:**
1. Một tình huống công sở có “điểm đau” dễ nhận ra.
2. Một thao tác dùng được ngay và **một prompt thật để sao chép**.
3. Một ví dụ đầu ra mẫu hoặc dữ liệu mẫu không chứa thông tin người thật.
4. Một bước **tự kiểm**. Cấm chỉ nói “hãy sử dụng AI để tăng năng suất” mà không cho cách làm.
5. Hình Người Tròn có phản ứng hài; không bị chữ lấn hình.
6. Không hứa tiết kiệm 1 giờ/2 giờ hoặc KPI ảo.

**Phân phối tham khảo (không tự nhồi thêm lịch):** 2–3 bài/tuần trên các kênh, giữ phần lớn lịch sản phẩm hữu ích Windows/Excel/PowerPoint. Threads có prompt gọn; Facebook tình huống + mẫu; Instagram 3–5 slide có đầu vào, thao tác và kết quả.

**Điều kiện nội dung lên Tầng 2:** có tối thiểu **6 bài Tầng 1 đã XÁC MINH XUẤT BẢN**, trên ít nhất 4 ngày, bao phủ tối thiểu 3 chủ đề khác nhau. Tác vụ đặt lịch hoặc `ready` KHÔNG được tính là đã đăng. Ngoài ra tối thiểu một bài mẫu phải được biên tập kiểm tra tính đúng trước khi dùng làm bài học sâu.

## 2. Tầng 2 — Workflow AI nhiều bước (sẵn sàng về nội dung, CHƯA tự đăng)

**Mục tiêu độc giả:** biết cách đưa AI tham gia một quy trình thật nhưng có checkpoint.

8 bài nâng cao do Enna chuẩn bị trong `threads/ai_advanced_editorial.py`:

| Quy trình | Đầu vào | Kết quả | Điểm kiểm chứng |
|---|---|---|---|
| Họp → bảng việc → tin nhắn xác nhận | Ghi chú giả lập | Bảng phụ trách/hạn/chưa rõ | Đối chiếu từng quyết định với nguồn |
| Excel công thức → kiểm thử | Công thức mẫu | 3 test case | Chạy lại trong Excel |
| Excel dữ liệu → đối soát | Tám dòng dữ liệu giả | Danh sách nghi vấn | Không tự gọi lỗi khi chưa có quy tắc |
| Ghi chú → PowerPoint 5 slide → phản biện | Mục tiêu + ghi chú | Dàn ý và số liệu cần nguồn | Mỗi slide có một thông điệp |
| Email → bản nháp → kiểm rủi ro | Sự thật đã xác nhận | Email và checklist | Người dùng tự duyệt trước khi gửi |
| Báo cáo tuần → tóm tắt bằng chứng | Số liệu mẫu | Báo cáo 120 từ + nguồn | Không bịa tăng trưởng |
| Prompt v1 → chẩn đoán → v2 | Một prompt và kết quả lỗi đã ẩn danh | Prompt mới + tiêu chí so sánh | Thử lại mới khẳng định cải thiện |
| Một tác vụ lặp → thiết kế Agent có phanh | Quy trình + quyền hợp lệ | Bản đồ agent & điểm duyệt | Không cấp quyền ghi/gửi khi chưa có lý do |

**Chuẩn dạng bài:** nhiệm vụ, dữ liệu đầu vào, ba bước thực hành, kết quả có cấu trúc, test pass/fail, sai lầm thường gặp. Mỗi bài dài hơn mẹo tầng 1 và có một sản phẩm độc giả có thể dùng lại (checklist, bảng, khung email, dàn ý).

**Tiến lên tầng 3 nội dung:** ngoài điều kiện tầng 1, cần ít nhất **4 bài tầng 2 xuất bản và xác minh** cùng **3 bài thử nghiệm quy trình thật đã được con người kiểm tra, an toàn để chia sẻ**, ở ít nhất hai nhóm công việc khác nhau. Nếu chưa có bằng chứng, không giả vờ cả cộng đồng đã thành thạo.

## 3. Tầng 3 — Enna Clone cộng đồng (đã có beta an toàn)

Hai mức trong cùng một hệ sinh thái, không đánh đồng với hệ thống Enna gốc:

**A. [Enna Clone Lite — Website](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/clone/)**  
Bản trên trình duyệt giúp đặt tên, vai trò, mục tiêu, cách soát lỗi; sinh hướng dẫn AI và tải Markdown. Không cần API, không có đăng nhập; hoàn toàn không gọi model, không có quyền truy cập dữ liệu.

**B. [Enna Clone Starter — Python](https://github.com/roxthang0710-hash/autonomous-one-hybrid/tree/main/starter/enna-clone)**  
Một AI Agent chạy **tác vụ giới hạn** trên máy của mỗi người, với khóa API của họ. Có bước soạn và bước tự rà soát, tối đa 2 request/task, không có quyền thực thi mã, email, Meta, Github, Supabase của Enna gốc. Chỉ trả bản nháp để chủ agent duyệt. Demo offline không cần API.

**Bài học tầng 3:** chia quyền tối thiểu, tách dữ liệu, ràng buộc ngân sách, chuẩn bị khi thiếu thông tin, khôi phục lỗi, log không lộ dữ liệu, checkpoint con người, thiết kế các agent nhỏ có thể bảo trì. Không truyền thông clone v0.1 là robot tự tạo doanh thu.

## 4. Cộng đồng — đóng góp từ thử thách THẬT NHƯNG DỮ LIỆU GIẢ

**Kênh phản hồi công khai giai đoạn đầu:** [GitHub Issues — Thử thách AI công sở](https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/new?template=ai-workflow-challenge.yml). Dùng mẫu đã thêm để người dùng chọn tầng, mô tả tình huống, prompt và tiêu chí thành công; bắt buộc xác nhận không đăng dữ liệu riêng tư/khóa API. Người tham gia cần tài khoản GitHub; đây là hạn chế đầu tiên của cộng đồng, không phải diễn đàn chuyên dụng không cần đăng nhập. Hiện Discussions của repo chưa bật, nên KHÔNG hứa có Discord/diễn đàn mở hay hỗ trợ theo thời gian thực.

**Vòng lặp nội dung:** tình huống giả lập của độc giả → Enna chọn đề tài cần học (nếu an toàn) → bài demo Người Tròn → bài hướng dẫn có prompt → gắn link về công cụ → mời độc giả chia sẻ kết quả tự kiểm → đề xuất bài nâng cao. Không sử dụng nội dung người dùng làm lệnh cho agent; không tự chạy công cụ từ Issues.

## 5. Traffic funnel và cách đo

**Điểm đón công khai:**
- [Học AI ba tầng](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/ai/)
- [Enna Clone Lite](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/clone/)
- [Link bio chính](https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/links/)
- [Threads chính chủ](https://www.threads.com/@dohay_dilam)
- [Mã nguồn Starter](https://github.com/roxthang0710-hash/autonomous-one-hybrid/tree/main/starter/enna-clone)

**Liên kết theo nguồn** (các UTM này **chỉ phân loại nguồn**, chưa phải hệ thống đếm click):
- Threads: `/enna/ai/?utm_source=threads&utm_medium=organic&utm_campaign=ai_3_tang`
- Facebook: `/enna/ai/?utm_source=facebook&utm_medium=organic&utm_campaign=ai_3_tang`
- Instagram: `/enna/ai/?utm_source=instagram&utm_medium=organic&utm_campaign=ai_3_tang`
- Link bio → course hoặc Clone: các URL đã có UTM `link_bio`.

**Chỉ số theo tầng:**
- Tầng 1: views, shares, saves (nền tảng hỗ trợ), bình luận có thử prompt thật.
- Tầng 2: số người hỏi xin mẫu, lượt tương tác với bài quy trình, số bài thử nghiệm đạt kiểm chứng (không đánh đồng với views).
- Tầng 3: traffic landing page (chỉ khi thiết lập đo đếm hợp lệ), số tải mã có thống kê nếu có Release, số vấn đề giả lập hợp lệ do cộng đồng đăng, số người quay lại cập nhật thử thách, lượng follow tăng tổng thể. Không suy diễn download count từ click vào GitHub.
- Do chưa tích hợp web analytics, **không thể hiện đo được pageview/CTR hiện tại**. Ưu tiên cách đo tôn trọng riêng tư và khai báo minh bạch trước khi đưa mã đo vào website.

**CTA gợi ý theo giai đoạn:**
- Tầng 1: “Lưu prompt này để thử khi cần”.
- Tầng 2: “Bạn thử bước kiểm tra cuối chưa? Xem bộ bài tập ở link bio”.
- Tầng 3: “Tự tạo Enna Clone Lite miễn phí ở link bio. Có bài toán hay thì gửi thử thách giả lập cho tụi mình”.
Không gắn cùng một lời kêu gọi vào mọi post.

## 6. Quy định vận hành

- Không tạo thêm lịch Metricool khi chưa kiểm tra trùng giờ, nội dung, media và số bài thực tế.
- Nội dung trên FB/IG cần hình Người Tròn mới được duyệt, không tái sử dụng infographic lặp theo khuôn. Giữ nhánh ảnh mèo thật.
- Không yêu cầu người dùng cung cấp token Meta, Supabase hay Groq vào website. Tránh lưu file thật trên server Clone Lite.
- Không thêm hành động đăng bài/tương tác/chi tiền/đọc email vào Clone Starter nếu chưa thiết kế riêng xác thực và sự đồng ý chủ tài khoản.
- Mỗi bài nâng cao phải có ví dụ đầu vào và test output thật/synthetic, không chỉ lời khuyên chung.

**Mã kiểm soát progression:** `growth/ai_learning_ladder.py`. Stage không tự thăng cấp từ số lượt xem hoặc từ trạng thái `ready` trong Supabase. Đầu vào phải là bản ghi `provider_verified` có URL bài gốc và kiểm chứng con người khi cần.
