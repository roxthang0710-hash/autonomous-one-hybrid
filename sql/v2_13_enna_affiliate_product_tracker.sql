-- Enna affiliate product assessment & placements, no live affiliate links until approved.
create table if not exists public.enna_affiliate_candidates (
  candidate_key text primary key check(candidate_key ~ '^[a-z0-9_]{3,60}$'),
  program_code text not null references public.affiliate_programs(code),
  category text not null,
  title text not null,
  reader_problem text not null,
  content_angle text not null,
  research_source_url text,
  product_page_url text,
  affiliate_url text,
  indicative_price_vnd bigint check(indicative_price_vnd is null or indicative_price_vnd >= 0),
  commission_pct numeric(7,3) check(commission_pct is null or (commission_pct >= 0 and commission_pct <= 100)),
  publisher_approved boolean not null default false,
  seller_verified boolean not null default false,
  product_verified boolean not null default false,
  disclosure_ready boolean not null default false,
  brand_fit smallint not null check(brand_fit between 0 and 5),
  reader_value smallint not null check(reader_value between 0 and 5),
  story_potential smallint not null check(story_potential between 0 and 5),
  affordability smallint not null check(affordability between 0 and 5),
  seller_confidence smallint not null default 0 check(seller_confidence between 0 and 5),
  internal_priority_score smallint generated always as
    (brand_fit * 6 + reader_value * 5 + story_potential * 4 +
     affordability * 3 + seller_confidence * 2) stored,
  stage text not null default 'research_only'
    check(stage in ('research_only','checking','owner_review','approved','published','retired')),
  last_checked_on date,
  notes text not null default '',
  updated_at timestamptz not null default now(),
  constraint affiliate_links_need_real_approval check (
    affiliate_url is null or (publisher_approved and seller_verified and
                              product_verified and disclosure_ready)
  ),
  constraint product_go_live_requires_verified check (
    stage not in ('approved','published') or
    (affiliate_url is not null and publisher_approved and seller_verified and
     product_verified and disclosure_ready)
  )
);
create index if not exists enna_affiliate_candidates_rank
  on public.enna_affiliate_candidates (internal_priority_score desc);
alter table public.enna_affiliate_candidates enable row level security;
revoke all on public.enna_affiliate_candidates from public,anon,authenticated;
grant select,insert,update,delete on public.enna_affiliate_candidates to service_role;

create table if not exists public.enna_affiliate_tests (
  id uuid primary key default gen_random_uuid(),
  candidate_key text not null references public.enna_affiliate_candidates(candidate_key),
  channel text not null check(channel in ('threads','facebook','instagram')),
  placement text not null check(placement in ('main_post','own_post_reply','profile_bio')),
  status text not null default 'planned'
    check(status in ('planned','needs_review','active','stopped')),
  planned_on date,
  published_post_ref text,
  observations_start date,
  observations_end date,
  post_views bigint check(post_views is null or post_views >= 0),
  link_visits bigint check(link_visits is null or link_visits >= 0),
  provider_clicks bigint check(provider_clicks is null or provider_clicks >= 0),
  provider_orders bigint check(provider_orders is null or provider_orders >= 0),
  provider_commission_vnd bigint check(provider_commission_vnd is null or provider_commission_vnd >= 0),
  metric_source text,
  evidence_ref text,
  notes text,
  checked_at timestamptz,
  constraint no_fabricated_placement_performance check (
    (coalesce(link_visits,0)=0 and coalesce(provider_clicks,0)=0 and
     coalesce(provider_orders,0)=0 and coalesce(provider_commission_vnd,0)=0)
    or (metric_source in ('platform_insights','verified_provider_export','owner_site_log')
        and nullif(btrim(evidence_ref),'') is not null)
  )
);
alter table public.enna_affiliate_tests enable row level security;
revoke all on public.enna_affiliate_tests from public,anon,authenticated;
grant select,insert,update,delete on public.enna_affiliate_tests to service_role;
create index if not exists enna_affiliate_test_by_candidate
  on public.enna_affiliate_tests(candidate_key,channel,placement);

create or replace function public.enna_affiliate_test_guard()
returns trigger language plpgsql set search_path=public,pg_temp as $$
declare approved boolean;
begin
 if new.status='active' then
   select (stage in ('approved','published') and affiliate_url is not null
           and publisher_approved and seller_verified and product_verified
           and disclosure_ready) into approved
   from public.enna_affiliate_candidates where candidate_key=new.candidate_key;
   if not coalesce(approved,false) then
     raise exception 'affiliate_candidate_not_fully_approved';
   end if;
 end if;
 return new;
