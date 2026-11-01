-- Run with project owner SQL access. Every test mutation is rolled back.
begin;
do $$
declare r uuid; p uuid; n integer;
begin
 insert into public.agent_runs(trigger_kind) values('integration_test') returning id into r;
 begin
  perform public.complete_agent_run(r,null,0,'test','test','[]','{"title":"integration only"}',
   '{"score":999,"verdict":"review","rubric":{},"findings":[],"evaluator_version":"test"}',
   '[]','{"mode":"simulation_only"}');
  raise exception 'Expected invalid score to fail';
 exception when check_violation then null;
 end;
 select count(*) into n from public.agent_proposals where run_id=r;
 assert n=0,'Failed completion left a partial proposal';
 p:=public.complete_agent_run(r,null,0,'test','test','[]','{"title":"integration only"}',
   '{"score":50,"verdict":"revise","rubric":{},"findings":[],"evaluator_version":"test"}',
   '[{"position":1,"kind":"owner_review","description":"test","status":"blocked"}]',
   '{"mode":"simulation_only","actual_spend_vnd":0,"actual_revenue_vnd":0}');
 assert (select status='success' from public.agent_runs where id=r),'Run not completed';
 assert (select count(*)=1 from public.agent_tasks where proposal_id=p),'Task not saved';
 assert (select count(*)=1 from public.agent_simulations where proposal_id=p),'Simulation not saved';
 begin
  perform public.complete_agent_run(r,null,0,'test','test','[]','{}','{}','[]','{}');
  raise exception 'Expected replay to fail';
 exception when raise_exception then
  if sqlerrm<>'Run not running' then raise; end if;
 end;
end $$;
set local role authenticated;
do $$ begin
 assert (select count(*)=0 from public.agent_proposals),'Unenrolled user can read data';
 assert not has_function_privilege('authenticated','public.claim_agent_event()','execute'),'Claim RPC exposed';
 assert not has_function_privilege('authenticated','public.complete_agent_run(uuid,uuid,integer,text,text,jsonb,jsonb,jsonb,jsonb,jsonb)','execute'),'Completion RPC exposed';
 assert not has_column_privilege('authenticated','public.agent_proposals','proposal','update'),'Model output editable';
end $$;
rollback;
select 'passed: atomic completion, rollback, replay, tasks, simulations, RLS and grants' as result;
-- Reviewer privileges are tested with a disposable identity inside a rollback.
begin;
insert into auth.users(id,aud,role,email) values ('00000000-0000-4000-8000-000000000013','authenticated','authenticated','integration-v13@example.invalid');
insert into public.agent_reviewers(user_id) values ('00000000-0000-4000-8000-000000000013');
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000013',true);
set local role authenticated;
do $$ declare n integer; begin
 assert (select count(*)>0 from public.agent_proposals),'Reviewer cannot read proposals';
 assert has_column_privilege('authenticated','public.agent_proposals','approval_status','update'),'Reviewer cannot decide';
 assert has_column_privilege('authenticated','public.agent_tasks','status','update'),'Reviewer cannot progress tasks';
 assert not has_column_privilege('authenticated','public.agent_tasks','description','update'),'Reviewer can alter task descriptions';
 update public.agent_proposals set approval_status='approved' where id=(select id from public.agent_proposals limit 1);
 get diagnostics n=row_count;
 assert n=1,'Reviewer decision failed';
end $$;
rollback;
select 'passed: reviewer read, decision and column restrictions; no test data persisted' as result;
