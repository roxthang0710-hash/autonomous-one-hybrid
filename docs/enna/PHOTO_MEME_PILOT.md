# Enna Real Photo Meme Lab — Pilot 05/11/2026

## Chọn ảnh thật có nguồn
3 ảnh CC0 đã đối chiếu trực tiếp trên trang Wikimedia Commons:
1. [Cat Sleeping on Keyboard](https://commons.wikimedia.org/wiki/File:Cat_Sleeping_on_Keyboard.jpg) — tác giả Panini!.
2. [Keyboard close-up](https://commons.wikimedia.org/wiki/File:Keyboard_close-up.jpg) — tác giả Jiafei Slay Queen.
3. [Lack of paper documents](https://commons.wikimedia.org/wiki/File:Lack_of_paper_documents.jpg) — tác giả Ірина Бучнєва.

## Bản thử
- Layout A: ảnh mèo thật + hội thoại công sở hài.
- Layout B: ảnh bàn phím thật + câu chuyện về bấm Ctrl+S lần thứ 17.
- Layout C: ghép hai ảnh thật + đối chiếu 8:30 và 16:59.
- Đầu ra: 3 PNG 1080×1350, và 3 tệp .rights.json ghi nguồn, tác giả, giấy phép và hash.
- Quy trình: GitHub Actions > **Enna — Authentic Photo Meme Pilot** > artifact **enna-photo-memes-preview**.
- Chạy thủ công: `python -m scripts.enna_photo_memes --render --output photo-meme-pilot`.

## Giới hạn bắt buộc
Tự tải chỉ ảnh được tuyển chọn từ Wikimedia Commons và kiểm tra lại giấy phép CC0 bằng API; không cào mạng xã hội, không sử dụng meme bên thứ ba không rõ quyền. Không tạo cảnh mô phỏng người thật làm điều xấu, không gán lời nói hoặc trải nghiệm thật cho người trong ảnh.

Bản thử là **DRAFT**, không tự đăng Meta, không thay lịch Metricool, không tải ảnh lên public Storage. Chỉ xuất bản sau khi duyệt ảnh, chữ tiếng Việt, chất lượng đùa, bố cục, tính phù hợp thương hiệu và quyền hình ảnh.

## Tiêu chí đánh giá nếu sau đó được đăng thử nghiệm
So sánh với nhóm thẻ minh họa cũ ở các khung giờ tương tự: lượt xem bài thực tế, chia sẻ, lưu, phản hồi tự nhiên, lượt xem hồ sơ và tăng follower. Không suy luận tác động nhân quả từ một vài bài.
