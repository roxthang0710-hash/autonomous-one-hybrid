-- Refresh verified 2026 Shopee KOC public eligibility ONLY.
-- Never infer the owner's registration or account approval from public rules.
update public.affiliate_programs
set evidence_url='https://help.shopee.vn/portal/10/article/122944',
    eligibility_notes='Theo điều khoản Shopee cập nhật 08/07/2026: KOC không có ngưỡng người theo dõi tối thiểu như KOL; ứng viên phải đăng ký và được Shopee xét duyệt. Chưa xác minh tài khoản chủ sở hữu.',
    access_notes='Tài khoản cá nhân có thể đăng ký từ affiliate.shopee.vn hoặc ứng dụng; chỉ tạo link sau khi tài khoản và chiến dịch được xét duyệt theo điều kiện áp dụng.',
    verified_on=date '2026-11-03',
    updated_at=now()
where code='shopee_koc' and review_status='research_only';
