-- Enna monetization readiness v1: owner-controlled, no automated sales.
-- All commercial tracks are hypotheses, not income or verified offers.
create table if not exists public.enna_monetization_tracks (
  track_key text primary key check(track_key in ('affiliate_work_gear','brand_partnerships','office_digital_goods')),
  label text not null,
  intended_audience text not null,
  proposed_value text not null,
  stage text not null default 'hypothesis'
    check(stage in ('hypothesis','testing','approved','live','paused')),
  owner_approved boolean not null default false,
  fulfillment_verified boolean not null default false,
  claims_verified boolean not null default false,
  disclosures_ready boolean not null default false,
  review_notes text not null default 'Chưa có bằng chứng thị trường.',
  evidence jsonb not null default '{}'::jsonb
    check(jsonb_typeof(evidence)='object'),
  updated_at timestamptz not null default now(),
  constraint no_unreviewed_commercial_go_live check (
    stage not in ('approved','live') or (
      owner_approved and fulfillment_verified and claims_verified and disclosures_ready
    )
  )
);
alter table public.enna_monetization_tracks enable row level security;
revoke all on public.enna_monetization_tracks from public,anon,authenticated;
grant select,insert,update,delete on public.enna_monetization_tracks to service_role;

create table if not exists public.enna_revenue_receipts (
  id uuid primary key default gen_random_uuid(),
  track_key text not null references public.enna_monetization_tracks(track_key),
  amount_received_vnd bigint not null check(amount_received_vnd > 0),
  received_on date not null,
  verification_method text not null
    check(verification_method in ('owner_bank_reconciliation','provider_settlement_export')),
  evidence_reference text not null check(length(btrim(evidence_reference)) >= 12),
  checked_at timestamptz not null default now(),
  dedup_key text not null unique check(length(dedup_key) between 12 and 150)
);
alter table public.enna_revenue_receipts enable row level security;
revoke all on public.enna_revenue_receipts from public,anon,authenticated;
grant select,insert,update,delete on public.enna_revenue_receipts to service_role;

insert into public.enna_monetization_tracks
(track_key,label,intended_audience,proposed_value,review_notes)
values
('affiliate_work_gear','KOC: đồ dùng làm việc hữu ích',
 'Nhân viên công sở và người học tập tại nhà',
 'Danh sách tiêu chí chọn phụ kiện bàn làm việc; chỉ chia sẻ sản phẩm được xác minh',
 'Chưa có tài khoản publisher được duyệt; chưa xác minh giá, sản phẩm và commission.'),
('brand_partnerships','Hợp tác thương hiệu',
 'Nhãn hàng phụ kiện văn phòng, công nghệ và dịch vụ người đi làm',
 'Các nội dung tài trợ minh bạch và đúng tệp độc giả sau khi có chỉ số thực tế',
 'Chưa có hợp đồng, báo giá hay booking thực tế.'),
('office_digital_goods','Bộ công cụ số cho dân công sở',
 'Nhân viên mới, thực tập sinh và người quản lý việc cá nhân',
 'Bản dùng thử checklist, mẫu tổ chức tệp và mẫu ưu tiên công việc; xác minh nhu cầu trước bán',
 'Chưa phỏng vấn người mua, chưa mở bán, chưa có thanh toán.')
on conflict(track_key) do nothing;
