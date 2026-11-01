# Affiliate Research v1.5 — Hướng dẫn vận hành

Phiên bản này **không phải hệ thống đã kiếm tiền**. Nó sử dụng Groq để chuẩn bị bản nháp nội dung tiếp thị liên kết, lưu Supabase cho chủ sở hữu xem và duyệt. Mọi tỷ lệ hoa hồng, điều kiện sản phẩm, tài khoản Publisher, sản phẩm cụ thể đều **chưa được xác minh**.

## Kiến trúc
- Workflow: [Affiliate Research](../.github/workflows/affiliate-research.yml), thứ Ba và thứ Sáu lúc 09:30 giờ Việt Nam (best effort), hoặc dùng GitHub Issue của chủ sở hữu.
- Model: `openai/gpt-oss-20b` (Groq), không phát sinh API trả phí bắt buộc trong quota miễn phí.
- Data: `affiliate_programs`, `affiliate_runs`, `affiliate_opportunities`, `affiliate_metrics`, và view `affiliate_review_dashboard`.
- Hạn mức: tối đa **3 lượt nghiên cứu/tuần** (bao gồm chạy tay), ngừng thêm ý tưởng nếu có **6 bản đang chờ duyệt**; không tự nâng hạn mức.

## Tự nghiên cứu & nhận ý tưởng ngay
1. [Tạo GitHub Issue](https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/new), với tiêu đề `affiliate: phụ kiện du lịch thiết thực`. Chỉ issue do chủ sở hữu repo tạo và có tiền tố `affiliate:` mới chạy.
2. Vào [Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions) và mở workflow **Autonomous One — Affiliate Research** để theo dõi run.
3. Mở [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor), tìm `affiliate_opportunities`, xem cột `proposal` (bản nháp) và `screening_notes` (những điều cần xác minh).
4. `review_status = pending` là mặc định. Nếu quyết định thử nghiệm ý tưởng, chủ sở hữu có thể chuyển thành `approved` trong Table Editor (chỉ là ghi nhận quyết định, **không tự đăng bài**).

Các GitHub Issue trong repo hiện có thể công khai: **đừng đưa token, số điện thoại, dữ liệu cá nhân, chiến lược bí mật hoặc thông tin ngân hàng vào Issue**.

## Chương trình và điều kiện
- **Shopee KOC**: [Chương trình](https://shopee.vn/affiliate/), [FAQ](https://help.shopee.vn/portal/4/article/91992). Tạo liên kết *chỉ sau khi đăng ký được duyệt*.
- **ACCESSTRADE Publisher**: [Đăng ký](https://accesstrade.vn/access-affiliate-publisher/), [quy trình](https://help.accesstrade.vn/knowledgebase/quy-trinh-co-ban/). Mỗi chiến dịch có quy tắc riêng.
- **TikTok Shop Affiliate**: [quy định tài khoản Việt Nam](https://seller-vn.tiktok.com/university/essay?knowledge_id=6837793229817601). Yêu cầu và quyền khác nhau theo loại tài khoản.

Đây là **danh mục chương trình cần kiểm tra**; không có bằng chứng về việc tài khoản cá nhân được chấp thuận, không có API affiliate riêng được kết nối và không có tỷ lệ hoa hồng được xác minh. Dữ liệu chương trình được rà soát ngày 02/11/2026, cần cập nhật khi điều khoản thay đổi.

## Các chỉ số sau khi chủ sở hữu đăng nội dung thực tế
`affiliate_metrics` lưu `impressions`, `clicks`, `conversions`, `confirmed_commission_vnd`, `evidence_url`. Không tự phát sinh doanh thu hay dữ liệu clicks. **Hoa hồng thực nhận phải có bằng chứng đối soát từ nhà cung cấp**.

Ví dụ báo cáo từ SQL Editor (không đăng lên GitHub Actions Public):

```sql
select program_name,niche,title,screening_score,review_status,
       impressions,clicks,conversions,confirmed_commission_vnd
from public.affiliate_review_dashboard
order by created_at desc limit 20;
```

`screening_score` là mức độ ưu tiên nghiên cứu, **không phải xác suất có doanh thu**.

## Quyền hạn an toàn
- Không tự đăng nhập tài khoản Affiliate, xác minh danh tính, tạo link tracking, xuất bản, nhắn tin, spam nhóm, chi tiền hay thao tác tài chính.
- Mọi bản nháp đều có `link_placeholder`, `affiliate_link = null`, `draft_status = needs_owner_review`.
- Không mặc định có quyền đọc dữ liệu từ browser; tables bật RLS, viewer/public không có policy.
- Token Groq và Supabase tồn tại trong GitHub Actions Secrets, không được ghi vào mã nguồn hoặc logs.

## Nâng cấp kế tiếp
Sau khi người dùng có tài khoản Publisher được duyệt, xây dựng import bảng sản phẩm được phép sử dụng, đối soát điều kiện chiến dịch và quy trình duyệt/đăng nội dung trên kênh do người dùng sở hữu. Không xây phần tự đăng công khai trước khi quyền và chính sách được xác minh.
