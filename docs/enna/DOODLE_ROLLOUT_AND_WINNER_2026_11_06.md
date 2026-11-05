# ENNA — Doodle 3.1 / Rollout actual & KPI signal (06 November 2026)

## Verified source of current numbers
Metricool connected to brand `7803567` ("Đồ Hay Đi Làm"), queried 06 Nov 2026 for period 01–05 Nov.

| Threads KPI | Value | Caution |
|---|---:|---|
| Outstanding post (05 Nov, 3 Windows shortcuts) | **4,370 views** | Snapshot as returned by Metricool, not platform live counter |
| Post likes | **69** | 05 Nov post only |
| Replies / reposts / shares | **3 / 4 / 7** | Can update asynchronously |
| Second strongest (03 Nov, shortcut article) | **2,069 views** | Same broad practical-tech topic |
| Median across 16 posts with reported views | **128** | Small sample, not a causal counterfactual |
| Threads followers on 04 Nov | **6** | Metricool evolution |
| Threads followers on 05 Nov | **21 (+15)** | DO NOT attribute +15 to a particular post |
| Account post views on 05 Nov | **4,854** | Metricool evolution, differs from per-post lifetime totals |
| Account profile views 05 Nov | **2,636** | Metricool evolution |

Winning post: https://www.threads.com/@dohay_dilam/post/DfV9pSaCiCK

**Editorial learning:** Practical, quickly useful, specific tech/work-life tips (“save it for later”) are consistently visible among top two posts. Illustrations should make those posts more memorable and shareable; no evidence yet shows doodles outperform text. Retain strong text-only formats for storytelling and niche conversation.

## What changed in real Metricool planner

14 ORIGINAL hand-drawn 1080×1350 PNGs generated and visually inspected, stored in existing Supabase media bucket, scheduled into **existing** PENDING slots (no new posts, no moved times, no UUID change). Confirmed by second live getScheduledPosts after tool updates: all 14 use **one Metricool-uploaded image each**, `autoPublish=true`, status `PENDING`.

- **2026-11-06 09:30 VN | Threads | `keyboard-rescue`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=8595030504777599850)
- **2026-11-06 12:20 VN | Threads | `twenty-urgent`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=2388644511915855276)
- **2026-11-06 19:20 VN | Instagram | `pen-missing`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-2390957387466191014)
- **2026-11-07 00:55 VN | Threads | `twelve-tabs`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-2242191102580667288)
- **2026-11-07 18:10 VN | Facebook | `weekend-brain`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-639766684539597589)
- **2026-11-08 09:30 VN | Threads | `headphones-left`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-8569019919648210208)
- **2026-11-08 18:30 VN | Facebook | `sunday-outfits`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-2179202125705492576)
- **2026-11-08 19:20 VN | Instagram | `sunday-anxiety`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=6312388424356349699)
- **2026-11-09 09:30 VN | Threads | `desk-hoarder`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-8911964076213057691)
- **2026-11-09 12:20 VN | Threads | `meeting-fast`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-705734222378480858)
- **2026-11-11 09:30 VN | Threads | `packing`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-4609536453140724294)
- **2026-11-12 09:30 VN | Threads | `accessory`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=3596593620645728090)
- **2026-11-13 09:30 VN | Threads | `cable-spaghetti`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=5717249331600641898)
- **2026-11-14 09:30 VN | Threads | `five-desk-items`** — [Planner](https://app.metricool.com/planner/calendar?blogId=7803567&openWithPostUuid=-6235659805054909144)

**2 FB / 2 Instagram / 10 Threads slots.**

## Data and safety
- `scripts/enna_doodle_batch.py` : 14 distinct fictional comic drawings. All source image assets are originals drawn with Python Pillow; no scraped image templates or copied social memes. Existing authentic cat photos unchanged.
- `.github/workflows/enna-doodle-batch.yml`: CI tests PNG and source hashes. Manually/owner-triggered run uploads to storage and the `enna_media_ideas` review queue. Never calls social posting APIs.
- Image upload run #42090727659: https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/42090727659
- Corrected shortcut media run #42091397690: https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/42091397690
- Shortcut poster was corrected to **Ctrl + Shift + Esc / Win + E / Win + L** to exactly match the already-booked Threads caption. Mismatched old version marked **rejected** in catalog.
- Current editorial-review assets remain `needs_review` in private ledger; scheduled posts are PENDING and must not be counted as public or as engagement.
- 14 scheduled slots registered in `public.enna_visual_rollouts` with `format_key=illustrated_meme`; four FB/IG post IDs and seven internal Threads calendar IDs synchronized after Metricool replaced numeric IDs.
- 05 Nov account insights persisted in `growth_metricool_daily` and active sprint `enna_growth_sprints`.

## What Enna should learn next

1. Check the provider after each scheduled time: status and actual public URL; never retry or resubmit simply because a post's status is uncertain.
2. Compare next-day and 7-day metrics per format (text-only vs illustrated, practical tech vs office humor, time slots). Explicitly report views, shares, replies, save rate where API supports it, and *total net follower change* without inventing per-post attribution.
3. Do not replace the user's already confirmed **cat real-photo reaction** with cartoons. Do not replace all Threads with images; reserve text-only for thoughtful debate/story posts.
4. Do not make broad claims of viral success or follower conversion until next published-post snapshots are verified.

Current snapshot is **14 PENDING illustrated media slots, 0 newly verified published**.
