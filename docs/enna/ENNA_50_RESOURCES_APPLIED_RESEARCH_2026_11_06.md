# Enna — Đối chiếu 50 tài nguyên AI Agent và kế hoạch nâng cấp

**Ngày đối chiếu:** 06/11/2026 (Asia/Ho_Chi_Minh). **Nguồn đầu vào:** danh sách 50 tên do chủ dự án gửi, không kèm URL của từng video, file khóa học hoặc toàn văn sách. Không xem kết quả tìm kiếm là đã học hết một khóa học hoặc đọc hết sách.

## 1. Kết luận kỹ thuật có thể áp dụng ngay

1. **Agent không đồng nghĩa với chuỗi cron.** Anthropic phân biệt workflow có đường thực thi định trước và agent chủ động chọn cách làm; dùng một bộ điều phối rõ quyền và bằng chứng, không phải nhiều bot tùy tiện.
2. **Observe → Decide → Act → Verify → Reflect.** Kết hợp kiến trúc Google Agents, ReAct, OpenAI Practical Guide và Stanford Agentic AI: phải có bằng chứng hiện trường mới, quyết định có lý do, đúng tool, rồi readback kết quả.
3. **Guardrail + evaluator đặt trước hành động.** Không dùng phản hồi LLM chưa xác minh làm quyền tự truy cập công cụ. Tool phải thuộc allowlist, có provenance, TTL, ít nhất một bằng chứng hậu hành động; chặn chi phí, spam và xóa nội dung chưa phê duyệt.
4. **Đánh giá hành vi thay vì đếm test pass.** Thêm 22 ca đặc biệt: stale data, permission missing, cached Metricool error, post duplicate, unsafe approval, fallback sau hai lần thất bại, chọn công việc đúng theo giá trị và thông tin.
5. **Bộ nhớ vận hành có cấu trúc và tiêu chí quên.** Từ Generative Agents: lưu quan sát, kinh nghiệm, kế hoạch, phản tỉnh. Không thu gom tin nhắn cá nhân hoặc suy diễn tính cách người theo dõi.
6. **Đo hiệu quả bằng dữ liệu thật.** Các khóa Meta/Google/Excel/SQL là hỗ trợ cho xác thực KPI, cohort và dashboard, không phải lý do huấn luyện mô hình riêng khi Enna còn thiếu đối soát bài và tài sản sáng tạo.
7. **Tự nâng cấp phải có thay đổi có kiểm chứng.** Theo thực hành Claude Code và AI Engineering: chuẩn bị thay đổi tách nhánh, dùng test/eval, dự phòng quay lui; không cấp quyền push code sản xuất hoặc mua dịch vụ chỉ vì model đề xuất.

## 2. Đã triển khai trong đợt này

- `config/enna_agent_learning_50_resources_2026_11_06.json`: inventory 50 ID, nguồn nếu xác định được, trạng thái truy cập thành thật, nhóm ứng dụng và mức ưu tiên.
- `growth/agent_decision_policy.py`: bộ kiểm soát đề xuất hành động và xếp hạng mục tiêu dựa trên bằng chứng có mốc thời gian. Chỉ hành động nội bộ hoặc đọc API được cấp quyền, không tự cấp quyền, xuất bản, mua hay đăng lại.
- `config/enna_agent_behavior_eval_cases_v1.json`: 22 tình huống có đáp án kỳ vọng; phải đạt **22/22** trước khi thay đổi worker tự chủ.
- `tests/test_enna_agent_decision_policy.py`: unit test bổ sung, kiểm tra an toàn, nguồn, khả năng thay chiến lược, giới hạn vòng công cụ.
- Cơ chế hiện có `growth/autonomy_controller.py` và `growth/metricool_threads_bridge.py` tiếp tục đảm nhiệm thao tác đã được chứng minh; policy mới là cổng kiểm định, **chưa biến toàn Enna thành hệ thống điều phối LLM tự chọn công cụ trong production**.

## 3. Kế hoạch nâng cấp theo thứ tự

