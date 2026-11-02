-- Enna live observatory: reviewer-only, bounded, read-only snapshot.
-- No Vault references, tokens, app secrets or owner identities returned.
begin;
create schema if not exists enna_private;
revoke all on schema enna_private from public,anon;
grant usage on schema enna_private to authenticated;
create or replace function enna_private.observatory_snapshot()
returns jsonb language plpgsql stable security definer set search_path = ''
as $$
begin
 if auth.uid() is null or not exists (
   select 1 from public.agent_reviewers where user_id=auth.uid()
 ) then raise exception 'Reviewer access required' using errcode='42501'; end if;
 return jsonb_build_object(
  'as_of',now(),
  'account',(select jsonb_build_object('username',verified_username,'status',status,
   'enable_replies',enable_replies,'expires_at',expires_at)
   from public.threads_vault_credentials where verified_username='dohay_dilam' limit 1),
  'channel',(select jsonb_build_object('auto_publish_enabled',auto_publish_enabled,
   'shopee_channel_approved',shopee_channel_approved) from public.threads_channels where username='dohay_dilam' limit 1),
  'post_counts',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb) from
   (select status,count(*) n from public.threads_posts group by status) t),
  'posts',(select coalesce(jsonb_agg(t),'[]'::jsonb) from
   (select id,status,text_content,scheduled_at,published_at,permalink from public.threads_posts
    order by scheduled_at desc nulls last limit 50) t),
  'runs',(select coalesce(jsonb_agg(t),'[]'::jsonb) from
   (select id,status,signal_count,shortlisted,drafts_created,source_summary->>'threads' discovery,
    error_kind,started_at,finished_at from public.growth_runs order by started_at desc limit 20) t),
  'drafts',(select coalesce(jsonb_agg(t),'[]'::jsonb) from
   (select id,kind,status,draft_text,relevance_reason,quality_score,created_at,expires_at
    from public.growth_opportunities order by created_at desc limit 20) t),
  'comments',(select jsonb_build_object('attempts_today',count(*) filter(where
    (attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=(now() at time zone 'Asia/Ho_Chi_Minh')::date),
    'posted_today',count(*) filter(where status='posted' and
    (attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=(now() at time zone 'Asia/Ho_Chi_Minh')::date),
    'posted_total',count(*) filter(where status='posted')) from public.growth_engagement_attempts),
  'metric_snapshots',(select count(*) from public.threads_metrics),
  'affiliate',(select jsonb_build_object('records',count(*),'commission_vnd',
    sum(confirmed_commission_vnd),'conversions',sum(conversions))
    from public.affiliate_metrics)
 );
end;
$$;
revoke all on function enna_private.observatory_snapshot() from public,anon,authenticated;
grant execute on function enna_private.observatory_snapshot() to authenticated;
create or replace function public.enna_observatory()
returns jsonb language sql stable security invoker set search_path=''
as $$ select enna_private.observatory_snapshot(); $$;
revoke all on function public.enna_observatory() from public,anon,authenticated;
grant execute on function public.enna_observatory() to authenticated;
notify pgrst,'reload schema';
commit;
