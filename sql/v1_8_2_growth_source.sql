-- v1.8.2: provenance for content selected from a current verified trend.
alter table public.threads_posts
add column if not exists origin_growth_opportunity_id uuid
references public.growth_opportunities(id);
create unique index if not exists threads_posts_one_per_growth_opportunity_idx
on public.threads_posts(origin_growth_opportunity_id)
where origin_growth_opportunity_id is not null;
