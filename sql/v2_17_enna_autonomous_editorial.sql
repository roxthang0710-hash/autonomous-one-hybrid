-- Enna independent content R&D queue. No browser grants, no direct publication.
create table if not exists public.enna_editorial_plans (
  id uuid primary key default gen_random_uuid(),
  brand_key text not null check (brand_key = 'do_hay_di_lam'),
  week_start date not null,
  idea_key text not null check (idea_key ~ '^[a-z0-9_]{3,80}$'),
  series text not null,
  pillar text not null check (pillar in ('work','travel','organize','conversation')),
  topic_prompt text not null,
  source_url text,
  status text not null default 'ready' check (status in ('ready','used','parked')),
  rationale_code text not null check (rationale_code in ('balanced_evergreen','provider_evidence')),
  evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  used_at timestamptz,
  unique (brand_key, week_start, idea_key)
);
create index if not exists enna_editorial_plans_ready
  on public.enna_editorial_plans (brand_key,status,created_at);
alter table public.enna_editorial_plans enable row level security;
revoke all on public.enna_editorial_plans from public,anon,authenticated;
grant select,insert,update on public.enna_editorial_plans to service_role;

-- Reviewer-only, aggregation-only operational telemetry; no raw credentials.
create or replace function public.enna_workflow_snapshot()
returns jsonb language plpgsql stable security definer
set search_path = ''
as $func$
declare
  result jsonb;
begin
  if auth.uid() is null or not exists (
    select 1 from public.agent_reviewers r
    where r.user_id = (select auth.uid())
  ) then
    raise exception 'Reviewer access required' using errcode='42501';
  end if;
  select jsonb_build_object(
    'as_of', now(),
    'events', coalesce((
      select jsonb_agg(to_jsonb(t) order by t.occurred_at desc)
      from (
        select kind,status,code,trigger_kind,occurred_at
        from public.enna_activity_events
        order by occurred_at desc limit 25
      ) t
    ), '[]'::jsonb),
    'editorial_ready', (
      select count(*) from public.enna_editorial_plans
      where status='ready' and brand_key='do_hay_di_lam'
    ),
    'editorial_used', (
      select count(*) from public.enna_editorial_plans
      where status='used' and brand_key='do_hay_di_lam'
    ),
    'last_publisher_at',(
      select max(occurred_at) from public.enna_activity_events
      where kind='publisher' and status in ('success','failed')
    ),
    'last_growth_at',(
      select max(occurred_at) from public.enna_activity_events
      where kind='growth' and status in ('success','failed')
    ),
    'last_research_at',(
      select max(occurred_at) from public.enna_activity_events
      where kind='research' and status in ('success','failed')
    ),
    'learning', (
      select jsonb_build_object('preferred_format',preferred_format,
             'version',version,'applied_at',applied_at)
      from public.enna_learning_policy where brand_key='do_hay_di_lam' limit 1
    ),
    'pending_research',(
      select count(*) from public.agent_proposals where approval_status='pending'
    ),
    'learning_latest',(
      select jsonb_build_object('decision',decision,
         'evaluated_at',evaluated_at)
      from public.enna_learning_decisions
      where brand_key='do_hay_di_lam'
      order by evaluated_at desc limit 1
    )
  ) into result;
  return result;
end $func$;
revoke all on function public.enna_workflow_snapshot() from public, anon;
grant execute on function public.enna_workflow_snapshot() to authenticated;
