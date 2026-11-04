import {createClient} from "https://esm.sh/@supabase/supabase-js@2.57.0";
const SUPABASE="https://gjdvdohylvsauphhkutw.supabase.co";
const KEY="sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H";
const API=SUPABASE+"/functions/v1/enna-desk";
const supabase=createClient(SUPABASE,KEY,{auth:{flowType:"pkce",detectSessionInUrl:true,persistSession:true,autoRefreshToken:true}});
const $=id=>document.getElementById(id);
let session=null,tasks=[],notes=[],research=[],currentTimer=null,busy=false;
const kindLabels={warroom:"Phòng điều hành",report:"Báo cáo",plan:"Chiến lược",diagnose:"Chẩn đoán",ideas:"Ý tưởng"};
const formatDate=s=>{if(!s)return "";const d=new Date(s);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat("vi-VN",{timeZone:"Asia/Ho_Chi_Minh",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}).format(d):""};
const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!=null)node.textContent=String(text);if(cls)node.className=cls;return node;};
function status(message,online=false){$("connection").textContent=message;$("pulse").classList.toggle("online",online);}
function error(message){$("task-error").textContent=message;$("task-error").hidden=!message;}
async function api(method="GET",payload=null){
 const {data:{session:s},error:authError}=await supabase.auth.getSession();
 if(authError||!s?.access_token)throw Error("Phiên đăng nhập hết hạn. Hãy kết nối lại GitHub.");
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),60000);
 try{
  const res=await fetch(API,{method,cache:"no-store",signal:ctrl.signal,
   headers:{"authorization":"Bearer "+s.access_token,"apikey":KEY,...(payload?{"content-type":"application/json"}:{})},
   body:payload?JSON.stringify(payload):undefined});
  const json=await res.json().catch(()=>({}));
  if(!res.ok)throw Error(({401:"Phiên đăng nhập không hợp lệ.",403:"Tài khoản không phải chủ Enna.",429:"Đã đạt giới hạn 6 nhiệm vụ trong 15 phút.",503:"Máy chủ Enna tạm thời chưa sẵn sàng."})[res.status]||json.error||("Lỗi máy chủ "+res.status));
  return json;
 }finally{clearTimeout(timer);}
}
function renderStats(s){
 $("followers").textContent=s.follower_count==null?"—":s.follower_count.toLocaleString("vi-VN");
 const percentage=Math.min(100,100*(s.follower_count||0)/1000);
 $("follower-progress").style.width=percentage+"%";
 $("follower-date").textContent=s.follower_count==null?"Chưa có dữ liệu xác minh.":"Đo ngày "+(s.follower_day||"không rõ")+(s.follower_stale?" · DỮ LIỆU CŨ":" · "+(s.follower_source==="meta_official"?"Meta chính thức":"Metricool đã lưu"));
 $("post-count").textContent=String(s.published_threads_in_sample??"—");
 $("topic-count").textContent=String(s.native_topic_requested??"—");
 $("meme-count").textContent=String(s.original_memes_ready??"—");
 $("video-count").textContent=String(s.original_videos_ready??"—");
 $("stats-caveat").textContent=s.caveat||"";
}
function renderSprint(sprint){
 const parent=$("growth-sprint");parent.replaceChildren();
 if(!sprint){parent.append(el("p","Chưa có thử nghiệm tăng trưởng đã ghi nhận.","muted"));return;}
 const meta=sprint.latest_observation||{};
 const proof=sprint.execution_proof||{};
 const h=el("div",null,"sprint-summary");
 h.append(el("strong",sprint.focus==="practical_follow_value"?"Thử nghiệm: nội dung thực dụng có ích":"Thử nghiệm: điều chỉnh phân phối"));
 h.append(el("p",sprint.status==="running"?"Đang chạy · Đánh giá ngày "+sprint.evaluation_due:"Trạng thái: "+sprint.status));
 const proofText=proof.policy_applied?
   (proof.actual_change?"Enna đã tự thay đổi chính sách biên tập cho các bản nháp tương lai.":"Chính sách phù hợp đã có sẵn; Enna không chỉnh sửa lại.") :
   "Chưa xác minh được thao tác thay đổi chính sách.";
 h.append(el("p",proofText));
 if(typeof meta.baseline_followers==="number")h.append(el("p",
   "Mốc ban đầu: "+meta.baseline_followers+" follower, "+(meta.baseline_profile_views??"—")+
   " lượt xem hồ sơ (mẫu Metricool)."));
 if(sprint.status==="completed"){
   const o=meta;
   h.append(el("p","Kết quả đánh giá: "+(sprint.decision||"chưa xác minh")+
     (typeof o.observed_net_change==="number"?" · Biến động follower: "+o.observed_net_change:"")));
 }
 h.append(el("p","Không tự coi sự thay đổi follower là hiệu quả do thử nghiệm gây ra. Enna không sửa bài Metricool đã lên lịch.","muted"));
 parent.append(h);
}
function renderTasks(){
 const parent=$("task-list");parent.replaceChildren();
 if(!tasks.length){parent.append(el("p","Chưa có nhiệm vụ. Hãy giao công việc đầu tiên cho Enna.","muted"));return;}
 for(const item of tasks){
  const node=el("article",null,"task");
  const head=el("div",null,"task-head");
  head.append(el("strong",kindLabels[item.kind]||"Nhiệm vụ"),el("small",formatDate(item.created_at)));
  node.append(head,el("p",item.request_text));
  const data=item.response||{};
  const aiComplete=item.status==="completed"&&item.model_used==="groq_task_specific_v2"&&typeof data.direct_answer==="string";
  const isFailed=item.status==="failed";
  const label=aiComplete?"Đã có phân tích AI":isFailed?"Không xử lý được":"Đang phân tích · chưa có kết quả AI";
  node.append(el("span",label,"tag"+(aiComplete?"":isFailed?" fail":" wait")));
  if(aiComplete){
   const answer=el("div",null,"agent-answer");
   answer.append(el("h3","Enna trả lời trực tiếp"),el("p",data.direct_answer));
   if(Array.isArray(data.verified_findings)&&data.verified_findings.length){
    answer.append(el("h4","Căn cứ đang có"));
    const list=el("ul");
    for(const fact of data.verified_findings.slice(0,4))list.append(el("li",fact));
    answer.append(list);
   }
   if(Array.isArray(data.action_plan)&&data.action_plan.length){
    answer.append(el("h4","Phương án hành động"));
    const list=el("ol");
    for(const step of data.action_plan.slice(0,5)){
     const li=el("li");
     li.append(el("strong",step.action||"Chưa xác định"));
     li.append(el("p",step.rationale||""));
     const actor=step.executor==="owner"?"Cần bạn":step.executor==="joint"?"Enna & bạn":"Enna";
     li.append(el("small",actor+" · "+(step.status==="needs_permission"?"Chờ cấp quyền":"Đề xuất, chưa thực hiện")+" · Kiểm chứng: "+(step.success_check||"Chưa có")));
     list.append(li);
    }
    answer.append(list);
   }
   if(Array.isArray(data.unknowns)&&data.unknowns.length){
    answer.append(el("h4","Điều chưa xác minh"));
    const list=el("ul");for(const v of data.unknowns.slice(0,3))list.append(el("li",v));answer.append(list);
   }
   const detail=el("details");
   detail.append(el("summary","Xem góc nhìn của ba chuyên trách"));
   for(const role of Array.isArray(data.roles)?data.roles:[]){
    const name=({analyst:"📈 Phân tích",strategist:"💡 Chiến lược",operator:"🛠 Vận hành"})[role.role]||role.role;
    detail.append(el("h4",name),el("p",role.summary||""));
   }
   answer.append(detail);
   answer.append(el("p","Đây là phân tích AI. Những hành động chưa có bằng chứng thực hiện đều được ghi là đề xuất.","muted"));
   node.append(answer);
  }else if(isFailed){
   node.append(el("p","Enna chưa xử lý được nhiệm vụ: "+(item.error_code||"lỗi không xác định")+". Không có câu trả lời mẫu được coi là hoàn thành.","muted"));
  }else{
   const oldAnswer=["rule_based_multi_role","groq_multi_role_partial"].includes(item.model_used);
   node.append(el("p",oldAnswer?
    "Enna đã nhận diện đây là phản hồi theo khuôn cũ và đang thay thế bằng phân tích thực sự theo nhiệm vụ. Nội dung cũ không còn được tính là kết quả đạt yêu cầu.":
    "Enna đã tiếp nhận nhiệm vụ. Đang phân tích số liệu và yêu cầu của bạn bằng mô hình; nhật ký sẽ tự cập nhật khi có câu trả lời được kiểm chứng.","processing-message"));
   if(item.error_code)node.append(el("p","Lượt phân tích trước chưa đạt: "+item.error_code+". Worker sẽ thử lại theo lịch, không gửi trùng nhiệm vụ.","muted"));
  }
  parent.append(node);
 }
}
function renderResearch(){
 const parent=$("research-list");parent.replaceChildren();
 if(!research.length){parent.append(el("p","Chưa có nghiên cứu được gửi từ Enna Desk.","muted"));return;}
 for(const run of research.slice(0,12)){
  const card=el("article",null,"task research-results");const heading=el("div",null,"task-head");
  heading.append(el("strong",run.topic||"Nghiên cứu"),el("small",formatDate(run.created_at)));
  card.append(heading,el("span",run.status==="completed"?"Đã hoàn thành":run.status==="failed"?"Gặp lỗi":run.status==="pending"?"Chờ worker":"Đang thực hiện","tag"+(run.status==="failed"?" fail":run.status==="completed"?"":" wait")));
  if(Array.isArray(run.proposals)&&run.proposals.length){
   for(const p of run.proposals.slice(0,3)){
    const proposal=p.proposal||{};
    const details=el("details");details.append(el("summary","Xem phương án nghiên cứu ("+(p.approval_status||"chờ duyệt")+")"));
    for(const k of ["title","target_customer","problem_hypothesis","zero_cost_experiment","success_metric","risks","recommended_next_step"]){
     const v=proposal[k];if(v==null)continue;
     const text=Array.isArray(v)?v.join("; "):String(v);
     details.append(el("p",k.replaceAll("_"," ")+": "+text.slice(0,900)));
    }
    card.append(details);
   }
  }else card.append(el("p","Chưa có đề xuất được xác nhận từ worker. Theo dõi trạng thái; không tự gửi lại nếu yêu cầu chưa rõ kết quả.","muted"));
  parent.append(card);
 }
}

