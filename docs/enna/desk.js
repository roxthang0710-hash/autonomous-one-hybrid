import {createClient} from "https://esm.sh/@supabase/supabase-js@2.57.0";
const SUPABASE="https://gjdvdohylvsauphhkutw.supabase.co";
const KEY="sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H";
const API=SUPABASE+"/functions/v1/enna-desk";
const supabase=createClient(SUPABASE,KEY,{auth:{flowType:"pkce",detectSessionInUrl:true,persistSession:true,autoRefreshToken:true}});
const $=id=>document.getElementById(id);
let session=null,tasks=[],notes=[],currentTimer=null,busy=false;
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
 $("follower-date").textContent=s.follower_count==null?"Chưa có dữ liệu xác minh.":"Đo ngày "+(s.follower_day||"không rõ")+(s.follower_stale?" · DỮ LIỆU CŨ":" · gần nhất trong hệ thống");
 $("post-count").textContent=String(s.published_threads_in_sample??"—");
 $("topic-count").textContent=String(s.native_topic_requested??"—");
 $("meme-count").textContent=String(s.original_memes_ready??"—");
 $("video-count").textContent=String(s.original_videos_ready??"—");
 $("stats-caveat").textContent=s.caveat||"";
}
function renderTasks(){
 const parent=$("task-list");parent.replaceChildren();
 if(!tasks.length){parent.append(el("p","Chưa có nhiệm vụ. Hãy giao công việc đầu tiên cho Enna.","muted"));return;}
 for(const item of tasks){
  const node=el("article",null,"task");const head=el("div",null,"task-head");
  head.append(el("strong",kindLabels[item.kind]||"Nhiệm vụ"),el("small",formatDate(item.created_at)));
  node.append(head,el("p",item.request_text));
  const badge=el("span",item.status==="completed"?"Đã trả kết quả":item.status==="failed"?"Gặp lỗi":"Đang xử lý","tag"+(item.status==="completed"?"":item.status==="failed"?" fail":" wait"));
  node.append(badge);
  const data=item.response;
  if(data){
   const details=el("details");const summary=el("summary","Xem kết quả và các chuyên trách");details.append(summary);
   const wrapper=el("div");
   const evidence=data.evidence||{};wrapper.append(el("p","Dữ liệu nguồn: "+(evidence.follower_count==null?"Chưa xác minh follower":evidence.follower_count+" follower"+(evidence.follower_stale?" (dữ liệu cũ)":""))));
   for(const role of Array.isArray(data.roles)?data.roles:[]){
    const title=el("h3",({analyst:"📈 Phân tích",strategist:"💡 Chiến lược",operator:"🛠 Vận hành"})[role.role]||role.role);wrapper.append(title);
    wrapper.append(el("p",role.summary||"Chưa có phản hồi từ chuyên trách."));
    if(Array.isArray(role.actions)){const ul=el("ul");for(const item of role.actions.slice(0,4))ul.append(el("li",item));wrapper.append(ul);}
   }
   wrapper.append(el("p","Lưu ý: đây là phân tích và đề xuất, chưa phải hành động đăng bài hay bình luận thực tế.","muted"));
   details.append(wrapper);node.append(details);
  }
  if(item.status==="failed")node.append(el("p","Lỗi: "+(item.error_code||"không rõ"),"muted"));
  parent.append(node);
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
  notes=Array.isArray(data.notifications)?data.notifications:[];
  renderStats(data.stats||{});renderTasks();renderNotes();
  status("Enna đã đồng bộ • "+new Intl.DateTimeFormat("vi-VN",{hour:"2-digit",minute:"2-digit",timeZone:"Asia/Ho_Chi_Minh"}).format(new Date()),true);
  if(force)error("");
 }catch(e){status("Chưa đồng bộ: "+e.message,false);if(force)error(e.message);}
 finally{busy=false;}
}
function sessionUi(){
 const logged=!!session;
 $("sign-in").hidden=logged;$("sign-out").hidden=!logged;
 $("submit").disabled=!logged;
 $("session-label").textContent=logged?"Đã xác thực chủ Enna":"Chưa đăng nhập";
 if(!logged){clearInterval(currentTimer);currentTimer=null;status("Chờ chủ dự án đăng nhập",false);$("task-list").replaceChildren(el("p","Vui lòng đăng nhập để giao việc.","muted"));return;}
 refresh(true);
 if(!currentTimer)currentTimer=setInterval(()=>{if(!document.hidden)refresh();},30000);
}
$("sign-in").addEventListener("click",async()=>{
 error("");try{
  const next=location.origin+location.pathname;
  const {error:e}=await supabase.auth.signInWithOAuth({provider:"github",options:{redirectTo:next,scopes:"read:user"}});
  if(e)throw e;
 }catch(e){error("Không thể mở GitHub OAuth: "+e.message);}
});
$("sign-out").addEventListener("click",async()=>{await supabase.auth.signOut();session=null;sessionUi();});
$("refresh").addEventListener("click",()=>refresh(true));
$("task-form").addEventListener("submit",async event=>{
 event.preventDefault();if(!session||busy)return;
 const txt=$("prompt").value.trim(),kind=document.querySelector('input[name="kind"]:checked')?.value;
 if(!kind||txt.length<8||txt.length>1200){error("Vui lòng nhập nhiệm vụ từ 8 đến 1.200 ký tự.");return;}
 if(/(?:mật khẩu|password|api[_-]?key|bearer\s|token[:=]|otp)/i.test(txt)){error("Không gửi mật khẩu, token hay OTP.");return;}
 const btn=$("submit");btn.disabled=true;btn.textContent="Enna đang phân tích...";error("");
 const key=crypto.randomUUID();
 try{
  const result=await api("POST",{action:"task",kind,text:txt,request_key:key});
  if(result.status==="completed")$("prompt").value="";
  await refresh(true);
 }catch(e){error("Chưa xác minh hoàn tất: "+e.message+". Kiểm tra nhật ký trước khi gửi lại để tránh tạo trùng.");await refresh(false);}
 finally{btn.disabled=!session;btn.textContent="Giao Enna xử lý →";}
});
supabase.auth.onAuthStateChange((_event, s)=>{session=s;sessionUi();});
(async()=>{try{const {data,error:e}=await supabase.auth.getSession();if(e)throw e;session=data.session;sessionUi();}catch(e){error("Không khôi phục được phiên đăng nhập: "+e.message);sessionUi();}})();
