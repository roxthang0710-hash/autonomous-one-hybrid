# Threads uncertain publication — safe runbook

An Actions job marked success does not prove that a Threads API write succeeded.

## Safety rules
1. When `threads_publish_attempts.outcome='uncertain'` or `threads_posts.status='uncertain'`, **never retry Meta POST automatically**.
2. Read `threads_publish_attempts`, `threads_posts`, job logs and official account's published media; match post content, timestamp, and ID.
3. Confirm publication only with authoritative Meta evidence; persist verified post ID and permalink via existing tested reconciliation path.
4. An empty or denied read is not proof of failure. Keep `uncertain` until sufficient evidence exists.
5. Report three separate outcomes: GitHub workflow status, API attempt status, verified publication status.
6. Do not change OAuth permissions or post a replacement while reconciling.

## Open incident — 2026-11-05
- `post_id`: `53db9021-5a53-4786-87b4-dd08555bd3d6`
- `operation`: `publish_text`; `outcome`: `uncertain`; `error_kind`: `HTTPError`
- No verified remote post ID.
- Action: https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/42000639174

## Read-only checks
```sql
SELECT attempted_at, post_id, operation, outcome, error_kind, remote_post_id
FROM public.threads_publish_attempts WHERE outcome='uncertain'
ORDER BY attempted_at DESC;

SELECT id, status, platform_post_id, permalink, published_at
FROM public.threads_posts WHERE status='uncertain'
ORDER BY updated_at DESC;
```

This runbook does not itself fix the publisher or authorize retrying a write.
