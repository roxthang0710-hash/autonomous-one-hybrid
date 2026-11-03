-- Owner-selected Threads post handoff from a GitHub Issue, not keyword search.
-- All posting is via official Meta API; one verified target per owner issue.
create table if not exists public.enna_companion_attempts (
 id uuid primary key default gen_random_uuid(),
 brand_key text not null default 'do_hay_di_lam' check(brand_key='do_hay_di_lam'),
 github_issue_id bigint not null unique check(github_issue_id > 0),
 target_post_id text not null unique check(target_post_id ~ '^[0-9]{10,28}$'),
 author_fingerprint text not null check(author_fingerprint ~ '^[a-f0-9]{64}$'),
 status text not null default 'started' check(status in ('started','posted','uncertain')),
 attempted_at timestamptz not null default now(),
 finished_at timestamptz,
 meta_reply_id text,
 error_kind text
);
create index if not exists enna_companion_author_time_idx
  on public.enna_companion_attempts(author_fingerprint,attempted_at desc);
alter table public.enna_companion_attempts enable row level security;
revoke all on public.enna_companion_attempts from public,anon,authenticated;
grant all on public.enna_companion_attempts to service_role;

create or replace function public.enna_claim_selected_reply(
 p_github_issue_id bigint, p_target_post_id text, p_author_fingerprint text)
returns table(attempt_id uuid)
language plpgsql security definer set search_path=''
as $f$
declare
 v_today date := (now() at time zone 'Asia/Ho_Chi_Minh')::date;
 v_count integer;
 v_claim uuid;
begin
 if p_github_issue_id is null or p_github_issue_id <= 0
 or coalesce(p_target_post_id,'') !~ '^[0-9]{10,28}$'
 or coalesce(p_author_fingerprint,'') !~ '^[a-f0-9]{64}$' then return; end if;

 -- The existing two reply workers use the same advisory lock and budget.
 perform pg_advisory_xact_lock(
   hashtext('autonomous_one_dohay_dilam_replies'),
   to_char(v_today,'YYYYMMDD')::integer);

 if not exists (
   select 1 from public.threads_vault_credentials v
   join public.threads_channels c on c.brand_key=v.brand_key
   where v.brand_key='do_hay_di_lam' and v.status='active'
     and v.enable_replies=true and v.expires_at>now()
     and v.verified_username='dohay_dilam'
     and c.status='connected' and c.authorized
     and c.platform_user_id=v.platform_user_id
 ) then return; end if;

 select (select count(*) from public.growth_engagement_attempts
   where (attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today)
 + (select count(*) from public.enna_community_attempts
   where (claimed_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today)
 + (select count(*) from public.enna_companion_attempts
   where (attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today)
 into v_count;
 if v_count >= 3 then return; end if;

 -- Never reply twice to this exact target, even through another worker.
 if exists(select 1 from public.enna_companion_attempts
   where github_issue_id=p_github_issue_id or target_post_id=p_target_post_id)
 or exists(select 1 from public.growth_engagement_attempts
   where target_post_id=p_target_post_id)
 or exists(select 1 from public.enna_community_attempts
   where target_reply_id=p_target_post_id)
 then return; end if;
 if exists(select 1 from public.enna_companion_attempts
   where author_fingerprint=p_author_fingerprint
     and attempted_at>now()-interval '7 days')
 then return; end if;
 insert into public.enna_companion_attempts (
  github_issue_id,target_post_id,author_fingerprint,status
 ) values(p_github_issue_id,p_target_post_id,p_author_fingerprint,'started')
 on conflict do nothing returning id into v_claim;
 if v_claim is not null then return query select v_claim; end if;
end $f$;
revoke all on function public.enna_claim_selected_reply(bigint,text,text)
  from public,anon,authenticated;
grant execute on function public.enna_claim_selected_reply(bigint,text,text) to service_role;

-- Extend both existing worker budgets without weakening their original checks.
do $$
declare existing_code text;
begin
 select pg_get_functiondef(p.oid) into existing_code
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='growth_claim_safe_reply';
 if existing_code is null
 or position('  if v_count >= 3 then return; end if;' in existing_code)=0 then
   raise exception 'Existing growth reply safety cap not found';
 end if;
 execute replace(existing_code,
 '  if v_count >= 3 then return; end if;',
 '  select v_count + count(*) into v_count from public.enna_companion_attempts'
 ||E'\n'||'  where (attempted_at at time zone ''Asia/Ho_Chi_Minh'')::date=v_today;'
 ||E'\n'||'  if v_count >= 3 then return; end if;');
 select pg_get_functiondef(p.oid) into existing_code
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='enna_claim_own_reply';
 if existing_code is null
 or position(' if v_external+v_own >= 3 or v_own >= 1 then return; end if;'
             in existing_code)=0 then
   raise exception 'Existing owned reply safety cap not found';
 end if;
 execute replace(existing_code,
 ' if v_external+v_own >= 3 or v_own >= 1 then return; end if;',
 ' if v_external+v_own + (select count(*) from public.enna_companion_attempts'
 ||E'\n'||' where (attempted_at at time zone ''Asia/Ho_Chi_Minh'')::date=v_today)'
 ||' >= 3 or v_own >= 1 then return; end if;');
end $$;
