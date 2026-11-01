-- Autonomous One v1.6.2: Metricool external scheduling ledger.
-- Deployed to Supabase on 2026-11-02.
alter table public.threads_posts drop constraint if exists threads_posts_status_check;
alter table public.threads_posts add constraint threads_posts_status_check
check(status in ('queued','scheduled_external','publishing','posted','uncertain','blocked','failed'));

create table if not exists public.threads_metricool_schedule (
 post_id uuid primary key references public.threads_posts(id) on delete cascade,
 metricool_brand_id text not null,
 metricool_post_id text,
 metricool_uuid text,
 planned_at timestamptz not null,
 send_state text not null default 'pending'
 check(send_state in ('pending','confirmed','uncertain','cancelled')),
 provider text not null default 'threads' check(provider='threads'),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.threads_metricool_schedule enable row level security;
revoke all on public.threads_metricool_schedule from anon,authenticated;
grant select,insert,update on public.threads_metricool_schedule to service_role;
create index if not exists threads_metricool_schedule_pending_idx on
public.threads_metricool_schedule(send_state,planned_at);
comment on table public.threads_metricool_schedule is
'External publication ledger; scheduled_external content is excluded from direct Meta API claims.';

-- For this project Metricool is the currently chosen publication service.
-- Direct Meta Graph API publisher remains dormant in GitHub Actions.
