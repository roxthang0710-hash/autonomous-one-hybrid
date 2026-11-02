# Enna — live observatory

Private owner dashboard for Autonomous One / Đồ Hay Đi Làm. Static frontend uses the existing Supabase Auth reviewer account. No service role or Meta credentials are delivered to the browser.

## Operations

- `dashboard/web/state.js`: truthful state derivation; old/future/stalled runs are never shown as active work.
- `dashboard/web/studio.js`: 30-second foreground polling, explicit stale/error state, read-only post queue, bounded execution history and recorded reasons.
- `backend/observatory.sql`: deployment snapshot of reviewer-only RPC. Privileged aggregation is in `enna_private`, public wrapper is SECURITY INVOKER; anonymous/non-reviewer calls fail. Existing backend tables remain inaccessible to browser roles.
- Existing proposal review, task management and local simulation remain available.
- Schedule shown is the configured expectation, not a promise of execution. Pending/Metricool scheduling is not a confirmed publication. Missing affiliate data is not represented as zero earnings.
- Animations are illustrative; work movement only represents a recent running research record. Reduced-motion preferences and manual motion toggle are supported.

## Validation

`node --test tests/test_observatory.cjs` (10 cases).
`node --check dashboard/web/app.js && node --check dashboard/web/studio.js`.
Database integration checked reviewer success, non-reviewer rejection and no anon/Vault-table privileges. Browser exercised local test fixtures for waiting state, filtering, motion toggle and inert HTML-like draft text. Fixtures are not deployed. End-to-end login with the owner's password was not performed in this session.

## Rollback

Deploy the previous Site version. The additive read-only RPC can remain in place; to remove it, drop public.enna_observatory() then enna_private.observatory_snapshot(). No existing worker, OAuth, schedule, or customer data is modified by this dashboard release.
