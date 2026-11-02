# Enna v2.1 — Đổi tên và nâng cấp vận hành thực tế

Ngày phát hành: 02/11/2026 · Asia/Ho_Chi_Minh  
Tên Agent: **Enna** · Thương hiệu Threads: **Đồ Hay Đi Làm** / `@dohay_dilam`

## Việc đã triển khai

**Đổi tên không phá liên kết:**
- Các workflow hiện có hiển thị tên Enna (Research, Threads, Growth Radar, Affiliate Research, OAuth kiểm tra, xuất bản website, CI).
- Cập nhật giao diện trang cấp Meta OAuth, trang điều hành và GitHub Pages; báo cáo nghiên cứu dùng tên Enna.
- **Không đổi** repository `roxthang0710-hash/autonomous-one-hybrid`, địa chỉ Supabase, Callback URL, `brand_key`, Threads username, bất kỳ token hay GitHub Secret nào. Đây là hệ thống kỹ thuật hiện có, không phải thay đổi tài khoản mạng xã hội.

**Nâng cấp thực hành và bảo vệ:**
1. Tạo `enna.py` với báo cáo điều hành đọc dữ liệu thật: tài khoản, token, 15 bài Metricool, bài đang chờ đăng, phản hồi hôm nay, trạng thái tìm kiếm Threads công khai, độ trễ nghiên cứu, Shopee chưa duyệt, không suy đoán follow và doanh thu.
2. Tích hợp báo cáo Enna vào cả workflow Threads và Growth Radar. Báo cáo tự động xuất trong GitHub Actions Summary, không chứa nội dung bài riêng tư hoặc token.
3. Lịch Threads Nurture mở rộng **09:45, 12:45, 18:45 giờ Việt Nam**, thêm hai lượt dự phòng khi GitHub Actions chậm hoặc lượt đầu không chạy. Database bảo đảm mỗi bài chỉ được claim một lần; nếu Meta trả kết quả mơ hồ, bài ở trạng thái `uncertain`, tuyệt đối không thử gửi lặp lại.
4. Enna biên tập các bài Threads mới theo phong cách trẻ trung, dí dỏm vừa phải; không giả làm người mua hàng hay cố gượng ép tiếng lóng. Lọc bài gần trùng trong 60 bài gần nhất. Các bài hiện đang ở hàng đợi **không bị tự ý sửa**.
5. **Sửa nguồn dữ liệu học hiệu quả thực tế:** `threads_metrics` bây giờ cho phép NULL với năm chỉ số, và bỏ `DEFAULT 0`. Thiếu chỉ số Meta đồng nghĩa **chưa có số liệu**, không phải bằng 0. `threads/insights.py` lưu từng chỉ số Meta có thật từ `values` hoặc `total_value`, không yêu cầu đủ cả năm mục. Dữ liệu/kiểm soát quyền cũ được giữ.
6. Kiểm thử bổ sung cho báo cáo Enna, công cụ bảo vệ trùng nội dung, partial insights, Groq, SQL, webhook, OAuth.

## Những giới hạn vẫn còn

- Token Meta dài hạn còn hiệu lực và chủ sở hữu đã bật `enable_replies=true`, nhưng truy vấn Threads keyword qua API có thể rỗng đến khi **Meta App Review phê duyệt public search**. Không sử dụng trình cào giao diện hay giả kết quả tìm kiếm. Số bình luận thực tế vẫn **0** theo kiểm tra đầu phiên.
- Chưa có bằng chứng bài AI đã xuất bản (15 bài Metricool là `scheduled_external`, bài Enna là `queued`). Có thể kiểm tra lại sau 03/11 đối với Metricool và sau 18/11 đối với Enna.
- Shopee Affiliate chưa xác nhận được tài khoản nhà phát hành được duyệt và chưa có liên kết theo dõi/hoa hồng xác thực. Enna sẽ không báo doanh thu giả hay tự lập tài khoản thay chủ sở hữu.
- GitHub Actions cron là lịch **best effort**, không cam kết chạy đúng giây/phút. Các lượt dự phòng giảm rủi ro nhưng không thay thế hạ tầng scheduler chuyên dụng.

## Liên kết

- [Enna — trang kết nối Threads](https://roxthang0710-hash.github.io/autonomous-one-hybrid/oauth/)
- [Các workflow Enna](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions)
- [Supabase: tình trạng thực tế](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor)
- [Meta App Review](https://developers.facebook.com/apps/)

**Nguyên tắc:** Enna hoạt động liên tục trong giới hạn quyền đã cấp; không tự vượt hạn mức, không gây tương tác giả, không chi tiền, không che giấu lỗi hoặc đặt tên khác cho người dùng Threads.

## Xác minh vận hành thực tế sau triển khai — 17:48 giờ Việt Nam, 02/11/2026

- [Enna Threads run 41431199562](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41431199562) **SUCCESS**: bộ biên tập đã phát hiện `near_duplicate_generated` và không đưa bài trùng vào lịch. Báo cáo Enna được tạo thành công, OAuth hợp lệ.
- Từ kết quả đó, Enna đã được nâng cấp cơ chế thử tối đa **hai góc nội dung khác** sau khi AI trả bài gần trùng hoặc không an toàn. Bounded retry không gửi lại các bài đã đăng; không gắn nhầm nguồn trend vào bài fallback.
- [Enna Threads run 41431701964](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41431701964) **SUCCESS** sau sửa: `editor=created_one`, hàng đợi **4 bài Enna** (trước đó 3); `scheduled_external=15` từ Metricool, `posted=0`, `publisher=no_due_post`. Dữ liệu đúng hạn và không đăng sớm.
- [Enna Growth run 41431269105](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41431269105) **SUCCESS**: `threads_discovery=empty_keyword_results`, `Growth engagement=no_eligible_replies`, không tạo bình luận giả. Meta App Review vẫn cần kiểm tra.
- [Enna CI 41431643097](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41431643097) **SUCCESS**, bao gồm dữ liệu insight từng phần, phát hiện bài trùng và kiểm tra an toàn người dùng. Không nên hiểu PASS unit test là đã kiếm tiền hoặc Meta App Review được phê duyệt.

**Kết luận:** Enna đã hoạt động thực tế dưới tên mới, tự sửa được tình huống bài gần trùng và tự ghi sức khỏe hệ thống. Chưa có bình luận công khai, chưa có bài AI nào đến hạn xuất bản, chưa có bằng chứng doanh thu Affiliate.
