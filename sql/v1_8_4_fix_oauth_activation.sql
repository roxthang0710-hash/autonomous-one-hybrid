-- Autonomous One v1.8.4: fix real Threads OAuth vault_save failure.
--
-- Root cause: row_number() returns bigint, while PostgreSQL has no date + bigint
-- operator. Even with zero queued posts the UPDATE statement's expression is
-- validated, causing activate_threads_channel() to fail and the surrounding
-- threads_finish_oauth() transaction (including Vault token) to roll back.
--
-- Safe change: explicit integer cast on row_number-derived day offset.
-- Existing scheduling, brand checks and service-role-only permissions remain.
create or replace function public.activate_threads_channel(
 p_brand_key text,p_username text,p_platform_user_id text
) returns integer language plpgsql security definer
set search_path=public,pg_temp as $$
declare c public.threads_channels%rowtype;
        last_external timestamptz;
        target_day date;
        changed integer;
begin
 if nullif(btrim(p_username),'') is null
 or nullif(btrim(p_platform_user_id),'') is null then
   raise exception 'Verified Threads identity required';
 end if;
 select * into c from public.threads_channels
 where brand_key=p_brand_key for update;
 if not found then raise exception 'Unknown Threads brand'; end if;
 if c.status='paused' then raise exception 'Channel paused'; end if;
 if c.username is not null and lower(c.username) <> lower(p_username) then
   raise exception 'Threads username mismatch';
 end if;
 if c.platform_user_id is not null and c.platform_user_id <> p_platform_user_id then
   raise exception 'Threads platform id mismatch';
 end if;
 if c.status='connected' and c.authorized and c.auto_publish_enabled then
   return 0;
 end if;

 select max(p.scheduled_at) into last_external
 from public.threads_posts p where p.channel_id=c.id
 and p.status='scheduled_external';
 target_day := ((now() at time zone 'Asia/Ho_Chi_Minh')::date + 1);
 if last_external is not null then
   target_day := greatest(target_day,
           (last_external at time zone 'Asia/Ho_Chi_Minh')::date + 1);
 end if;

 update public.threads_channels
 set username=lower(p_username),platform_user_id=p_platform_user_id,
 status='connected',authorized=true,auto_publish_enabled=true,updated_at=now()
 where id=c.id;

 with ordered as (
    select id, (row_number() over(order by scheduled_at,created_at,id)-1)::integer as n
    from public.threads_posts
    where channel_id=c.id and status='queued'
 )
 update public.threads_posts p
 set scheduled_at=((target_day + ordered.n)::timestamp +
    interval '9 hours 30 minutes') at time zone 'Asia/Ho_Chi_Minh',
 updated_at=now()
 from ordered where p.id=ordered.id;
 get diagnostics changed=row_count;
 return changed;
end $$;
revoke all on function public.activate_threads_channel(text,text,text)
from public,anon,authenticated;
grant execute on function public.activate_threads_channel(text,text,text)
to service_role;
