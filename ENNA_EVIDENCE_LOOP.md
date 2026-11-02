# Enna — Vòng học hỏi dựa trên dữ liệu (02/11/2026)

## Đích đến

**Tín hiệu hợp pháp → ý tưởng có nguồn → nội dung hoặc thử nghiệm được phép → kết quả thực → quyết định tiếp theo.**
Không dùng tương tác làm doanh thu, không tự chi tiêu, không tự tham gia chương trình Affiliate hay tạo liên kết giả. AI không tự sửa mã nguồn và phát hành âm thầm; mọi thay đổi kỹ thuật có kiểm thử và lịch sử GitHub.

## Đang hoạt động

- `agent.py`: nghiên cứu cơ hội kinh doanh và tạo đề xuất chờ duyệt.
- `growth/runner.py`: tìm tín hiệu RSS và Threads qua API chính thức nếu có quyền, lọc và tạo nội dung phù hợp.
- `threads/daily.py`: bảo vệ lịch Metricool, kiểm tra quyền Meta, đăng bài đúng hạn và thu thập insight khi nền tảng cung cấp.
- `affiliate/runner.py`: nghiên cứu chương trình, đề xuất nội dung hữu ích không ngân sách; không tự xuất bản thương mại.
- `growth/learning.py`: lấy dữ liệu đã lưu, xếp hạng việc ưu tiên; yêu cầu ít nhất **7 ngày hoàn chỉnh gần nhất trong 30 ngày** và tối thiểu **5 bài được đo lường** trước khi đề nghị thử nghiệm tối ưu.
- `enna.py`: ghi các việc tiếp theo, cảnh báo thiếu dữ liệu và trạng thái thương mại hóa vào GitHub Actions Summary. Không có bản nháp, token hoặc đường dẫn chứng từ nội bộ trong báo cáo công khai.
- Workflow Affiliate cũng gọi báo cáo Enna sau mỗi lượt nghiên cứu.

## Điểm gốc đo lường

Ngày 02/11/2026, Metricool kết nối với nhãn **Đồ Hay Đi Làm** (brand ID 7803567) trả về các trường Threads:
- **01/11**: 1 bài được Metricool ghi nhận; 0 người theo dõi và thay đổi 0 theo trường trả về. Lượt xem và tương tác **NULL**, nghĩa là không có dữ liệu từ nhà cung cấp.
- **02/11 (ngày chưa kết thúc)**: lượt xem 0, tương tác 0, phản hồi 0 trong lần đọc tạm thời; các trường số bài đăng/người theo dõi không có giá trị. Không dùng ngày hiện tại làm dữ liệu đủ ngày.
- Một bài có URL công khai được Metricool trả về ngày 01/11. Đây là bài ngoại vi; **không** cộng nhầm vào `threads_posts.status=posted` của Enna.
- 15 bài của Metricool đang ở `PENDING`, nên không coi là đã xuất bản.
- Những bản ghi trên đã được nhập vào `growth_metricool_daily` với `source='metricool'` và giữ chính xác `NULL` cho giá trị chưa trả về. Đây là **lần nhập thực tế trong phiên ChatGPT**, chưa phải một kết nối server-to-server chạy không cần người. Muốn cập nhật hằng ngày tự động cần quyền API phía máy chủ được phép hoặc dữ liệu Meta chính thức.

## Tiêu chí ra quyết định

1. **Bằng chứng**: không số liệu, hoặc nguồn hỏng → dừng mọi khẳng định hiệu quả; kiểm tra nhà cung cấp.
2. **Rủi ro**: chỉ dùng quyền Meta chính thức; bình luận đúng bài, không spam; không vượt hạn mức chủ sở hữu đã đặt.
3. **Thử nghiệm**: chỉ khi đủ dữ liệu, đổi **một biến** trong tối thiểu **7 ngày**; đo mức xem/tương tác từ nguồn thật, không mô tả chúng thành đơn hàng.
4. **Thương mại hóa**: phải xác minh chương trình được chấp thuận, điều kiện sản phẩm và kênh. `affiliate_metrics` chỉ có thể ghi là **hoa hồng có chứng từ từ nhà cung cấp** khi nguồn `provider_export` có URL HTTPS. Đó **không phải** chứng nhận tiền đã được thanh toán.
5. **Thanh toán**: hiện chưa có đường đối soát tiền vào tài khoản. Chỉ báo tiền thực nhận sau bằng chứng thanh toán rõ ràng; không suy đoán.

## Các điều kiện hiện vẫn chặn tăng trưởng/doanh thu

- Cần quyền Meta App Review cho Threads keyword search ngoài chính tài khoản, nếu API hiện trả kết quả rỗng.
- Metricool/Threads chưa đủ ngày và bài có số liệu thật để phân tích. Giữ bài chưa tới hạn theo lịch, không tăng lịch để đạt chỉ tiêu ảo.
- Chủ tài khoản chưa xác minh Publisher Affiliate được chấp thuận và chưa có link hoa hồng có nguồn.
- Không có chứng từ hoa hồng hay bằng chứng tiền nhận vào tài khoản. Chỉ số doanh thu ở trạng thái **không xác minh**, không tự động ghi bằng 0 một cách gây hiểu lầm.

## Mở rộng tiếp theo

- Đồng bộ số liệu Metricool qua API chính thức khi chủ tài khoản có quyền server-to-server; có nhật ký lỗi và bản ghi NULL cho trường thiếu.
- Gắn nhãn nội dung có nguồn (chủ đề, thời gian, thử nghiệm) để so sánh kết quả theo nhóm mà không suy luận nhân quả thiếu đối chứng.
- Khi chương trình Affiliate được duyệt, thêm quy trình kiểm duyệt link và chứng từ, đối soát đơn/hoa hồng, theo dõi tỷ lệ chuyển đổi và quy tắc dừng thử nghiệm.
- Chỉ tăng mức tự động hóa sau khi kiểm chứng tác động; không tự mở quyền, không tạo tài khoản giả hoặc chi tiền.
