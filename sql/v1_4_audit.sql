create table public.agent_review_audit (
 id uuid primary key default gen_random_uuid(),
 proposal_id uuid not null references public.agent_proposals(id),
 actor_id uuid,
 old_status text not null,
 new_status text not null,
 created_at timestamptz not null default now()
);
alter table public.agent_review_audit enable row level security;
revoke all on public.agent_review_audit from anon,authenticated;
grant select on public.agent_review_audit to authenticated;
grant all on public.agent_review_audit to service_role;
create index agent_review_audit_proposal_idx on public.agent_review_audit(proposal_id,created_at desc);
create policy reviewer_audit_read on public.agent_review_audit for select to authenticated
 using(exists(select 1 from public.agent_reviewers where user_id=(select auth.uid())));
create schema if not exists private;
-- Definer needed only for append-only audit: reviewers cannot insert/delete audit rows.
create function private.audit_agent_review() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if old.approval_status is distinct from new.approval_status then
  insert into public.agent_review_audit(proposal_id,actor_id,old_status,new_status)
  values(new.id,auth.uid(),old.approval_status,new.approval_status);
 end if;
 return new;
end $$;
revoke all on function private.audit_agent_review() from public,anon,authenticated;
create trigger audit_agent_review after update of approval_status on public.agent_proposals
 for each row execute function private.audit_agent_review();

create function public.recover_abandoned_agent_runs() returns integer
language plpgsql security invoker set search_path='' as $$
declare n integer;
begin
 update public.agent_runs set status='failed',error_message='WorkerInterrupted',finished_at=now()
 where status='running' and started_at<now()-interval '20 minutes';
 get diagnostics n=row_count;
 return n;
end $$;
revoke all on function public.recover_abandoned_agent_runs() from public,anon,authenticated;
grant execute on function public.recover_abandoned_agent_runs() to service_role;
