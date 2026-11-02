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
