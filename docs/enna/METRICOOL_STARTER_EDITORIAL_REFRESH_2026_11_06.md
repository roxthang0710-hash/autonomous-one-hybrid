# Metricool Starter — kế hoạch tăng trưởng và kiểm soát chất lượng Đồ Hay Đi Làm
*Kiểm tra và triển khai: 06/11/2026, Asia/Ho_Chi_Minh.*

## 1. Kết quả thực thi trên lịch hiện hữu
- Đọc trực tiếp Metricool brand 7803567, không suy từ bản ghi Supabase. Chỉ chọn **27 bài PENDING** của 07–17/11, bao gồm **21 Threads, 3 Facebook và 3 Instagram**. Hai bài ERROR cũ và mọi bài đã PUBLISHED KHÔNG chỉnh sửa, không retry.
- Đã viết lại và cập nhật trực tiếp **27/27 caption** theo bản kiểm duyệt tại `config/enna_metricool_copy_refresh_2026_11_06.json`. Phong cách: tình huống đời thực, câu thoại quen thuộc, cú chốt hài có hình dung được, một mẹo có ích khi phù hợp, CTA theo dõi đặt có chọn lọc; không ép tất cả thành câu hỏi kết bài, không giả mạo trải nghiệm cá nhân.
- Metricool readback xác nhận 27 bản nháp đang chờ có chính xác văn bản mới, thời điểm đăng và UUID cũ, autoPublish vẫn bật; **16 bài giữ nguyên media, 11 bài vẫn chưa có media**. Trong số bài có media, một số ảnh vẽ tay/mèo thật đã lên lịch từ trước nhưng KHÔNG có xác nhận chất lượng theo ảnh tham chiếu mới của chủ tài khoản. Chưa thêm hay thay ảnh.
- Đồng bộ lại 6 Metricool post IDs mới của Facebook/Instagram và 11 IDs mới của Threads trong Supabase; UUID vẫn là khóa ổn định. CI kiểm tra tĩnh nội dung tại `tests/test_enna_metricool_copy_refresh.py`. Lưu ý: cập nhật tạo ID mới, không được dùng lại ID cũ.
- Bài Threads có lượt xem lớn nhất trong tập Metricool ban đầu: bài 3 phím tắt ngày 05/11 có snapshot ~4.370 lượt xem/69 thích; bài mẹo phím tắt trước đó ~2.069 lượt xem. Các bài kể chuyện và câu hỏi chung trong cùng snapshot thường thấp hơn, nhưng chưa thể khẳng định quan hệ nhân quả vì thời điểm, định dạng và khối lượng mẫu khác nhau. Dùng bài phím tắt làm giả thuyết, không viết 20 bài phím tắt giống nhau.

## 2. Bộ nhận diện và QA nội dung mới
**Cảm hứng visual do chủ tài khoản chọn:** kết hợp đời thật + hài công sở + nét vẽ tay mạnh, chưa trau chuốt quá mức, panel thật/ngộ/so sánh và hội thoại chat hư cấu. Ví dụ ảnh tham chiếu: mèo thật ôm laptop + bong bóng thoại sếp; đoạn chat công sở doodle + phản ứng; ly cà phê vẽ tay từ nóng tới kiệt sức.

- Hook đầu: mở bằng một tình huống dễ nhận ra, động từ cụ thể, thoại tự nhiên, không cần hô "cùng khám phá" hay "có 2 loại người..." mỗi ngày.
- Cú chốt: một hình ảnh hoặc đảo chiều cụ thể khiến người xem bật cười; tránh giảng đạo dài dòng hoặc mỗi bài đều kết thúc "theo mọi người có công bằng không".
- Value: phím tắt có thể thử, checklist hai–ba bước, nguồn/tính năng có thật. Không tuyên bố trải nghiệm hàng hóa khi chưa thử.
- Tránh clip/meme người khác chưa có quyền, nhạc bản quyền, nội dung ngụy tạo, thông tin đời tư, ảnh không khớp caption.
- Chỉ khoảng 5–8 CTA follow trong một chuỗi 27 bài; phần còn lại mời lưu bài, nhận xét tự nhiên hoặc kết bằng punchline. Mọi affiliate link vẫn chặn.
- Đa dạng format: truyện một cảnh, chat hư cấu, hai panel trước/sau, mẹo trực quan, ảnh thật + doodle. **Không tự động quay về poster chữ lớn lặp khuôn**.

## 3. Tận dụng Starter có mục tiêu, không chạy theo số lượng
Starter có **unlimited publishing theo Fair Use**, tối đa 100 đối thủ, PDF/PPT reports, lịch sử analytics không giới hạn, SmartLinks và tích hợp Canva/Google Drive. **Không có Metricool API chính thức hoặc workflow approval nâng cao của Advanced**. Không mua add-on (Advanced Analytics, X) nếu chưa có nhu cầu đo rõ ràng.

