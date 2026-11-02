# Enna — Organic Threads Growth Sprint, 02–09/11/2026

## Objective, baseline and hard limits
- Target: **1,000 authentic followers by 09/11/2026**, a stretch KPI, NOT a promised result or guaranteed forecast.
- Baseline: Metricool Threads evolution reported **0 followers on 01/11** (THEV01), with no reliable 02/11 follower value. Never claim follower count for 02/11 before provider confirms.
- By 09/11, compare **verified** follower metric to baseline and target; record daily actuals rather than imputing zeros.
- Only operate from genuine `@dohay_dilam`. No purchased followers, coordinated/inauthentic engagement, multi-account seeding, follow/unfollow, DM spam or engagement bait. No automatic comments without official Meta permission, relevant public source and safety policy.
- Do not edit or bypass Meta OAuth flags, 3-replies/day safety cap, author cooldown, consent or app review restrictions.

## Executed campaign changes
- Rewrote the seven Metricool 09:30 posts for 03–09/11 with original, concrete advice + natural humor. Each retains its original UUID, date, native Threads provider and autoPublish=true.
- Added three distinct evening conversations 04, 06, 08/11 at 19:15 local. Total during 03–09/11: **10 scheduled posts** (7 morning + 3 evening), not 10 confirmed publications.
- Preserved all other previously scheduled posts. Do not duplicate into the Supabase direct Meta queue; Metricool handles these. Pre-existing Enna direct posts remain outside reserved Metricool slots.
- Live replies remain through `growth.engage` using official Meta API, owner OAuth, max 3 eligible organic replies/day. As of the latest test, Threads keyword search returned `empty_keyword_results` and confirmed replies = 0; never fake comments or infer that seeding succeeded.

## Seven-day editorial experiment
- Pillar A: work-day comedy with a specific human problem, NOT generic engagement prompts.
- Pillar B: mini practical advice people can save/share.
- Pillar C: genuine open-ended conversations on work and office life.
- Evening posts only on alternating days, so each morning post has time to circulate. Do not exceed scheduled frequency merely to reach a quota.
- The 03/11 morning post is a work-desk organization quick win; 04/11 evening is a short-meeting trope; 06/11 evening is a familiar office moment; 08/11 evening is a Sunday planning prompt.
- Avoid exaggerated promises, copied memes, invented personal anecdotes, product claims, engagement trading or affiliate CTAs.

## Measurement and decision gates
Each day through 09/11 retrieve the official Metricool Threads evolution metrics `THEV01` (followers), `THEV03` (delta followers), `THEV02` (published posts), `THEV05` (interactions), `THEV06` (views) and, for posts, `THPO08`–`THPO12`. Distinguish complete days vs today, and NULL from 0. Record actual deltas, profile conversion if provider exposes enough metrics, and topic engagement per real post.
- Day 1–2: confirm publication, follower baseline and first interactions. If metrics are delayed, label unavailable.
- Day 3–4: identify genuine discussions and which post patterns drew meaningful replies/saves/shares; do not declare statistical winners from tiny samples.
- Day 5–7: adjust subsequent *unpublished* posts only if verified evidence supports it, not just AI intuition.
- Postmortem: follower count vs 1,000; actual posts published; replies by owner account confirmed; genuine interactions and view metrics; no claim about sales.
- Review the need to repeat every post with the same hook. Lack of evidence is reason to collect data, not to accelerate spam.

## Main blocker
Official Threads keyword search returned `empty_keyword_results` on multiple growth runs 02/11. Meta App Review/permission limitations must be handled by official process. The agent must NOT scrape the interface or simulate comments to meet KPI.

## Links
- Metricool Threads brand: ID 7803567
- `growth/runner.py` and `growth/engage.py`: current research / genuine reply workflow.
- `.github/workflows/growth-radar.yml`: 09:15, 14:15, 19:15 VN best-effort research schedule.
- `ENNA_EVIDENCE_LOOP.md`: evidence and revenue truthfulness policy.

## 02/11 evening audit — V2: 26 posts and official-API diagnosis

The owner requested a Threads-native growth plan instead of 1–2 generic posts/day.

