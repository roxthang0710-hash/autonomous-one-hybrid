-- A2.1: immutable provider provenance, private read-only publication observations.
create table if not exists public.enna_official_threads_observations (
 brand_key text not null check (brand_key = 'do_hay_di_lam'),
 meta_post_id text not null check (meta_post_id ~ '^[0-9]{5,30}$'),
 published_at timestamptz not null,
 permalink text,
 text_sha256 text check (text_sha256 is null or text_sha256 ~ '^[0-9a-f]{64}$'),
 first_observed_at timestamptz not null default now(),
 last_observed_at timestamptz not null default now(),
 source text not null default 'meta_official' check(source='meta_official'),
 primary key (brand_key, meta_post_id)
);
comment on table public.enna_official_threads_observations is
 'Verified own-account Threads publications, including posts scheduled through third-party tools. No raw captions, private replies or tokens.';
create index if not exists enna_official_threads_observed_idx
 on public.enna_official_threads_observations(brand_key,published_at desc);
alter table public.enna_official_threads_observations enable row level security;
revoke all on public.enna_official_threads_observations from public, anon, authenticated;
grant select,insert,update on public.enna_official_threads_observations to service_role;