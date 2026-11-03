# ENNA PROJECT HANDOFF — 2026-11-03 (Asia/Ho_Chi_Minh)

**Purpose:** stable, non-secret source of truth for new ChatGPT conversations about Enna, Enna Mini, affiliate preparation and online tracking. Verify live status against GitHub, Supabase and Metricool before reporting facts. This note is a checkpoint, not a replacement for live queries.

## Identity and boundaries
- Agent: Enna, the ongoing AI content and growth assistant for public brand **Đồ Hay Đi Làm**, Threads @dohay_dilam.
- GitHub: roxthang0710-hash/autonomous-one-hybrid, branch main. Do not rename repository, Supabase project, Meta OAuth callbacks, brand_key or account names.
- Supabase project: gjdvdohylvsauphhkutw (autonomous-one).
- Metricool brand ID: 7803567. Scheduled posts and published posts must be distinguished.
- Agent dashboard: https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/ ; Github Actions workflow logs for run evidence.
- Original account remains real; no sockpuppets, scraping, fake clicks/followers, unverified revenue. Automation does not spend money or publish affiliate links before owner approval.

## Enna Mini (free, non-commercial)
- Code: docs/enna/kit/index.html
- Intended public GitHub Pages URL: https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/kit/
- Three office utilities: (1) copy text for negotiating unexpected urgent tasks; (2) meeting action summary, copy and CSV; (3) three daily priorities.
- No user accounts, server-side work data collection or paid plan. Next development: usability improvements, multiple action items, personalization, voluntary privacy-conscious feedback. Do not claim paid-market validation.

## Public link-in-bio
- Code: docs/enna/links/index.html and approved.json
- Intended public URL: https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/links/
- Categories: desk, bag, workplace tips, night owls; includes link to Enna Mini.
- approved.json has stage pre_revenue and empty items at checkpoint. No live affiliate link. Any future revenue-marked item must be fully verified and disclosed.
- Shopee affiliate accounts and the use of Threads/link-hub as a marketing medium require official approval; an available technical link does not imply eligibility.
- Links in replies beneath **own** relevant Threads posts are a future **planned experiment**, not current marketing. One relevant disclosure-compliant reply where permitted, not spam, and subject to platform and program conditions.

## Enna affiliate preparation
- Shopee KOC registration can be attempted by the owner, but publisher approval was **not confirmed** as of checkpoint. 1,000 followers is a separate growth goal, not presumed universal KOC application minimum.
- Decision: prioritize genuine office-useful objects, editorial fit and utility rather than unverifiable commission rates.
- PRIVATE Supabase tables: enna_affiliate_candidates (8 real merchandise hypotheses), enna_affiliate_tests (3 **planned** test placements), plus affiliate_programs and other affiliate reports.
- Hypotheses: cable clips, cable pouch, laptop stand, desk organizer, daily planner, phone stand, desk lamp, power bank. These are categories, not verified Shopee SKUs.
- Placement plans: cable clips Threads bio; cable clips Threads own-post reply; laptop stand Instagram bio. All planned, not active.
- Scores 0–100 are internal editorial rank, not price/quality/sale likelihood. Grade: brand_fit×6 + reader_value×5 + story_potential×4 + affordability×3 + seller_confidence×2.
- Preserve empty vs zero. For actual click/order/commission metrics require provider/platform evidence; no fabricated data. Candidate approval requires verified publisher, seller, item, disclosures, owner approval, linked evidence, and applicable link. Database has constraints/trigger.
- Commercial tracks: affiliate work gear, brand partnerships, office digital goods; remain hypotheses without receipts.

## NEW online tracker replacing Excel as primary working tool
- Source: docs/enna/affiliate/index.html
- Intended URL: https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/affiliate/
- Browser app uses existing Supabase publishable key (never service-role) and password login via Supabase Auth. Login access requires membership in private public.agent_reviewers. There is one authorized reviewer as of checkpoint.
- Supports searching/filtering/sorting 8 candidates, editing/adding hypotheses with review fields and notes, editing/adding 3 placement plans, readouts and CSV backup.
- SQL source: sql/v2_16_enna_affiliate_online_tracker.sql. Reviewer-only SELECT/UPDATE/INSERT RLS policies on two tables were applied via direct SQL in conversation on 2026-11-03; read/write policies confirmed in pg_policies and no public anon grant. Column-limited insert/update on candidates, no delete. Do not share the authorized reviewer's email/ID.
- **Verification boundary:** source code and RLS verified; public Pages deployment/access and end-to-end browser login/writes have **NOT** been independently verified. Do not claim usable in-browser until those checks pass. If Pages fails check Actions and deployed Pages source. For authenticated tests need authorized owner participation; never request their password in chat.
- Excel is a backup/export only, not source of truth. Do not reimport blindly.

