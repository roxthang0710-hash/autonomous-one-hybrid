# Enna Desk v1.1 — release candidate (05/11/2026 VN)

## User-facing URL
https://roxthang0710-hash.github.io/autonomous-one-hybrid/enna/desk.html

## Shipped
- Independent web UI with sheep mascot, GitHub OAuth through Supabase Auth PKCE, direct task composer, 5 types, 3 specialized analysis roles, signed-in private history, 30-second foreground polling and proactive alerts.
- Supabase Edge Function `enna-desk`, JWT required, getUser server validation, `enna_desk_owners` allowlist tied to official GitHub provider numeric ID, service-role-only DB access, 6 requests/15 minutes, idempotency UUID.
- Safe rule-based 3-role fallback if Groq is not configured on Supabase Edge. These responses are NOT a substitute for true AI model reasoning and are labelled in the UI.
- GitHub Actions proactive `enna-desk-monitor.yml`, four runs/day VN, provider grounded notifications, duplicate prevention. One owner-only smoke trigger verified: Issue #54, run 41888241699 SUCCESS. Four owner-only notifications persisted.
- Chrome Companion v1.1 locally packaged from the exact v1.0 owner ZIP; opens independent Desk; preserves original selection and experimental AutoReply flows and tests.
- Existing public Enna dashboard now links to Enna Desk.
- Full GitHub Actions CI 41888860532 SUCCESS, including live HTTP 200 from hosted Desk and live HTTP 401/403 when calling Edge API without owner authentication.

## Not yet possible to verify without owner's browser/session
- Owner completes GitHub OAuth redirect from the hosted Desk and requests first authenticated task.
- Exact Chrome v1.1 appearance and Threads reply click on the owner's logged-in browser.
- Whether Groq is configured inside Supabase Edge (the API always has a bounded rule-based fallback).
- Actual follower growth, posting performance or external comments caused by Desk. The Desk currently provides analysis, alerts and tasks, not social publishing rights.

## Owner acceptance test
1. Open Desk URL and sign in with GitHub owner.
2. If Supabase OAuth rejects redirect, add exact URL above to Supabase Authentication > URL Configuration > Redirect URLs, then retry.
3. Send `Báo cáo KPI hiện tại và nêu 3 cải tiến có bằng chứng` in `Phòng điều hành`. Confirm 3 roles return or disclose rule-based fallback and task persists after refresh.
4. Confirm four proactive alerts in the owner-only notification area; mark one as read.
5. Open extension ZIP v1.1 (overwrite existing load-unpacked folder, then Reload) and press `🐑 Mở Enna Desk trực tiếp`.
6. AutoReply remains separate and experimental; never retry uncertain reply Issues. No Meta permissions or browser posting are used by Enna Desk.

## Architectural boundaries
- No PAT/service-role key in browser.
- Supabase user identity is checked on every request; RLS deny-by-default on three new tables.
- Never treat request for a plan as a completed social post or comment.
- Generated answers cannot execute arbitrary code, SQL, URLs, or system instructions.
- AutoReply from original extension remains limited to user-selected posts and one local browser attempt/day.
