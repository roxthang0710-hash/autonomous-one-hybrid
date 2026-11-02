-- Enna: adaptive publish gate, 2026-11-02.
-- Retain official account, publishing authorization, idempotent row claim and
-- the strict rejection of ambiguous/uncertain writes.
-- Replace *whole-day* Metricool lock with protected time proximity.
-- The planner may add at most one experimental extra without engagement data.
-- A daily ceiling of 5 is a safety cap, not a posting target.
create or replace function public.claim_threads_post(p_brand_key text)
returns setof public.threads_posts
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  c public.threads_channels%rowtype;
  p public.threads_posts%rowtype;
  vn_now timestamp;
  local_day date;
  today_count integer;
begin
  select * into c from public.threads_channels where brand_key=p_brand_key;
  if not found or c.status<>'connected' or not c.authorized
      or not c.auto_publish_enabled or c.platform_user_id is null
      or c.username is null then return; end if;

  -- One claim decision per brand per transaction, even if multiple
  -- workflow invocations overlap across platforms.
  if not pg_try_advisory_xact_lock(hashtext('enna_claim:' || p_brand_key)) then
    return;
  end if;

  vn_now := now() at time zone 'Asia/Ho_Chi_Minh';
  local_day := vn_now::date;
  -- Experimental night-owl window 22:15–03:00, one native Meta
  -- publishing attempt per cross-midnight night; 03:00–08:00 stays quiet.
  if vn_now::time >= time '03:00' and vn_now::time < time '08:00' then
    return;
  end if;
  if vn_now::time >= time '22:15' or vn_now::time < time '03:00' then
    if exists (
      select 1 from public.threads_posts n
      where n.channel_id = c.id
        and n.status in ('posted','publishing','uncertain')
        and coalesce(n.published_at,n.scheduled_at) >=
          (((case when vn_now::time < time '03:00'
                then vn_now::date - 1 else vn_now::date end) + time '22:15')
             at time zone 'Asia/Ho_Chi_Minh')
        and coalesce(n.published_at,n.scheduled_at) <
          (((case when vn_now::time < time '03:00'
                then vn_now::date else vn_now::date + 1 end) + time '03:00')
             at time zone 'Asia/Ho_Chi_Minh')
    ) then return; end if;
  end if;

  -- Count already reserved and real posts in Vietnam local day.
  select count(*) into today_count
  from public.threads_posts x
  where x.channel_id=c.id and x.status in
      ('scheduled_external','posted','publishing','uncertain')
    and (coalesce(x.published_at,x.scheduled_at) at time zone 'Asia/Ho_Chi_Minh')::date=local_day;
  if today_count >= (case when local_day = date '2026-11-03' then 6 else 5 end) then return; end if;

  select * into p
  from public.threads_posts x
  where x.channel_id=c.id and x.status='queued'
    and x.content_type='editorial'
    and x.scheduled_at <= now()
    -- A stale draft must never burst onto a feed after a delayed workflow.
    and x.scheduled_at >= now() - interval '4 hours'
    and jsonb_typeof(x.risk_flags)='array'
    and jsonb_array_length(x.risk_flags)=0
    -- A booked Metricool post near this moment has priority.
    and not exists (
      select 1 from public.threads_posts m
      where m.channel_id=c.id and m.id<>x.id
        and m.status in ('scheduled_external','posted','publishing','uncertain')
        and abs(extract(epoch from
           (coalesce(m.published_at,m.scheduled_at)-now()))) < 90*60
    )
    and not exists (
      select 1 from public.threads_metricool_schedule m
      where m.send_state in ('confirmed','pending','uncertain')
        and abs(extract(epoch from (m.planned_at-now()))) < 90*60
    )
  order by x.scheduled_at,x.created_at limit 1 for update skip locked;
  if not found then return; end if;
  update public.threads_posts
     set status='publishing',attempt_started_at=now(),updated_at=now()
   where id=p.id returning * into p;
  return next p;
end $$;
-- Restrict the existing privileged RPC: it is a worker-only operation.
revoke all on function public.claim_threads_post(text) from public, anon, authenticated;
grant execute on function public.claim_threads_post(text) to service_role;
