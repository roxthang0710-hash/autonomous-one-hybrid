alter table public.enna_activity_events
  add column if not exists trigger_kind text not null default 'unknown';
alter table public.enna_activity_events
  drop constraint if exists enna_activity_trigger_kind_allowed;
alter table public.enna_activity_events
  add constraint enna_activity_trigger_kind_allowed
  check(trigger_kind in ('schedule','issues','workflow_dispatch','database','unknown'));
update public.enna_activity_events
set trigger_kind='database'
where origin='database' and trigger_kind='unknown';
-- Known owner-triggered smoke test, not an autonomous scheduled run.
update public.enna_activity_events
set trigger_kind='issues'
where origin='github' and run_key='41592121515' and trigger_kind='unknown';