end $$;
revoke all on function public.enna_affiliate_test_guard() from public,anon,authenticated;
drop trigger if exists enna_affiliate_test_gate on public.enna_affiliate_tests;
create trigger enna_affiliate_test_gate before insert or update of status,candidate_key
 on public.enna_affiliate_tests for each row
 execute function public.enna_affiliate_test_guard();

insert into public.enna_affiliate_candidates (
 candidate_key,program_code,category,title,reader_problem,content_angle,
 research_source_url,brand_fit,reader_value,story_potential,affordability,
 seller_confidence,notes
) values
('cable_clips','shopee_koc','Góc làm việc','Kẹp giữ dây sạc và dây cáp',
 'Dây sạc luôn rơi xuống sau bàn','Hài vô tri: vừa dọn bàn, dây sạc lại đi lạc',
 null,5,5,5,5,0,'Chưa chọn SKU/nhà bán; độ tin cậy nhà bán=0 cho đến khi kiểm tra.'),
('cable_pouch','shopee_koc','Đồ đi làm','Túi sắp xếp dây sạc và phụ kiện',
 'Đồ công nghệ lẫn trong balô','Một ngày trong balô của nhân viên mới',
 null,5,5,4,4,0,'Cần xem chất liệu, khóa kéo, kích cỡ và giá thực.'),
('laptop_stand','shopee_koc','Góc làm việc','Giá đỡ laptop gập gọn',
 'Bàn chật, màn hình ở vị trí khó nhìn','Bàn làm việc bỗng bớt hỗn loạn',
 'https://shopee.vn/list/gi%C3%A1%20%C4%91%E1%BB%A1%20laptop/nh%C3%B4m',5,5,4,4,0,
 'Không khẳng định chữa đau cổ; cần thử độ ổn định, tương thích thiết bị, chiều cao.'),
('desk_organizer','shopee_koc','Góc làm việc','Hộp/khay chia ngăn để bàn',
 'Đồ nhỏ để đâu cũng quên','Bàn gọn 10/10 nhưng cây bút mất tích',
 null,5,4,5,4,0,'Phân biệt phụ kiện trang trí với đồ thực sự dùng được.'),
('daily_planner','shopee_koc','Đồ dùng công sở','Sổ kế hoạch và checklist',
 'Mỗi ngày quá nhiều việc gấp','Cuộc họp về ưu tiên của 3 deadline',
 null,5,5,4,5,0,'Phải giải thích vì sao sản phẩm giấy đáng mua hơn mẫu miễn phí.'),
('phone_stand','shopee_koc','Góc làm việc','Giá đỡ điện thoại để bàn',
 'Dễ mất tập trung, điện thoại hay đổ','Màn hình công việc và màn hình báo giờ nghỉ',
 null,4,4,4,5,0,'Cần test độ chắc, kích cỡ; không tuyên bố tăng hiệu suất.'),
('desk_lamp','shopee_koc','Góc làm việc','Đèn bàn điều chỉnh hướng sáng',
 'Khu vực làm việc thiếu ánh sáng phù hợp','Người đi làm ca tối: đèn muốn về trước',
 null,4,4,5,3,0,'Sản phẩm điện: kiểm chứng an toàn, nguồn, chứng nhận, bảo hành.'),
('power_bank','shopee_koc','Đồ đi làm','Pin dự phòng mang đi làm',
 'Hết pin giữa cuộc họp hoặc khi di chuyển','Báo pin yếu đúng lúc sếp nhắn việc',
 null,4,4,4,3,0,'Sản phẩm pin: cần nhãn hàng chính thống, kiểm tra an toàn, hàng giả.'),
('office_toolkit','shopee_koc','Tài nguyên miễn phí','Enna Mini: mẫu chốt việc & ưu tiên',
 'Thiếu mẫu ghi việc rõ ràng','Cho người đọc dùng công cụ miễn phí trước',
 null,5,5,5,5,0,'Không phải sản phẩm Affiliate; mục chỉ để so sánh nhu cầu nội dung, không gắn link thương mại.')
on conflict(candidate_key) do nothing;
