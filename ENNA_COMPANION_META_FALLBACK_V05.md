# Enna Companion v0.5 — Meta API fallback and one-click draft retrieval (2026-11-04)

## Verified cause and safe recovery

- User asked for a practical resolution after Issue #43 initially failed with `no_safe_draft`.
- Debugged `growth/companion_selected_reply.py`: incorrect Python raw regex `\\s` was left in the timestamp stripper, which also broke a preflight regression test. Fixed the matcher and added tests for a humane non-office story and no-Meta-draft path.
- The owner-only GitHub workflow `.github/workflows/enna-selected-reply.yml` now supports `/enna retry` on owner-issued Issues through `issue_comment.created`. We issued **one** controlled retry in Issue #43: https://github.com/roxthang0710-hash/autonomous-one-hybrid/issues/43
- GitHub Actions confirmed the NEW outcome, not merely a planned deployment: `🟠 Enna đã soạn bình luận nhưng Meta chưa cho phép xác minh bài mục tiêu qua API chính thức`. Supabase audit shows `companion_draft_only`, and `enna_companion_attempts` remains empty. **NO automatic Threads reply was posted.**
- Root remaining limitation is Meta's ability to read the **other account's** public Threads media via official Graph GET. An owner's chosen permalink and user OAuth cannot substitute for App Review/advanced access. Do not bypass by scraping/clicking browser DOM to post. No more uncontrolled retries.
- Python refactor: model attempts before Meta OAuth; even an expired/missing token returns a draft, not blank failure. Groq `openai/gpt-oss-20b` structured JSON support confirmed from official docs. Increased completion budget and focused prompt on *new insight*, not simply summarizing original post. Added phrase-level generic-filler gate to trigger at most one revision.

## New local extension artifact — Enna Companion Chrome v0.5

Generated `/mnt/data/enna_companion_chrome_v0.5.zip` for delivery in the **originating conversation**. Chrome extension source files inside `enna_companion_extension_v05` (manifest, background/content/panel JS/CSS, README, local tests). Path is session-specific; do not fabricate a link in future chats.

- Existing `✳ Gửi Enna` selection button unchanged: only reads one public post chosen by user, no passive feed harvesting.
- After user submits prefilled GitHub Issue, extension watches the recent Issue tab URL (not its HTML content) and remembers the Issue number in `chrome.storage.session`.
- New side-panel **Kiểm tra kết quả Enna** fetches just that Issue + its comments from the GitHub **public REST API**, validates repo, owner, issue title, canonical Threads source and `github-actions[bot]` identity; extracts only explicitly labeled draft text.
- If Meta reports a confirmed reply, panel says already posted; it will NOT invite duplicate submission. If Meta read denied but AI draft exists, button **Sao chép bình luận và mở bài Threads** copies the proposal and opens original post. **User still pastes and clicks Đăng manually.** This is human-in-the-loop, not background auto-commenting.
- No GitHub PAT or Threads access token/cookies, no page scraping or automated form submission. Extension permission added for `https://api.github.com/*`. Public GitHub API rate limits apply. Manual Issue number entry is fallback.
- Local validation: `node --check` all JS; `node test_local.js` PASS (hand-off and broad-interest post); `node test_result.js` PASS (target ownership, bot source, draft extraction and duplicate avoidance); zip integrity PASS, 10 files, ~20KB. **Chrome live DOM and API read in user's browser not independently verified.**
- v0.4 must be disabled/uninstalled before installing v0.5 at `chrome://extensions`. Load unpacked `enna_companion_extension_v05`. Chrome Side Panel result check can show issue #43 by typing 43. The most recent bot draft in Issue #43 was generically repetitive; owner should review rather than post unchanged.
- Never claim full automatic posting of third-party Threads replies absent permission, even if the Chrome extension can copy/open the post.

## Follow-up and evidence
- Production backend and GitHub owner-only retry are present. `companion_draft_only` audit confirmed. New quality prompt and filler filter committed after that retry; a future owner-selected issue would test them.
- For compliant fully automatic engagement, prioritize permitted own-account replies and an approved Meta App Review or compliant third-party provider. Avoid an unattended DOM automation bypass.
