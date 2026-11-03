# Enna — Multi-platform organic growth rollout (03–09/11/2026)

## Verification at rollout

Connected Metricool brand: Đồ Hay Đi Làm, brand ID `7803567`.
Networks connected: Threads `@dohay_dilam`, Instagram `@dohay_dilam`,
Facebook page ID `1474032685783831`.

**PENDING means booked, not published.** At the first rollout, six
cross-channel slots had `autoPublish=true`, confirmed by the Metricool scheduling API.
A second rollout on 03/11 increased this to 14 slots (seven per platform).
These bookings are visible in `enna_multichannel_posts`; Dashboard displays
upcoming slots only. This is a snapshot-based monitor, not a live Metricool API
connector inside Supabase. No automated status flip is claimed after its due time.

| Date Vietnam | Platform | Content | Media | Status at creation |
|---|---|---|---|---|
| 03/11 17:25 | Instagram | Họp 15 phút kéo dài 1 giờ 18 phút | `enna-hop-15-phut.png` | PENDING |
| 03/11 18:20 | Facebook | Chuyện họp 15 phút, vấn đề việc cần chốt | Text post | PENDING |
| 04/11 12:50 | Facebook | Tệp final, tên tập tin dễ tìm | Text post | PENDING |
| 05/11 12:45 | Instagram | Tệp final_final_2_v3 | `enna-file-final.png` | PENDING |
| 05/11 19:40 | Facebook | Nhân viên làm nhanh, nhận thêm việc | Text post | PENDING |
| 06/11 19:20 | Instagram | Bàn gọn 10/10, tìm bút 0/10 | `enna-ban-gon.png` | PENDING |

PNG assets 1080 × 1350 are generated from the repository's own
Enna SVG mascot via `scripts/generate_enna_cards.py` and published by
`.github/workflows/enna-social-cards.yml`. They are hosted publicly by
GitHub Pages and ingested successfully by Metricool, which now uses static
Metricool-hosted media URLs. Instagram posts set `isAiGenerated=true`
conservatively for illustrations derived from an AI-assisted mascot.

## Threads follow CTA experiment (four edited PENDING posts)

- 03/11 21:30 — Light CTA for after-work study/tips.
- 04/11 09:30 — CTA for practical file naming.
- 05/11 18:30 — CTA for fictional office storytelling.
- 07/11 00:55 — CTA for the night-owl audience.

The full captions were updated in Metricool and synchronized to Supabase.
Unedited slots remain a natural comparison group. The editor prompt in
`threads/content.py` only permits occasional, relevant follow invitations
when the four most recent posts lack one; it does not guarantee every eligible
post gets a CTA. No reward bait, fake engagement or repetitive spam.

## Evaluation rules

1. Track genuine per-post Meta impressions/views/likes/replies/reposts and
   Metricool followers/delta by platform when they become available.
2. Compare with/without CTA under similar formats/time windows, without
   inferring individual-post follower attribution from account-wide deltas.
3. Do not extrapolate from a few views to a follower forecast. If a CTA hurts
   engagement or makes the voice robotic, reduce its frequency and retain
   value-first content.
4. FB/IG media must be accepted by the provider; a successful schedule API
   response does not prove publication.
5. The original KPI is 1,000 real Threads followers by Nov 9, 2026;
   Facebook/Instagram growth complements this, never substitutes for it.
6. A cross-channel account connection does not grant permission to publish
   into a Threads Community via API.

## Advance preparation — verified 03/11/2026

Enna prepared in advance for the entire 03–09/11 campaign, not at the
scheduled publication minute:

- **Facebook:** 7 text-based posts, 1/day from Nov 3 to Nov 9. Four
  additional posts are booked on Nov 6 18:15, Nov 7 18:10, Nov 8 18:30,
  Nov 9 18:20 (Vietnam time). All autoPublish true and provider PENDING.
- **Instagram:** 7 posts, 1/day Nov 3–9. The earlier Nov 4 gap has been
  filled at 19:15 with `enna-ctrl-z.png`. The Nov 7, 8, 9 slots are
  12:45, 19:20, 12:45, with original prepared images
  `enna-thu-bay-nao-truc.png`, `enna-chu-nhat.png`, and
  `enna-deadline.png`. All autoPublish true and provider PENDING.
- **Original images:** The GitHub card-generation workflow built and
  verified four additional 1080 × 1350 PNGs before they were accepted by
  Metricool, using the existing original Enna mascot; no borrowed meme
  pictures or claimed human portraits.
- **Supabase:** All 14 booking records are stored in
  `enna_multichannel_posts` with provider ID/UUID, provider status, scheduled
  time, auto-delivery and media-presence flags. The public Dashboard exposes
  only aggregated counts, not drafts or account tokens.

### Early checks and actual independence

- `growth/multichannel_preflight.py`: read-only check of the next three
  Vietnam local days, detecting missing Facebook/Instagram bookings, duplicate
  slots, absent Instagram media, inactive auto-publish, provider errors, stale
  provider snapshots, and past-due unverified posts. Never claims that the
  scheduled posts have published.
- `.github/workflows/enna-autonomous-ops.yml`: runs preflight as part of
  periodic operations before publishing.
- `.github/workflows/enna-preflight.yml`: independent GitHub Actions
  check at 08:15 and 16:15 Vietnam daily, plus manual owner smoke tests.
- The owner-authorized smoke-test on 03/11 at 14:45 passed and inserted six
  `preflight_ready` events (two platforms × three dates). This proves the
  code and its journal work, **not** yet that GitHub's cron fired unattended.
- A separate ChatGPT recurring task, **Enna — Chuẩn bị nội dung trước**,
  was created for morning review of the *live* Metricool schedule and
  proactive preparation where connected integrations permit. The existing
  18:00 KPI summary remains independent. Do not claim an automation run
  before its run status is actually recorded.
- Enna public viewer displays 72-hour readiness, next unprepared date and
  overdue posts requiring provider re-verification. The Supabase provider
  table is explicitly a snapshot, not live streaming from Metricool.

### Next content horizon

The current campaign is covered through Nov 9; Nov 10 is the earliest
currently unprepared Facebook/Instagram day. Morning checks should begin
proposing the next wave before it enters the 72-hour window. Follow
engagement evidence and keep <=1 post/day per FB/IG channel while testing
organic content; don't blindly fill unbounded calendars.
