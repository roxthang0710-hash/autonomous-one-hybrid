# Enna Autonomy Completion Matrix — 2026-11-06

## Definition of autonomous, not merely scheduled
Every capability must pass the same closed loop: **detect from timestamped source -> choose bounded action -> execute with minimum access -> verify independent readback -> persist outcome -> recover/rollback or stop safely**. No "completed" status from a green CI run alone; real provider confirmation required for external actions.

## Source-of-truth checklist

| ID | Capability | Last verified state | Option and reason | Completion gate |
| --- | --- | --- | --- | --- |
| A1 | Central orchestrator and incident queue | **A1.1 implemented and live-tested 2026-11-06**, A1.2/1.3 open | Deterministic source checks and severity ordering first, AI only for permitted novel diagnosis; avoids competing workers | One consistent incident queue, deduped stable IDs, one safe verified remedy, persistence across runs, no duplicate mutation |
| A2 | Fresh provider data | Partially: Meta official follower snapshots, Metricool stored booking state can be stale | Use official Meta insights/read endpoints and explicit TTL + source metadata; Metricool MCP in chat is not a GitHub Action API | Live-permission verified FB/IG/Threads/Metricool sync or explicit source unavailable; every row shows at/source and never invents freshness |
| A3 | Diagnosis + solution policy | Fixed runbooks and owner-selected reply draft selfheal only | Rule-first candidate generation, AI proposal as untrusted suggestion, constrained planner with cost/permission/quality limits | Proven error types automatically mapped to bounded safe runbook; 2–3 forced-failure integration tests |
| A4 | Execution by action | Threads guarded publishing exists; FB/IG managed through Metricool, selected reply limited | Capability matrix: read, prepare, post, reply, reschedule, delete, spend; issue one scoped OAuth permission per needed action | At least one authorized real action with provider permalink/id and dedup guard; high-risk operations retain owner approval |
| A5 | Verification and rollback | CI + partial provider verification, ambiguous writes are held | Readback every state-changing action and only rollback reversible internal changes; never auto-retry uncertain Meta posts | Can prove outcome/status and preserve error evidence; lost response does not duplicate post; rollback test green |
| A6 | Self learning | Evidence gated story-vs-practical, minimum sample, 48h cooldown | Matched format/cohort comparison and holdout, outcome audits, scorecard | Two verified experiment cycles with measurable insight (not fabricated attribution) and tracked policy changes |
| A7 | Real original media/video | 3 20-second script/SRT packages; 11 pending Threads without media, visual approval incomplete | Production assets from original photo/doodle/storytelling style approved by owner, rights and quality gates before scheduled upload | At least one real MP4/image reviewed, uploaded, provider-post confirmed; same style guidelines persist |
| A8 | Commercial outcomes | Affiliate ideas only; zero verified payout | Checkout and affiliate provider accepted via owner, validate product claims and privacy-safe aggregate link tracking | First independently verified order and eventual settled receipt; no assumed revenue |

### A1.1: evidence from an actual unattended GitHub worker
- Code: `growth/autonomy_controller.py`. Private owner-only notification sink uses existing Supabase `enna_desk_notifications` and dedup `(owner_id,source_key)`. No new public RLS surfaces.
- Tests: `tests/test_autonomy_controller.py`, eight success cases, including stale follower self-refresh followed by DB readback, no unnecessary Meta GET when source fresh, safe incident triage, no social POST.
- Workflow: `.github/workflows/enna-autonomy-controller.yml`, cron `37 */2 * * *` UTC; can be tested with owner-created `autonomy-check:` issue.
- **Live proof:** GitHub run `42222014968` SUCCESS, 8/8 targeted tests, `ENNA_AUTONOMY_RESULT`: `{"status":"triaged","follower_action":"already_fresh","incidents":1,"selected_codes":["provider_error"],"notices_written":1,"external_posts_created":0}`. Supabase confirmed new private alert `autonomy-v1:provider_error:facebook:407100825539987565`.
- **Meaning:** the controller DID automatically read, rank and record a real known blocker, without asking the owner. It DID NOT refresh Meta in this run because its last official follower snapshot was fresh. A stale-path recovery is verified in unit mocks, not live. It DID NOT access live Metricool or publish/fix the failed Facebook post.
- A1 is **not completed overall** until source refresh on a truly stale day is independently verified, persistent incident lifecycle (resolved/blocked/reopened) exists, safe job-runner remediations are proven, and an action outcome is confirmed. Do not mark A1 complete based on alert creation.

## Explicit access inventory and cost decision
| Permission/integration | Currently available | If needed in later phase | Gate |
| --- | --- | --- | --- |
| GitHub repo workflow + Supabase backend | Connected workers and backend, GitHub workflow contents:read; private notifications supported | To let Enna propose code patches automatically, use dedicated branch/PR action with scoped contents:write, checks required and owner review for merging | Never hand unreviewed agent write access to main/release/credentials |
| Official Threads owner OAuth | Stored connection mechanism / official account insights; permissions must be checked individually | `threads_basic`, `threads_manage_insights`, `threads_read_replies`, `threads_manage_replies`, `threads_content_publish` per action, plus app review where required | Consent through Meta OAuth, encrypted token; never post/reply when permission missing |
| Metricool | Starter publishing and ChatGPT MCP connector; **Starter has no Metricool public API for independent GitHub worker** | Option A: keep MCP for operator-in-chat and combine official Meta read APIs; Option B: owner explicitly pays for Advanced API when demonstrably needed | Do not silently upgrade, invent API credentials or promise Cron can invoke ChatGPT-only app |
| Facebook/Instagram | Scheduled through Metricool | Meta Graph permissions as appropriate and linked Professional IG account; provider review / page authorization | Only existing owner accounts, never assume Meta permissions |
| Browser companion | Limited owner-verified local interactive steps, not a remotely auditable full browser worker | Explicit owner session, permitted app connection, scoped approvals for interactive actions | No background clicking, no CAPTCHA/2FA bypass, no unverified "posted" |
| Media/rendering | Storyboards/SRT and research assets | Original rendered MP4, licensed sound library, visual QA matching owner's authentic meme/photo/doodle style | Upload and schedule only after media/rights verification |
| Affiliate / payments | Research candidates and hypotheses | Owner registers and approves partner account/product, law/ad disclosure, settlement evidence | No commission estimates presented as payouts, no bank/payment action without owner |

Metricool API conditions (checked 2026-11-06): https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u

Official Meta Threads OAuth permission reference (checked 2026-11-06): https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api

## Work order — one proven stage at a time
1. **A1.1 — DONE for triage:** safe controller, idempotency, private incident persisted, real workflow tested.
2. **A1.2 — NEXT:** verify real stale-source follower recovery after TTL, add incident state transition and clear closed alerts only on newer verified source, never based on a repeated test.
3. **A2.1:** distinguish Metricool live state from cached DB in every dashboard; add bounded authorized read-only source sync or a clearly marked manual operator handoff while Starter is used.
4. **A3.1:** standardized error-to-safe-runbook policy and test suite; automatic safe action only for exact allowlist.
5. **A4.1 + A5.1:** verified owner-only Meta/Metricool workflow for one reversible operation, provider-side readback and no duplicate retry.
6. **A6.1 + A7.1:** measure 3 original creative tests and require actual approved media, not only captions/storyboards.
7. **A8.1:** verify one approved affiliate account/product, then trial only with disclosure; no sale/commission claim until evidence exists.

**Control rule:** no automatic posting, comment/reply to unrelated users, rescheduling, deleting media, buying services, or changing permissions solely to satisfy an autonomy milestone. Require provider identity, authorization and publication evidence.
