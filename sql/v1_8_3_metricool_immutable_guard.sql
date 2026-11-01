
-- v1.8.3: keep collision guard even after a Metricool post was confirmed via Meta.
create or replace function public.claim_threads_post(p_brand_key text)
returns setof public.threads_posts
language plpgsql security definer set search_path=public,pg_temp
as $$
declare c public.threads_channels%rowtype; p public.threads_posts%rowtype;
begin
 select * into c from public.threads_channels where brand_key=p_brand_key;
 if not found or c.status<>'connected' or not c.authorized
 or not c.auto_publish_enabled or c.platform_user_id is null or c.username is null
 then return; end if;
 select * into p from public.threads_posts x
 where x.channel_id=c.id and x.status='queued'
 and x.content_type='editorial' and x.scheduled_at<=now()
 and jsonb_typeof(x.risk_flags)='array' and jsonb_array_length(x.risk_flags)=0
 and not exists (
   select 1 from public.threads_metricool_schedule m
   where m.send_state in ('confirmed','pending','uncertain')
   and (m.planned_at at time zone 'Asia/Ho_Chi_Minh')::date =
       (x.scheduled_at at time zone 'Asia/Ho_Chi_Minh')::date
 )
 order by x.scheduled_at,x.created_at
 limit 1 for update skip locked;
 if not found then return; end if;
 update public.threads_posts set status='publishing',attempt_started_at=now(),
 updated_at=now() where id=p.id returning * into p;
 return next p;
end $$;
revoke all on function public.claim_threads_post(text)
 from public,anon,authenticated;
grant execute on function public.claim_threads_post(text) to service_role;
