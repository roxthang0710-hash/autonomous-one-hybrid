-- Store the native Topic requested on the Meta API container.
-- A requested Topic is NOT proof that the post appeared in a Community.
alter table public.threads_posts
  add column if not exists topic_tag_requested text;
alter table public.threads_posts
  drop constraint if exists threads_topic_request_allowed;
alter table public.threads_posts add constraint threads_topic_request_allowed
check (topic_tag_requested is null or
       topic_tag_requested in ('Công sở','Đời sống đi làm','Góc làm việc','Du lịch'));
