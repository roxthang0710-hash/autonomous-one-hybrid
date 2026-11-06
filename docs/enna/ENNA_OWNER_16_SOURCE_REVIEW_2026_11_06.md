# Enna — Owner source pack: 16 links, careful reading notes (06/11/2026)

**Scope note:** The owner supplied 16 original URLs. Transcript availability ≠ confirmed audiovisual review, README ≠ complete repo audit, O'Reilly table of contents ≠ paid full book, Coursera syllabus ≠ enrolled course completion. These annotations are summaries of accessible sources, not copies of copyrighted full text.

## Source by source

### #1 — Intro to Large Language Models — Andrej Karpathy

Source: https://www.youtube.com/watch?v=zjkBMFhNj_g

Access: **Full public transcript available (~12k words)**

**Key points & Enna use:** Inference vs pretraining, tokens and gradient optimization, SFT/RLHF, scaling limits, tool use, multimodality, thinking, prompt injection/jailbreak/data poisoning. Enna: separate observed content from authorized system instructions and verify tool outputs.

### #2 — Stanford CS229: Building Large Language Models — Yann Dubois

Source: https://www.youtube.com/watch?v=9vM4p9NN0Ts

Access: **Full public third-party transcript (~18k words)**

**Key points & Enna use:** Language modeling objective and loss, data quality and dedup, eval contamination/perplexity, compute scaling, SFT, RLHF and preference alignment, inference cost. Enna: high-quality labeled data, versioned eval, trace costs; not worth pretraining a new LLM now.

### #3 — Stanford: Agentic AI Overview

Source: https://www.youtube.com/watch?v=kJLiOGle3Lw

Access: **Video original validated; only topic summary accessible**

**Key points & Enna use:** Iterative calls, reflection, planning, tool selection and failure patterns. Full transcript/slide-specific details NOT verified. Enna: decision trace with observable source age and failure outcome.

### #4 — Building and Evaluating Agents — Sayash Kapoor

Source: https://www.youtube.com/watch?v=d5EltXhbcfA

Access: **Detailed timestamped talk synopsis; not full transcript**

**Key points & Enna use:** A benchmark or polished demo does not demonstrate reliability; evaluate end-to-end success, reliability, cost and human expert assessments. Enna: separate offline eval pass from real provider execution success; report false positives/negative retries.

### #5 — How We Build Effective Agents — Barry Zhang, Anthropic

Source: https://www.youtube.com/watch?v=D7_ipDqhtwk

Access: **Video synopsis + separate full public Anthropic guide**

**Key points & Enna use:** Do not agentify every deterministic task; prefer simplest model+tools+feedback loop, maintain visibility into the model context. Enna: route fixed tasks to safe cron, novel cases to bounded plan; no multi-agent theater.

### #6 — Building Agents with MCP — Mahesh Murag, Anthropic

Source: https://www.youtube.com/watch?v=kQmXtrmQ5Zg

Access: **Full public transcript (~16k words)**

**Key points & Enna use:** MCP solves many tools×many apps integration; host/client/server concepts, tools (model-called) vs resources (app-injected) vs prompts; authorization is separate. Enna: permission registry and scope-specific connectors; ChatGPT-installed Metricool MCP does NOT imply independent GitHub API access.

### #7 — Let's Build an Agent from Scratch — Cam Sater

Source: https://www.youtube.com/watch?v=xzXdLRUyjUg

Access: **Author description and detailed synopsis; not full transcript**

**Key points & Enna use:** Start from model call and add judge stop rule, tool result handling, parallel tools and self-maintained TODO list inside bounded loop. Enna: plan→act→observe→replan, prove stop condition and single-action idempotency.

### #8 — Philo Agents playlist

Source: https://www.youtube.com/playlist?list=PLacQJwuclt_sV-tfZmpT1Ov6jldHl30NR

Access: **Playlist link recorded; episode list and transcripts unavailable**

**Key points & Enna use:** Do not attribute specific knowledge or episode count until playlist contents verified. Additional accessible transcript/export can be indexed later.

### #15 — Hands-On AI Engineering

Source: https://github.com/Sumanth077/Hands-On-AI-Engineering

Access: **README and project index read; nested code not audited**

**Key points & Enna use:** Research Assistant with Memory (planner/research/writer/critic), self-reflective RAG, marketing strategy and Instagram content examples, transcript RAG. Enna: borrow patterns conceptually; review per-subproject license/secrets/providers/cost before porting code.

### #17 — Designing Machine Learning Systems — Chip Huyen companion