function renderNotes(){
 const parent=$("notification-list");parent.replaceChildren();
 const active=notes.filter(n=>!n.acknowledged_at);
 $("notification-count").textContent=active.length+" cần xem";
 if(!active.length){parent.append(el("p","Chưa có cảnh báo chưa xử lý. Enna sẽ cập nhật khi có nguồn dữ liệu mới.","muted"));return;}
 for(const n of active.slice(0,18)){
  const box=el("article",null,"note "+(n.severity||"info"));
  box.append(el("h3",n.title),el("p",n.details),el("p","Đề xuất: "+n.suggested_action));
  const b=el("button","Đã xem");b.type="button";b.addEventListener("click",async()=>{b.disabled=true;try{await api("POST",{action:"ack",notification_id:n.id});await refresh(true);}catch(e){error(e.message);b.disabled=false;}});
  box.append(b);parent.append(box);
 }
}
async function refresh(force=false){
 if(!session||busy)return;
 busy=true;
 try{
  const data=await api("GET");
  tasks=Array.isArray(data.tasks)?data.tasks:[];
  research=Array.isArray(data.research)?data.research:[];
  notes=Array.isArray(data.notifications)?data.notifications:[];
  renderStats(data.stats||{});renderSprint(data.growth_sprint||null);renderTasks();renderNotes();renderResearch();
  status("Enna đã đồng bộ • "+new Intl.DateTimeFormat("vi-VN",{hour:"2-digit",minute:"2-digit",timeZone:"Asia/Ho_Chi_Minh"}).format(new Date()),true);
  if(force)error("");
 }catch(e){status("Chưa đồng bộ: "+e.message,false);if(force)error(e.message);}
 finally{busy=false;}
}
function sessionUi(){
 const logged=!!session;
 $("sign-in").hidden=logged;$("sign-out").hidden=!logged;
 $("submit").disabled=!logged;
 $("sign-in-hero").hidden=logged;
 $("hero-auth").classList.toggle("connected",logged);
 $("research-submit").disabled=!logged;
 $("session-label").textContent=logged?"Đã xác thực chủ Enna":"Chưa đăng nhập";
 if(!logged){clearInterval(currentTimer);currentTimer=null;status("Chờ chủ dự án đăng nhập",false);$("task-list").replaceChildren(el("p","Vui lòng đăng nhập để giao việc.","muted"));return;}
 refresh(true);
 if(!currentTimer)currentTimer=setInterval(()=>{if(!document.hidden)refresh();},10000);
}
async function beginOwnerSignIn(){
 error("");
 try{
  const next=location.origin+location.pathname;
  status("Đang mở GitHub để kết nối Enna...",false);
  const {error:e}=await supabase.auth.signInWithOAuth({provider:"github",options:{redirectTo:next,scopes:"read:user"}});
  if(e)throw e;
 }catch(e){
   status("Chưa kết nối được với GitHub",false);
   error("Không mở được đăng nhập GitHub: "+(e?.message||"Không rõ lỗi")+". Kiểm tra trình duyệt có chặn chuyển hướng không.");
 }
}
$("sign-in").addEventListener("click",beginOwnerSignIn);
$("sign-in-hero").addEventListener("click",beginOwnerSignIn);
$("sign-out").addEventListener("click",async()=>{await supabase.auth.signOut();session=null;sessionUi();});
$("copy-profile-bio").addEventListener("click",async()=>{
 const text=$("profile-bio-copy").textContent.trim();
 const status=$("bio-copy-result");
 try{
  await navigator.clipboard.writeText(text);
  status.textContent="Đã sao chép bản bio. Hãy dán trên Threads và gắn liên kết trang bio; Enna chưa tự thay đổi hồ sơ.";
 }catch(e){
  status.textContent="Trình duyệt chặn sao chép. Chọn và chép trực tiếp nội dung bio trong ô phía trên.";
 }
});
$("refresh").addEventListener("click",()=>refresh(true));
$("research-form").addEventListener("submit",async e=>{
 e.preventDefault();if(!session||busy)return;
 const topic=$("research-topic").value.trim();
 if(topic.length<3||topic.length>140){error("Chủ đề nghiên cứu cần 3–140 ký tự.");return;}
 if(/(?:mật khẩu|password|api[_-]?key|token|otp|https?:)/i.test(topic)){error("Không gửi thông tin riêng tư hoặc URL qua nhiệm vụ nghiên cứu.");return;}
 const btn=$("research-submit");btn.disabled=true;btn.textContent="Đang giao worker...";error("");
 const request_key=crypto.randomUUID();
 try{
  const result=await api("POST",{action:"run_research",topic,request_key});
  if(result.dispatch_status==="uncertain_do_not_retry")error("Máy chủ không xác nhận được lệnh nghiên cứu. Không gửi lại cùng chủ đề ngay; hãy kiểm tra nhật ký.");
  else if(result.queued){$("research-topic").value="";status("Enna đã nhận nghiên cứu. Worker đang xử lý, kết quả sẽ xuất hiện trong nhật ký.",true);}
  else error("Đã tạo yêu cầu nhưng chưa xác minh worker chạy. Kiểm tra nhật ký, không gửi lại.");
  await refresh(true);
 }catch(e){error("Không bắt đầu được nghiên cứu: "+e.message);}
 finally{btn.disabled=!session;btn.textContent="Chạy nghiên cứu";}
});
$("task-form").addEventListener("submit",async event=>{
 event.preventDefault();if(!session||busy)return;
 const txt=$("prompt").value.trim(),kind=document.querySelector('input[name="kind"]:checked')?.value;
 if(!kind||txt.length<8||txt.length>1200){error("Vui lòng nhập nhiệm vụ từ 8 đến 1.200 ký tự.");return;}
 if(/(?:mật khẩu|password|api[_-]?key|bearer\s|token[:=]|otp)/i.test(txt)){error("Không gửi mật khẩu, token hay OTP.");return;}
 const btn=$("submit");btn.disabled=true;btn.textContent="Enna đang phân tích...";error("");
 const key=crypto.randomUUID();
 try{
  const result=await api("POST",{action:"task",kind,text:txt,request_key:key});
  if(result.accepted===true||result.status==="completed"){
   $("prompt").value="";
   status("Enna đã nhận nhiệm vụ; đang chờ mô hình trả lời đúng câu hỏi.",true);
  }
  await refresh(true);
 }catch(e){error("Chưa xác minh hoàn tất: "+e.message+". Kiểm tra nhật ký trước khi gửi lại để tránh tạo trùng.");await refresh(false);}
 finally{btn.disabled=!session;btn.textContent="Giao Enna xử lý →";}
});
supabase.auth.onAuthStateChange((_event, s)=>{session=s;setTimeout(sessionUi,0);});
(async()=>{try{const {data,error:e}=await supabase.auth.getSession();if(e)throw e;session=data.session;sessionUi();}catch(e){error("Không khôi phục được phiên đăng nhập: "+e.message);sessionUi();}})();
