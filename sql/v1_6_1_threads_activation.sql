-- v1.6.1: rebase the editorial calendar to the day after real account OAuth.
-- Called only after Meta /me confirms username and id, and GH enable switch is true.
create or replace function public.activate_threads_channel(
    p_brand_key text, p_username text, p_platform_user_id text
)
returns integer
language plpgsql security definer set search_path=public,pg_temp
as $$
declare c public.threads_channels%rowtype;
        changed integer;
begin
 if nullif(btrim(p_username),'') is null
    or nullif(btrim(p_platform_user_id),'') is null then
   raise exception 'Verified Threads identity is required';
 end if;
 select * into c from public.threads_channels
 where brand_key=p_brand_key for update;
 if not found then raise exception 'Unknown brand'; end if;
 if c.status='paused' then raise exception 'Paused channel cannot activate'; end if;
 if c.status='connected' then
   if lower(c.username) <> lower(p_username)
      or c.platform_user_id <> p_platform_user_id then
      raise exception 'Connected identity mismatch';
   end if;
   return 0;
 end if;
 update public.threads_channels
 set username=lower(p_username), platform_user_id=p_platform_user_id,
     status='connected', authorized=true, auto_publish_enabled=true,
     updated_at=now()
 where id=c.id;

 -- All queued posts are spaced one/day starting NEXT local morning at 09:30.
 -- Nothing is sent during account activation.
 with ordered as (
   select id, row_number() over(order by scheduled_at,created_at,id)-1 as n
   from public.threads_posts
   where channel_id=c.id and status='queued'
 )
 update public.threads_posts p
 set scheduled_at=(
   date_trunc('day',now() at time zone 'Asia/Ho_Chi_Minh')
   + interval '1 day'
   + interval '9 hours 30 minutes'
   + ordered.n*interval '1 day'
 ) at time zone 'Asia/Ho_Chi_Minh',
 updated_at=now()
 from ordered where p.id=ordered.id;
 get diagnostics changed=row_count;
 return changed;
end $$;
revoke all on function public.activate_threads_channel(text,text,text)
from public,anon,authenticated;
grant execute on function public.activate_threads_channel(text,text,text) to service_role;
