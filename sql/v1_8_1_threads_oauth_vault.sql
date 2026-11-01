
-- Secure OAuth authorization sessions and renewable Meta credentials.
-- The sole operator is the already-provisioned Supabase reviewer.
create table if not exists public.threads_oauth_sessions(
 id uuid primary key default gen_random_uuid(),
 state_hash text not null unique check(length(state_hash)=64),
 owner_user_id uuid not null references auth.users(id),
 app_id text not null check(app_id ~ '^[0-9]{8,30}$'),
 app_secret_ref uuid not null,
 redirect_uri text not null check(redirect_uri like 'https://%.supabase.co/functions/v1/threads-oauth/callback'),
 enable_replies boolean not null default false,
 created_at timestamptz not null default now(),
 expires_at timestamptz not null default (now() + interval '10 minutes'),
 consumed_at timestamptz
);
alter table public.threads_oauth_sessions enable row level security;
revoke all on public.threads_oauth_sessions from anon,authenticated;
grant select,insert,update on public.threads_oauth_sessions to service_role;

create table if not exists public.threads_vault_credentials(
 brand_key text primary key references public.threads_channels(brand_key),
 owner_user_id uuid not null references auth.users(id),
 app_id text not null,
 app_secret_ref uuid not null,
 access_token_ref uuid not null,
 platform_user_id text not null,
 verified_username text not null,
 expires_at timestamptz not null,
 connected_at timestamptz not null default now(),
 refreshed_at timestamptz,
 enable_replies boolean not null default false,
 status text not null default 'active'
  check(status in ('active','needs_reauth','revoked')),
 updated_at timestamptz not null default now()
);
alter table public.threads_vault_credentials enable row level security;
revoke all on public.threads_vault_credentials from anon,authenticated;
grant select,insert,update on public.threads_vault_credentials to service_role;

create or replace function public.threads_begin_oauth(
 p_owner_user_id uuid,p_state_hash text,p_app_id text,
 p_app_secret text,p_redirect_uri text,p_enable_replies boolean default false
) returns boolean
language plpgsql security definer
set search_path=public,vault,pg_temp
as $$
declare sid uuid;
begin
 if not exists(select 1 from public.agent_reviewers where user_id=p_owner_user_id) then
  raise exception 'Account is not authorized for Autonomous One';
 end if;
 if p_state_hash !~ '^[a-f0-9]{64}$' or p_app_id !~ '^[0-9]{8,30}$'
 or length(p_app_secret) not between 16 and 400 then
  raise exception 'Invalid Meta app settings';
 end if;
 if p_redirect_uri <> 'https://gjdvdohylvsauphhkutw.supabase.co/functions/v1/threads-oauth/callback' then
  raise exception 'Callback URL not registered';
 end if;
 -- Save app secret encrypted, not as plaintext in Supabase public tables.
 sid := vault.create_secret(p_app_secret);
 insert into public.threads_oauth_sessions(
 state_hash,owner_user_id,app_id,app_secret_ref,redirect_uri,enable_replies
 ) values(p_state_hash,p_owner_user_id,p_app_id,sid,p_redirect_uri,p_enable_replies);
 return true;
end $$;
revoke all on function public.threads_begin_oauth(uuid,text,text,text,text,boolean)
 from public,anon,authenticated;
grant execute on function public.threads_begin_oauth(uuid,text,text,text,text,boolean)
 to service_role;

create or replace function public.threads_claim_oauth(p_state_hash text)
returns table(owner_user_id uuid,app_id text,app_secret text,
 redirect_uri text,enable_replies boolean,app_secret_ref uuid)
language plpgsql security definer set search_path=public,vault,pg_temp
as $$
declare v public.threads_oauth_sessions%rowtype;
begin
 select * into v from public.threads_oauth_sessions s
 where s.state_hash=p_state_hash
 and s.consumed_at is null and s.expires_at>now()
 for update skip locked;
 if not found then return; end if;
 update public.threads_oauth_sessions s
 set consumed_at=now() where s.id=v.id;
 return query
 select v.owner_user_id,v.app_id,d.decrypted_secret,
        v.redirect_uri,v.enable_replies,v.app_secret_ref
 from vault.decrypted_secrets d where d.id=v.app_secret_ref;
end $$;
revoke all on function public.threads_claim_oauth(text) from public,anon,authenticated;
grant execute on function public.threads_claim_oauth(text) to service_role;

