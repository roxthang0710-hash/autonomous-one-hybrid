## v1.9 — Threads Nurture + Growth Radar an toàn (02/11/2026)

Đã xác minh **Threads @dohay_dilam kết nối qua Supabase Vault**. 15 bài Metricool từ 03–17/11/2026 được giữ nguyên; Autonomous One đã tạo và xếp hàng 2 bài tiếp theo từ 18/11. GitHub Actions tự chạy theo lịch, không đăng trùng, không coi bài chờ đăng là bài đã xuất bản.

Growth Radar giờ bỏ qua bản nháp AI vi phạm bộ lọc và thử nguồn đã kiểm duyệt khác trong giới hạn, thay vì dừng toàn bộ workflow. Có kiểm tra sức khỏe tài khoản, hạn token và trạng thái chuẩn bị Shopee Affiliate (chưa được duyệt, chưa có doanh thu).

**Lượt chạy xác thực:** [Threads Agent thành công](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41422313540) · [Growth Radar thành công](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41421857399) · [Báo cáo đầy đủ](RELEASE_v1_9_AUTONOMOUS_OPERATIONS.md).

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

## v1.3 — Reliability, internal plans and private web review

Private dashboard: https://autonomous-one-control-thang.fairysage513.chatgpt.site

- Proposal, evaluation, three internal tasks, synthetic scenario, run completion and event completion commit in one PostgreSQL transaction (`complete_agent_run`). A stale attempt cannot complete a reclaimed event. Only the service role can execute worker RPCs.
- Failures after claiming an event release the matching attempt; expired leases recover after worker interruption. GET requests retry transient failures; writes are never automatically replayed.
- Model output is type checked. Nonzero declared cost is rejected rather than overwritten. Error records contain exception classes, not potentially sensitive URLs. Missing Actions configuration now fails visibly.
- Memory supplies up to 200 historical titles to generation and screening. Similar titles receive a penalty and `hold` verdict. Topic ties select the longest-idle topic. This is bounded title-based memory, not semantic deduplication.
- Every new proposal gets internal preparation tasks. Reviewers can complete/reopen internal tasks; the `owner_review` task remains blocked. Idea approval does not execute an external action.
- `simulator.py` computes three deterministic scenarios. Auto-saved scenarios use default assumptions (100 visitors, 5% conversion, zero hypothetical price/cost); dashboard inputs run locally without persistence. Neither creates revenue records or evidence of market demand.

### Dashboard account setup (one-time)

1. In the project's **Authentication → Users → Add user**, create your own email/password account. Keep the password private; do not put it in GitHub Secrets or chat.
2. Copy its user UUID. In the Supabase SQL Editor run:

   ```sql
   insert into public.agent_reviewers(user_id)
   values ('REPLACE_WITH_YOUR_AUTH_USER_UUID') on conflict do nothing;
   ```

3. Open the private dashboard and log in with that account. Both site privacy and Supabase RLS protect data. A newly registered account alone has no review permissions.

Reviewers can read project records, update only proposal approval status, and update only eligible internal task status. They cannot edit model output, grant themselves access, call worker RPCs, or modify financial records. Browser auth tokens stay in memory and refresh while the page stays open; reloading requires login again. `dashboard/web` contains the deployable static source. The publishable browser key is intentionally public, and grants no access without RLS authorization.

