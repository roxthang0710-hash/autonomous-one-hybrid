-- Principle of least privilege for autonomous evidence-only workers.
-- Service role can observe and annotate evidence; never delete or truncate it.
revoke all on table public.enna_autonomy_incidents
 from anon, authenticated, service_role;
revoke all on table public.enna_official_threads_observations
 from anon, authenticated, service_role;
grant select, insert, update on table public.enna_autonomy_incidents
 to service_role;
grant select, insert, update on table public.enna_official_threads_observations
 to service_role;