create or replace function public.threads_finish_oauth(
 p_owner_user_id uuid,p_app_id text,p_app_secret_ref uuid,
 p_access_token text,p_username text,p_platform_user_id text,
 p_expires_at timestamptz,p_enable_replies boolean default false
) returns boolean
language plpgsql security definer set search_path=public,vault,pg_temp
as $$
declare present_record public.threads_vault_credentials%rowtype;
        secretid uuid;
begin
 if not exists(select 1 from public.agent_reviewers where user_id=p_owner_user_id)
 or p_username <> 'dohay_dilam' or p_platform_user_id = ''
 or length(p_access_token) not between 40 and 4096
 or p_expires_at < now()+interval '1 day'
 or p_expires_at > now()+interval '70 days'
 then raise exception 'Token failed ownership or lifetime validation'; end if;
 if not exists(select 1 from public.threads_oauth_sessions
  where owner_user_id=p_owner_user_id and app_secret_ref=p_app_secret_ref
  and app_id=p_app_id and consumed_at is not null
  and consumed_at>now()-interval '5 minutes')
 then raise exception 'No valid OAuth session'; end if;

 select * into present_record from public.threads_vault_credentials
 where brand_key='do_hay_di_lam' for update;
 if found then
  if present_record.owner_user_id<>p_owner_user_id or
     present_record.platform_user_id<>p_platform_user_id then
   raise exception 'Threads account swap denied';
  end if;
  secretid := present_record.access_token_ref;
  perform vault.update_secret(secretid,p_access_token);
 else
  secretid := vault.create_secret(p_access_token);
 end if;
 insert into public.threads_vault_credentials(
  brand_key,owner_user_id,app_id,app_secret_ref,access_token_ref,
  platform_user_id,verified_username,expires_at,enable_replies,status
 ) values(
  'do_hay_di_lam',p_owner_user_id,p_app_id,p_app_secret_ref,secretid,
  p_platform_user_id,p_username,p_expires_at,p_enable_replies,'active'
 )
 on conflict (brand_key) do update set
  app_id=excluded.app_id,app_secret_ref=excluded.app_secret_ref,
  access_token_ref=excluded.access_token_ref,
  expires_at=excluded.expires_at,enable_replies=excluded.enable_replies,
  status='active',updated_at=now();

 -- Account switch and backlog rebasing are atomic with saving the token.
 perform public.activate_threads_channel('do_hay_di_lam',
                                         p_username,p_platform_user_id);
 return true;
end $$;
revoke all on function public.threads_finish_oauth(uuid,text,uuid,text,text,text,timestamptz,boolean)
 from public,anon,authenticated;
grant execute on function public.threads_finish_oauth(uuid,text,uuid,text,text,text,timestamptz,boolean)
 to service_role;

create or replace function public.threads_read_vault_token(p_brand_key text)
returns table(access_token text,verified_username text,platform_user_id text,
 expires_at timestamptz,enable_replies boolean)
language plpgsql security definer set search_path=public,vault,pg_temp
as $$
begin
 return query select d.decrypted_secret,v.verified_username,v.platform_user_id,
 v.expires_at,v.enable_replies from public.threads_vault_credentials v
 join vault.decrypted_secrets d on d.id=v.access_token_ref
 where v.brand_key=p_brand_key and v.status='active';
end $$;
revoke all on function public.threads_read_vault_token(text)
 from public,anon,authenticated;
grant execute on function public.threads_read_vault_token(text) to service_role;

create or replace function public.threads_refresh_vault_token(
 p_brand_key text,p_platform_user_id text,p_new_token text,p_new_expiry timestamptz
) returns boolean
language plpgsql security definer set search_path=public,vault,pg_temp
as $$
declare v public.threads_vault_credentials%rowtype;
begin
 select * into v from public.threads_vault_credentials
 where brand_key=p_brand_key and status='active'
 for update;
 if not found or v.platform_user_id<>p_platform_user_id
 or length(p_new_token) not between 40 and 4096
 or p_new_expiry < now()+interval '1 day'
 or p_new_expiry > now()+interval '70 days'
 then raise exception 'Token refresh identity or lifetime invalid'; end if;
 perform vault.update_secret(v.access_token_ref,p_new_token);
 update public.threads_vault_credentials set expires_at=p_new_expiry,
 refreshed_at=now(),updated_at=now() where brand_key=p_brand_key;
 return true;
end $$;
revoke all on function public.threads_refresh_vault_token(text,text,text,timestamptz)
 from public,anon,authenticated;
grant execute on function public.threads_refresh_vault_token(text,text,text,timestamptz)
 to service_role;

-- Prevent storing short-lived OAuth state beyond usefulness.
create index if not exists threads_oauth_session_ttl_idx
 on public.threads_oauth_sessions(expires_at,consumed_at);
