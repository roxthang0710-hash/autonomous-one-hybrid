-- Keep only actual merchant-product hypotheses in the affiliate candidate table.
delete from public.enna_affiliate_candidates
where candidate_key='office_toolkit'
  and stage='research_only' and affiliate_url is null;

-- Future placement tests are explicitly planned, not executed or published.
with plans(candidate_key,channel,placement,notes) as (
 values
 ('cable_clips','threads','profile_bio',
  'Sẽ dùng trang bio tổng nếu Shopee duyệt kênh và SKU; chưa gắn affiliate link.'),
 ('cable_clips','threads','own_post_reply',
  'Chỉ một phản hồi trong bài của chính mình có nội dung liên quan, có disclosure sau khi được duyệt.'),
 ('laptop_stand','instagram','profile_bio',
  'Chỉ thử khi có ảnh thật, link affiliate được cấp hợp lệ và người sở hữu duyệt.')
)
insert into public.enna_affiliate_tests(candidate_key,channel,placement,status,notes)
select v.candidate_key,v.channel,v.placement,'planned',v.notes
from plans v
where not exists (
 select 1 from public.enna_affiliate_tests x
 where x.candidate_key=v.candidate_key and x.channel=v.channel
   and x.placement=v.placement and x.status in ('planned','needs_review')
);
