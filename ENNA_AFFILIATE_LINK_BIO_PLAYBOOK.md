# Enna Affiliate × Link-in-bio Strategy — 03/11/2026

## Đánh giá hiện tại

**Có thể đăng ký Shopee KOC; chưa xác nhận được duyệt.** KOC Affiliate
không có ngưỡng follower của KOL, nhưng Shopee vẫn yêu cầu xét duyệt
định danh, phương tiện tiếp thị và tuân thủ nội dung. Tài khoản
`@dohay_dilam` có snapshot follower gần nhất **3 vào 02/11/2026** theo
Metricool; dữ liệu follower 03/11 chưa đủ. Mục tiêu 1.000 follower không
phải điều kiện tối thiểu chung để nộp Shopee KOC.

Threads **không được nêu cụ thể** trong danh sách ngưỡng KOL của Shopee;
không suy ra quyền sử dụng Threads làm nguồn thương mại đã được duyệt.
Fanpage Facebook và Instagram đã kết nối; khai báo kênh sở hữu chính
chủ, sau đó hỏi Shopee có cần thêm URL Threads và trang link hub dưới
danh mục phương tiện tiếp thị không. Không đăng ký tự động.

Official:
- https://help.shopee.vn/portal/10/article/122944
- https://help.shopee.vn/portal/10/article/123083
- https://help.shopee.vn/portal/10/article/152864

## Hướng doanh thu phù hợp định hướng Đồ Hay Đi Làm

Ưu tiên nhu cầu thực, không xếp hạng theo hoa hồng chưa xác minh:
1. Kẹp dây cáp, giữ dây sạc — câu chuyện 'dây sạc mất tích'.
2. Sổ checklist / planner — gắn với 'họp 15 phút và 3 deadline'.
3. Túi phụ kiện công sở — trong balô dân văn phòng.
4. Giá đỡ laptop gập — chỉ nhận xét chất lượng sau thử nghiệm thực tế.
5. Khay bàn; giá điện thoại — đánh giá sản phẩm có thực sự hữu ích.
6. Đèn bàn và pin dự phòng — xem xét rủi ro điện/nguồn gốc trước.

**Điểm 0–100 trong bảng là độ ưu tiên biên tập giả thuyết, KHÔNG là
giá, chất lượng, xác suất bán được hay hoa hồng.** Điểm:
brand_fit×6 + reader_value×5 + story_potential×4 +
affordability×3 + seller_confidence×2. Seller confidence ban đầu = 0,
chưa có SKU và nhà bán nào được xác minh.

Bảng nguồn: `enna_affiliate_candidates` (8 rows, private RLS) và
`enna_affiliate_tests` (vị trí link, thử nghiệm, chứng cứ nguồn).
Bản Excel độc lập cung cấp 5 tab cho người sở hữu sử dụng ngoại tuyến.

## Hai phương án gắn link (chưa triển khai thương mại)

### A. Một bình luận có liên kết dưới bài chính chủ

- Threads API chính thức hỗ trợ reply bằng `reply_to_id`; về mặt nền
  tảng có thể đăng phản hồi chứa liên kết văn bản, cần test tài khoản
  thực tế và giao diện trước khi khẳng định mọi link đều nhấp được.
- Chỉ dưới **bài do `@dohay_dilam` sở hữu**, phải tương quan nội dung,
  chỉ một bình luận nếu hữu ích, không tự rải links vào bài người lạ,
  cộng đồng, hoặc nhiều bài hàng loạt.
- Không "giấu" thông báo trong bình luận: bài chính cần thông báo rõ
  khi quảng cáo/affiliate; sử dụng nhãn quan hệ thương mại nếu yêu cầu.
- Shopee cảnh báo link trơ trọi/đăng lặp lại; trong trường hợp link
  bị nền tảng hạn chế có hướng dẫn riêng về **mã sản phẩm**, không
  tự suy rằng mã đó đảm bảo ghi nhận hoa hồng trên Threads.
- Kịch bản chỉ ở trạng thái `planned` cho tới khi tài khoản publisher,
  sản phẩm, link, kênh quảng bá, công bố và duyệt của chủ sở hữu đạt
  đủ điều kiện.

