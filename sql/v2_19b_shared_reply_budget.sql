-- Keep external and own-audience replies within the same atomic 3/day.
do $$
declare
  old_def text;
  changed_def text;
  needle text := '  if v_count >= 3 then return; end if;';
begin
  select pg_get_functiondef(p.oid) into old_def
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='growth_claim_safe_reply';
  if old_def is null or position(needle in old_def)=0 then
    raise exception 'Cannot locate existing external reply safety cap';
  end if;
  changed_def:=replace(old_def,needle,
    '  -- Include own-audience comment claims in the same 3/day cap.'||E'\n'||
    '  select v_count + count(*) into v_count'||E'\n'||
    '  from public.enna_community_attempts a'||E'\n'||
    '  where (a.claimed_at at time zone ''Asia/Ho_Chi_Minh'')::date=v_today;'||E'\n'||
    needle);
  execute changed_def;
end $$;