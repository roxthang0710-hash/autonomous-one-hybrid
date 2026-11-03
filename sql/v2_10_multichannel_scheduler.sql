-- Enna: verified Metricool cross-channel bookings, not fabricated publications.
create table if not exists public.enna_multichannel_posts (
  brand_key text not null,
  provider text not null check (provider in ('facebook','instagram')),
  metricool_uuid text not null,
  metricool_post_id text not null,
  scheduled_at timestamptz not null,
  provider_status text not null check (provider_status in ('PENDING','PUBLISHED','ERROR')),
  auto_publish boolean not null default false,
  has_media boolean not null default false,
  checked_at timestamptz not null default now(),
  primary key (brand_key,provider,metricool_uuid)
);
create index if not exists enna_multichannel_schedule_idx
  on public.enna_multichannel_posts (scheduled_at desc,provider);
alter table public.enna_multichannel_posts enable row level security;
revoke all on public.enna_multichannel_posts from public,anon,authenticated;
grant select,insert,update,delete on public.enna_multichannel_posts to service_role;
