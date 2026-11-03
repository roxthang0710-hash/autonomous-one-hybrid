# Enna v0.6 — Experimental owner-approved Chrome AutoReply

**Prepared:** 04/11/2026 (VN). This is an **experimental user-local browser UI automation** path, NOT an approved Meta Threads API integration. Technical feasibility does not establish permission from Meta. Terms may restrict automated browser access, and the profile may be limited. Keep a separate Chrome profile, opt-in explicitly, and stop on errors.

## Evidence that led to v0.6
- Existing Chrome owner-selection handoff → GitHub Issue #43 → AI draft works.
- An official Meta one-shot selected-post reply experiment was implemented (source `growth/selected_direct_reply.py`, owner-only `growth/companion_selected_reply.py`).
- GitHub run **41701366676** on 2026-11-04 02:14 VN: **20/20 targeted tests PASS**, job completed; a real official reply attempt was claimed. Supabase `enna_companion_attempts` records status **`uncertain`**, `error_kind=HTTPError`, with **no `meta_reply_id`**. Issue #43 bot comment says it cannot confirm if a reply was posted and will not retry. **NO confirmed reply**, do NOT retry #43 automatically or through the browser extension.
- Added safe step-specific HTTP diagnostics for future one-shot attempts (`growth/selected_direct_reply.py` and `growth/companion_selected_reply.py`). No automated retries on ambiguous writes.

## Two mutually exclusive lanes after human selection
Owner-selected Issue title `enna-pick:<shortcode>` and public issue body (3 or 4 lines):
`ENNA_PICK_V2`, `THREADS_URL: <exact_permalink>`, `SELECTED_TEXT_BASE64URL: <utf8_payload>`, optional fourth line **`ENNA_LOCAL_BROWSER_MODE: true`**.

1. Normal mode (no 4th line): official Meta GET verifies post; on a narrow read-scope denial and a new owner Issue, one official Meta write trial is enabled by workflow. One atomic `enna_claim_selected_reply` claim and no repeat. If confirmed, store official Meta ID. If refusal known, mark `meta_rejected`. If write result ambiguous, mark `uncertain` and stop.
2. **Local Browser experimental mode (4th line, owner browser opt-in):** when Meta read scope is blocked, **do not launch the direct API-write trial**; Enna returns a contextual draft with an explicit `draft_only_meta_cannot_verify_target` state. The independently opt-in local Chrome extension polls **only the owner's selected Issue** and may open **exactly that target post** and attempt one UI reply click. If the official API already reports posted or uncertain at any time in that Issue's bot comments, browser fallback **does not run**. The extension never retrieves cookies, accesses hidden Threads API, scans the full feed, or creates bulk comments.

## Chrome v0.6
ZIP was created in the current conversation's working directory: `/mnt/data/enna_companion_chrome_v0.6_experimental.zip`. Source folder: `/mnt/data/enna_companion_extension_v06/`, based on v0.5 plus `auto-worker.js`, `auto-post.js`, and updated manifest/panel/background. **GitHub does not yet hold this ZIP/source**, so owners should save their downloaded ZIP. In new sessions never invent a sandbox link; use previous artifact attachment or ask for upload.

Chrome MV3 permissions: `sidePanel`, `tabs`, `storage`, `alarms`; content scripts for Threads domains, REST read access only to `https://api.github.com/*`. No privileged bearer token / PAT stored in the extension. The selected GitHub Issue is already public (base64 is not encryption).

### One-time user setup
1. Keep a **separate Chrome profile** actually logged in to Threads `@dohay_dilam`.
2. Disable or remove the old Companion extension, unzip v0.6, load unpacked via `chrome://extensions`.
3. Open Enna side panel, enter `dohay_dilam`, explicitly check **AutoReply experimental** and save. The extension also tries to detect the own profile permalink in the actual Threads navigation; if not found, it aborts rather than posting from an unknown account.
4. For a **NEW** safe public post, click `✳ Gửi Enna` on the post and confirm `Submit new issue` on GitHub. This remains a two-click handoff — the automatic part is after that.
5. Leave the computer and Chrome profile awake. A Chrome alarm checks that one submitted Issue ~once per minute (up to 2 hours). When bot explicitly provides a draft-only *non-posted* result, the extension opens precisely the selected post, checks the visible profile and target, fills the reply if composer is empty, and **tries to click Post once**.
6. Check the local Enna panel for status. `likely_posted` is **UI evidence only**, NOT a verified Threads post ID. `uncertain` means do not resend. `blocked` means account or DOM check failed; can require a new compatibility update, not a workaround.

### Important safeguards / limitations
- User-selected links only, 1 local browser action per VN day, dedup and 2-hour handoff expiry. Existing backend API limit is up to 3/day but the browser-only action is **not yet included in Supabase's global DB accounting**; don't report aggregate cap as synchronously enforced.
- Prompt injection ignored; server still requires real owner GitHub Issue and safe contextual draft; extension validates bot authorship, exact canonical URL, supported draft formats and prior bot statuses. It refuses any Issue with a prior Meta-confirmed or ambiguous write.
- Chrome MV3 service worker can sleep; `chrome.alarms` wakes it while browser runs. Closing Chrome, computer sleep, extensions reloading, page layout changes, reply restrictions or CAPTCHAs may prevent success.
- **No actual live Chrome/Threads auto-comment has yet been observed or verified.** The code only passes local JavaScript syntax and test simulations: `test_local.js`, `test_result.js`, `test_auto.js` + ZIP CRC validation. No DOM end-to-end test with a logged-in real Threads page has been performed.
- Threads Terms restrict automated access and potentially use of browser agents. This experimental workflow may lead to account restrictions. Do not claim it is an officially supported or risk-free way to bypass Meta App Review. Prefer a third-party publisher with genuine approved Meta permissions where available.

## Relevant documentation
- Official Meta Threads API: https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- Chrome extension background worker lifecycle: https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle/
- Threads Terms snapshot: https://tosdiff.org/document/292/snapshot/804/
- Issue #43: https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/43
- Backend workflow: `.github/workflows/enna-selected-reply.yml`
- Enna handoff: `ENNA_PROJECT_HANDOFF.md`
