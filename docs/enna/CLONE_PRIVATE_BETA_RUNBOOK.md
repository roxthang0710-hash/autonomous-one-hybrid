# Enna Clone — PRIVATE BETA runbook and staged rollout
Updated: 2026-11-06 · Owner project `gjdvdohylvsauphhkutw` · Repository `roxthang0710-hash/autonomous-one-hybrid`

## Current public vs private status

- **Public:** `/enna/clone/` — Enna Clone Lite 0.1: build/copy/download instructions, NO model calls.
- **Public changelog:** `/enna/clone/updates/` — ONLY published versions (currently 0.1).
- **Private preview:** `/enna/clone/beta/` — HTML + standalone JS login, chat, history, owner memory/docs/agents, tasks and suggestions. **Not linked** from public Lite, access controlled by Supabase Auth + beta whitelist + release flags. Code/UI deployment and static tests are NOT evidence of a successful live beta user chat.
- **Edge:** Supabase `enna-clone-api`, `verify_jwt=true`, owner-specific records, service role backend ONLY.
- **Multi-user privacy:** 12 `public.enna_clone_*` tables, RLS ON, user only SELECT own records; backend is the only writer. Beta access & global quotas are not readable by public clients. One account cannot query another's conversation, memory, docs, profile, schedule or runs via REST privileges.
- **Usage:** atomic limit 4 provider calls per user per Ho Chi Minh day, 40 globally, even across concurrent function requests; scheduled worker separately checks and reserves quota.
- **Agent schedule:** `growth/enna_clone_worker.py`, GitHub Actions `enna-clone-personal-jobs.yml`. Claims max 4 due tasks, advances the next-run timestamp before work, writes output into owner-private runs. No emails, meta APIs or shell execution. In-DB `schedules` flag currently CLOSED; worker claims nothing.
- **Suggestions:** if enabled, separate quota-limited AI pass generates task-specific possible improvements; no automatic code changes, OAuth, spending, sending or publishing.
- **AI provider key:** strictly **`ENNA_CLONE_GROQ_API_KEY`**, separate from original Enna's `GROQ_API_KEY`; no fallback to original Enna. Until an independent key is provisioned securely, beta chat returns a configuration error rather than borrowing Enna's original credits.

## Release flags currently

| Release | Feature flags | Status |
|---|---|---|
| 0.2 | accounts, live_chat | enabled for **beta access list only**; 0 invited accounts last checked |
| 0.3 | private_memory, document_workspace, agent_builder | code written, release CLOSED |
| 0.4 | schedules | worker and DB claim created; release CLOSED |
| 0.5 | proactive_suggestions | code written; release CLOSED |
| 0.6 | external_connectors | no real provider OAuth, release CLOSED |

**Never change flags just to show a demo.** For 0.2, verify a real authenticated browser session and Groq conversation twice (two test users), check no cross-owner reads, and ensure cost limit. For 0.3 onward, pass respective gates in `config/enna_clone_release_train.json` before opening a phase.

## Remaining external actions / blockers

1. Provision a **new dedicated provider API key** for Clone in *Supabase function secrets* and corresponding *GitHub Actions repository secret*, both named `ENNA_CLONE_GROQ_API_KEY`. Never copy or send Enna production key. Secrets remain server-side. User must perform key creation and provision through approved provider UI unless compatible secret tools become available.
2. Verify Auth signup/sign-in email templates, redirect URL allowlist and magic links for the actual beta domain, including verification email deliverability. These settings are shared at Supabase project level; do not change production Enna login without risk review.
3. Grant 1–2 real testers via `enna_clone_beta_access` only after explicit owner selection; do not invent or enroll fake community members.
4. Run **cross-user negative tests** with real user JWTs. SQL RLS privilege audit and CI do not replace end-to-end multiuser tests.
5. Configure Google/Microsoft OAuth apps, scopes and token vault to introduce read-only external connectors safely. No Gmail, Google Sheets, Outlook, Meta or publishing OAuth connector exists in the clone today. This requires consent and often provider app review.
6. Validate webhook, scheduling SLA, local-time semantics and model outcomes with real job records before release of 0.4.
7. Add privacy-first traffic analytics later; current UTM and public pages are NOT evidence of users, clicks, subscribers or traffic conversion.

## Gradual Threads communication

Only one functional improvement per announcement. Do not mention later capabilities until they are released and verified. Use **Người Tròn** original artwork, with a distinct office scene and a short real-life test; never use the repetitive framed poster batch. No automatic social publish from private beta workflows.

For each phase:
- Verify actual public availability, account/permission behavior, user outcome and rate limiting.
- Create one Threads update focused on one benefit and one prompt/workflow example.
- Offer public link only after feature is unlocked for that audience.
- Measure actual outcomes and resolve user problems before revealing the next phase.

**Release train:** [`config/enna_clone_release_train.json`](../../config/enna_clone_release_train.json) (internal editorial, not a public changelog).
**CI:** `.github/workflows/enna-clone-cloud-ci.yml`, tests browser JS with Node, Edge TS with Deno, and private backend with Python offline unit tests.
**Important:** A green CI verifies code quality and structure; it does **not** prove a real user completed a chat successfully.

## Privacy reference

Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
Supabase function auth: https://supabase.com/docs/guides/functions/auth
Supabase CORS: https://supabase.com/docs/guides/functions/cors

Do not pass credential values in issue comments, Threads content, analytics logs or screenshots.
