-- Autonomous One v1.6 — Threads channel / editorial queue.
-- Deployed to Supabase on 2026-11-02; repeatable schema snapshot.
-- This SQL creates internal data only, NOT a social account or account access token.

create table if not exists public.threads_channels (
  id uuid primary key default gen_random_uuid(),
  brand_key text not null unique,
  display_name text not null,
  bio text not null,
  username text,
  platform_user_id text,
  status text not null default 'awaiting_account'
    check(status in ('awaiting_account','awaiting_oauth','connected','paused')),
  authorized boolean not null default false,
  auto_publish_enabled boolean not null default false,
  account_created_at timestamptz,
  shopee_channel_approved boolean not null default false,
  updated_at timestamptz not null default now(),
  constraint threads_publish_requires_connection check (
    not auto_publish_enabled or
    (status='connected' and authorized and
     nullif(btrim(username),'') is not null and
     nullif(btrim(platform_user_id),'') is not null)
  )
);
alter table public.threads_channels enable row level security;
revoke all on public.threads_channels from anon,authenticated;
grant select,insert,update on public.threads_channels to service_role;

create table if not exists public.threads_posts (
  id uuid primary key default gen_random_uuid(),
  channel_id uuid not null references public.threads_channels(id),
  content_key text not null unique,
  pillar text not null,
  text_content text not null check(char_length(text_content) between 60 and 500),
  content_type text not null default 'editorial'
    check(content_type in ('editorial','affiliate')),
  status text not null default 'queued'
    check(status in ('queued','publishing','posted','uncertain','blocked','failed')),
  risk_flags jsonb not null default '[]'::jsonb,
  scheduled_at timestamptz not null,
  platform_post_id text,
  permalink text,
  published_at timestamptz,
  attempt_started_at timestamptz,
  created_by text not null default 'agent' check(created_by in ('agent','seed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint threads_affiliate_draft_only check(
    content_type='editorial' or status in ('blocked','failed')
  ),
  constraint threads_no_public_link check(
    text_content !~* '(https?://|www\.|shopee\.vn|shope\.ee|bit\.ly|affiliate)'
  )
);
create index if not exists threads_posts_due on public.threads_posts(channel_id,scheduled_at)
where status='queued';
alter table public.threads_posts enable row level security;
revoke all on public.threads_posts from anon,authenticated;
grant select,insert,update on public.threads_posts to service_role;

create table if not exists public.threads_publish_attempts (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.threads_posts(id),
  operation text not null check(operation in ('publish_text','reconcile')),
  outcome text not null check(outcome in ('started','posted','uncertain','failed')),
  remote_container_id text, remote_post_id text, error_kind text,
  attempted_at timestamptz not null default now()
);
alter table public.threads_publish_attempts enable row level security;
revoke all on public.threads_publish_attempts from anon,authenticated;
grant select,insert,update on public.threads_publish_attempts to service_role;

create table if not exists public.threads_metrics (
  post_id uuid not null references public.threads_posts(id),
  collected_at timestamptz not null default now(),
  views bigint not null default 0 check(views>=0),
  likes bigint not null default 0 check(likes>=0),
  replies bigint not null default 0 check(replies>=0),
  reposts bigint not null default 0 check(reposts>=0),
  quotes bigint not null default 0 check(quotes>=0),
  source text not null default 'threads_api' check(source='threads_api'),
  primary key(post_id,collected_at)
);
alter table public.threads_metrics enable row level security;
revoke all on public.threads_metrics from anon,authenticated;
grant select,insert,update on public.threads_metrics to service_role;

create or replace function public.claim_threads_post(p_brand_key text)
returns setof public.threads_posts
language plpgsql security definer set search_path=public,pg_temp
as $$
declare v_channel public.threads_channels%rowtype;
        v_post public.threads_posts%rowtype;
begin
 select * into v_channel from public.threads_channels where brand_key=p_brand_key;
 if not found or not v_channel.auto_publish_enabled
   or not v_channel.authorized or v_channel.status <> 'connected'
   or v_channel.platform_user_id is null or v_channel.username is null then
   return;
 end if;
 select * into v_post from public.threads_posts p
 where p.channel_id=v_channel.id and p.status='queued'
 and p.content_type='editorial' and p.scheduled_at<=now()
 and jsonb_array_length(p.risk_flags)=0
 order by p.scheduled_at,p.created_at limit 1 for update skip locked;
 if not found then return; end if;
 update public.threads_posts
 set status='publishing', attempt_started_at=now(), updated_at=now()
 where id=v_post.id returning * into v_post;
 return next v_post;
end $$;
revoke all on function public.claim_threads_post(text) from public,anon,authenticated;
grant execute on function public.claim_threads_post(text) to service_role;

create or replace function public.mark_stale_threads_uncertain()
returns integer language plpgsql security definer set search_path=public,pg_temp
as $$
declare v_count integer;
begin
 update public.threads_posts set status='uncertain',updated_at=now()
 where status='publishing' and attempt_started_at < now()-interval '20 minutes';
 get diagnostics v_count=row_count;
 return v_count;
end $$;
revoke all on function public.mark_stale_threads_uncertain() from public,anon,authenticated;
grant execute on function public.mark_stale_threads_uncertain() to service_role;

insert into public.threads_channels(brand_key,display_name,bio,status)
values ('do_hay_di_lam','Đồ Hay Đi Làm',
 'Góc mẹo nhỏ cho người đi làm và những chuyến công tác gọn nhẹ. Chia sẻ kiến thức hữu ích, không giả vờ đã dùng sản phẩm.',
 'awaiting_account')
on conflict(brand_key) do nothing;
