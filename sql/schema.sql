-- Already applied to Supabase project autonomous-one, 2026-11-01.
-- Safe to keep under version control for reproducibility. No public RLS policies.
create table if not exists public.agent_events (
 id uuid primary key default gen_random_uuid(),
 request_id text not null unique,
 kind text not null check(kind in ('research_request','feedback')),
 payload jsonb not null default '{}'::jsonb,
 status text not null default 'pending' check(status in ('pending','processing','completed','failed')),
 attempts integer not null default 0,
 lease_until timestamptz,
 created_at timestamptz not null default now(),
 finished_at timestamptz,
 last_error text
);
create index if not exists agent_events_queue_idx on public.agent_events(status,created_at);
create table if not exists public.agent_runs (
 id uuid primary key default gen_random_uuid(),
 started_at timestamptz not null default now(),
 finished_at timestamptz,
 trigger_kind text not null,
 event_id uuid references public.agent_events(id),
 status text not null default 'running' check(status in ('running','success','failed')),
 error_message text
);
create table if not exists public.agent_proposals (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references public.agent_runs(id),
 event_id uuid unique references public.agent_events(id),
 topic text not null,
 model text not null,
 research_sources jsonb not null default '[]'::jsonb,
 proposal jsonb not null,
 approval_status text not null default 'pending' check(approval_status in ('pending','approved','rejected')),
 created_at timestamptz not null default now()
);
alter table public.agent_events enable row level security;
alter table public.agent_runs enable row level security;
alter table public.agent_proposals enable row level security;
create or replace function public.claim_agent_event()
returns setof public.agent_events
language plpgsql security definer set search_path = ''
as $$
begin
 update public.agent_events set status='failed',last_error='Exceeded retries',lease_until=null
 where status='processing' and lease_until < now() and attempts>=3;
 return query
 with picked as (
  select id from public.agent_events
  where status='pending' or (status='processing' and lease_until < now() and attempts<3)
  order by created_at asc limit 1 for update skip locked
 )
 update public.agent_events e
 set status='processing', attempts=attempts+1,
 lease_until=now()+interval '9 minutes',last_error=null
 from picked where e.id=picked.id returning e.*;
end;
$$;
revoke all on function public.claim_agent_event() from public,anon,authenticated;
grant execute on function public.claim_agent_event() to service_role;
