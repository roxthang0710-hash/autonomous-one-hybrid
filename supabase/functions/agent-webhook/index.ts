// This is the Edge Function deployed as agent-webhook to Supabase project autonomous-one.
// The platform JWT check is disabled for this endpoint; authentication is via x-agent-secret.
import { createClient } from 'npm:@supabase/supabase-js@2.57.0';

const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status, headers: { 'content-type': 'application/json' },
  });

async function sameSecret(a: string, b: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest('SHA-256', encoder.encode(a)),
    crypto.subtle.digest('SHA-256', encoder.encode(b)),
  ]);
  const x = new Uint8Array(ha), y = new Uint8Array(hb);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
  const expected = Deno.env.get('WEBHOOK_SECRET');
  if (!expected || expected.length < 32 ||
      !(await sameSecret(req.headers.get('x-agent-secret') ?? '', expected))) {
    return json({ error: 'unauthorized' }, 401);
  }
  const raw = await req.text();
  if (raw.length > 4096) return json({ error: 'payload_too_large' }, 413);
  let body: Record<string, unknown>;
  try { body = JSON.parse(raw); }
  catch { return json({ error: 'invalid_json' }, 400); }
  const { kind, topic, request_id } = body;
  if (kind !== 'research_request' || typeof topic !== 'string' ||
      topic.trim().length < 3 || topic.length > 140) {
    return json({ error: 'invalid_topic' }, 400);
  }
  if (typeof request_id !== 'string' ||
      !/^[a-zA-Z0-9_-]{8,80}$/.test(request_id)) {
    return json({ error: 'invalid_request_id' }, 400);
  }
  const base = Deno.env.get('SUPABASE_URL');
  const key = Deno.env.get('DB_SERVICE_KEY');
  const token = Deno.env.get('GITHUB_DISPATCH_TOKEN');
  const repo = Deno.env.get('GITHUB_REPOSITORY_NAME');
  if (!base || !key || !token || !repo || !/^[\w.-]+\/[\w.-]+$/.test(repo)) {
    return json({ error: 'server_configuration_incomplete' }, 503);
  }
  const db = createClient(base, key, { auth: { persistSession: false } });
  const { data, error } = await db.from('agent_events').upsert({
    request_id, kind, payload: { topic: topic.trim() }, status: 'pending',
  }, { onConflict: 'request_id', ignoreDuplicates: true }).select('id');
  if (error) return json({ error: 'database_insert_failed' }, 500);
  if (!data?.length) return json({ accepted: true, duplicate: true });
  try {
    const response = await fetch('https://api.github.com/repos/' + repo + '/dispatches', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + token,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
        'User-Agent': 'autonomous-one-agent-webhook',
      },
      body: JSON.stringify({
        event_type: 'agent_event', client_payload: { event_id: data[0].id },
      }),
    });
    if (!response.ok) {
      return json({ accepted: true, queued: true, dispatch_failed: true }, 202);
    }
    return json({ accepted: true, queued: true, event_id: data[0].id }, 202);
  } catch {
    return json({ accepted: true, queued: true, dispatch_failed: true }, 202);
  }
});
