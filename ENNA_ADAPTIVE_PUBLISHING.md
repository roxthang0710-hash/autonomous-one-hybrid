# Enna Adaptive Publishing — active from 02/11/2026

## What changed

The strategy is now **evaluate → publish only when suitable → observe**, instead of "post 1–2 every day" or "publish on every check". GitHub Actions evaluates roughly every two hours between 09:05 and 21:05 Vietnam time. A scheduled check can validly do nothing. GitHub cron is best-effort, not minute-accurate.

The 26 Metricool posts booked for 03–09/11, including 7 fictional office-story episodes, are **not deleted or duplicated**. Existing Metricool posts are authoritative for those slots. `threads_posts.status='scheduled_external'` is not proof that a post is published.

Enna can now prepare **at most one exploratory Meta-native extra per day while post-level evidence is insufficient**. If at least 3 different posts have valid positive view counts and at least one genuine like/reply, the system may consider up to two extras, subject to the final safety ceiling. This is NOT a quota: the number can be zero. If enough measured posts show no engagement, the extras pause.

## Safety and quality gates

- Genuine owner's Meta OAuth must be connected and automatic publishing enabled.
- Native Meta publication is only possible with live official Meta API permissions. Never bypass App Review, scrape browser UI or fake identities.
- Every candidate must pass Threads editorial policy, have a specific micro-scene or practical takeaway, natural human pacing, helpful rationale, a character/role when telling a story, and no baited follows or false real-life attribution.
- Near-duplicate content (similarity >= .75 against recent authored posts) is blocked; recently generated content isn't blindly repeated.
- The database RPC `claim_threads_post` independently checks no existing planned/actual post within **90 minutes**, a total maximum of **5 reserved/posted/uncertain items in one Vietnam-local day**, and publication between **08:00 and 22:15** only. These are absolute safety ceilings, not mandated target numbers.
- Enna never auto-retries an ambiguous Meta write; publishing stays `uncertain` until independently verified. Advisory lock prevents overlapping workers from claiming concurrently.
- The claim RPC is executable by `service_role` only, not `anon` or `authenticated`.
- Existing drafted Meta posts and Metricool slots retain their official recorded status; the SQL claim checks both `threads_posts` and `threads_metricool_schedule`.

## Files and proof

- `threads/adaptive.py`: preflight and post-generation checks, novelty and usefulness score, evidence-aware experimental cap.
- `threads/content.py`: more natural Vietnamese prompts that can generate honest practical tips or nuanced fictional office micro-stories.
- `threads/daily.py`: evaluates adaptive editorial before guarded official publishing.
- `.github/workflows/threads-nurture.yml`: multiple evaluation windows per day; a window may skip.
- `sql/v2_2_adaptive_cadence.sql`: applied via Supabase SQL on 02/11/2026. Privileges verified: anon false, authenticated false, service_role true. Atomic lock, 90m spacing, and cap 5 verified.
- `tests/test_threads_adaptive.py`: cover quality, duplicate prevention, quiet hours, spacing, daily ceiling, no-evidence cap and disabled OAuth.

## Known limitations

- GitHub Actions cron can start late or be skipped; there is no continuous real-time worker.
- Metrics from Metricool currently require external data sync. Enna's own `threads_metrics` collects real Meta observations for reconciled posts; missing observations are NOT zeros.
- Metricool does not confirm native Threads Topic Tag via this connector. Direct Meta posts use an allowlisted `topic_tag` but may need verification after publication. Topic Tag does not imply posting inside a Threads Community.
- 1,000 genuine followers before 09/11 is an ambitious KPI, not guaranteed by a higher posting frequency. Each additional post must win on utility and relevance.
- Manual toggles allow owners to stop the adaptive worker (`THREADS_ADAPTIVE_ENABLED` in workflow), or disable Meta publishing / OAuth.

## Example decision (03/11 15:05 VN)

Existing Metricool slots 09:30, 12:20, 17:40, 21:30; no post within ±90 minutes at 15:05; 4 booked total. If AI has generated a genuinely useful, original, safe post, at most one exploratory extra could be queued and published by Meta. If quality is low, or the feed changes before commit, Enna does nothing. After 5th post is reserved/confirmed, the database won't claim a 6th.

This is an **adaptive publishing mechanism**, not proof it has published any extra yet.
