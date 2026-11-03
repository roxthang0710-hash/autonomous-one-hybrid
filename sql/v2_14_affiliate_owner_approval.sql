-- Extra owner approval and evidence before publishing ANY candidate.
alter table public.enna_affiliate_candidates
  add column if not exists owner_approved boolean not null default false;
alter table public.enna_affiliate_candidates
  add column if not exists owner_approval_ref text;
alter table public.enna_affiliate_candidates
  add column if not exists publisher_approval_ref text;
alter table public.enna_affiliate_candidates
  drop constraint if exists candidate_requires_evidence;
alter table public.enna_affiliate_candidates
  add constraint candidate_requires_evidence check (
    ((affiliate_url is null) or
      (nullif(btrim(publisher_approval_ref),'') is not null)) and
    (stage not in ('approved','published') or
      (owner_approved and
       nullif(btrim(owner_approval_ref),'') is not null and
       nullif(btrim(publisher_approval_ref),'') is not null))
  );
