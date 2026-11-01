# Autonomous One v1.8.3 — Long-Running Threads Growth + Owner OAuth

Verified on 2026-11-02, Vietnam time.

## What is deployed

- Supabase Edge Function **threads-oauth**, active **v3**, public entry page at https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth . It contains a Supabase-Auth-protected owner-only OAuth start endpoint and a one-time CSRF-state-validated public Meta callback. The callback verifies @dohay_dilam before storing anything.
- Encrypted Meta Threads credential vault: secret and token values are encrypted using Supabase Vault; only service-role RPCs can retrieve them. One-time OAuth sessions expire after 10 minutes.
- GitHub Actions daily Threads workflow updated: after owner OAuth, the agent can renew long-lived Meta tokens without requiring token copy-paste into GitHub, generate drafts and publish from the verified Threads account.
- Threads publish database collision guard checks the immutable Metricool appointment ledger. The 15 scheduled Metricool posts (03–17 November) will not be double-posted from GitHub. New drafts begin after their last booked day.
- Growth Radar integration uses the same verified owner token when growth scopes are approved. The optional reply checkbox remains unticked by default. With explicit consent and authorization, the system may send a maximum of one useful, on-topic, noncommercial reply per day.
- A source-attributed content selector and just-in-time trend replacement allow **up to two relevant trend posts per rolling week**, based on current evidence and only before the post is published.
- A reconciliation worker uses real Meta GET /me/threads IDs, exact text, and timestamps to confirm which Metricool-scheduled posts were actually published; only then is the post marked posted and made available for Meta insights.

## Verified tests

- [Owner OAuth portal smoke test 41348403916](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41348403916) **SUCCESS**: public HTML and JavaScript load correctly; unauthenticated /start rejected (401); bad callback state rejected (400). Previous test 41348332979 failed due to Edge route normalization, fixed and redeployed before the successful test.
- Full Python / JavaScript CI passed including encrypted credential lifecycle, Vault-based OAuth readiness, wrong-account and expired-token rejection, cross-provider scheduling, fresh trend policy, original content safety, and Meta ID reconciliation.
- Supabase restricted function access verified: anon and authenticated cannot execute sensitive token RPCs, service_role can.
- Meta OAuth application **has not yet been created/authorized by the account owner**: Supabase Vault connection count was 0 at verification. **No live Meta API post/reply or Meta-token exchange can honestly be claimed.**

## Exact steps the owner has left

1. At https://developers.facebook.com/apps/ create an app for **Threads API**.
2. Enter exact valid redirect URI in Threads App settings:
   https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth/callback
3. Add @dohay_dilam as Threads Tester, and accept the invitation in Threads > Settings > Account > Website permissions > Invites.
4. Copy Threads App ID and Threads App Secret *only* to https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth, after signing in with the existing owner Supabase Auth account.
5. Optionally opt into one per day genuine reply when Meta grants permissions. Otherwise leave reply option unchecked for standard publishing access.
6. Accept Meta's OAuth permission screen for @dohay_dilam. Server handles code exchange, Vault encryption, exact account checks, refresh and queued publish activation.

No password, token, code or App Secret should be pasted into public GitHub, chat, or stored in plaintext.

## Operating limits and why

- No automated engagement without a real owner token and explicit consent. No fake personas, fake testimonials, group spam, brigading, aggressive reply bursts, or unapproved Shopee affiliate links.
- No fabricated views, clicks or revenue. Metrics remain unavailable if Meta has not returned numeric data.
- Google News/Trends signals are distinct from actual Threads trending discussions; native Threads search requires extra permissions.
- GitHub scheduled execution is best-effort; even valid OAuth access can be interrupted by service outages, rate limits, user revocation or app review.
- Supabase Auth security advisor still warns that leaked-password detection is disabled; this is an account-setting issue, not a new public database permission. Newly added backend-only tables intentionally have RLS on with no anon/authenticated policy.

## Implementation entry points

- [threads/OAUTH.md](threads/OAUTH.md) — steps, permissions and portal
- [threads/README.md](threads/README.md) — daily operation and policies
- [supabase/functions/threads-oauth/index.ts](supabase/functions/threads-oauth/index.ts) — Edge Function
- [threads/credentials.py](threads/credentials.py) — token refresh + Vault
- [threads/daily.py](threads/daily.py) — scheduler
- [threads/reconcile.py](threads/reconcile.py) — Metricool reconciliation
- [threads/trends.py](threads/trends.py) and [threads/refresh.py](threads/refresh.py) — verified topical posts
- [growth/runner.py](growth/runner.py), [growth/engage.py](growth/engage.py) — trend research and opt-in authentic conversations
