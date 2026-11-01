# Autonomous One — Hybrid Cloud Agent v1.0

Agent nghiên cứu cơ hội kinh doanh chạy trên **GitHub Actions + Groq + Supabase**, không cần máy tính cá nhân bật thường xuyên.

**Trạng thái:** phiên bản thử nghiệm **research & proposal only**. Agent không có quyền chi tiền, mua quảng cáo, gửi tin nhắn cho khách hàng, phát hành sản phẩm hay tự sửa code.

## Hạ tầng
- GitHub Actions: lịch 08:15, 12:15, 16:15, 20:15 (Asia/Ho_Chi_Minh, UTC+7), chạy thủ công hoặc repository_dispatch.
- Groq: mô hình `openai/gpt-oss-20b`, tạo đề xuất theo JSON Schema.
- Supabase: dự án `autonomous-one` (Singapore), tables `agent_events`, `agent_runs`, `agent_proposals`; RPC `claim_agent_event`.
- Edge Function `agent-webhook`: nhận một sự kiện đã xác thực và kích hoạt GitHub; nếu dispatch không thành công, sự kiện vẫn trong queue để chu kỳ tiếp theo xử lý.

## Cấu hình bắt buộc

Trong [GitHub Actions Secrets](https://github.com/roxthang0710-hash/autonomous-one-hybrid/settings/secrets/actions) tạo:

| Secret | Giá trị |
|---|---|
| `SUPABASE_URL` | `https://gjdvdohylvsauphhkutw.supabase.co` |
| `DB_SERVICE_KEY` | Supabase secret API key (chỉ ở backend) |
| `GROQ_API_KEY` | Groq API key còn hiệu lực |

Không thêm secret vào commit, log hoặc file `.env`. Khi chưa có đủ ba secrets, lịch chạy vẫn hoạt động nhưng bỏ qua bước gọi AI.

Để nhận sự kiện qua [Supabase Edge Function Secrets](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/functions), tạo:
- `WEBHOOK_SECRET`: một chuỗi ngẫu nhiên ít nhất 32 ký tự.
- `DB_SERVICE_KEY`: key backend tương ứng.
- `GITHUB_DISPATCH_TOKEN`: fine-grained GitHub PAT giới hạn ở repository này, Contents: Read and write.
- `GITHUB_REPOSITORY_NAME`: `roxthang0710-hash/autonomous-one-hybrid`.

`SUPABASE_URL` do nền tảng Supabase Edge Functions cung cấp mặc định.

## Chạy thử
1. Vào [Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions), chọn **Autonomous One — Hybrid Agent** → **Run workflow**; có thể nhập chủ đề `marketing reporting pain points`.
2. Mở Supabase Table Editor và kiểm tra `agent_runs` có trạng thái `success`, `agent_proposals` có một bản ghi với `approval_status = pending`.
3. Chạy unit test: `python -m unittest discover -s tests -v`.
4. Theo dõi thời gian chạy GitHub Actions và hạn mức Groq miễn phí; workflow không tự tăng phí.

## Kích hoạt bằng sự kiện
Gửi POST đến `https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/agent-webhook`.

- Header `x-agent-secret`: WEBHOOK_SECRET đã cấu hình.
- JSON body ví dụ:

```json
{"request_id":"demo-20261101-001","kind":"research_request","topic":"small business reporting automation"}
```

Mỗi yêu cầu phải có `request_id` mới. Edge Function được triển khai với `verify_jwt=false` nhưng tự kiểm tra header bí mật. Chưa cấu hình `WEBHOOK_SECRET` sẽ trả HTTP 401.

## Giới hạn hiện tại
- Chưa tự kiếm tiền, chưa có website dashboard và chưa có bộ nhớ dạng vector.
- Nguồn nghiên cứu v1 lấy tiêu đề công khai qua Hacker News Algolia; không được coi là xác minh nhu cầu thị trường.
- Các đề xuất chỉ để chủ sở hữu xem xét. Thay đổi `approval_status` không tự kích hoạt hành động kinh doanh.
- GitHub Actions schedule là best-effort. Hạn mức Groq và Supabase Free có thể thay đổi.

**Nguyên tắc vận hành:** không tự chi tiền, không tự nâng quyền, không thực hiện hành động công khai trước khi được phê duyệt.
