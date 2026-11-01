-- Owners can mark internal preparation complete; external-action gate stays blocked.
grant update(status) on public.agent_tasks to authenticated;
create policy reviewer_task_progress on public.agent_tasks for update to authenticated
 using (kind<>'owner_review' and status in ('pending','completed') and exists(
 select 1 from public.agent_reviewers where user_id=(select auth.uid())))
 with check (kind<>'owner_review' and status in ('pending','completed') and exists(
 select 1 from public.agent_reviewers where user_id=(select auth.uid())));
