-- Enna Affiliate online tracker: private reviewer access only.
-- Public GitHub Pages hosts UI only; no service_role or secret is put in browser.
-- Reuse existing agent_reviewers allowlist and existing candidate/test safeguards.
alter table public.enna_affiliate_candidates enable row level security;
alter table public.enna_affiliate_tests enable row level security;
revoke all on public.enna_affiliate_candidates, public.enna_affiliate_tests from anon;
grant select on public.enna_affiliate_candidates, public.enna_affiliate_tests to authenticated;
grant update (
  category, title, reader_problem, content_angle,
  research_source_url, product_page_url, affiliate_url,
  indicative_price_vnd, commission_pct, publisher_approved,
  seller_verified, product_verified, disclosure_ready,
  brand_fit, reader_value, story_potential, affordability,
  seller_confidence, stage, last_checked_on, notes,
  updated_at, owner_approved, owner_approval_ref, publisher_approval_ref
) on public.enna_affiliate_candidates to authenticated;
grant insert (
  candidate_key, program_code, category, title, reader_problem,
  content_angle, research_source_url, product_page_url, affiliate_url,
  indicative_price_vnd, commission_pct, publisher_approved,
  seller_verified, product_verified, disclosure_ready, brand_fit,
  reader_value, story_potential, affordability, seller_confidence,
  stage, last_checked_on, notes, owner_approved,
  owner_approval_ref, publisher_approval_ref
) on public.enna_affiliate_candidates to authenticated;
grant select, insert, update on public.enna_affiliate_tests to authenticated;

drop policy if exists enna_tracker_candidates_read on public.enna_affiliate_candidates;
create policy enna_tracker_candidates_read on public.enna_affiliate_candidates
  for select to authenticated
  using (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));
drop policy if exists enna_tracker_candidates_edit on public.enna_affiliate_candidates;
create policy enna_tracker_candidates_edit on public.enna_affiliate_candidates
  for update to authenticated
  using (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())))
  with check (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));
drop policy if exists enna_tracker_candidates_add on public.enna_affiliate_candidates;
create policy enna_tracker_candidates_add on public.enna_affiliate_candidates
  for insert to authenticated
  with check (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));

drop policy if exists enna_tracker_tests_read on public.enna_affiliate_tests;
create policy enna_tracker_tests_read on public.enna_affiliate_tests
  for select to authenticated
  using (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));
drop policy if exists enna_tracker_tests_edit on public.enna_affiliate_tests;
create policy enna_tracker_tests_edit on public.enna_affiliate_tests
  for update to authenticated
  using (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())))
  with check (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));
drop policy if exists enna_tracker_tests_add on public.enna_affiliate_tests;
create policy enna_tracker_tests_add on public.enna_affiliate_tests
  for insert to authenticated
  with check (exists(select 1 from public.agent_reviewers r where r.user_id=(select auth.uid())));
