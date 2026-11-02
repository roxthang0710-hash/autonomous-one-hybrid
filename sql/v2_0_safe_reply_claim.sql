-- Autonomous One v2.0: atomic, owner-authorized Threads public reply claim.
-- One genuine brand identity. MAXIMUM 3 external reply attempts per VN day.
-- Never bypass Meta permissions or publish if the owner has not reauthorized.
create or replace function public.growth_claim_safe_reply(
  p_opportunity_id uuid,
  p_target_post_id text
) returns table(attempt_id uuid)
language plpgsql
security definer
set search_path = public, pg_temp
as $function$
declare
  v_today date := (now() at time zone 'Asia/Ho_Chi_Minh')::date;
  v_count integer;
  v_target_username text;
  v_attempt_id uuid;
begin
  if p_opportunity_id is null or nullif(btrim(p_target_post_id),'') is null
     or length(p_target_post_id) > 100 then
    return;
  end if;
  -- Serialize all claims for this account/day, even if two workflows overlap.
  perform pg_advisory_xact_lock(
    hashtext('autonomous_one_dohay_dilam_replies'),
    to_char(v_today,'YYYYMMDD')::integer
  );
  -- Meta authorization is a prerequisite, not just a GitHub environment flag.
  if not exists (
    select 1
    from public.threads_vault_credentials v
    join public.threads_channels c on c.brand_key=v.brand_key
    where v.brand_key='do_hay_di_lam'
      and v.status='active' and v.expires_at>now()
      and v.enable_replies=true
      and v.verified_username='dohay_dilam'
      and c.status='connected' and c.authorized=true
      and c.platform_user_id=v.platform_user_id
  ) then return; end if;
  select count(*) into v_count
    from public.growth_engagement_attempts a
    where (a.attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today;
  if v_count >= 3 then return; end if;

  select lower(s.source_username) into v_target_username
    from public.growth_opportunities o
    join public.growth_signals s on s.id=o.signal_id
   where o.id=p_opportunity_id
     and o.kind='reply_suggestion'
     and o.status='needs_review'
     and o.target_post_id=p_target_post_id
     and o.quality_score>=75
     and o.expires_at>now()
     and length(o.draft_text) between 60 and 380
     and s.source='threads_keyword_api'
     and s.source_post_id=p_target_post_id
     and s.relevance_score>=60
     and s.risk_flags='[]'::jsonb
     and s.published_at between now()-interval '24 hours'
                             and now()+interval '2 minutes'
     and nullif(btrim(s.source_username),'') is not null
     and lower(s.source_username)<>'dohay_dilam'
   limit 1;
  if v_target_username is null then return; end if;
  -- No coordinated piling-on: at most one attempt to the same author per
  -- 7 rolling days, including uncertain/failed sends.
  if exists (
    select 1 from public.growth_engagement_attempts a
    join public.growth_opportunities o on o.id=a.opportunity_id
    join public.growth_signals s on s.id=o.signal_id
    where lower(s.source_username)=v_target_username
      and a.attempted_at>now()-interval '7 days'
  ) then return; end if;

  insert into public.growth_engagement_attempts (
    opportunity_id,target_post_id,status,attempted_at
  ) values(p_opportunity_id,p_target_post_id,'started',now())
  on conflict do nothing
  returning id into v_attempt_id;
  if v_attempt_id is not null then
    return query select v_attempt_id;
  end if;
end;
$function$;

revoke all on function public.growth_claim_safe_reply(uuid,text)
  from public, anon, authenticated;
grant execute on function public.growth_claim_safe_reply(uuid,text)
  to service_role;
