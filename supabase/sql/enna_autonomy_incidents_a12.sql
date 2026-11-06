-- A1.2: private evidence lifecycle. Only a trusted backend can read/write.
-- This does not grant new access to user sessions or make any public content.
create table if not exists public.enna_autonomy_incidents (
  brand_key text not null check (brand_key = 'do_hay_di_lam'),
  incident_key text not null check (length(incident_key) between 8 and 180),
  incident_code text not null,
  provider text,
  priority integer not null default 0 check (priority between 0 and 100),
  state text not null check (state in ('open','blocked','resolved')),
  source_kind text not null check (source_kind in ('supabase_snapshot','meta_official')),
  evidence_at timestamptz,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolution_source text,
  resolution_evidence_at timestamptz,
  reason_code text not null,
  primary key (brand_key,incident_key),
  constraint enna_incident_resolution_consistency
    check ((state = 'resolved') = (resolved_at is not null))
);
comment on table public.enna_autonomy_incidents is
 'Private, idempotent autonomous incident lifecycle. Cached Metricool state is never considered proof of issue resolution.';
create index if not exists enna_autonomy_incidents_state_idx
  on public.enna_autonomy_incidents (brand_key,state,last_seen_at desc);
alter table public.enna_autonomy_incidents enable row level security;
revoke all on public.enna_autonomy_incidents from public, anon, authenticated;
grant select,insert,update on public.enna_autonomy_incidents to service_role;
