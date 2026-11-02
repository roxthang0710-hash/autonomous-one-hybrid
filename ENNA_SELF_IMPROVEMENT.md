# Enna Self-Improvement — audited release 02/11/2026

## Contract

Enna is a scheduled AI editorial agent, **not an always-on autonomous programmer**. Its self-improvement operates on a bounded, reversible **editorial preference**, not arbitrary source-code edits, unapproved permissions, or uncontrolled auto-replies.

Workflow:
1. Publish through Metricool or official Meta Threads API. Metricool PUBLISHED is tracked separately from an official Meta post ID.
2. Reconcile exact text and timestamp from official `GET /me/threads`. A mismatch is **not** a successful publication verification.
3. Read genuine Meta post insights for confirmed posts.
4. At most once per local day, compare >=3 real storytelling posts with >=3 comparable practical posts, each 24h old and with numeric view/reply metrics. Missing means unknown.
5. Use a minimum 35% advantage in replies per 1,000 views and no large view disadvantage before a style switch.
6. Apply either `balanced`, `story`, or `practical` for **future generated content only**, never rewrite 26 existing Metricool bookings. Wait 48 hours between strategy changes.
7. Roll back to `balanced` first if new evidence contradicts the current strategy.
8. Log `insufficient_evidence`, `hold`, `promote_story`, `promote_practical`, `rollback_balanced` or error-safe outcomes without inventing causal follower claims.

Implementation:
- `growth/self_improvement.py` orchestrates evidence-gated decisions and policy changes.
- `threads/adaptive.py` reads `enna_learning_policy` only when `ENNA_SELF_IMPROVEMENT_ENABLED=true`; safe fallback is balanced.
- `sql/v2_3_enna_learning.sql` defines three RLS-protected, service-only operational tables.
- `.github/workflows/threads-nurture.yml` runs daily content and metric reconciliation, then observational insights and learning.
- `enna-public-status` Edge Function v2 surfaces only aggregate evidence and safe learning state to the public Enna observer; dashboard animates an illustration, not an always-on execution trace.
- `tests/test_self_improvement.py` covers insufficient observations, safe promotion, rollback, cooldown, close/mixed evidence and no post fabrication.

## Publication status 02/11

Metricool post `414010336` at 21:20 VN returned PUBLISHED, and the owner independently verified it appeared on Threads. The evidence is saved in `enna_publication_evidence` as `PUBLISHED`, with null `meta_post_id`. **Do not mark `threads_posts.status=posted` until official Meta reconciliation provides a unique media ID.** This data mismatch is a known outstanding task. The first actual learning run on 02/11 recorded `insufficient_evidence` with 0/0 qualifying story/practical posts, so policy correctly remains `balanced`.

## Topic vs Community

Meta official `POST /me/threads` accepts `topic_tag` on text container creation. `threads/publisher.py` sends an allowlisted native Topic, with office-story `conversation` pillar using `Công sở`. A successful post records `topic_tag_requested` on `threads_posts`, which proves what Enna **requested**, NOT that Threads surfaced it in discovery.

Meta's public API does **not** provide a parameter for choosing a Community destination. Native Topic Tags and Community placement must never be conflated. Enna may only post to a Community manually via the official Threads interface unless official API capability changes.

References:
- https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- https://help.metricool.com/api-limitations-per-social-network-n7zlr
- https://about.fb.com/news/2025/10/introducing-threads-communities-find-your-people/

## Boundaries

No guaranteed 1,000 followers, 24/7 execution, self-editing source, unreviewed Meta access, fake engagement, external scraping, fabricated facts or unverified live Topic/Community claim. GitHub Actions cron runs approximately and may be late; a successful CI run is not proof of a scheduled production run. The 26 queued Metricool posts are retained and remain subject to provider publication verification.
