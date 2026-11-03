# Enna · Chuẩn bị tạo doanh thu (kiểm chứng ngày 03/11/2026)

**Trạng thái:** `pre_revenue`. Đã có mã vận hành, lịch đa kênh,
2 đề xuất Shopee KOC chờ duyệt, 3 hướng kinh doanh giả thuyết và bản mẫu
Enna Mini. **Không có tài khoản affiliate được xác nhận active, đơn hàng,
hoa hồng hay doanh thu tiền thực nhận.** Không đưa số tiền dự báo thành kết quả.

## Nguyên tắc vận hành

- Nội dung giữ vai trò chính: hữu ích, hài hước và đúng chất Đồ Hay Đi Làm.
- Đề xuất thương mại là nội dung **nháp**, không tự ghép sản phẩm/giá/đường
  dẫn tracking khi chưa có nhà cung cấp và thử nghiệm thật.
- Chỉ xét quảng cáo khi chủ sở hữu đã duyệt bằng chứng sản phẩm, kênh được
  phép, điều kiện công bố, giao hàng và chính sách nền tảng. Không tự liên
  hệ thương hiệu, tự ký hợp đồng, tự nhận thanh toán, tự đăng nội dung
  tài trợ hoặc tự đăng vào Community.
- Thử nghiệm giai đoạn đầu dùng mẫu nhỏ và quan sát thật; không mua
  follower, lượt thích hoặc tạo bình luận ảo.

## Ba tuyến doanh thu đang ở trạng thái giả thuyết

| Tuyến | Việc chuẩn bị được phép làm | Điều kiện chuyển bước |
|---|---|---|
| Shopee KOC / Affiliate đồ dùng làm việc | Nghiên cứu tiêu chí chọn sản phẩm, soạn bài dạng checklist, kiểm chứng tài liệu nguồn | Cá nhân chủ sở hữu đăng ký, được nhà cung cấp duyệt, xác minh sản phẩm và điều khoản cụ thể, có công bố quảng cáo phù hợp |
| Hợp tác thương hiệu | Lưu số liệu thật theo kênh, xác định tệp khán giả và định dạng hợp tác, viết media-kit nháp | Có insight nhiều ngày, nội dung đã chứng minh hiệu quả, chủ sở hữu duyệt đề xuất và đối tác hợp pháp |
| Sản phẩm số nhỏ cho dân văn phòng | Bản thử miễn phí `products/office-kit/index.html`, thử với người dùng thật và hỏi tính hữu ích | Có phản hồi nhu cầu, phạm vi sản phẩm rõ, chủ sở hữu xác nhận quyền lợi khách hàng và khâu thanh toán/pháp lý trước mở bán |

### Ưu tiên đầu tiên

Shopee công bố hình thức KOC Affiliate cho người không đủ ngưỡng KOL và
không bắt buộc có số follower tối thiểu như KOL; đó không đồng nghĩa
tài khoản hiện tại đã được xét duyệt. Mọi mức hoa hồng tùy điều khoản,
chưa được xác nhận cho bất kỳ sản phẩm cụ thể nào.

Nguồn Shopee:
- https://help.shopee.vn/portal/10/article/122944
- https://help.shopee.vn/portal/10/article/123083

### Công bố thương mại và luật áp dụng

Luật Quảng cáo sửa đổi có hiệu lực từ 01/01/2026. Người có ảnh hưởng
truyền tải quảng cáo có nghĩa vụ xác minh độ tin cậy bên quảng cáo, kiểm
tra tài liệu về sản phẩm và thông báo việc quảng cáo; không giới thiệu
sản phẩm chưa sử dụng hoặc chưa hiểu rõ. Nghị định 342/2025/NĐ-CP
áp dụng từ 15/02/2026. Cần kiểm tra yêu cầu mới nhất và cách áp dụng
vào từng hình thức trước khi công bố.

Nguồn chính phủ:
- https://vanban.chinhphu.vn/?classid=1&docid=214561&pageid=27160
- https://chinhphu.vn/?docid=216403&pageid=27160&typegroupid=4

Cách thông báo gợi ý (chỉ cho bài đã đủ điều kiện và có xác minh):
> *Đây là nội dung tiếp thị liên kết. Mình có thể nhận hoa hồng khi bạn
> mua hàng qua liên kết hợp lệ, không phát sinh phí cộng thêm từ mình.*

Với hợp tác tặng sản phẩm hoặc nhận tiền, cần khai báo quan hệ thương
mại đúng thực tế và sử dụng nhãn nền tảng tương ứng khi bắt buộc; chỉ
thêm thông báo văn bản không phải lúc nào cũng thay thế được nhãn.

## Dữ liệu và độ tin cậy

- `enna_monetization_tracks`: chính sách cấp phép, tình trạng chuẩn bị và
  bằng chứng; RLS riêng và service role.
- `affiliate_opportunities`: 2 bản nháp đang `pending`, **không phải
  cơ hội có hợp đồng**.
- `enna_revenue_receipts`: chỉ ghi nhận các khoản tiền thực nhận có
  chứng từ nhập từ chủ sở hữu hoặc sao kê đối soát; hiện 0 dòng.
- `affiliate_metrics`: báo cáo impressions/click/conversion/commission
  theo chứng từ nhà cung cấp khi có; không phải tiền đã nhận.
- `growth/monetization.py`: kiểm tra chỉ đọc, không bán hàng. Chạy trong
  workflow vận hành và workflow nghiên cứu affiliate, nhật ký thành công
  chỉ được ghi sau khi nguồn dữ liệu trả về hợp lệ.
- Dashboard công khai chỉ hiển thị trạng thái, số hạng mục và số bản chờ
  duyệt. **Không hiển thị doanh thu, thương lượng, chứng từ hoặc link riêng**.

## Các mốc kiểm chứng nội bộ, không phải doanh thu cam kết

**7 ngày đầu:** đọc số liệu thật và xét nội dung hữu ích có người xem;
chọn một đề xuất KOC kiểm tra tiêu chí sản phẩm; cho 5 người dùng thử
Enna Mini nếu chủ sở hữu chủ động mời và họ đồng ý.

**14 ngày:** đánh giá >=3/5 người thử nói công cụ hữu ích, >=2 người
muốn dùng lại; nếu không thì sửa sản phẩm, không ép bán. Mời người dùng
cho biết họ cần tính năng nào nhưng không thu dữ liệu nhạy cảm.

**Sau khi được duyệt chương trình/đối tác:** thử một nội dung thương
mại minh bạch có phân phối tự nhiên; các bài bình thường vẫn chiếm
đa số. Chỉ đo affiliate clicks/conversions từ xuất dữ liệu chính thức,
không quy tăng follower của cả trang cho riêng một bài.

Dừng nếu xảy ra khiếu nại, thông tin sản phẩm sai, tracking thiếu nguồn,
người dùng mất tin tưởng hoặc nội dung thương mại làm giảm chất lượng
kênh. Không tự mở bán nếu chưa có bằng chứng và quyền hợp lệ.
