// Public Enna observatory: read-only, allowlisted aggregate telemetry.
// NEVER expose credentials, draft copy, private proposals, error strings or raw records.
const CORS = {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Allow-Headers':'content-type, apikey, authorization','Access-Control-Max-Age':'86400'};
const reply = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{...CORS,'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store, max-age=0, must-revalidate','X-Content-Type-Options':'nosniff'}});
Deno.serve(async (request: Request) => {
  if (request.method === 'OPTIONS') return new Response(null,{status:204,headers:CORS});
  if (request.method !== 'GET') return reply({error:'Method not allowed'},405);
  try {
    const url = Deno.env.get('SUPABASE_URL');
    const keys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') || '{}');
    const secret = keys.default || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    if (!url || !secret) return reply({error:'Dữ liệu chưa sẵn sàng'},503);
    // Lightweight redacted operational journal for frequent dashboard polling.
    // RLS protects the raw table; this endpoint never returns drafts or secrets.
    if (new URL(request.url).searchParams.get('mode') === 'events') {
      const endpoint='enna_activity_events?select=occurred_at,kind,status,code,trigger_kind&order=occurred_at.desc&limit=60';
      const res=await fetch(url+'/rest/v1/'+endpoint,{
        headers:{apikey:secret,Authorization:'Bearer '+secret,Accept:'application/json'},
        signal:AbortSignal.timeout(8000)
      });
      if(!res.ok) throw new Error('journal_source_unavailable');
      const events=(await res.json()) as Array<{occurred_at:string;kind:string;status:string;code:string;trigger_kind:string}>;
      const activity=events.filter(e=>Number.isFinite(Date.parse(e.occurred_at)))
        .map(e=>({at:e.occurred_at,kind:e.kind,status:e.status,code:e.code,trigger_kind:e.trigger_kind}));
      return reply({updatedAt:new Date().toISOString(),activity,source:'verified_backend_events'});
    }
    const endpoints: Record<string,string> = {
      research: 'agent_runs?select=started_at,finished_at,status,trigger_kind&order=started_at.desc&limit=25',
      growth: 'growth_runs?select=started_at,finished_at,status,signal_count,shortlisted,drafts_created&order=started_at.desc&limit=25',
      posts: 'threads_posts?select=id,status,scheduled_at,published_at,platform_post_id,topic_tag_planned,topic_tag_requested,editorial_series&limit=500',
      tasks: 'agent_tasks?select=status,kind&limit=500',
      replies: 'growth_engagement_attempts?select=status,finished_at&limit=500',
      account: 'threads_channels?select=username,status,authorized,auto_publish_enabled&limit=1',
      learning: 'enna_learning_policy?select=preferred_format,applied_at,version&brand_key=eq.do_hay_di_lam&limit=1',
      learningDecisions: 'enna_learning_decisions?select=evaluated_at,decision&brand_key=eq.do_hay_di_lam&order=evaluated_at.desc&limit=8',
      providerEvidence: 'enna_publication_evidence?select=scheduled_post_id,provider_status,meta_post_id,checked_at&brand_key=eq.do_hay_di_lam&limit=200',
      events: 'enna_activity_events?select=occurred_at,kind,status,code,trigger_kind&order=occurred_at.desc&limit=80',
      metricoolDaily: 'growth_metricool_daily?select=measured_on,followers,new_followers&metricool_brand_id=eq.7803567&order=measured_on.desc&limit=14'
    };
    const entries = await Promise.all(Object.entries(endpoints).map(async ([name, endpoint])=>{
      const res = await fetch(url+'/rest/v1/'+endpoint,{headers:{apikey:secret,Authorization:'Bearer '+secret,Accept:'application/json'},signal:AbortSignal.timeout(8000)});
      if(!res.ok) throw new Error('source_failure');
      return [name,await res.json()] as const;
    }));
    const s = Object.fromEntries(entries) as Record<string,any[]>;
    const by = (rows:any[],status:string) => rows.filter(r=>r.status===status).length;
    // Keep provider confirmation and Meta media-ID verification separate.
    // A PUBLISHED Metricool post still marked scheduled_external in our DB
    // MUST show as published without falsifying its Meta reconciliation status.
    const metaPosted = new Set(s.posts.filter(r=>r.status==='posted' &&
      typeof r.platform_post_id==='string' && r.platform_post_id.length>0).map(r=>r.id));
    const providerPublished = s.providerEvidence.filter(r=>r.provider_status==='PUBLISHED');
    const providerPublishedIds = new Set(providerPublished.map(r=>r.scheduled_post_id).filter(Boolean));
    const providerOnly = providerPublished.filter(r=>!r.scheduled_post_id || !metaPosted.has(r.scheduled_post_id));
    const publishedTotal = metaPosted.size + providerOnly.length;
    const followerRow=s.metricoolDaily.find(r=>Number.isInteger(r.followers) && r.followers>=0)||null;
    const awaitingExternal = s.posts.filter(r=>r.status==='scheduled_external' && !providerPublishedIds.has(r.id)).length;
    const runTimeline = [
      ...s.research.map(r=>({at:r.started_at,kind:'research',status:r.status})),
      ...s.growth.map(r=>({at:r.started_at,kind:'growth',status:r.status}))
    ].filter(r=>r.at && Number.isFinite(Date.parse(r.at)))
      .sort((a,b)=>Date.parse(b.at)-Date.parse(a.at));
    const recentEvents = s.events.filter(e=>Number.isFinite(Date.parse(e.occurred_at)))
      .map(e=>({at:e.occurred_at,kind:e.kind,status:e.status,code:e.code,trigger_kind:e.trigger_kind}));
    const timeline = [
      ...recentEvents,
      ...runTimeline,
      ...s.learningDecisions.map(r=>({at:r.evaluated_at,kind:'learning',status:r.decision})),
      ...providerPublished.map(r=>({at:r.checked_at,kind:'publication',status:'provider_published'}))
    ].filter(r=>r.at && Number.isFinite(Date.parse(r.at)))
      .sort((a,b)=>Date.parse(b.at)-Date.parse(a.at)).slice(0,45);
    const latest = runTimeline[0] || null;
    const connected = !!(s.account[0]?.authorized && s.account[0]?.status==='connected');
    const lifecycle=s.events.filter(e=>e.kind==='publisher' &&
      ['ops_started','ops_completed','ops_failed','publisher_started','publisher_completed','publisher_failed'].includes(e.code));
    const currentWorker=lifecycle[0]||null;
    const lastScheduledWorker=lifecycle.find(e=>e.trigger_kind==='schedule' &&
      ['ops_completed','publisher_completed','ops_failed','publisher_failed'].includes(e.code))||null;
    const lastWorkerAt=currentWorker?.occurred_at||null;
    const ageMinutes=lastWorkerAt?(Date.now()-Date.parse(lastWorkerAt))/60000:null;
    const working=!!(currentWorker?.status==='started' && ageMinutes!==null &&
      ageMinutes>=0 && ageMinutes<12);
    const stale=!!(currentWorker?.status==='started' && ageMinutes!==null && ageMinutes>=12);
    const failed=!!(currentWorker?.status==='failed');
    const taskStatus = {completed:by(s.tasks,'completed'),pending:by(s.tasks,'pending'),blocked:by(s.tasks,'blocked')};
    return reply({
      updatedAt: new Date().toISOString(),
      account: { username:'@dohay_dilam',connected,autoPublishEnabled:!!s.account[0]?.auto_publish_enabled },
      runtime: {
        state:working?'working':stale||failed||latest?.status==='failed'?'attention':connected?'scheduled':'attention',
        lastRunAt:lastWorkerAt||latest?.at||null,
        workerLastResult:currentWorker?.code||'no_worker_heartbeat',
        workerTrigger:currentWorker?.trigger_kind||'unknown',
        lastScheduledRunAt:lastScheduledWorker?.occurred_at||null,
        workerLastAt:lastWorkerAt
      },
      posts: {queued:by(s.posts,'queued'),scheduledExternal:awaitingExternal,
              published:publishedTotal, posted:metaPosted.size,
              providerOnlyPublished:providerOnly.length,
              uncertain:by(s.posts,'uncertain'),totalInSample:s.posts.length},
      tasks: taskStatus,
      replies: {posted:by(s.replies,'posted')+by(s.replies,'success'),attempts:s.replies.length},
      runs: {recentResearch:s.research.length,recentGrowth:s.growth.length,
             verifiedWorkerEvents:lifecycle.length},
      learning: {format:['balanced','story','practical'].includes(s.learning[0]?.preferred_format)
                      ? s.learning[0].preferred_format : 'unknown',
                 version:Number(s.learning[0]?.version)||null,
                 updatedAt:s.learning[0]?.applied_at||null,
                 lastDecision:s.learningDecisions[0]?.decision||'not_evaluated',
                 lastEvaluatedAt:s.learningDecisions[0]?.evaluated_at||null},
      providerPublications: {
        metricoolReportedPublished:providerPublished.length,
        metaIdsConfirmed:metaPosted.size
      },
      followerKpi: {
        goal:1000,
        latestKnown:followerRow?.followers??null,
        asOf:followerRow?.measured_on||null,
        latestDailyDelta:followerRow?.new_followers??null,
        upToDate:false
      },
      topics: {
        nativeQueued:s.posts.filter(r=>r.status==='queued' && !!r.topic_tag_planned).length,
        nativeRequestedOnPublished:s.posts.filter(r=>r.status==='posted' && !!r.topic_tag_requested).length,
        communityPostsConfirmed:0
      },
      contentSeries: {
        nightScheduled:s.posts.filter(r=>r.editorial_series==='night_owl' && r.status==='scheduled_external').length,
        nightConfirmed:s.posts.filter(r=>r.editorial_series==='night_owl' && r.status==='posted').length,
        officeStoryScheduled:s.posts.filter(r=>r.editorial_series==='office_story' && r.status==='scheduled_external').length
      },
      activity:timeline
    });
  } catch (_error) {
    return reply({error:'Không thể đồng bộ dữ liệu lúc này. Thử lại sau.'},502);
  }
});