-- Run in Supabase SQL Editor for private monitoring (no public access).
-- Summary: proposal quality is NOT a profitability forecast.
select
  count(*) as proposals_total,
  count(*) filter (where approval_status = 'pending') as awaiting_owner,
  count(*) filter (where approval_status = 'approved') as idea_approved,
  count(*) filter (where verdict = 'review') as ready_for_human_review,
  coalesce(sum(experiments),0) as experiments_recorded,
  coalesce(sum(observed_signals),0) as observed_signals,
  coalesce(sum(revenue_received_vnd),0) as revenue_received_vnd,
  coalesce(sum(actual_cost_vnd),0) as actual_cost_vnd,
  coalesce(sum(revenue_received_vnd - actual_cost_vnd),0) as recorded_net_vnd
from public.agent_review_dashboard;

-- Recent ideas awaiting approval; score is based on completeness and evidence leads.
select proposal_id, created_at, topic, title, review_score,
  verdict, evidence_status, approval_status
from public.agent_review_dashboard
where approval_status = 'pending'
order by review_score desc, created_at desc
limit 30;

-- Follow-up on experiments (financial figures must be entered from real records).
select e.id, p.proposal->>'title' as title, e.status, e.observed_signals,
  e.revenue_received_vnd, e.actual_cost_vnd,
  (e.revenue_received_vnd - e.actual_cost_vnd) as recorded_net_vnd,
  e.evidence_url, e.owner_notes, e.updated_at
from public.agent_experiments e
join public.agent_proposals p on p.id=e.proposal_id
order by e.updated_at desc
limit 50;
