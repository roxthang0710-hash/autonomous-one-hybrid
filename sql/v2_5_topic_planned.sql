-- Native Threads Topic experiment metadata; one topic per candidate.
-- planned = intent, requested = written only after confirmed Meta publish.
alter table public.threads_posts add column if not exists topic_tag_planned text;
alter table public.threads_posts
  drop constraint if exists threads_topic_planned_allowed;
alter table public.threads_posts add constraint threads_topic_planned_allowed
  check (topic_tag_planned is null or topic_tag_planned in
         ('Công sở','Góc làm việc','Đời sống đi làm','Du lịch'));
update public.threads_posts
set topic_tag_planned=case
  when id='223367c4-f428-4e58-b9bd-80fd8e2eb8be'::uuid then 'Công sở'
  when id='53db9021-5a53-4786-87b4-dd08555bd3d6'::uuid then 'Góc làm việc'
end, updated_at=now()
where status='queued'
and id in ('223367c4-f428-4e58-b9bd-80fd8e2eb8be'::uuid,
           '53db9021-5a53-4786-87b4-dd08555bd3d6'::uuid);