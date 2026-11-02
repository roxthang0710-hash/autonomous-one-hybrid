-- Enna evidence-backed self-improvement, 2026-11-02
-- Nonpublic operational tables: service role only, with RLS defense in depth.
create table if not exists public.enna_learning_policy (
  brand_key text primary key,
  preferred_format text not null default 'balanced'
    check (preferred_format in ('balanced','story','practical')),
  applied_at timestamptz not null default now(),
  evidence jsonb not null default '{}'::jsonb
    check (jsonb_typeof(evidence)='object'),
  version integer not null default 1 check (version>=1)
);
create table if not exists public.enna_learning_decisions (
  brand_key text not null,
  evaluated_on date not null,
  evaluated_at timestamptz not null default now(),
  decision text not null
    check (decision in ('insufficient_evidence','hold','promote_story',
                       'promote_practical','rollback_balanced','source_unavailable')),
  reason text not null,
  evidence jsonb not null default '{}'::jsonb check (jsonb_typeof(evidence)='object'),
  primary key(brand_key,evaluated_on)
);
create table if not exists public.enna_publication_evidence (
  brand_key text not null,
  metricool_post_id text not null,
  scheduled_post_id uuid references public.threads_posts(id),
  provider_status text not null check (provider_status in ('PUBLISHED','PENDING','ERROR')),
  checked_at timestamptz not null default now(),
  meta_post_id text,
  notes text not null default '',
  primary key(brand_key,metricool_post_id)
);
alter table public.enna_learning_policy enable row level security;
alter table public.enna_learning_decisions enable row level security;
alter table public.enna_publication_evidence enable row level security;
revoke all on public.enna_learning_policy, public.enna_learning_decisions,
  public.enna_publication_evidence from public, anon, authenticated;
grant select,insert,update,delete on public.enna_learning_policy,
  public.enna_learning_decisions,public.enna_publication_evidence to service_role;

insert into public.enna_learning_policy (brand_key,preferred_format)
values ('do_hay_di_lam','balanced')
on conflict (brand_key) do nothing;
