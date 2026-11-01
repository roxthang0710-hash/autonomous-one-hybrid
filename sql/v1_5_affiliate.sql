-- Autonomous One Affiliate Research v1.5.
-- Applied to Supabase project gjdvdohylvsauphhkutw on 2026-11-02.
-- Research-only: no automated registration, posting, commissions or affiliate links.
create table if not exists public.affiliate_programs (
 code text primary key check (code ~ '^[a-z0-9_]{3,36}$'),
 name text not null,
 official_url text not null,
 evidence_url text not null,
 market text not null default 'VN',
 access_notes text not null,
 eligibility_notes text not null,
 review_status text not null default 'research_only'
   check (review_status in ('research_only','owner_registered','active','inactive')),
 commission_verified boolean not null default false,
 commission_notes text not null default 'Chưa xác minh; phụ thuộc chiến dịch.',
 verified_on date not null,
 updated_at timestamptz not null default now()
);
alter table public.affiliate_programs enable row level security;

create table if not exists public.affiliate_runs (
 id uuid primary key default gen_random_uuid(),
 run_key text not null unique,
 trigger_kind text not null check (trigger_kind in ('scheduled','manual','bootstrap')),
 program_code text references public.affiliate_programs(code),
 status text not null default 'running'
   check(status in ('running','success','skipped','failed')),
 opportunity_id uuid,
 error_code text,
 started_at timestamptz not null default now(),
 finished_at timestamptz
);
alter table public.affiliate_runs enable row level security;

create table if not exists public.affiliate_opportunities (
 id uuid primary key default gen_random_uuid(),
 fingerprint text not null unique,
 program_code text not null references public.affiliate_programs(code),
 niche text not null,
 proposal jsonb not null,
 official_evidence jsonb not null default '[]'::jsonb,
 screening_score smallint not null check(screening_score between 0 and 100),
 screening_notes jsonb not null default '[]'::jsonb,
 review_status text not null default 'pending'
   check(review_status in ('pending','approved','rejected')),
 publishing_status text not null default 'draft_only'
   check(publishing_status='draft_only'),
 affiliate_link text,
 source_run_id uuid not null references public.affiliate_runs(id),
 created_at timestamptz not null default now(),
 constraint no_auto_affiliate_link check(affiliate_link is null)
);
create index if not exists affiliate_opportunities_review_idx
 on public.affiliate_opportunities(review_status,created_at desc);
alter table public.affiliate_opportunities enable row level security;
-- First deployment adds the constraint exactly once.
do $$ begin
 if not exists (select 1 from pg_constraint where conname='fk_affiliate_run_opportunity') then
  alter table public.affiliate_runs add constraint fk_affiliate_run_opportunity
   foreign key(opportunity_id) references public.affiliate_opportunities(id);
 end if;
end $$;

create table if not exists public.affiliate_metrics (
 id uuid primary key default gen_random_uuid(),
 opportunity_id uuid not null references public.affiliate_opportunities(id),
 period_start date not null,
 impressions integer not null default 0 check(impressions >= 0),
 clicks integer not null default 0 check(clicks >= 0),
 conversions integer not null default 0 check(conversions >= 0),
 confirmed_commission_vnd bigint not null default 0 check(confirmed_commission_vnd >= 0),
 evidence_url text,
 evidence_notes text,
 provenance text not null default 'owner_manual'
   check(provenance in ('owner_manual','provider_export')),
 created_at timestamptz not null default now(),
 constraint commission_requires_evidence check (
   confirmed_commission_vnd=0 or nullif(btrim(evidence_url),'') is not null
 )
);
alter table public.affiliate_metrics enable row level security;

create or replace view public.affiliate_review_dashboard with (security_invoker=true) as
select o.id, o.program_code, p.name as program_name, o.niche, o.created_at,
 o.proposal->>'title' as title, o.screening_score, o.review_status,
 o.publishing_status, coalesce(m.impressions,0) as impressions,
 coalesce(m.clicks,0) as clicks, coalesce(m.conversions,0) as conversions,
 coalesce(m.confirmed_commission_vnd,0) as confirmed_commission_vnd
from public.affiliate_opportunities o
join public.affiliate_programs p on p.code=o.program_code
left join lateral (
 select sum(impressions)::bigint as impressions,
  sum(clicks)::bigint as clicks, sum(conversions)::bigint as conversions,
  sum(confirmed_commission_vnd)::bigint as confirmed_commission_vnd
 from public.affiliate_metrics x where x.opportunity_id=o.id
) m on true;

revoke all on public.affiliate_review_dashboard from public,anon,authenticated;
grant select on public.affiliate_review_dashboard to service_role;

insert into public.affiliate_programs
(code,name,official_url,evidence_url,access_notes,eligibility_notes,commission_notes,verified_on)
values
('accesstrade','ACCESSTRADE Publisher','https://accesstrade.vn/access-affiliate-publisher/',
 'https://help.accesstrade.vn/knowledgebase/quy-trinh-co-ban/',
 'Publisher đăng ký, xin duyệt chiến dịch và tự tạo liên kết trong tài khoản được duyệt.',
 'Kiểm tra điều kiện của từng chiến dịch và kênh quảng bá theo chính sách nhà cung cấp.',
 'Tỷ lệ và điều kiện ghi nhận hoa hồng thay đổi theo chiến dịch, chưa xác minh.','2026-11-02'),
('shopee_koc','Shopee KOC Affiliate','https://shopee.vn/affiliate/',
 'https://help.shopee.vn/portal/4/article/91992',
 'Người dùng cần đăng ký chương trình Shopee Affiliate, tạo liên kết hợp lệ trong tài khoản.',
 'Chương trình KOC mở đăng ký, nhưng cần kiểm tra trạng thái được duyệt và điều khoản.',
 'Chưa có tỷ lệ hoa hồng được xác minh cho sản phẩm cụ thể.','2026-11-02'),
('tiktok_shop','TikTok Shop Affiliate Creator',
 'https://seller-vn.tiktok.com/university/essay?knowledge_id=6837793229817601',
 'https://seller-vn.tiktok.com/university/essay?knowledge_id=10013032&lang=en',
 'Cần tài khoản TikTok Shop Creator đủ điều kiện và quyền affiliate được duyệt.',
 'Theo hướng dẫn ngày 17/07/2026: đầy đủ tính năng Affiliate Creator thường cần từ 1.000 người theo dõi, từ 18 tuổi; kiểm tra Link-Share Only riêng.',
 'Chưa xác minh tỷ lệ hoa hồng hay tính đủ điều kiện của tài khoản.','2026-11-02')
on conflict (code) do nothing;
