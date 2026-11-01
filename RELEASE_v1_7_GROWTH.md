# Autonomous One v1.7.2 — Growth Radar / Threads Engagement

Verified 2026-11-02 (Asia/Ho_Chi_Minh). Upgrade of existing repo, preserving the earlier Affiliate and Metricool schedule.

## Delivered
- Two scheduled research sweeps daily, **09:15 and 17:15 Vietnam time** via `.github/workflows/growth-radar.yml`
- Public, source-attributed signals from Google Trends VN RSS and narrow Google News RSS queries
- Deterministic relevance, 96-hour freshness and safety filtering, including rejection of unrelated labor-migration / politics / health / controversy
- One original Vietnamese Groq content draft per relevant run, saved into private Supabase `growth_opportunities` with a source link; rolling cap 5 drafts/7 days
- Optional official Meta Threads keyword search (`threads_keyword_search` permission) for identifying timely genuine discussions
- Optional genuine Threads reply worker (OAuth-only, disabled by default), strict real-account identity, max 1/day, no links/affiliate pitches, idempotent attempt log and no retry after an ambiguous write
- Evidence-based analysis from `growth_metricool_daily` after at least seven days and five real published posts; insufficient samples are explicitly labelled
- Private tables `growth_signals`, `growth_runs`, `growth_opportunities`, `growth_metricool_daily`, `growth_engagement_attempts`, and restricted views

## Live verification
- Run [41344931287](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41344931287): success, 75 public signals observed, 14 relevant prospects, 1 Groq draft stored
- Run [41345825735](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41345825735): success, 74 public signals observed, 14 relevant prospects, 1 additional draft stored, optional reply worker safely skipped
- Supabase has **2 growth drafts**. **0 replies have been sent by Growth Radar**. No confirmed income or affiliate links
- GitHub CI passed following the newer source filtering and mock reply tests
- Older unrelated labor-migration signals were manually reclassified as rejected with an audit trail

## Limitations
1. Metricool on chat is connected, but its *server-to-server API* requires Advanced/Custom; GitHub cannot schedule further Metricool posts unattended via the chat connector.
2. Existing 15 Metricool posts remain scheduled for 03–17 November 2026 and are not modified by Growth Radar.
3. No Meta Threads search/reply OAuth is configured in GitHub; do not claim actual Threads hot debates were read or replied to.
4. Viral reach, engagement and Affiliate income cannot be inferred from keyword interest or a small number of posts.
5. The response engine is specifically designed for genuine useful participation and rejects impersonation, undisclosed promotions and mass replies.

## Files
- `growth/sources.py`, `growth/scoring.py`, `growth/generator.py`, `growth/runner.py`
- `growth/conversations.py` and `growth/engage.py`
- `growth/optimizer.py`, `growth/report.py`, `growth/README.md`
- `.github/workflows/growth-radar.yml`
- `tests/test_growth_*.py`
