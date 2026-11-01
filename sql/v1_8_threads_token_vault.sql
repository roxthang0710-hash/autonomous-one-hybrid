
-- v1.8: authenticated unattended Threads operation.
-- Ciphertext only: symmetric key stored exclusively in GitHub Actions Secrets.
create table if not exists public.threads_connection_tokens (
 brand_key text primary key references public.threads_channels(brand_key),
 ciphertext text not null check(length(ciphertext) between 50 and 4096),
 token_sha256 text not null check(length(token_sha256) = 64),
 verified_username text not null,
 platform_user_id text not null,
 issued_at timestamptz not null,
 expires_at timestamptz not null,
 refreshed_at timestamptz,
 status text not null default 'active' check(status in ('active','expired','revoked','needs_reauth')),
 last_error_code text,
 updated_at timestamptz not null default now(),
 constraint token_time_order check(expires_at > issued_at)
);
alter table public.threads_connection_tokens enable row level security;
revoke all on public.threads_connection_tokens from anon,authenticated;
grant select,insert,update on public.threads_connection_tokens to service_role;

-- Meta may be activated before the Metricool queue has finished.
-- Preserve the exclusive scheduling lane by starting no earlier than
-- the *day after* the last externally scheduled post.
create or replace function public.activate_threads_channel(
 p_brand_key text,p_username text,p_platform_user_id text
) returns integer language plpgsql security definer set search_path=public,pg_temp
as $$
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
    select id,row_number() over(order by scheduled_at,created_at,id)-1 as n
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
grant execute on function public.activate_threads_channel(text,text,text) to service_role;

-- Additional safety guard against publishing on a day already booked
-- in Metricool (even if the queue was generated before OAuth).
create or replace function public.claim_threads_post(p_brand_key text)
returns setof public.threads_posts
language plpgsql security definer set search_path=public,pg_temp
as $$
declare c public.threads_channels%rowtype; p public.threads_posts%rowtype;
begin
 select * into c from public.threads_channels
 where brand_key=p_brand_key;
 if not found or c.status<>'connected' or not c.authorized
 or not c.auto_publish_enabled or c.platform_user_id is null or c.username is null
 then return; end if;
 select * into p from public.threads_posts x
 where x.channel_id=c.id and x.status='queued'
 and x.content_type='editorial'
 and x.scheduled_at <= now()
 and jsonb_typeof(x.risk_flags)='array'
 and jsonb_array_length(x.risk_flags)=0
 and not exists (
  select 1 from public.threads_posts e where e.channel_id=c.id
   and e.status='scheduled_external'
   and (e.scheduled_at at time zone 'Asia/Ho_Chi_Minh')::date =
       (x.scheduled_at at time zone 'Asia/Ho_Chi_Minh')::date
 )
 order by x.scheduled_at,x.created_at
 limit 1 for update skip locked;
 if not found then return; end if;
 update public.threads_posts
 set status='publishing',attempt_started_at=now(),updated_at=now()
 where id=p.id returning * into p;
 return next p;
end $$;
revoke all on function public.claim_threads_post(text) from public,anon,authenticated;
grant execute on function public.claim_threads_post(text) to service_role;