### Verification and operations

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -v
node --check dashboard/web/app.js
```

Run `tests/integration_v13.sql` with project owner SQL access to test atomic rollback, replay rejection, tasks, simulation and reviewer policies. It rolls back all test mutations. Apply `sql/schema.sql`, `sql/v1_1_evaluations.sql`, `sql/v1_3_reliability.sql`, then `sql/v1_3_task_review.sql` when provisioning a fresh project; versioned upgrade scripts are applied once, not repeatedly. Run Supabase security/performance advisors after upgrades.

The `Tests` workflow runs on pushes and pull requests without production secrets. The agent workflow also runs tests before research. Do not treat a passing unit suite as proof of a working provider integration: confirm a new successful `agent_runs` record plus its evaluation, tasks and simulation after deployment.

Known limits: no semantic/vector memory, automated task executor, causal market validation, external outreach, or financial transactions. Decisions are current-state records; a full immutable decision audit trail is a next upgrade. Pending backlog is measured within the latest 200 proposals. Supabase login must be enrolled before authenticated browser flows can be exercised by the owner.

## v1.4 — Problem memory and review history

Generation now receives bounded historical problem/customer/decision context. A local normalized text matcher checks both problem and customer even when the title changes; matched ideas are held and reference their prior proposal ID and decision in the evaluation rubric. This is explainable text similarity, not embeddings or a claim of semantic understanding.

Plans now include each proposal's actual hypothesis and success metric. The append-only `agent_review_audit` records approval changes through a database trigger; reviewer clients cannot write or delete audit rows. Worker cycles recover orphan `running` rows older than 20 minutes, above the eight-minute Actions job timeout. Simulation inputs above one billion VND are rejected to prevent overflow.

Apply `sql/v1_4_audit.sql` after the v1.3 migrations. No historical audit events are invented. Automatic account provisioning was blocked by approval review; no persistent login account was created and the existing login setup remains required.


## v1.5 — Affiliate Marketing research

Đã triển khai module Affiliate Research riêng (không thay thế Agent chính), chạy nghiên cứu **thứ Ba và thứ Sáu lúc 09:30 giờ Việt Nam** hoặc từ GitHub Issue với tiêu đề `affiliate:` do chủ repo tạo. Chương trình nghiên cứu: Shopee KOC, ACCESSTRADE và TikTok Shop Affiliate.

- [Hướng dẫn sử dụng & giới hạn](affiliate/README.md)
- [Báo cáo triển khai và kiểm thử v1.5](RELEASE_v1_5_AFFILIATE.md)
- [Workflow Affiliate Research](.github/workflows/affiliate-research.yml)
- [Supabase Table Editor](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor) — bảng `affiliate_opportunities` và `affiliate_review_dashboard`

**Bản này chỉ đề xuất nội dung, không tự đăng bài hoặc tự tạo link nhận hoa hồng.** Các chương trình, sản phẩm và điều kiện cần chủ sở hữu xác minh và duyệt trước khi kiếm tiền thật.


## v1.6.1 — Threads Nurture (Meta API)

- **Đã triển khai:** bộ hồ sơ thương hiệu nội bộ, lịch 14 ngày, 1 bài AI tạo qua Groq, hàng đợi an toàn, kết nối API xuất bản có kiểm soát, ghi nhận số liệu Meta (khi được cấp quyền).
- **Chưa được kết nối:** tài khoản Threads thật và Meta OAuth — do đó **chưa có bài công khai**. Việc tạo hồ sơ trên Supabase không đồng nghĩa đã đăng ký tài khoản ngoài đời.
- [Báo cáo kiểm thử và trạng thái v1.6.1](RELEASE_v1_6_THREADS.md)
- [Hướng dẫn kích hoạt Threads đúng quyền](threads/README.md)
- [Workflow nuôi kênh hàng ngày](.github/workflows/threads-nurture.yml)
- [Supabase](https://supabase.com/dashboard/project/gjdvdohylvsauphhkutw/editor): `threads_channels`, `threads_posts`, `threads_publish_attempts`, `threads_metrics`


## v1.7.2 — Growth Radar & authentic Threads engagement

Tự đọc tín hiệu quan tâm từ Google Trends Việt Nam và RSS tin tức theo ngách công sở/du lịch, phân loại nguồn, chặn tin giật gân/không liên quan, tạo bản nháp Groq và lưu Supabase để chọn nội dung phù hợp. Growth Radar chạy **09:15 và 17:15 mỗi ngày theo giờ Việt Nam** trên GitHub Actions.

- [Báo cáo phát triển v1.7.2](RELEASE_v1_7_GROWTH.md)
- [Cơ chế Radar, quyền Threads và giới hạn tương tác](growth/README.md)
- [Workflow Growth Radar](.github/workflows/growth-radar.yml)
- [Bản cấu trúc CSDL v1.7](sql/v1_7_growth_radar.sql)

Có sẵn mã tìm cuộc trò chuyện và phản hồi hữu ích qua Threads API, nhưng **mặc định tắt**, chỉ hoạt động sau khi Meta OAuth và các quyền riêng được cấp hợp lệ. Không tạo tương tác giả, không phản hồi hàng loạt, không tự gắn liên kết Affiliate. Kết nối Metricool trong ChatGPT không tự cấp Meta Developer token cho GitHub.


## v1.8.3 — Threads OAuth + Continuous Growth

Trang OAuth chính chủ đã được triển khai tại [Kết nối Threads Autonomous One](https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth). Tài khoản chủ sở hữu cấp quyền một lần qua ứng dụng Meta Threads API; server tự đổi mã OAuth, lưu token trong Supabase Vault, kiểm tra đúng @dohay_dilam và tự gia hạn token dài hạn. Không cần sao chép token vào ChatGPT hoặc thêm secret thủ công vào GitHub Actions.

Sau Meta OAuth, Agent tự tạo nội dung, thay tối đa 2 bài/tuần bằng góc viết xu hướng còn mới, đăng một bài/ngày và đối soát bài Metricool theo ID Meta thật. 15 ngày 03–17/11/2026 đã được Metricool đặt lịch độc quyền, không đăng trùng. Đọc/chủ động phản hồi tối đa 1 cuộc thảo luận liên quan/ngày chỉ khi chủ sở hữu tích chọn rõ ràng và Meta chấp thuận quyền bổ sung.

- [Báo cáo phát hành v1.8.3](RELEASE_v1_8_THREADS_OAUTH.md)
- [Hướng dẫn Meta Developer App & cấp quyền](threads/OAUTH.md)
- [Quy trình chạy Agent sau cấp quyền](threads/README.md)
- [Lượt smoke test OAuth thành công](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41348403916)

**Giới hạn thật:** Chưa có Meta OAuth token chính chủ trong Vault trước khi người sở hữu chấp thuận, nên các chức năng đăng/phản hồi trực tiếp qua Meta hiện vẫn tắt. Shopee Affiliate chưa được duyệt nên chưa có doanh thu tiếp thị liên kết.
