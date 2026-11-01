# Autonomous One v1.5 — Affiliate Research handover

Implemented and verified **02 November 2026 (Vietnam)** in the existing Autonomous One GitHub repository and Supabase project `gjdvdohylvsauphhkutw`. The v1.4 core and Soát Lịch pilot are retained unchanged.

## Delivered
- Three Vietnam affiliate program leads (**Shopee KOC, ACCESSTRADE Publisher, TikTok Shop Affiliate Creator**) with official source links, eligibility caveats and **unverified** commission terms.
- Protected Supabase tables: `affiliate_programs`, `affiliate_runs`, `affiliate_opportunities`, `affiliate_metrics`; backend-only `affiliate_review_dashboard` view.
- Strict Groq JSON draft generation: customer, problem, organic channel, draft text, validation plan, metric, stop rule, risk, claims to verify, owner action.
- Deterministic review score indicating research completeness, not a chance of earning commissions.
- Tracking links remain null; predicted expenses must equal zero; disclosures added to drafts.
- New [GitHub Actions workflow](.github/workflows/affiliate-research.yml): scheduled Tuesday and Friday at **09:30 Vietnam time**, manual dispatch, and owner-only `affiliate:` GitHub Issues.
- At most 3 research runs per UTC week, up to 6 drafts pending human approval. Supabase idempotency by run key and opportunity fingerprint; re-running a job must not duplicate a draft.
- No payouts, affiliate logins, external posting, customer outreach, purchases, advertising, or paid services.

## Verified integration
- [Affiliate live run #41336504442](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41336504442): **success**.
- Retried the same GitHub job: **success**, still **1** affiliate opportunity, **1** run row.
- First candidate: Shopee KOC, travel accessories for business travelers, screening score **69/100**, review_status=`pending`, publishing_status=`draft_only`, affiliate_link=null, expected_spend_vnd=0.
- Existing [GitHub unit test workflow](.github/workflows/ci.yml) passed following the new files and schema mirror.
- Anonymous and ordinary authenticated users do not have direct SELECT access to the review view; service_role does.

## Files
- `affiliate/catalog.py`: curated programs and deterministic research priority.
- `affiliate/runner.py`: Groq research engine, validation, quotas and idempotency.
- `sql/v1_5_affiliate.sql`: schema snapshot corresponding to deployed Supabase migration.
- `affiliate/README.md`: setup, links, owner review, metrics and constraints.
- `tests/test_affiliate_*.py`: offline validation and policy regression tests.
- `.github/workflows/affiliate-research.yml`: new schedule and event workflow.

## Not complete / blockers
1. No Affiliate Publisher account or per-campaign commission details have been verified; no tracking link can be used yet.
2. Content remains a draft. Any product claims, performance metrics, social-group posting and affiliate disclosure must be checked against platform policy before publication.
3. The existing private website dashboard owner account setup is still a v1.4 blocker. Until fixed, review in Supabase Table Editor.
4. The official program catalog is a dated source snapshot, not an automatic current-offer scraper.
5. Free-tier usage limits can change. No guarantee of income or market demand.

## Next milestone
Owner registers/validates ONE Affiliate Publisher account and authorizes an owned content channel. Then integrate provider-approved product feed/links, content compliance checks and confirmed click/order/commission imports **without storing credentials in GitHub code**.

Source pages: [Shopee Affiliate](https://shopee.vn/affiliate/), [Shopee KOC FAQ](https://help.shopee.vn/portal/4/article/91992), [ACCESSTRADE Publisher](https://accesstrade.vn/access-affiliate-publisher/), [ACCESSTRADE help](https://help.accesstrade.vn/knowledgebase/quy-trinh-co-ban/), [TikTok Shop Creator policy](https://seller-vn.tiktok.com/university/essay?knowledge_id=6837793229817601).
