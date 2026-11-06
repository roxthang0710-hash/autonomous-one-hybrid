-- A2.2: safe evidence bridge between user-authorized Metricool snapshot
-- and official owner Meta post IDs. Never publish or silently rewrite a calendar.
create table if not exists public.enna_metricool_threads_links (
  brand_key text not null default 'do_hay_di_lam'
    check (brand_key = 'do_hay_di_lam'),
  metricool_uuid text not null
    check (metricool_uuid ~ '^-?[0-9]{5,25}$'),
  metricool_post_id text not null
    check (metricool_post_id ~ '^[0-9]{5,25}$'),
  scheduled_at timestamptz not null,
  provider_status_last_seen text not null
    check (provider_status_last_seen in ('PUBLISHED','PENDING')),
  provider_permalink text,
  expected_text_sha256 text
    check (expected_text_sha256 is null or expected_text_sha256 ~ '^[0-9a-f]{64}$'),
  provider_observed_at timestamptz not null,
  provider_source text not null
    check(provider_source = 'metricool_owner_connector_snapshot'),
  meta_post_id text check(meta_post_id is null or meta_post_id ~ '^[0-9]{5,30}$'),
  meta_published_at timestamptz,
  match_basis text check(match_basis is null or match_basis in
    ('exact_verified_permalink','unique_caption_hash_and_time')),
  verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(brand_key, metricool_uuid),
  constraint verified_meta_link_consistency check (
    (meta_post_id is null and meta_published_at is null
       and match_basis is null and verified_at is null)
    or (meta_post_id is not null and meta_published_at is not null
       and match_basis is not null and verified_at is not null)
  )
);
create unique index if not exists enna_metricool_threads_meta_unique
  on public.enna_metricool_threads_links (brand_key,meta_post_id)
  where meta_post_id is not null;
create index if not exists enna_metricool_threads_due
  on public.enna_metricool_threads_links (brand_key,scheduled_at)
  where meta_post_id is null;
comment on table public.enna_metricool_threads_links is
 'Private bridge: owner-authorized Metricool snapshot + official Meta evidence. No raw captions, no token, no social writes. Provider status is a dated snapshot, not live background API.';
alter table public.enna_metricool_threads_links enable row level security;
revoke all on public.enna_metricool_threads_links from public, anon, authenticated, service_role;
grant select, insert, update on public.enna_metricool_threads_links to service_role;