### Content schedule — now saved in Metricool
- **26 scheduled Threads posts** across 03–09/11: 4, 4, 3, 4, 4, 4, 3 per day (confirmed by getScheduledPosts).
- The initial 7 morning posts remain reworked; 3 evening posts from V1 remain; 16 additional original posts were scheduled with distinct times 12:20, 17:40/18:30, 21:30/22:00 as applicable.
- Each is `PENDING`, `autoPublish=true`. *Scheduled does not mean published.* No affiliate links, follow trades, invented experience or misleading sales claims.
- Editorial families: office humor, useful work-tech tips, study/work-life learning, organizing desks, travel bag habits, and open-ended peer discussion. Prefer a useful point even if no one replies.
- Trial frequency 3–4/day is an **experiment**, not an official Meta algorithm guarantee. Meta guidance reports correlation between more posts and impressions; it does not promise outcomes or necessarily recommend four daily posts.
- Keep same-account organic comments capped at 3/day, only on qualified fresh posts under official rights. Never substitute scripted seeding/fake accounts or paid engagement.

### Native Topic tags — verified limitation
- Meta's official Threads API supports `topic_tag` as a separate field, not merely a literal hashtag in text.
- A live Metricool create-post test supplied `threadsData.topicTag`; Metricool accepted the scheduled text but stripped the `topicTag` field from its response. **Do not claim** Metricool's 26 posts have native Topics attached. Some posts contain one topical hashtag in text, which is not verified as a native Topic tag.
- `threads/publisher.py` now adds an allowlisted native `topic_tag` (Công sở / Du lịch / Góc làm việc / Đời sống đi làm) to future *direct Meta posts*, only when they are already due and independently authorized. This does not migrate, duplicate or alter existing Metricool scheduled content.
- For profile Topic settings, the existing tools do not provide a verified edit endpoint; do not claim they were updated.

### Official search diagnosis on 02/11 — evidence, not guesswork
- Workflow `.github/workflows/threads-search-diagnostic.yml` ran **GET-only** with the existing owner-granted OAuth token, safe counters only; no content/tokens were logged.
- Verified GET `/me` correct brand account and GET `/me/threads` returned one owned post.
- Official `/keyword_search?q=làm việc` returned one **owned** post. Queries for `bàn làm việc` (RECENT), `công sở` (TOP), `văn phòng` (TAG, TOP), and a narrow own-post phrase returned zero raw posts. No foreign posts were returned by these checks.
- This strongly suggests **scope-limited Meta search or App Review access**, not missing real public conversations. It is not proof of review outcome: only the Meta App Dashboard/official permission review status can confirm the cause.
- The old `growth/conversations.py` counted self posts only *after* dropping posts older than 24 hours, which could incorrectly label scope-limited results as absent; fixed. `growth/runner.py` now rotates broader TOP/RECENT queries and uses a bounded own-post control when no external post appears.
- Relevant official search and post docs: https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api and Meta's Topics official update: https://about.fb.com/news/2025/03/new-threads-features-more-personalized-experience-you-control/
- Automated external replies remain **0 confirmed** as of diagnostic. Zero search results are not evidence that viral conversations are absent. The direct search API does not expose reliable public like/view rankings to this app.

### Learning loop & decision triggers
- Daily Metricool follower count from `THEV01`, change `THEV03`, published posts `THEV02`, interactions `THEV05`, views `THEV06`, post-level fields when available.
- Segment posts by work humor, practical how-to, study, gadget/desk, leisure conversation, travel; compare actual views and substantive replies *per post*, not only raw frequency.
- After 48–72 h: if verified data show one topic consistently performs better and samples are meaningful, prioritize it in **future unpublished slots**. Never retroactively assign native Topic tags or modify old posts.
- If repeated posts have negligible reactions or users complain about volume, decrease to 2–3/day; if interactions stay healthy and people follow, keep 3–4/day; no guessed follower growth.
- One existing ChatGPT KPI automation was updated to track 26 scheduled posts and the App Review blocker; it does not self-deploy code or silently change your Metricool plan.
- No monetization until audience/engagement evidence and legitimate affiliate approval are present.