### Cadence thử nghiệm 14 ngày
- **Threads:** giữ những bài đã xác nhận 07–17/11 không chỉnh lịch sau đợt đổi caption; sau đó thử nhịp 2–3 bài/ngày, khác loại và khác thời điểm. Không coi 5 bài cùng ngày là mặc định bắt buộc; so sánh hiệu quả/đơn vị bài để tránh tự cạnh tranh.
- **Facebook:** hiện có các bài tới 09/11, sau đó trống. Chỉ lên lịch thêm khi có artwork/clip hợp quy chuẩn mới; thử 1 nội dung độc lập/ngày, từ 1–2 video Reels tự sản xuất mỗi tuần sau QA.
- **Instagram:** cũng trống sau 09/11; chỉ tạo post/reel có media hợp lệ. Thử 3–5 nội dung nguyên bản/tuần và tối đa 2 video ngắn ban đầu; carousel nên có lý do vuốt (3 tình huống / 3 thao tác), không cắt một poster thành năm ảnh chỉ để đủ slide.
- **Stories:** chỉ hỗ trợ nhịp phụ trợ khi có media thực, không tạo ảnh trống hay đăng cho đủ chỉ tiêu. Mỗi ảnh/video đủ quyền phải được duyệt.
- **Crosspost:** cùng một ý tưởng nhưng hook/caption khác nhau theo nền tảng; dùng Metricool Planner để xếp lịch riêng. Không xem unlimited là lý do tạo bản sao.
- **Assets:** 11 bài Threads còn thiếu hình có thể vẫn là bài text-native; chỉ thêm artwork khi đúng câu chuyện và đạt chuẩn. Kiểm toán 16 ảnh đã gắn bằng mắt người trước khi coi đạt style mới; không tự thay artwork đang PENDING nếu chưa có bản mới được duyệt.

### Các tính năng nên tận dụng
1. **Planner và trạng thái provider:** xem PENDING/PUBLISHING/PUBLISHED/ERROR, đối soát ID trước mọi retry; giữ lịch 72 giờ và không đăng trùng bài chính chủ qua Meta.
2. **Analytics & báo cáo PDF/PPT:** theo dõi follower, views, tương tác, profile views, saves/shares riêng từng kênh; báo cáo tuần với top 3 bài tốt và 3 bài yếu, kèm nguyên nhân giả thuyết để thử tiếp.
3. **SmartLinks/link bio:** trang tổng có mục “12 phím tắt miễn phí”, “Mẹo góc làm việc”, “Đồ dùng đã kiểm chứng”, về sau mới thêm affiliate được duyệt. Chưa tự tạo hay đưa link affiliate vào.
4. **Competitors:** chọn 5 tài khoản Việt Nam liên quan năng suất/văn phòng/meme để học format và hook, không lấy lại hình/nội dung; khi thấy tín hiệu tốt mới mở rộng tới tối đa 100.
5. **Canva/Google Drive:** nguồn ảnh chính chủ, nguyên bản, quản lý phiên bản và thời điểm duyệt rõ ràng. Không cần bật kết nối khi chưa có media QA.
6. **Best times:** trong lần đọc 06/11, Instagram trả toàn số 0; Metricool cho biết tài khoản IG cần >=100 follower để có dữ liệu cá nhân hóa và dữ liệu có thể mất <=7 ngày sau kết nối. Facebook best-times sau 2024 là dữ liệu nghiên cứu chung chứ không phải hành vi follower riêng. Không tuyên bố giờ đăng tối ưu khi không có dữ liệu cá nhân hóa.

## 4. Thước đo và quyết định
- **24 giờ sau đăng:** lượt xem, reply, like/share/save khi được hỗ trợ, trạng thái đăng thực tế và profile views toàn kênh, không gán follow cho riêng một bài.
- **72 giờ:** xem giữ chân video, xem tăng trưởng ngoài 24h, bài nào được chia sẻ/lưu và CTA nào tạo truy cập tài nguyên; để null nếu nguồn không cung cấp.
- **Mỗi tuần:** so sánh theo cùng kênh và nhóm giờ đăng: median views/post, reply/1000 views, saves/shares/1000 views, profile views, follower delta, tỷ lệ bài đăng thành công; không lấy tổng views làm lý do đăng ồ ạt.
- **Sau ít nhất 3 video/format:** giữ format có hiệu quả ổn định; 1 video viral đơn lẻ không đủ để nhân bản.
- **Commercial:** chỉ thử sản phẩm đã được chủ sở hữu, nhà bán, chương trình duyệt, có disclosure và link thật. Không giả doanh thu.

## 5. Bước làm tiếp không phụ thuộc mua thêm gói
1. Đối chiếu ca Metricool ERROR Facebook 06/11 và Threads 05/11 với bài thật trước khi xác định có nên đăng lại. Không tự bù.
2. Ưu tiên dựng ảnh/clip chuẩn style 3 tình huống thật–hài–doodle theo ảnh tham chiếu đã duyệt; đảm bảo nội dung hình khớp caption mới. Có thể giữ text-native Threads nếu không có hình.
3. Tạo bản đồ nội dung FB/IG từ 10/11 trở đi, sản xuất asset trước khi xếp lịch. Tránh dùng ảnh cũ chỉ để lấp khoảng trống.
4. Tiếp tục video pipeline 3 concept (shortcuts, chat 22:47, 3 dòng sau họp); chưa có MP4 thực tế trong repo và chưa đăng clip pilot.
5. Báo cáo so sánh 24h/72h rồi mới tăng nhịp.

## Nguồn Metricool
- Plans/addons, Starter và giới hạn Advanced API: https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u
- Best Times/các điều kiện dữ liệu cá nhân hóa: https://help.metricool.com/best-time-to-post-on-social-media-in-metricool-w7ll9
- Competitor metrics và giới hạn: https://help.metricool.com/competitor-analysis-ouhue
- SmartLinks trên gói trả phí: https://help.metricool.com/faqs-about-smartlinks-in-metricool-hue3f
- Phân biệt nâng cao analytics add-on của Starter: https://help.metricool.com/advanced-analytics-see-the-detailed-evolution-of-your-posts-up-to-their-first-30-days-fkhu6