## Other known operations
- Enna posting is subject to Meta OAuth permissions; reply feature had enable_replies=true but public keyword search and App Review may block legitimate discovery. Do not assume successful replies.
- Metricool scheduled backlog of 15 posts 03–17 Nov 2026 was known; run times, follower counts and growth must be rechecked in live tools. No fabricated posting evidence.
- Daily follow-up monitoring automations exist for Enna preparing upcoming content and 1,000 real follower KPI by 09/11/2026. Consult current automations if managing them.
- Sources worth checking: README.md, RELEASE_v2_1_ENNA.md, ENNA_AFFILIATE_LINK_BIO_PLAYBOOK.md, related GitHub commits; Supabase tables; Metricool if connected.
- Never infer a current follower count or current approval state from this checkpoint; check dated data.

## Next steps in priority order
1. Verify Pages deployment and in-browser authenticated login and data edits; fix any UI or auth bugs without exposing private data. Prefer non-destructive tests; preserve 8+3 live records.
2. Improve board UX (review audit, product SKU details, verification checklist, source dates, provider evidence, click/commission records once approved), maintain separation between hypothesis and approved item.
3. Prepare owner-controlled Shopee KOC application instructions and required promotion-channel approvals. Do not register on their behalf without permission.
4. Validate Enna Mini with actual users before monetizing digital goods; keep link bio useful and non-spammy.
5. Update this file after a major decision/change, with date and evidence, so new chats have continuity.

## Resume protocol for user
In a new conversation request reading **ENNA_PROJECT_HANDOFF.md** from repository roxthang0710-hash/autonomous-one-hybrid (main); compare with live GitHub, Supabase project gjdvdohylvsauphhkutw and Metricool 7803567; list confirmed, tentative and blocked state, then continue latest task. Never prompt the user to reshare chat history or credentials if connectors can retrieve state. This prompt cannot guarantee access when connectors aren't attached.

## Password recovery enhancement (2026-11-03)
- User forgot the Supabase Auth reviewer password. Passwords cannot be retrieved in plaintext; preserve the original authorized Auth user and its public.agent_reviewers membership.
- Added a "Quên mật khẩu?" link on docs/enna/affiliate/index.html and email recovery page at docs/enna/affiliate/reset/index.html. The recovery page requests a reset email via Supabase Auth /recover and updates the password using an authenticated recovery access token through /user; no service key or passwords stored.
- Intended reset URL: https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/affiliate/reset/
- Owner must verify that this exact URL is permitted in Supabase Dashboard → Authentication → URL Configuration → Redirect URLs. Supabase email delivery must work (free SMTP has restrictions). Email used must belong to the existing Auth user.
- GitHub code was committed; public Pages live availability, actual delivery and successful password change have NOT been independently verified. Never claim success without owner verification. Do not ask owner to paste passwords/reset tokens into ChatGPT. Do not create another reviewer without explicit permission.

## Supabase Dashboard password-reset returning to /oauth/ (2026-11-03)
- User observed an actual Supabase Auth password-reset email landing on the Threads connection page /oauth/ instead of the password editor. Root cause: Supabase default Site URL points to /oauth/; the OAuth client's magic-link handler previously treated any bearer fragment (including recovery) as a normal owner login.
- Fixed docs/oauth/index.html by redirecting #type=recovery&access_token=... to /enna/affiliate/reset/ *before* Threads OAuth scripts handle it. Fixed docs/oauth/client.js with a second safety check against consuming recovery tokens as regular login.
- **Do not change the existing default Site URL /oauth/ just to solve this issue; it supports the working Threads flow.** A new password reset email is required since earlier one-time links may have been consumed. Alternatively, the dedicated reset form provides explicit redirect_to=/enna/affiliate/reset/, which must be allowlisted under Supabase Auth URL Configuration → Redirect URLs.
- Warning: GitHub commits and code paths verified; live GitHub Pages deployment and completed reset flow could not be tested from this environment. The owner should not paste recovery URL fragment, JWT, email codes or password into chat.