| Mốc | Điều kiện hoàn thành, không phải việc cần báo cáo |
| --- | --- |
| E1. Behavior Evals | 22/22 ca hành vi qua CI; ca chi tiền, đăng trùng và quyền thiếu đều bị chặn |
| E2. Evidence-driven work selection | Chọn được một trong các việc an toàn dựa trên Meta freshness, follower freshness, số pending đến hạn và lịch sử thất bại; ghi decision/rationale, thực hiện tối đa 1 hành động và đọc lại |
| E3. Tool boundary & MCP | Danh mục công cụ + scope + idempotency keys, 2/3 lỗi được tự phân loại thay vì lặp thao tác, bảo vệ trước công cụ giả |
| E4. Memory & reflection | Lưu kết quả và bài học đã xác minh; không lặp phương án thất bại trong cửa sổ cooldown; có test 2 chu kỳ liên tiếp |
| E5. Editorial evaluator-optimizer | Đánh giá tình huống công sở cụ thể, câu chốt hài, độ hữu ích, CTA và visual Người Tròn thật–hài–doodle; dùng samples do chủ tài khoản duyệt; không lấy AI-judge làm bằng chứng bản quyền hình |
| E6. Safe self-upgrade | Mọi đề xuất mã tạo nhánh/PR, kiểm thử, so sánh benchmark trước/sau; chỉ triển khai sau policy gate và quyền hợp lệ; hoàn nguyên nếu lỗi |

## 4. Đánh giá trọng tâm tài liệu

| Tài liệu | Bài học dùng với Enna | Nguồn |
| --- | --- | --- |
| Anthropic — Building Effective Agents | Chọn workflow đơn giản hoặc điều phối agent theo độ bất định; xác minh ngoài đời | https://www.anthropic.com/research/building-effective-agents |
| OpenAI — A Practical Guide to Building Agents | Mục tiêu/điều phối/công cụ/guardrails/hand-off/hậu kiểm | https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/ |
| Google — Agents + Companion | Orchestration, memory, tool use, agent evaluation và vận hành | https://www.kaggle.com/whitepaper-agents ; https://www.kaggle.com/whitepaper-agent-companion |
| Stanford CS329Z & CS224V | Task decomposition, chọn thành phần phù hợp, eval và kiểm định | https://cs329z.stanford.edu/ ; https://web.stanford.edu/class/cs224v/ |
| ReAct | Xen kẽ chọn hành động và quan sát kết quả; không lập kế hoạch giả định | https://arxiv.org/abs/2210.03629 |
| Generative Agents | Quan sát, ghi nhớ, phản tỉnh và lập kế hoạch có trạng thái | https://arxiv.org/abs/2304.03442 |
| Toolformer | Nguyên tắc chọn API/công cụ phù hợp; không sao chép việc tự huấn luyện mô hình vào Enna | https://arxiv.org/abs/2302.04761 |
| Chain-of-Thought | Hỗ trợ phân tích/nhiệm vụ phức tạp, nhưng chỉ lưu quyết định và bằng chứng kiểm chứng được | https://arxiv.org/abs/2201.11903 |
| MCP Authorization | OAuth đúng audience, scope tối thiểu, token bí mật không truyền cho công cụ khác | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/authorization.mdx |
| OpenAI Agents SDK Testing | Scripted tests để bắt regressions; không gọi model hay provider trong unit tests | https://openai.github.io/openai-agents-python/testing/ |

## 5. Danh mục đủ 50 tài nguyên

**Nhãn:** `verified_public_landing` = đã xác định đúng trang nguồn công khai, *không phải đã xem/đọc xong*; `exact_source_unresolved` = tên chưa đủ để chọn đúng bản; `related_source_only` = tài liệu liên quan, chưa chứng minh là đúng video; `duplicate_of_X` = cùng tài nguyên xuất hiện hai lần. Sách/khóa học chỉ kiểm tra thông tin mở, không giả định có quyền truy cập phần trả phí.