Nguồn:
- https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- https://junction.cj.com/article/how-to-share-affiliate-links-on-social-media
- https://help.shopee.vn/portal/10/article/153028-C%C3%A1c%20b%E1%BA%A1n%20KOL%2FKOC%20n%C3%AAn%20l%C3%A0m%20g%C3%AC%20n%E1%BA%BFu%201%20s%E1%BB%91%20n%E1%BB%81n%20t%E1%BA%A3ng%20m%E1%BA%A1ng%20x%C3%A3%20h%E1%BB%99i%20kh%C3%B4ng%20cho%20ph%C3%A9p%20%C4%91%C4%83ng%20tr%E1%BB%B1c%20ti%E1%BA%BFp%201%20link%20ti%E1%BA%BFp%20th%E1%BB%8B%20li%C3%AAn%20k%E1%BA%BFt%3F
- https://help.shopee.vn/portal/10/article/206670

### B. Trang bio tổng (đề xuất ưu tiên)

- Threads hỗ trợ **tối đa 5 link hồ sơ**, có Insights về liên kết.
  Dùng một URL sở hữu chính chủ để cập nhật danh mục tập trung và
  phân phối cho Threads/Instagram/Facebook.
- Trang bản thử: `docs/enna/links/index.html` được GitHub Pages build.
  URL dự kiến:
  `https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/links/`
- Có danh mục góc làm việc, đồ đi làm, mẹo công sở, cú đêm;
  search/filter hoạt động trong trình duyệt.
- Đã xuất bản bộ mẫu **Enna Mini miễn phí** tại `docs/enna/kit/`.
- **`approved.json` đang là danh sách rỗng**, không có link Affiliate.
  Trang chỉ hiển thị link thương mại khi chủ sở hữu phát hành
  dữ liệu duyệt đã được kiểm tra, kèm thông báo có hoa hồng.
- Trang không theo dõi cookies, không tự chuyển hướng, không
  thu email, không gắn mã theo dõi ẩn. Không thể tự coi page views
  là clicks của nhà cung cấp.
- Trước khi đặt link Affiliate vào hub, chủ sở hữu cần hỏi Shopee
  xác nhận URL trang điều hướng có được đăng ký như phương tiện
  tiếp thị hay không; không làm redirect tự động / cloaking.

Nguồn:
- https://about.fb.com/news/2025/03/new-threads-features-more-personalized-experience-you-control/
- https://help.shopee.vn/portal/10/article/122944

## Đo hiệu quả không bịa số liệu

Theo thứ tự: `impressions bài` → `lượt bấm bio theo Threads Insights`
→ `lượt xem trang bio (chưa có tracking)` →
`clicks provider` → `orders provider` →
`commission provider được đối soát` →
`tiền thực nhận có chứng từ`.

Tại thời điểm tạo **0 link hợp lệ, 0 thử nghiệm đang hoạt động, 0 đơn,
0 commission**. Ba kịch bản private hiện là kế hoạch, không phải post
đã phát hành. Không gán toàn bộ lượt tăng follower cho link Affiliate.

Thử nghiệm sau khi được duyệt:
- Đầu tiên thử bio miễn phí không có link bán để xem người dùng có
  quan tâm đến tài nguyên nào.
- Sau khi Shopee duyệt: thử một loại nội dung phù hợp với một SKU
  đã kiểm tra, có công bố minh bạch; không công kích sản phẩm cạnh tranh.
- Nếu có lượt click provider thực, thử một bình luận liên quan dưới
  bài chính chủ, so sánh theo tuần, không spam, không coi tương quan
  là nguyên nhân.
- Giữ đa số bài có giá trị miễn phí, không thay Enna thành trang rao bán.

## Quyền và hành động của chủ sở hữu

**Bước duy nhất phải làm thủ công ngay nếu muốn:**
Đăng ký Shopee KOC chính chủ tại https://affiliate.shopee.vn, khai báo
mạng xã hội sở hữu và hỏi về link hub/Threads trước khi kiếm tiền.
Bản bio hiện hữu có thể gắn lên hồ sơ dưới dạng **trang tài nguyên miễn
phí**; chưa có giao diện sửa bio chính thức qua kết nối hiện tại nên
chủ sở hữu phải sửa trong app Threads/Instagram. Không thay đổi profile
bằng cách vòng qua Meta API.

Chỉ báo đã kiếm tiền khi có xuất dữ liệu nguồn và xác nhận thực nhận.
