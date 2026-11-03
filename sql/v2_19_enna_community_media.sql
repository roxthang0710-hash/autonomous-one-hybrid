-- v2.19: owned Threads conversation care + visual content research
-- All raw data stays service-role-only; public dashboards receive aggregates.
create table if not exists public.enna_community_attempts (
 id uuid primary key default gen_random_uuid(),
 brand_key text not null default 'do_hay_di_lam' check (brand_key='do_hay_di_lam'),
 own_post_id text not null,
 target_reply_id text not null unique,
 author_fingerprint text not null check (length(author_fingerprint)=64),
 status text not null default 'started' check (status in ('started','posted','uncertain','blocked')),
 claimed_at timestamptz not null default now(),
 finished_at timestamptz,
 meta_reply_id text,
 error_kind text
);
create index if not exists enna_community_attempts_date_idx on public.enna_community_attempts (claimed_at desc);
create index if not exists enna_community_author_idx on public.enna_community_attempts (author_fingerprint,claimed_at desc);
alter table public.enna_community_attempts enable row level security;
revoke all on public.enna_community_attempts from public,anon,authenticated;
grant all on public.enna_community_attempts to service_role;

create table if not exists public.enna_media_ideas (
 id uuid primary key default gen_random_uuid(),
 brand_key text not null default 'do_hay_di_lam' check(brand_key='do_hay_di_lam'),
 idea_key text not null unique check (idea_key ~ '^[a-z0-9_-]{8,100}$'),
 media_type text not null check (media_type in ('original_meme','licensed_photo','licensed_video','video_storyboard')),
 title text not null,
 creative_brief text not null,
 hook_text text,
 source_provider text not null check(source_provider in ('original','wikimedia_commons','pexels')),
 source_url text,
 creator_credit text,
 license_code text,
 license_url text,
 rights_status text not null check(rights_status in ('original','review_required','source_unverified')),
 status text not null default 'research' check (status in ('research','needs_review','ready','used','rejected')),
 pillar text not null check(pillar in ('work','organize','travel','conversation')),
 evidence jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 reviewed_at timestamptz,
 used_at timestamptz,
 check(media_type in ('original_meme','video_storyboard') or (source_url is not null and rights_status='review_required'))
);
create index if not exists enna_media_ideas_review_idx on public.enna_media_ideas (status,created_at desc);
alter table public.enna_media_ideas enable row level security;
revoke all on public.enna_media_ideas from public,anon,authenticated;
grant all on public.enna_media_ideas to service_role;

-- One owned-audience reply per Vietnam day, shared global maximum three
-- across owned-audience and existing public Thread comment worker.
-- This RPC is *only* for the trusted backend. No anon/authenticated execution.
create or replace function public.enna_claim_own_reply(
 p_own_post_id text,p_target_reply_id text,p_author_fingerprint text)
returns table(attempt_id uuid)
language plpgsql security definer set search_path = ''
as $f$
declare
 v_today date := (now() at time zone 'Asia/Ho_Chi_Minh')::date;
 v_id uuid;
 v_external integer;
 v_own integer;
begin
 if coalesce(length(p_own_post_id),0) not between 8 and 100
    or coalesce(length(p_target_reply_id),0) not between 8 and 100
    or coalesce(p_author_fingerprint,'') !~ '^[a-f0-9]{64}$' then return; end if;
 -- Match the lock used by growth_claim_safe_reply to prevent cross-worker races.
 perform pg_advisory_xact_lock(hashtext('autonomous_one_dohay_dilam_replies'),
                              to_char(v_today,'YYYYMMDD')::integer);
 if not exists (
   select 1 from public.threads_vault_credentials v
   join public.threads_channels c on c.brand_key=v.brand_key
   where v.brand_key='do_hay_di_lam' and v.enable_replies=true
     and v.status='active' and v.expires_at>now()
     and v.verified_username='dohay_dilam'
     and c.authorized=true and c.status='connected'
     and c.platform_user_id=v.platform_user_id
 ) then return; end if;
 if not exists(select 1 from public.threads_posts p
   where p.platform_post_id=p_own_post_id and p.status='posted') then return; end if;
 select count(*) into v_external from public.growth_engagement_attempts
   where (attempted_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today;
 select count(*) into v_own from public.enna_community_attempts
   where (claimed_at at time zone 'Asia/Ho_Chi_Minh')::date=v_today;
 if v_external+v_own >= 3 or v_own >= 1 then return; end if;
 if exists(select 1 from public.enna_community_attempts
   where target_reply_id=p_target_reply_id) then return; end if;
 if exists(select 1 from public.enna_community_attempts
   where author_fingerprint=p_author_fingerprint
     and claimed_at>now()-interval '7 days') then return; end if;
 insert into public.enna_community_attempts(
   own_post_id,target_reply_id,author_fingerprint,status)
 values(p_own_post_id,p_target_reply_id,p_author_fingerprint,'started')
 on conflict do nothing returning id into v_id;
 if v_id is not null then return query select v_id; end if;
end;
$f$;
revoke all on function public.enna_claim_own_reply(text,text,text) from public,anon,authenticated;
grant execute on function public.enna_claim_own_reply(text,text,text) to service_role;