| ID | Nhóm | Tài nguyên | Trạng thái nguồn | Ứng dụng | Mức ưu tiên |
| ---: | --- | --- | --- | --- | --- |
| 1 | Video | LLM Introduction | `exact_source_unresolved` | foundations | later |
| 2 | Video | LLMs from Scratch | `exact_source_unresolved` | foundations | later |
| 3 | Video | Agentic AI Overview (Stanford) | `related_source_only` | agent_architecture | high |
| 4 | Video | Building & Evaluating Agents | `exact_source_unresolved` | evaluation | high |
| 5 | Video | [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) | `verified_public_landing` | agent_architecture | high |
| 6 | Video | Building Agents with MCP | `exact_source_unresolved` | tools_security | high |
| 7 | Video | Building an Agent from Scratch | `exact_source_unresolved` | agent_architecture | high |
| 8 | Video | Philo Agents | `exact_source_unresolved` | agent_architecture | later |
| 9 | GitHub | [GenAI Agents](https://github.com/NirDiamant/GenAI_Agents) | `verified_public_landing` | agent_architecture | medium |
| 10 | GitHub | [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) | `verified_public_landing` | agent_architecture | high |
| 11 | GitHub | [Prompt Engineering Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | `verified_public_landing` | prompt_context | medium |
| 12 | GitHub | [Hands-On Large Language Models](https://github.com/HandsOnLLM/Hands-On-Large-Language-Models) | `verified_public_landing` | foundations | later |
| 13 | GitHub | [GenAI Agents](https://github.com/NirDiamant/GenAI_Agents) | `duplicate_of_9` | agent_architecture | medium |
| 14 | GitHub | [Made with ML](https://github.com/GokuMohandas/Made-With-ML) | `verified_public_landing` | reliability | medium |
| 15 | GitHub | Hands-On AI Engineering | `exact_source_unresolved` | reliability | medium |
| 16 | GitHub | [Awesome Generative AI Guide](https://github.com/aishwaryanr/awesome-generative-ai-guide) | `verified_public_landing` | reliability | medium |
| 17 | GitHub | Designing Machine Learning Systems | `exact_source_unresolved` | reliability | later |
| 18 | GitHub | [Machine Learning for Beginners](https://github.com/microsoft/ML-For-Beginners) | `verified_public_landing` | foundations | later |
| 19 | GitHub | [LLM Course](https://github.com/mlabonne/llm-course) | `verified_public_landing` | foundations | medium |
| 20 | Guide | [Google's Agent Whitepaper](https://www.kaggle.com/whitepaper-agents) | `verified_public_landing` | agent_architecture | high |
| 21 | Guide | [Google's Agent Companion](https://www.kaggle.com/whitepaper-agent-companion) | `verified_public_landing` | evaluation | high |
| 22 | Guide | [Building Effective Agents by Anthropic](https://www.anthropic.com/research/building-effective-agents) | `duplicate_of_5` | agent_architecture | high |
| 23 | Guide | [Claude Code Agentic Coding Practices](https://www.anthropic.com/engineering/claude-code-best-practices) | `verified_public_landing` | self_upgrade | high |
| 24 | Guide | [OpenAI's Practical Guide to Building Agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) | `verified_public_landing` | agent_architecture | high |
| 25 | Book | Understanding Deep Learning | `exact_source_unresolved` | foundations | later |
| 26 | Book | [Building an LLM from Scratch](https://sebastianraschka.com/llms-from-scratch/) | `verified_public_landing` | foundations | later |
| 27 | Book | The LLM Engineering Handbook | `exact_source_unresolved` | reliability | medium |
| 28 | Book | [AI Agents: The Definitive Guide](https://www.oreilly.com/library/view/ai-agents-the/0642572247775/) | `verified_public_landing` | reliability | high |
| 29 | Book | [Building Applications with AI Agents](https://www.oreilly.com/library/view/building-applications-with/9781098176495/) | `verified_public_landing` | agent_architecture | high |
| 30 | Book | [AI Agents with MCP](https://www.oreilly.com/library/view/ai-agents-with/9798341639546/) | `verified_public_landing` | tools_security | high |
| 31 | Book | [AI Engineering](https://www.oreilly.com/library/view/ai-engineering/9781098166298/) | `verified_public_landing` | evaluation | high |
| 32 | Research | [ReAct](https://arxiv.org/abs/2210.03629) | `verified_public_landing` | agent_architecture | high |
| 33 | Research | [Generative Agents](https://arxiv.org/abs/2304.03442) | `verified_public_landing` | memory | high |
| 34 | Research | [Toolformer](https://arxiv.org/abs/2302.04761) | `verified_public_landing` | tools_security | medium |
| 35 | Research | [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | `verified_public_landing` | prompt_context | medium |
| 36 | Course | [Meta Data Analyst Professional Certificate](https://www.coursera.org/professional-certificates/meta-data-analyst/) | `verified_public_landing` | analytics | medium |
| 37 | Course | Google Advanced Data Analytics Professional Certificate | `exact_source_unresolved` | analytics | medium |
| 38 | Course | [Microsoft Power BI Data Analyst Professional Certificate](https://www.coursera.org/professional-certificates/microsoft-power-bi-data-analyst) | `verified_public_landing` | analytics | later |
| 39 | Course | [Google Data Analytics Professional Certificate](https://www.coursera.org/professional-certificates/google-data-analytics) | `verified_public_landing` | analytics | medium |
| 40 | Course | [Introduction to Data Analytics](https://www.coursera.org/learn/introduction-to-data-analytics) | `verified_public_landing` | analytics | medium |
| 41 | Course | [Machine Learning Specialization](https://www.coursera.org/specializations/machine-learning-introduction) | `verified_public_landing` | foundations | later |
| 42 | Course | [IBM Deep Learning with PyTorch, Keras and Tensorflow Professional Certificate](https://www.coursera.org/professional-certificates/ibm-deep-learning-with-pytorch-keras-tensorflow) | `verified_public_landing` | foundations | later |
| 43 | Course | Deep Learning Specialization | `exact_source_unresolved` | foundations | later |
| 44 | Course | [Crash Course on Python](https://www.coursera.org/learn/python-crash-course) | `verified_public_landing` | engineering | medium |
| 45 | Course | Python for Data Science, AI & Development | `exact_source_unresolved` | engineering | medium |
| 46 | Course | [ChatGPT + Excel: AI-Enhanced Data Analysis & Insight Specialization](https://www.coursera.org/specializations/chatgpt-excel) | `verified_public_landing` | analytics | medium |
| 47 | Course | [Work Smarter with Microsoft Excel](https://www.coursera.org/learn/microsoft-excel-work-smarter) | `verified_public_landing` | analytics | later |
| 48 | Course | Microsoft Excel Professional Certificate | `exact_source_unresolved` | analytics | later |
| 49 | Course | [Excel Basics for Data Analysis](https://www.coursera.org/learn/excel-basics-data-analysis-ibm) | `verified_public_landing` | analytics | later |
| 50 | Course | [SQL Foundations](https://www.coursera.org/learn/sql-foundations) | `verified_public_landing` | analytics | medium |

## 6. Giới hạn đã xác minh

- Không có file ebook hoặc video khóa học được đính kèm trong lượt gửi này. Hầu hết tên video không đủ để xác nhận kênh/đường dẫn; không tự gắn video khác vào như nguồn gốc.
- ID 9/13 cùng tên và ID 5/22 có thể cùng tài liệu; bảng ghi quan hệ trùng, tránh tính là bốn nguồn độc lập.
- Mốc E1 chỉ kiểm tra quyết định từ các ca mô phỏng. **Không chứng minh** mô hình LLM tự lập kế hoạch ngoài kịch bản, không chứng minh một video được dựng hoặc bài đã đăng.
- Không tự cài toàn bộ framework hoặc copy mã GitHub vì có thể có khác biệt giấy phép, phụ thuộc, dữ liệu và rủi ro bảo mật.
- Sau khi có nguồn chính xác cho 14 mục chưa rõ, có thể tăng độ bao phủ nghiên cứu, nhưng không trì hoãn các cải tiến có bằng chứng từ nguồn chính thống.
