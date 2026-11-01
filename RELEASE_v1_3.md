# Autonomous One v1.3 — verified handover

Session: 2 November 2026, approximately 00:32–00:47 Vietnam time. The session completed within the requested 60-minute ceiling; no unattended reactivation was scheduled.

Implementation commit: `a68604f37865552ca56cdae2acc1397ad656f2db` on `main`.

## Delivered

- Owner-private web dashboard: https://autonomous-one-control-thang.fairysage513.chatgpt.site
- Supabase Auth login with explicit reviewer enrollment and RLS. Search, status filters, pagination, approve/reject/reset review, internal task progress, recent execution history, and a local scenario calculator.
- One atomic PostgreSQL completion transaction for proposal, evaluation, internal tasks, saved synthetic baseline, run and event. Expired leases respect maximum attempts, and stale workers cannot complete a new worker's lease.
- Recovery covers failures between event claim and history/run creation. Conditional status updates avoid corrupting completed work after an ambiguous timeout. Transient reads retry; mutations do not automatically retry.
- Strict model field validation rejects nonzero declared budgets instead of relabelling them free. Logs and stored errors avoid printing private proposal titles and raw exception messages.
- Memory window expanded to 200 historical titles; similar ideas are held for review. Topic ties choose the least recently covered topic.
- Bounded internal plans with a blocked external-action step. Three deterministic hypothetical scenarios stored separately from actual experiment records.
- Dedicated secret-free CI on pushes/PRs, plus tests before every agent execution. Missing agent secrets produce a visible failed run.

## Verification evidence

| Check | Observed result |
| --- | --- |
| Local Python suite | 29 tests passed |
| JavaScript syntax | `node --check dashboard/web/app.js` passed |
| Production agent integration | [Actions run 41332979241](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41332979241), success, exact implementation commit |
| Independent CI | [Actions run 41332908526](https://github.com/roxthang0710-hash/autonomous-one-hybrid/actions/runs/41332908526), success |
| Database run | `63d55e71-9b07-4b24-afdc-d40ddffb8337`, success at 00:44:29 Vietnam time |
| Atomic output | One proposal, evaluator `rubric-v1.3`, three tasks, one simulation associated with that run |
| SQL integration | Completion rollback, replay rejection, task/simulation persistence, expired-lease recovery, exhausted pending attempt handling, reviewer read/update restrictions and worker RPC grants passed |
| Test isolation | All SQL test mutations, including disposable auth identity, rolled back |
| Security advisor | No findings after migrations |
| Performance advisor | Missing foreign-key indexes fixed; new indexes have informational unused-index notices because they are new |
| Browser | Preview rendered; three scenario calculations responded correctly. Production private ChatGPT sign-in gate observed |
| Hosted version | Site source commit `d6c5c3c44a564c499f642f2598b41e37db3a4862`, deployment `appgdep_6ae77a48d3a48191921107373ac26994`, succeeded |

Migrations applied only to Supabase project `gjdvdohylvsauphhkutw`: `v1_3_reliability` and `v1_3_task_review`. No paid services, purchases, financial transactions, real customer outreach, or changes to unrelated projects were performed.

## Owner action required

The project has zero persistent Supabase Auth users. The dashboard is deployed but authenticated browser workflows cannot be completed until the owner creates a personal account and enrolls its UUID in `agent_reviewers`. See the exact three-step instructions in README. The private Site first requires the owner's ChatGPT sign-in, then the enrolled Supabase account. No service key belongs in browser code or in chat.

Reviewer SQL policies were exercised directly with a disposable identity inside a rolled-back transaction. This is not an end-to-end browser login test. No persistent test account or password was created.

## Limits and next work

1. Memory is a bounded title comparison, not semantic/vector retrieval or a complete research ledger. Next: topic/problem fingerprints, decision notes and versioned feedback.
2. The internal plan is a three-step template, not a general autonomous task executor. Owner review remains blocked intentionally; no outreach or purchases are executed.
3. The simulator is arithmetic over declared assumptions, not market validation. Default saved baselines use zero price/cost. Browser-adjusted scenarios are local and are not saved to Supabase.
4. A full immutable decision audit trail, richer task dependencies and alerting for orphan `running` rows remain future work.
5. Historical proposals retain their existing evaluations and have no new tasks/baselines. New v1.3 cycles get the full bundle. The latest-200 backlog window remains bounded.
6. The legacy webhook was inspected but not redeployed in this session. Its authenticated production route was not exercised; GitHub owner-issue triggering was exercised instead.
7. GitHub logged Node 20 deprecation warnings for existing action versions, but execution succeeded. Upgrade verified action versions in a later maintenance change.
8. Eight pending proposals now fill the configured backlog threshold; scheduled generation is expected to pause until ideas are reviewed. Owner-requested research still obeys the daily cap.

To reverse application code, revert the implementation commit. The database migrations are additive: leave data intact while rolling back code; do not drop the new tables as a routine rollback. To remove dashboard access for a reviewer, remove its membership row through the project owner's SQL access. Re-run SQL integration checks and advisors after future policy changes.
