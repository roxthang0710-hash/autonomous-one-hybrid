-- v1.1: deployed to Supabase autonomous-one by applied migration.
create table if not exists public.agent_evaluations (
  proposal_id uuid primary key references public.agent_proposals(id) on delete cascade,
  score integer not null check (score between 0 and 100),
  verdict text not null check (verdict in ('review','revise','hold')),
  rubric jsonb not null default '{}'::jsonb,
  findings jsonb not null default '[]'::jsonb,
  evidence_status text not null default 'unvalidated'
    check (evidence_status in ('unvalidated','partially_validated','verified')),
  evaluator_version text not null,
  evaluated_at timestamptz not null default now()
);
alter table public.agent_evaluations enable row level security;
create table if not exists public.agent_experiments (
  id uuid primary key default gen_random_uuid(),
  proposal_id uuid not null references public.agent_proposals(id) on delete restrict,
  status text not null default 'proposed'
    check (status in ('proposed','approved','running','completed','stopped')),
  observed_signals integer not null default 0 check (observed_signals >= 0),
  revenue_received_vnd bigint not null default 0 check (revenue_received_vnd >= 0),
  actual_cost_vnd bigint not null default 0 check (actual_cost_vnd >= 0),
  evidence_url text, owner_notes text,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists idx_agent_experiments_proposal on public.agent_experiments(proposal_id);
alter table public.agent_experiments enable row level security;
create or replace view public.agent_review_dashboard with (security_invoker = true) as
select
  p.id as proposal_id, p.created_at, p.topic,
  p.proposal->>'title' as title, p.approval_status,
  coalesce(e.score, 0) as review_score,
  coalesce(e.verdict, 'hold') as verdict,
  coalesce(e.evidence_status, 'unvalidated') as evidence_status,
  coalesce(x.experiments, 0) as experiments,
  coalesce(x.total_signals, 0) as observed_signals,
  coalesce(x.total_revenue, 0) as revenue_received_vnd,
  coalesce(x.total_cost, 0) as actual_cost_vnd
from public.agent_proposals p
left join public.agent_evaluations e on e.proposal_id = p.id
left join lateral (
  select count(*)::integer as experiments,
    coalesce(sum(observed_signals),0)::bigint as total_signals,
    coalesce(sum(revenue_received_vnd),0)::bigint as total_revenue,
    coalesce(sum(actual_cost_vnd),0)::bigint as total_cost
  from public.agent_experiments t where t.proposal_id=p.id
) x on true;
revoke all on public.agent_review_dashboard from public, anon, authenticated;
