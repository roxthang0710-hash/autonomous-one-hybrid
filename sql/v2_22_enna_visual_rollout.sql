-- Enna Visual 2.0: private, provider-grounded tracking of real media changes.
-- This table never treats a scheduled item as a published item.
create table if not exists public.enna_visual_rollouts (
  platform text not null check (platform in ('threads','facebook','instagram')),
  metricool_uuid text not null,
  metricool_post_id text not null,
  brand_key text not null default 'do_hay_di_lam',
  scheduled_at timestamptz not null,
  format_key text not null check (format_key in ('photo_meme','photo_album','photo_carousel')),
  media_keys text[] not null,
  media_count integer not null check (media_count between 1 and 10),
  provider_status text not null default 'PENDING',
  verified_at timestamptz not null default now(),
  content_series text not null,
  comparison_note text not null default 'observational; not causal',
  verified_publication_id text,
  published_at timestamptz,
  performance_evidence jsonb,
  primary key (platform,metricool_uuid),
  constraint visual_media_count_matches check (media_count=cardinality(media_keys)),
  constraint verified_post_requires_id check (
     (provider_status!='POSTED' and verified_publication_id is null and published_at is null)
     or (provider_status='POSTED' and verified_publication_id is not null and published_at is not null)
  )
);
create index if not exists enna_visual_rollouts_schedule_idx
  on public.enna_visual_rollouts (scheduled_at,platform);
alter table public.enna_visual_rollouts enable row level security;
revoke all on public.enna_visual_rollouts from anon, authenticated;
grant select, insert, update, delete on public.enna_visual_rollouts to service_role;
comment on table public.enna_visual_rollouts is 'Private visual test slots confirmed via live Metricool; PENDING is not published. Human/owner-only review; no public roles.';
