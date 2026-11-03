-- Official API single-shot owner-selected reply trials may receive a definitive
-- Meta rejection. Unlike ambiguous timeouts, this is NOT a successful post.
alter table public.enna_companion_attempts
  drop constraint if exists enna_companion_attempts_status_check;
alter table public.enna_companion_attempts
  add constraint enna_companion_attempts_status_check
  check(status in ('started','posted','uncertain','meta_rejected'));
comment on table public.enna_companion_attempts is
 'Private idempotent owner-selected reply attempts; Meta declines are recorded once and never retried automatically.';