## Reset email quota diagnosed (2026-11-03, subsequent screenshot)
- User's Enna Affiliate reset form opens correctly, but Supabase Auth returns `email rate limit exceeded` before a new recovery email can be sent. This is not proof of bad redirect URL.
- Supabase docs: built-in Auth email provider has a shared project quota of 2 emails/hour for /recover and other email-send endpoints, plus a default 60-second per-user reset request limit. Do not repeatedly send requests. Check Authentication → Rate Limits and allow time for quota to renew; custom SMTP if production demand warrants.
- Code verification: docs/enna/affiliate/reset/index.html constructs `redirect_to = location.origin + location.pathname` and passes it to `/auth/v1/recover`. The intended destination is https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/affiliate/reset/ . Supabase actual Redirect URLs allowlist was NOT directly retrievable by the connector; owner can review it in Authentication → URL Configuration. Site URL /oauth/ retained to protect Threads sign-in.
- Updated reset page error handling to explain `email rate limit exceeded` without incorrectly labeling it a redirect problem. Public deployment and end-to-end reset still require live verification.

## Enna editorial expansion: work software, tool tips and office workflows (2026-11-03)

User explicitly requested researching and building new content lanes for sharing useful software, digital tools, methods and small work hacks; maintain youthful but natural Vietnamese voice, not constant product sales. Six lanes:
1. Phần mềm hay, đi làm đỡ cực (PowerToys and practical apps).
2. Mẹo máy tính 30 giây (Windows shortcuts).
3. Bớt khổ với bảng tính (Google Sheets).
4. AI làm trợ lý, không làm hộ suy nghĩ (prompting, fact checks, privacy).
5. Quy trình nhỏ, hiệu quả lớn (meeting, daily task planning).
6. Enna Mini – Công cụ nhà làm (truthful demonstration of existing free functionality).

Implementation:
- Research/editorial rules and 4-week plan: `ENNA_EDITORIAL_TOOL_SERIES_2026.md`.
- Sourced curated topic bank: `threads/tech_editorial.py` with 10 briefs and source links from Microsoft/Google/Enna Mini.
- Future-generation integration: `threads/content.py` calls `choose_tech_brief(len(history))` once per three newly generated posts; existing SEEDS, 4 database pillar enum values, scheduling and duplicate checks remain unchanged. Trend-driven override is skipped for that specific tool-tip selection. Adds explicit no-invented-capability editorial instructions.
- Regression checks authored in `tests/test_tech_editorial.py`.
- Online searchable **draft library**: `docs/enna/content-lab/index.html` intended at https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/content-lab/ . 14 draft captions, filter by series and week, copy text button. Drafts are public-source-based *ideas*, not Metricool scheduled posts nor approval to publish.
- Metricool brand 7803567 still contains prebooked dates through 17/11 and Supabase queue has posts through 21/11/2026 09:30 Vietnam. Preserve these; do not inject extra posts or edit old dates.
- Tech rotation only affects **new** generated content when ordinary low-watermark queue logic starts creating again. Do not claim new content has published or even been queued yet.
- GitHub code and contents confirmed from connector. GitHub Pages public availability could not be verified through web, and full repo Python tests could not run in this environment because outgoing GitHub network DNS was unavailable; unit test code exists but PASS is not proven. Re-check deployment and CI later.
- Future: compare sourced tool-tip content performance with humor/office-life once there is enough REAL Metricool and Threads data. Keep attribution, no fake tutorials/reviews and no confidential files pasted into AI.

## v2.18 — Autonomous editorial R&D and visible real worker activity (2026-11-03 evening VN)
**User's goal:** Enna should work independently of ChatGPT conversation prompts, continuously prepare valuable software/tool/workflow content, use real Threads observations to evolve a balanced editorial policy, and show real worker activity like an animated but honest agent. Do not imply continuous computing; GitHub Actions runs at discrete checkpoints.

