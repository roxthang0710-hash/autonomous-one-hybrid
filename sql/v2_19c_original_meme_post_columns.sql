-- Original Enna meme card publishing metadata, never outside media domains.
alter table public.threads_posts
  add column if not exists media_url text,
  add column if not exists media_alt_text text,
  add column if not exists media_idea_id uuid references public.enna_media_ideas(id);
alter table public.threads_posts
  add constraint threads_licensed_original_media_only
  check (
    (media_url is null and media_alt_text is null and media_idea_id is null)
    or
    (media_url ~ '^https://gjdvdohylvsauphhkutw[.]supabase[.]co/storage/v1/object/public/enna-original-media/meme/original-[a-z0-9_-]+[.]png$'
     and media_idea_id is not null and length(media_alt_text) between 12 and 180
     and editorial_series='visual_meme'
     and content_type='editorial')
  );
