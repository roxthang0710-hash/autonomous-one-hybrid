// Public Enna observatory: read-only, allowlisted aggregate telemetry.
// NEVER expose credentials, draft copy, private proposals, error strings or raw records.
const CORS = {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Allow-Headers':'content-type, apikey, authorization','Access-Control-Max-Age':'86400'};
const reply = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{...CORS,'Content-Type':'application/json; charset=utf-8','Cache-Control':'public, max-age=45, s-maxage=60','X-Content-Type-Options':'nosniff'}});
Deno.serve(async (request: Request) => {
  if (request.method === 'OPTIONS') return new Response(null,{status:204,headers:CORS});
  if (request.method !== 'GET') return reply({error:'Method not allowed'},405);
  try {
    const url = Deno.env.get('SUPABASE_URL');
    const keys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') || '{}');
    const secret = keys.default || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    if (!url || !secret) return reply({error:'Dữ liệu chưa sẵn sàng'},503);
    const endpoints: Record<string,string> = {
      research: 'agent_runs?select=started_at,finished_at,status,trigger_kind&order=started_at.desc&limit=25',
      growth: 'growth_runs?select=started_at,finished_at,status,signal_count,shortlisted,drafts_created&order=started_at.desc&limit=25',
      posts: 'threads_posts?select=status,scheduled_at,published_at&limit=500',
      tasks: 'agent_tasks?select=status,kind&limit=500',
      replies: 'growth_engagement_attempts?select=status,finished_at&limit=500',
      account: 'threads_channels?select=username,status,authorized,auto_publish_enabled&limit=1',
      learning: 'enna_learning_policy?select=preferred_format,applied_at,version&brand_key=eq.do_hay_di_lam&limit=1',
      learningDecisions: 'enna_learning_decisions?select=evaluated_at,decision&brand_key=eq.do_hay_di_lam&order=evaluated_at.desc&limit=8',
      providerEvidence: 'enna_publication_evidence?select=provider_status,meta_post_id,checked_at&brand_key=eq.do_hay_di_lam&limit=60'
    };
    const entries = await Promise.all(Object.entries(endpoints).map(async ([name, endpoint])=>{
      const res = await fetch(url+'/rest/v1/'+endpoint,{headers:{apikey:secret,Authorization:'Bearer '+secret,Accept:'application/json'},signal:AbortSignal.timeout(8000)});
      if(!res.ok) throw new Error('source_failure');
      return [name,await res.json()] as const;
    }));
    const s = Object.fromEntries(entries) as Record<string,any[]>;
    const by = (rows:any[],status:string) => rows.filter(r=>r.status===status).length;
    const timeline = [
      ...s.research.map(r=>({at:r.started_at,kind:'research',status:r.status})),
      ...s.growth.map(r=>({at:r.started_at,kind:'growth',status:r.status})),
      ...s.learningDecisions.map(r=>({at:r.evaluated_at,kind:'learning',status:r.decision}))
    ].filter(r=>r.at && Number.isFinite(Date.parse(r.at)))
      .sort((a,b)=>Date.parse(b.at)-Date.parse(a.at)).slice(0,15);
    const latest = timeline[0] || null;
    const connected = !!(s.account[0]?.authorized && s.account[0]?.status==='connected');
    const working = !!(latest?.status==='running' && Date.now()-Date.parse(latest.at)<15*60000 && Date.now()>=Date.parse(latest.at));
    const taskStatus = {completed:by(s.tasks,'completed'),pending:by(s.tasks,'pending'),blocked:by(s.tasks,'blocked')};
    return reply({
      updatedAt: new Date().toISOString(),
      account: { username:'@dohay_dilam',connected,autoPublishEnabled:!!s.account[0]?.auto_publish_enabled },
      runtime: { state:working?'working':latest?.status==='failed'?'attention':connected?'scheduled':'attention',lastRunAt:latest?.at||null },
      posts: {queued:by(s.posts,'queued'),scheduledExternal:by(s.posts,'scheduled_external'),posted:by(s.posts,'posted'),uncertain:by(s.posts,'uncertain'),totalInSample:s.posts.length},
      tasks: taskStatus,
      replies: {posted:by(s.replies,'posted')+by(s.replies,'success'),attempts:s.replies.length},
      runs: {recentResearch:s.research.length,recentGrowth:s.growth.length},
      learning: {format:['balanced','story','practical'].includes(s.learning[0]?.preferred_format)
                      ? s.learning[0].preferred_format : 'unknown',
                 version:Number(s.learning[0]?.version)||null,
                 updatedAt:s.learning[0]?.applied_at||null,
                 lastDecision:s.learningDecisions[0]?.decision||'not_evaluated',
                 lastEvaluatedAt:s.learningDecisions[0]?.evaluated_at||null},
      providerPublications: {
        metricoolReportedPublished:s.providerEvidence.filter(r=>r.provider_status==='PUBLISHED').length,
        metaIdsConfirmed:s.providerEvidence.filter(r=>r.provider_status==='PUBLISHED' && !!r.meta_post_id).length
      },
      activity:timeline
    });
  } catch (_error) {
    return reply({error:'Không thể đồng bộ dữ liệu lúc này. Thử lại sau.'},502);
  }
});