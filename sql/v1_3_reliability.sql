-- v1.3: restricted review access, persistent plans and atomic completion.
create table public.agent_reviewers (
 user_id uuid primary key references auth.users(id) on delete cascade,
 created_at timestamptz not null default now()
);
alter table public.agent_reviewers enable row level security;
revoke all on public.agent_reviewers from anon, authenticated;
grant select on public.agent_reviewers to authenticated;
create policy reviewer_self on public.agent_reviewers for select to authenticated
 using (user_id=(select auth.uid()));
create table public.agent_tasks (
 id uuid primary key default gen_random_uuid(),
 proposal_id uuid not null references public.agent_proposals(id),
 position integer not null check(position>0), kind text not null,
 description text not null,
 status text not null check(status in ('pending','blocked','completed')),
 created_at timestamptz not null default now(), unique(proposal_id,position)
);
alter table public.agent_tasks enable row level security;
create table public.agent_simulations (
 id uuid primary key default gen_random_uuid(),
 proposal_id uuid not null references public.agent_proposals(id),
 result jsonb not null check(result->>'mode'='simulation_only'),
 created_at timestamptz not null default now()
);
alter table public.agent_simulations enable row level security;
grant all on public.agent_tasks, public.agent_simulations, public.agent_reviewers to service_role;
revoke all on public.agent_tasks, public.agent_simulations from anon, authenticated;
grant select on public.agent_proposals, public.agent_runs, public.agent_evaluations,
 public.agent_events, public.agent_experiments, public.agent_tasks, public.agent_simulations to authenticated;
-- Reviewers may change only approval status, never model outputs or financial records.
revoke update on public.agent_proposals from authenticated;
grant update(approval_status) on public.agent_proposals to authenticated;
do $$ declare t text; begin
 foreach t in array array['agent_proposals','agent_runs','agent_evaluations','agent_events','agent_experiments','agent_tasks','agent_simulations'] loop
 execute format('create policy reviewer_read on public.%I for select to authenticated using (exists (select 1 from public.agent_reviewers where user_id=(select auth.uid())))',t);
 end loop;
end $$;
create policy reviewer_decision on public.agent_proposals for update to authenticated
 using (exists(select 1 from public.agent_reviewers where user_id=(select auth.uid())))
 with check (exists(select 1 from public.agent_reviewers where user_id=(select auth.uid())));
create index agent_proposals_run_idx on public.agent_proposals(run_id);
create index agent_runs_event_idx on public.agent_runs(event_id);
create index agent_runs_started_idx on public.agent_runs(started_at desc);
create index agent_proposals_created_idx on public.agent_proposals(created_at desc);
create index agent_simulations_proposal_idx on public.agent_simulations(proposal_id);

create or replace function public.claim_agent_event()
returns setof public.agent_events language plpgsql security invoker set search_path='' as $$
begin
 update public.agent_events set status='failed',last_error='Exceeded retries',lease_until=null,finished_at=now()
 where attempts>=3 and (status='pending' or (status='processing' and lease_until<now()));
 return query with picked as (
 select id from public.agent_events where kind='research_request' and attempts<3
 and (status='pending' or (status='processing' and lease_until<now()))
 order by created_at limit 1 for update skip locked
 ) update public.agent_events e set status='processing',attempts=attempts+1,
 lease_until=now()+interval '9 minutes',last_error=null
 from picked where e.id=picked.id returning e.*;
end $$;
revoke all on function public.claim_agent_event() from public,anon,authenticated;
grant execute on function public.claim_agent_event() to service_role;

create function public.complete_agent_run(p_run_id uuid,p_event_id uuid,p_attempt integer,
 p_topic text,p_model text,p_sources jsonb,p_proposal jsonb,p_evaluation jsonb,p_tasks jsonb,p_simulation jsonb)
returns uuid language plpgsql security invoker set search_path='' as $$
declare proposal_id uuid; task jsonb;
begin
 perform 1 from public.agent_runs where id=p_run_id and status='running' for update;
 if not found then raise exception 'Run not running'; end if;
 if p_event_id is not null then
  perform 1 from public.agent_events where id=p_event_id and status='processing'
   and attempts=p_attempt and lease_until>now() for update;
  if not found then raise exception 'Event lease lost'; end if;
 end if;
 insert into public.agent_proposals(run_id,event_id,topic,model,research_sources,proposal)
 values(p_run_id,p_event_id,p_topic,p_model,p_sources,p_proposal) returning id into proposal_id;
 insert into public.agent_evaluations(proposal_id,score,verdict,rubric,findings,evidence_status,evaluator_version)
 values(proposal_id,(p_evaluation->>'score')::int,p_evaluation->>'verdict',p_evaluation->'rubric',
 p_evaluation->'findings','unvalidated',p_evaluation->>'evaluator_version');
 for task in select * from jsonb_array_elements(p_tasks) loop
 insert into public.agent_tasks(proposal_id,position,kind,description,status)
 values(proposal_id,(task->>'position')::int,task->>'kind',task->>'description',task->>'status');
 end loop;
 insert into public.agent_simulations(proposal_id,result) values(proposal_id,p_simulation);
 update public.agent_runs set status='success',finished_at=now() where id=p_run_id;
 update public.agent_events set status='completed',lease_until=null,finished_at=now() where id=p_event_id;
 return proposal_id;
end $$;
revoke all on function public.complete_agent_run(uuid,uuid,integer,text,text,jsonb,jsonb,jsonb,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.complete_agent_run(uuid,uuid,integer,text,text,jsonb,jsonb,jsonb,jsonb,jsonb) to service_role;
