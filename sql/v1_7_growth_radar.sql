-- Autonomous One v1.7.2 Growth Radar schema snapshot.
-- Already applied through Supabase migrations growth_radar_v17,
-- growth_engagement_outbox_v171 and growth_reply_freshness_v172.
-- All entities are private, backend-only. Reapplying after migrations is unnecessary.
create table if not exists public.growth_signals (
 id uuid primary key default gen_random_uuid(),
 fingerprint text not null unique,
 source text not null check(source in ('google_trends_vn','google_news_vn','threads_keyword_api')),
 title text not null check(char_length(title) between 4 and 350),
 source_url text not null,
 source_post_id text, source_username text,
 published_at timestamptz, discovered_at timestamptz not null default now(),
 relevance_score integer not null check(relevance_score between 0 and 100),
 state text not null default 'candidate' check(state in ('candidate','rejected','expired')),
 niche text not null,
 risk_flags jsonb not null default '[]'::jsonb,
 notes jsonb not null default '[]'::jsonb
);
create index if not exists growth_signals_recent_idx
 on public.growth_signals(discovered_at desc,relevance_score desc);
alter table public.growth_signals enable row level security;
revoke all on public.growth_signals from anon,authenticated;
grant select,insert,update on public.growth_signals to service_role;

create table if not exists public.growth_opportunities (
 id uuid primary key default gen_random_uuid(),
 signal_id uuid not null references public.growth_signals(id) on delete cascade,
 kind text not null check(kind in ('trend_post','reply_suggestion')),
 status text not null default 'draft'
   check(status in ('draft','needs_review','approved','dismissed','expired')),
 draft_text text not null check(char_length(draft_text) between 60 and 500),
 hook text not null, relevance_reason text not null,why_safe text not null,
 target_post_url text,target_post_id text,
 quality_score integer not null check(quality_score between 0 and 100),
 generated_by text not null default 'groq' check(generated_by in ('groq','rule_based')),
 expires_at timestamptz not null,created_at timestamptz not null default now(),
 unique(signal_id,kind),
 constraint only_replies_have_targets check (
 kind='trend_post' or (target_post_url is not null and target_post_id is not null)
 )
);
create index if not exists growth_opportunities_recent_idx
 on public.growth_opportunities(created_at desc,status);
alter table public.growth_opportunities enable row level security;
revoke all on public.growth_opportunities from anon,authenticated;
grant select,insert,update on public.growth_opportunities to service_role;

create table if not exists public.growth_runs (
 id uuid primary key default gen_random_uuid(),
 run_key text not null unique,
 status text not null default 'running'
  check(status in ('running','success','no_relevant_signals','source_unavailable','failed')),
 signal_count integer not null default 0 check(signal_count>=0),
 shortlisted integer not null default 0 check(shortlisted>=0),
 drafts_created integer not null default 0 check(drafts_created>=0),
 source_summary jsonb not null default '{}'::jsonb,
 error_kind text, started_at timestamptz not null default now(),
 finished_at timestamptz
);
alter table public.growth_runs enable row level security;
revoke all on public.growth_runs from anon,authenticated;
grant select,insert,update on public.growth_runs to service_role;

create table if not exists public.growth_metricool_daily (
 measured_on date primary key,metricool_brand_id text not null,
 source text not null default 'metricool' check(source='metricool'),
 followers integer check(followers>=0), post_views integer check(post_views>=0),
 new_followers integer,interactions integer check(interactions>=0),
 replies integer check(replies>=0),published_posts integer check(published_posts>=0),
 fetched_at timestamptz not null default now(),notes text
);
alter table public.growth_metricool_daily enable row level security;
revoke all on public.growth_metricool_daily from anon,authenticated;
grant select,insert,update on public.growth_metricool_daily to service_role;

create table if not exists public.growth_engagement_attempts (
 id uuid primary key default gen_random_uuid(),
 opportunity_id uuid not null unique references public.growth_opportunities(id),
 target_post_id text not null unique,
 status text not null default 'started'
 check(status in ('started','posted','uncertain','blocked')),
 meta_container_id text,meta_reply_id text,error_kind text,
 attempted_at timestamptz not null default now(),finished_at timestamptz
);
create index if not exists growth_engagement_attempts_daily_idx
 on public.growth_engagement_attempts(attempted_at desc,status);
alter table public.growth_engagement_attempts enable row level security;
revoke all on public.growth_engagement_attempts from anon,authenticated;
grant select,insert,update on public.growth_engagement_attempts to service_role;

create or replace view public.growth_review_dashboard
with (security_invoker=true) as
select o.id,o.kind,o.status,o.draft_text,o.quality_score,
 o.created_at,o.expires_at,s.source,s.niche,
 s.title as source_title,s.source_url,s.relevance_score,
 s.published_at,s.risk_flags
from public.growth_opportunities o
join public.growth_signals s on s.id=o.signal_id;
revoke all on public.growth_review_dashboard from public,anon,authenticated;
grant select on public.growth_review_dashboard to service_role;

create or replace view public.growth_engagement_queue
with (security_invoker=true) as
select o.id as opportunity_id,o.status,o.kind,o.draft_text,o.quality_score,
 o.target_post_id,o.target_post_url,o.expires_at,
 s.relevance_score,s.risk_flags,s.source,s.niche,
 s.title as original_post_text,s.published_at as target_published_at
from public.growth_opportunities o
join public.growth_signals s on s.id=o.signal_id
where o.kind='reply_suggestion';
revoke all on public.growth_engagement_queue from public,anon,authenticated;
grant select on public.growth_engagement_queue to service_role;
