# Autonomous One — Hybrid Cloud Agent v1.2

AI Agent nghiên cứu cơ hội kinh doanh chạy trên GitHub Actions, Groq và Supabase. **Đã kiểm thử thành công trên Cloud** với cả lịch kích hoạt nội bộ và sự kiện GitHub Issues.

**Quyền hạn hiện tại:** research / evaluate / report only. Agent **không tự chi tiền, mua quảng cáo, gửi khách hàng, phát hành sản phẩm hoặc tự sửa code**.

## Trạng thái hệ thống
- **GitHub Actions:** theo lịch 08:15 / 12:15 / 16:15 / 20:15 giờ Việt Nam (best effort), chạy thủ công và nhận sự kiện.
- **Groq:** `openai/gpt-oss-20b`; lấy ý tưởng có cấu trúc (JSON Schema).
- **Supabase:** project `autonomous-one`, region Singapore; bảng `agent_events`, `agent_runs`, `agent_proposals`, `agent_evaluations`, `agent_experiments`.
- **Evaluations:** chấm mức độ đầy đủ của kế hoạch theo 5 tiêu chí, nhận diện ý tưởng tiêu đề tương tự; **không phải dự đoán xác suất kiếm tiền**.
- **Planner:** chọn chủ đề ít nghiên cứu; tạm dừng tạo đề xuất theo lịch nếu đã có **8 đề xuất chờ duyệt** (sự kiện do chủ sở hữu tạo vẫn có thể đưa vào hàng đợi).
- **Dashboard nội bộ:** Supabase Table Editor và GitHub Actions Run Summary; không cần xuất bản dữ liệu ra ngoài.
- **Webhook nâng cao:** Supabase Edge Function `agent-webhook` đã triển khai nhưng cần secret riêng để sử dụng từ dịch vụ bên ngoài.

## Cấu hình Secrets cho GitHub
Đã thiết lập cho repo này tại [Settings → Secrets → Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/settings/secrets/actions):
- `SUPABASE_URL`: `https://gjdvdohylvsauphhkutw.supabase.co`
- `DB_SERVICE_KEY`: Supabase server secret (không commit)
- `GROQ_API_KEY`: Groq API key (không commit)

Không đưa secret vào file, issue, commit hay log. Nếu thiếu secret, job bỏ qua bước gọi AI.

## Sử dụng Agent ngay (không cần thêm key)
### Cách 1 — GitHub Issue
1. Truy cập [New issue](https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/new).
2. **Chủ sở hữu repo** tạo issue có tiêu đề bắt đầu bằng `agent:`, ví dụ:
   `agent: zero-cost marketing analytics tool for small hotels`.
3. GitHub Actions tự nhận sự kiện, ghi một nhiệm vụ vào `agent_events`, thực hiện nghiên cứu và lưu đề xuất `agent_proposals` cùng điểm đánh giá `agent_evaluations`.
4. Xem kết quả trong [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor). Ghi chú: ticket trên GitHub có thể hiển thị công khai nếu repo đang Public.

Issue không do chủ sở hữu tạo hoặc thiếu tiền tố `agent:` **không được chạy job Agent**. Nếu vượt giới hạn lượt chạy, sự kiện đã được lưu và chờ chu kỳ sau.

### Cách 2 — Run workflow
Vào [Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions), chọn **Autonomous One — Hybrid Agent → Run workflow**, nhập `topic` tùy ý.

### Cách 3 — Tự chạy theo lịch
Agent tự chạy bốn lần mỗi ngày cho đến khi đạt giới hạn 8 đề xuất đang chờ chủ sở hữu phê duyệt. Khi backlog đầy, workflow vẫn chạy nhưng tránh gọi Groq không cần thiết.

## Theo dõi
- [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor): `agent_review_dashboard`, `agent_proposals`, `agent_evaluations`, `agent_experiments`, `agent_events`, `agent_runs`.
- [GitHub Actions](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions): mở một run để xem các bước và Summary thống kê (không công khai nội dung kinh doanh).
- [Các câu truy vấn báo cáo](dashboard/queries.sql) và [hướng dẫn duyệt ý tưởng](dashboard/README.md).
- `approval_status = approved` chỉ ghi nhận việc duyệt ý tưởng; **không kích hoạt một hoạt động kinh doanh hay chi tiền**.

## Webhook dành cho hệ thống ngoài (chưa cấu hình xong)
Để gửi sự kiện từ dịch vụ khác, cấu hình trong **Supabase Edge Function Secrets**:
- `WEBHOOK_SECRET`: chuỗi ngẫu nhiên ít nhất 32 ký tự.
- `DB_SERVICE_KEY`: backend key có quyền truy cập Supabase.
- `GITHUB_DISPATCH_TOKEN`: fine-grained PAT chỉ cho repo này, quyền cần thiết để dispatch event.
- `GITHUB_REPOSITORY_NAME`: `roxthang0710-hash/autonomous-one-hybrid`.

POST đến `https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/agent-webhook`, header `x-agent-secret` và body:

```json
{"request_id":"demo-20261101-001","kind":"research_request","topic":"small business automation"}
```

Webhook khi thiếu secret trả 401; không thay thế phương án GitHub Issue đã chạy thành công.

## Giới hạn
- Đã kiểm thử tích hợp tạo ý tưởng và ghi vào Supabase, **chưa có cơ chế tạo doanh thu**.
- Các điểm đánh giá là rubric máy móc và nghiên cứu dựa trên nguồn công khai, chưa chứng minh nhu cầu thị trường.
- Dữ liệu doanh thu trong `agent_experiments` do chủ sở hữu nhập và phải có bằng chứng.
- GitHub Actions cron có thể chạy trễ; quota Groq/Supabase/GitHub Free có giới hạn.
- Repository hiện đang Public: khuyến nghị đổi sang Private trong GitHub Settings trước khi lưu nội dung kinh doanh nhạy cảm.

## Thử nghiệm
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Chỉ chạy `python agent.py` khi đã cấu hình env vars ở môi trường bảo mật.
