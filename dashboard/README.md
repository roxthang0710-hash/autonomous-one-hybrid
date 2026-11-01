# Báo cáo & đánh giá ý tưởng v1.1

## Xem bảng điều khiển nội bộ
- Mở [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor) và chọn view `agent_review_dashboard` hoặc bảng `agent_evaluations`.
- Mở [SQL Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/sql/new), sao chép lần lượt các câu truy vấn từ `dashboard/queries.sql` để xem chỉ số, danh sách chờ duyệt và thử nghiệm.
- Sau mỗi lượt GitHub Actions, mở chi tiết run và xem phần **Summary**. Vì repository hiện là Public, Summary chỉ hiển thị thống kê tổng hợp, không hiển thị nội dung ý tưởng hoặc số tiền cụ thể.

## Cơ chế Agent
1. Tạo đề xuất mới qua Groq.
2. Tự chấm 5 tiêu chí về ngân sách, mục tiêu đo lường, nguồn nghiên cứu, độ chi tiết và rủi ro.
3. Trừ điểm khi ý tưởng tương tự các đề xuất trước.
4. Ghi vào `agent_evaluations`; để `agent_proposals.approval_status='pending'`.
5. Lưu báo cáo tổng hợp trong GitHub Actions run Summary.

**Điểm đánh giá (0–100) chỉ đo độ đầy đủ của kế hoạch**, không phải xác suất thành công hay xác minh nhu cầu.

## Cách duyệt và ghi nhận kết quả
1. Vào Supabase Table Editor > `agent_proposals` > chỉnh `approval_status` thành `approved` hoặc `rejected`. Việc phê duyệt này **chỉ ghi nhận ý kiến**, không tự kích hoạt xuất bản hoặc giao dịch.
2. Khi đã có thử nghiệm thực tế do bạn giám sát, thêm bản ghi mới vào `agent_experiments` với `proposal_id`, `status`, các tín hiệu thực và chi phí/doanh thu *đã xác minh*.
3. Cột `evidence_url` và `owner_notes` giúp lưu nguồn chứng minh và bài học.
4. Số liệu trong bảng là do chủ sở hữu nhập, không phải dữ liệu ngân hàng được hệ thống tự xác minh.

## Giới hạn
Đây là *monitoring dashboard v1.1* sử dụng giao diện Supabase và GitHub Actions. Chưa có website dashboard đăng nhập riêng hoặc tự thực thi ý tưởng đã duyệt. Các bảng và view không cấp quyền xem công khai (RLS).
