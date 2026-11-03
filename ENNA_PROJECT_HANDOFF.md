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