Source: https://github.com/chiphuyen/dmls-book

Access: **README and 11 chapter summaries read; original book still separate**

**Key points & Enna use:** Start with business objectives; training data labeling/quality, time-split validation, leakage, offline+online evaluation, deployment, data drift, monitoring, continual learning, infra and human factors. Enna: post experiment cohorts, KPI/ROI, source quality, audit trail; green CI is not revenue.

### #25 — Understanding Deep Learning — Simon Prince

Source: https://udlbook.github.io/udlbook/

Access: **Open book site identified, chapters 1–21 released; NOT all chapter pages/figures read**

**Key points & Enna use:** Deep networks, training/backprop, optimization/regularization, CNNs, transformers and modern generative models; foundational future research. Enna: assess model quality and uncertainty; do not pretrain without dataset and ROI.

### #27 — LLM Engineer's Handbook — Paul Iusztin, Maxime Labonne

Source: https://www.oreilly.com/library/view/llm-engineers-handbook/9781836200079/

Access: **Detailed O'Reilly TOC and preview; paid full text not accessible**

**Key points & Enna use:** Feature/training/inference pipelines; ingestion and RAG chunks/vectors; SFT/LoRA, preference alignment/DPO, task+RAG evaluation, inference optimization, CI/LLMOps. Enna: grounded knowledge retrieval, prompt/version tracing and lean monitoring, not overbuild AWS infrastructure.

### #37 — Google Advanced Data Analytics

Source: https://www.coursera.org/professional-certificates/google-advanced-data-analytics

Access: **Official public curriculum; submitted imp.i384100.net affiliate redirect not readable**

**Key points & Enna use:** Statistics, experimental design, regression, Python and ML, business-facing insights. Enna: normalize impressions, engagement and follow conversion; maintain cohort-sized comparisons and confidence caveats.

### #43 — Deep Learning Specialization

Source: https://www.coursera.org/specializations/deep-learning

Access: **Public syllabus; not enrolled lessons**

**Key points & Enna use:** Neural networks, optimization, bias/variance, CNN and sequence modeling. Enna: foundation for future text/vision model customization only after grounded data.

### #45 — Python for Data Science, AI & Development

Source: https://www.coursera.org/learn/python-for-applied-data-science-ai

Access: **Official course page/syllabus; not enrolled lessons**

**Key points & Enna use:** Python control flow, files, NumPy/Pandas, APIs and data processing. Enna: robust time-zone conversion, pagination, readback checks, data-cleaning tests.

### #48 — Microsoft Excel Professional Certificate

Source: https://www.coursera.org/professional-certificates/microsoft-excel-skills

Access: **Official syllabus; affiliate redirect not a learning credential**

**Key points & Enna use:** Spreadsheet preparation, Power Query/automation, pivot and dashboards. Enna: optional editable owner KPI and affiliate tracker, not a substitute for verified source data.

## Applied upgrade: E3 failure memory & fallback

- A previously failed Meta refresh is classified by `result_code` before another call: `meta_owner_oauth_unavailable` and missing permission pause that action for 72h; internal DB readback errors pause 12h; newly independently verified official source evidence can unlock normal validation.
- Another authorized stale-source action may be selected instead. Missing permission must never be fixed by self-granting OAuth, duplicate social POST or unreviewed production code.
- Guarded code and new tests are proposed on branch `enna/e3-evidence-based-fallback-20261106` for PR/CI; no claim of live failure recovery until a real provider error has been observed and resolved.

## Next verified gates

| Gate | Evidence required |
| --- | --- |
| E3 | PR CI green, then two real independent runs showing previous failure → different authorized action → provider readback |
| E4 | Proven private episodic memory with TTL/provenance, no raw token or personal follower data |
| E5 | Owner-labeled natural office humor + real-photo/sketch visual + meaningful CTA; compare platform performance, not volume |
| E6 | Reviewable branch/PR, unit+behavior+integration gates, owner approval on consequential deployments, rollback test |

## Known research gaps

- #8 playlist episode contents could not be enumerated in the available browsing runtime; #3/#4/#5/#7 lack complete verified captions, so their notes use speaker/organizer summaries.
- #25 public book can be read further from legally available chapter files, but a full 21-chapter page-by-page audit is not established here.
- #27 full 522-page O'Reilly text requires valid subscription or user-authorized copy. No paywall bypass or fabricated read completion.
- Submitted four affiliate tracking URLs are not used as reference text or product recommendations; canonical Coursera pages remain the knowledge source.
