-- Enna operational audit: safe summary events, no post copy, tokens or raw logs.
create table if not exists public.enna_activity_events (
  id uuid primary key default gen_random_uuid(),
  occurred_at timestamptz not null default now(),
  origin text not null check(origin in ('github','database','watchdog')),
  kind text not null check(kind in ('publisher','editor','reconcile','insights','learning','growth','research','system','metricool')),
  status text not null check(status in ('started','success','skipped','failed','uncertain','pending')),
  code text not null check(code ~ '^[a-z0-9_:-]{2,80}$'),
  run_key text,
  entity_id uuid,
  dedup_key text not null unique
);
create index if not exists enna_activity_recent_idx on public.enna_activity_events (occurred_at desc);
alter table public.enna_activity_events enable row level security;
revoke all on public.enna_activity_events from public, anon, authenticated;
grant select,insert on public.enna_activity_events to service_role;

create or replace function public.enna_audit_post_status()
returns trigger
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare v_status text;
begin
  if TG_OP='UPDATE' and NEW.status is not distinct from OLD.status then return NEW; end if;
  v_status := case NEW.status
    when 'posted' then 'success'
    when 'publishing' then 'started'
    when 'uncertain' then 'uncertain'
    when 'failed' then 'failed'
    else 'pending' end;
  insert into public.enna_activity_events(
    origin,kind,status,code,entity_id,dedup_key,occurred_at
  ) values(
    'database','publisher',v_status,'post_'||NEW.status,NEW.id,
    'post:'||NEW.id::text||':'||NEW.status,
    case when NEW.status='posted' then coalesce(NEW.published_at,now()) else now() end
  ) on conflict(dedup_key) do nothing;
  return NEW;
exception when others then
  -- Publication must never fail because the *observer* is unavailable.
  return NEW;
end $$;
revoke all on function public.enna_audit_post_status() from public,anon,authenticated;
grant execute on function public.enna_audit_post_status() to service_role;
drop trigger if exists enna_audit_posts_insert on public.threads_posts;
drop trigger if exists enna_audit_posts_update on public.threads_posts;
create trigger enna_audit_posts_insert
after insert on public.threads_posts
for each row execute function public.enna_audit_post_status();
create trigger enna_audit_posts_update
after update of status on public.threads_posts
for each row execute function public.enna_audit_post_status();

-- Backfill only confirmed public posting events, not pending/unverified data.
insert into public.enna_activity_events(origin,kind,status,code,entity_id,dedup_key,occurred_at)
select 'database','publisher','success','post_posted',id,
       'post:'||id::text||':posted',coalesce(published_at,updated_at)
from public.threads_posts where status='posted'
on conflict(dedup_key) do nothing;
