-- E2: private, immutable-key evidence of an actual one-action agent cycle.
-- Service worker only; no public reads or deletes.
create table if not exists public.enna_agent_goal_runs (
  run_key text primary key check (run_key ~ '^enna-e2:[0-9]{8}:[0-9]{1,2}$'),
  brand_key text not null default 'do_hay_di_lam' check (brand_key='do_hay_di_lam'),
  status text not null check (status in ('running','verified','no_safe_action','blocked','unverified')),
  selected_action text,
  selected_goal text,
  chosen_verifier text,
  observed_at timestamptz,
  source text,
  result_code text not null default 'started',
  candidates integer not null default 0 check(candidates between 0 and 50),
  verified_at timestamptz,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  external_social_writes integer not null default 0 check(external_social_writes=0),
  money_spent_vnd integer not null default 0 check(money_spent_vnd=0),
  constraint enna_goal_cycle_consistent
  check ((status='verified') = (verified_at is not null))
);
create index if not exists enna_agent_goal_runs_recent
 on public.enna_agent_goal_runs (brand_key,started_at desc);
alter table public.enna_agent_goal_runs enable row level security;
revoke all on public.enna_agent_goal_runs from public,anon,authenticated,service_role;
grant select,insert,update on public.enna_agent_goal_runs to service_role;
comment on table public.enna_agent_goal_runs is
 'Enna one-action evidence ledger, no raw prompts, tokens, unpublished copy, financial or personal data; service_role only.';