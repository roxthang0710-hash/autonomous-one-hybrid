# Soát Lịch — kế hoạch kiểm chứng doanh thu

Trạng thái: bản dùng thử riêng; chưa mở bán, chưa liên hệ khách hàng, chưa thu tiền.

## Lựa chọn sản phẩm

Khách hàng giả định: người quản lý nội dung tại khách sạn/nhà hàng nhỏ, làm lịch bằng bảng tính và cần chuyển lịch cho người duyệt.

Công việc: rà soát lịch trước khi duyệt, đối chiếu lỗi từng dòng và xuất danh sách cần sửa. Không tự đăng bài và không yêu cầu kết nối tài khoản mạng xã hội. Dữ liệu CSV được xử lý tại trình duyệt, không gửi đến máy chủ.

Các công cụ lập lịch tổng quát đã có trên thị trường: Buffer có trình lập lịch và lịch nội dung (https://buffer.com/publish). Vì vậy hướng thử nghiệm ở đây là quy trình rà soát theo từng đơn vị và hỗ trợ thiết lập, không giả định rằng thêm một lịch nội dung chung sẽ đủ để bán. Chưa có bằng chứng khách hàng sẵn sàng trả tiền cho Soát Lịch.

## Gói thử nghiệm để chủ sở hữu duyệt

Giá giả định: 490.000 VNĐ một lần cho một đơn vị. Đây là giả thuyết giá, chưa công bố và chưa tạo đơn hàng.

Phạm vi: chuẩn hóa một mẫu CSV; rà soát một lịch tối đa 30 bài; hướng dẫn sử dụng 30 phút; một vòng điều chỉnh quy tắc/mẫu. Tổng công thực hiện mục tiêu không quá 2 giờ. Không bao gồm viết lại toàn bộ nội dung, thiết kế hình ảnh, đăng bài hoặc cam kết doanh số. Chủ sở hữu cần xác định nghĩa vụ hóa đơn/thuế và điều kiện dịch vụ trước khi mở bán; chưa có tích hợp thu tiền.

Gói đầu tiên bán công việc thiết lập và hỗ trợ cụ thể. Không thu phí chỉ vì sử dụng các quy tắc kiểm tra cơ bản miễn phí. Chỉ cân nhắc phí định kỳ sau khi người dùng quay lại dùng ít nhất hai kỳ lập lịch.

## Thử nghiệm sau khi được duyệt tiếp cận khách hàng

1. Chọn 5 người quản lý nội dung phù hợp, được chủ sở hữu xác định và duyệt liên hệ.
2. Cho từng người kiểm tra một lịch đã loại dữ liệu nhạy cảm; ghi thời gian rà soát thủ công và thời gian dùng công cụ trên các tập bài tương đương.
3. Ghi lỗi thật người dùng xác nhận, lỗi cảnh báo nhầm, khó khăn khi chuyển CSV; không tính dữ liệu mẫu là tín hiệu.
4. Hỏi trực tiếp liệu họ có đồng ý mua gói 490.000 VNĐ với phạm vi đã nêu. Đồng ý dùng miễn phí không được ghi thành ý định mua.
5. Chỉ báo đã có doanh thu sau khi chủ sở hữu duyệt giao dịch và xác nhận tiền thực nhận; lời hứa, hóa đơn chưa trả và dự báo đều không phải doanh thu.

Tiêu chí quyết định nội bộ (chưa được kiểm chứng): ít nhất 3/5 người hoàn tất, 2 người muốn dùng lại, 2 người nêu ý định mua với giá cụ thể. Nếu không ai muốn trả tiền, phỏng vấn nguyên nhân trước khi thêm tính năng. Nếu phần lớn vướng CSV, ưu tiên nhập trực tiếp từ bảng tính trước tính năng AI. Nếu phát hiện lỗi đã có sẵn trong quy trình của họ, chuyển sang vấn đề khác.

## Dữ liệu cần ghi

Mỗi lượt thử: mã người thử (không cần tên/email trong repository), ngày thử, số bài, phút rà soát trước/sau, số lỗi được xác nhận, số cảnh báo nhầm, có muốn dùng lại, giá được đưa ra, câu trả lời về ý định mua, liên kết bằng chứng được phép lưu. Không đăng lịch hoặc phản hồi riêng của khách hàng lên repository công khai.

Supabase `agent_experiments` đã có bản ghi `Soat Lich pilot v1`, trạng thái proposed, observed_signals=0, revenue_received_vnd=0. Chỉ cập nhật tổng hợp sau khi có bằng chứng thực. Số lượt chạy mẫu trong trình duyệt không phải số khách hàng.

## Kiểm thử và giới hạn

12 kiểm thử Node bao phủ CSV có ngoặc kép/dấu phẩy/xuống dòng, ngày nhuận, trùng theo đơn vị/kênh, hạn ưu đãi, dữ liệu thiếu và vô hiệu hóa công thức khi xuất CSV. Kiểm thử trình duyệt: mẫu 4 bài có 3 lỗi quy tắc và 2 cảnh báo, đúng kỳ vọng.

Chỉ hỗ trợ CSV UTF-8 theo tên cột mẫu; 2 MB/1.000 bài. Không kiểm tra tính đúng của giá/hotline/thương hiệu; không sửa bài tự động; không kết nối Google Sheets; không suy luận chất lượng nội dung bằng mô hình AI. Không lưu lịch khi tải lại trang. Quyền truy cập Site hiện chỉ dành cho chủ sở hữu; cần duyệt phát hành công khai trước khi gửi cho người thử.