### Existing system verified at deployment
- `.github/workflows/threads-nurture.yml` already runs at UTC 02:05,04:05,06:05,08:05,10:05,12:05,14:05 (09:05–21:05 VN). Also `.github/workflows/growth-radar.yml` has 3 research checks/day and `.github/workflows/agent.yml` has 4 research checks/day.
- Supabase audit proves scheduled worker executions with last observed publisher completion 2026-11-03 15:20Z, 6 Meta-ID confirmed posts, 18 Threads metric snapshots. Latest data available at inspection, not fabricated.
- `agent_runs` old because research proposals `approval_status=pending` = 9; `agent.py` documented cap = 8, so creating more research proposals stops intentionally (not a dead agent).
- Existing `growth/self_improvement.py` + `growth/story_insights.py` require verified, mature provider evidence and currently maintain preferred_format=`balanced`; only 2 daily Metricool observations, no valid 7-day baseline yet. No causal follower attribution.

### New deployed architecture
1. **Private Supabase R&D source of truth:** `enna_editorial_plans` created via migration `enna_autonomous_editorial_reviewer_workflow_snapshot`, migration SQL is `sql/v2_17_enna_autonomous_editorial.sql`. Worker-only SELECT/INSERT/UPDATE, no anon or authenticated table grants; RLS enabled. Columns are curated idea, source, rationale, evidence, ready/used/parked, week identity.
2. **`growth/editorial_autopilot.py`** scheduled in existing `threads-nurture.yml`, after reading actual Posts/Meta snapshots, creates up to 2 new curated briefs per Vietnam day, bounded max 8 ready, no duplicated topic within week. If 7 distinct published days AND at least 3 mature posts for 2 pillars plus a conservative performance advantage, can prefer the evidence-backed pillar while preserving diversity. Otherwise keeps balanced evergreen topics. Never creates published social posts, changes old schedules, invents follow counts or commissions, or edits code.
3. **`threads/content.py`** reads next ready source-checked plan *only during its existing 1-in-3 tech-tip rotation when queued backlog < 6*, falls back safely if plan store fails; marks plan used after actual draft successfully queued. Existing 8 queued posts and 34 booked external records remain unchanged. This is not an invitation to over-post.
4. **`growth/activity_log.py`** allows `editorial_checked`; workflow logs scheduled editorial pass with status success/failed. 7 tests authored in `tests/test_editorial_autopilot.py`; GitHub Actions test step runs before publishing, but end-to-end CI after this commit not directly verifiable from connected tools.
5. **Review-only observability API:** `public.enna_workflow_snapshot()` SECURITY DEFINER verifies `auth.uid()` membership in `agent_reviewers`; anon execute revoked. Returns safe aggregate private audit: latest workflow events, ready/used briefs, research pending count and learning policy. Private `dashboard/web/studio.js` and `state.js` now display actual worker lifecycle and accurate GitHub scheduled checkpoints.
6. **Public observability (no drafts/secrets):** Supabase Edge Function `enna-public-status` updated to ACTIVE version 13, queries private plans internally but returns only redacted aggregate `editorialAutonomy.readyIdeas, usedIdeas, lastPreparedAt, researchPendingApprovals` to public client. `docs/enna/index.html` displays counts and next best-effort scheduled checkpoint. Visual sheep animation is decorative, not proof of a worker running.

### Bootstrapping and limitations
- 2 source-curated ready ideas were inserted manually by assistant 2026-11-03 15:45Z (`windows_clipboard`, `sheets_filter_view`); explicitly tagged `initial_curated_seed` and `not_autonomous_run:true`. These initial manual seeds must NOT be described as proof the new scheduled worker has run.
- Source/API permissions checked 2026-11-03: anon cannot read plans or execute private workflow snapshot; service role can read/write; authenticated can call snapshot but function checks reviewer; Edge function shows ACTIVE. Six previously published and 8 queued Threads records remain unchanged after deployment. No new public post triggered.
- **Not yet verified:** next independent GitHub Actions run after code deployment, Python unit test PASS from GitHub CI, full client JS on a browser or public status HTTP response (web fetch unavailable). Check `Actions → Enna — Threads Content & Publishing` after next scheduled checkpoint and `enna_activity_events` for `editorial_checked`, `enna_editorial_plans` for new `not_autonomous_run`-absent ideas.
- User's Supabase Auth password recovery issue remains separate; private dashboard sign-in may require reset, but public Enna dashboard does not.
- GitHub Actions cron can be delayed/skipped by provider. Do not claim always-on or real-time performance. No direct autonomous code modification, ad spending, Affiliate publication or unsafe Threads interactions.
