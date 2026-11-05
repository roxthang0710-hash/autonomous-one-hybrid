"use strict";
// Enna Clone browser beta. The only key in this file is a PUBLIC Supabase
// publishable key (not a service role key). Tokens stay in sessionStorage.
const PROJECT="https://gjdvdohylvsauphhkutw.supabase.co";
const PUBLIC_KEY="sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H";
const API=PROJECT+"/functions/v1/enna-clone-api";
const el=id=>document.getElementById(id);
const state={session:null,user:null,data:null,section:"chat",busy:false};
const attrs={"apikey":PUBLIC_KEY,"Content-Type":"application/json"};
function status(msg, auth=false){(auth?el("authstatus"):el("status")).textContent=String(msg||"");}
const text=v=>v==null?"":String(v);
function node(tag, body, cls=""){
  const x=document.createElement(tag);
  if(cls)x.className=cls;
  if(body!=null)x.textContent=text(body);
  return x;
}
function appendMessage(role,content){
  const box=node("div",null,"bubble "+(role==="user"?"user":"assistant"));
  box.appendChild(node("div",role==="user"?"BẠN":"ENNA CLONE","meta"));
  box.appendChild(node("div",content));
  el("chatlog").appendChild(box);
  el("chatlog").scrollTop=el("chatlog").scrollHeight;
}
function fieldOptions(id,items,kind){
  const select=el(id),value=select.value;
  while(select.options.length>1)select.remove(1);
  for(const item of items){
    const option=document.createElement("option");
    option.value=item.id;option.textContent=text(item.title||item.name||"Không tên").slice(0,80);
    select.appendChild(option);
  }
  if(Array.from(select.options).some(x=>x.value===value))select.value=value;
}
function renderItems(id,items,description,deleteAction,field){
  const container=el(id);container.replaceChildren();
  if(!items?.length){container.appendChild(node("p","Chưa có dữ liệu trong mục này.","empty"));return;}
  for(const item of items){
    const box=node("div",null,"item");
    box.appendChild(node("strong",text(item.title||item.name||item.note||item.suggestion).slice(0,500)));
    if(description)box.appendChild(node("small",text(item[description]||"").slice(0,1000)));
    if(deleteAction){
      const btn=node("button",deleteAction==="suggestion_update"?"Bỏ qua":"Xóa","secondary");
      btn.type="button";btn.onclick=async()=>{
        if(!confirm("Xác nhận thao tác đối với dữ liệu của bạn?"))return;
        try{
          await api({action:deleteAction,id:item.id,...(deleteAction==="suggestion_update"?{status:"dismissed"}:{})});
          await refresh();status("Đã cập nhật.");
        }catch(e){status("Không thực hiện được: "+e.message);}
      };
      box.appendChild(btn);
    }
    container.appendChild(box);
  }
}
function feature(name){return state.data?.flags?.find(x=>x.feature===name)?.available===true;}
function render(){
 const d=state.data;if(!d)return;
 fieldOptions("conversation",d.conversations||[],"conversation");
 fieldOptions("chatagent",(d.agents||[]).map(x=>({...x,title:x.name})),"agent");
 fieldOptions("chatdoc",(d.documents||[]),"document");
 renderItems("memorylist",d.memories||[],null,"memory_delete");
 renderItems("documentlist",d.documents||[],"title","document_delete");
 renderItems("agentlist",d.agents||[],null,"agent_delete");
 renderItems("tasklist",d.tasks||[],"instruction","task_delete");
 renderItems("runlist",d.runs||[],"summary",null);
 renderItems("suggestionlist",d.suggestions||[],"status","suggestion_update");
 el("usage").textContent=(d.quota||"Giới hạn dùng")+
  " · "+(d.usage?.[0] ? ("Hôm gần nhất: "+d.usage[0].requests+" lượt"):"Chưa dùng AI");
 const gates=[["memory","private_memory"],["documents","document_workspace"],["agents","agent_builder"],
              ["tasks","schedules"],["suggestions","proactive_suggestions"]];
 for(const [tab,gate] of gates){
   const btn=document.querySelector('[data-tab="'+tab+'"]');
   btn.classList.toggle("locked",!feature(gate));
   btn.setAttribute("aria-disabled",String(!feature(gate)));
 }
 el("taskGate").hidden=feature("schedules");
 el("taskform").hidden=!feature("schedules");
 el("suggestionGate").hidden=feature("proactive_suggestions");
 for(const [tab,gate] of gates){
   const sec=document.querySelector('[data-section="'+tab+'"]');
   const form=sec?.querySelector("form");
   if(form)form.hidden=!feature(gate);
 }
}
function section(id){
 state.section=id;
 for(const b of document.querySelectorAll("[data-tab]"))
   b.setAttribute("aria-selected",String(b.dataset.tab===id));
 for(const x of document.querySelectorAll("[data-section]"))
   x.hidden=x.dataset.section!==id;
}
function persist(){if(state.session)sessionStorage.setItem("enna_clone_session_v1",JSON.stringify(state.session));
 else sessionStorage.removeItem("enna_clone_session_v1");}
async function authCall(path,payload,method="POST",authenticated=false){
 const headers={...attrs};
 if(authenticated&&state.session)headers.Authorization="Bearer "+state.session.access_token;
 const r=await fetch(PROJECT+"/auth/v1/"+path,{
   method,headers,body:payload===undefined?undefined:JSON.stringify(payload),
   cache:"no-store"
 });
 const data=await r.json().catch(()=>({}));
 if(!r.ok)throw new Error(data.msg||data.error_description||data.message||"Xác thực không thành công.");
 return data;
}
async function refreshToken(){
 if(!state.session?.refresh_token)throw new Error("Phiên đã hết hạn, vui lòng đăng nhập lại.");
 const data=await authCall("token?grant_type=refresh_token",{refresh_token:state.session.refresh_token});
 state.session={access_token:data.access_token,refresh_token:data.refresh_token};
 persist();return state.session.access_token;
}
async function api(payload,retry=true){
 if(!state.session)throw new Error("Vui lòng đăng nhập.");
 const make=async()=>{
   const r=await fetch(API,{
     method:"POST",cache:"no-store",
     headers:{...attrs,"Authorization":"Bearer "+state.session.access_token},
     body:JSON.stringify(payload)
   });
   const data=await r.json().catch(()=>({}));
   if(!r.ok){const e=new Error(data.error||"Máy chủ chưa đáp ứng.");e.code=r.status;throw e;}
   return data;
 };
 try{return await make();}
 catch(e){
   if(e.code===401&&retry){await refreshToken();return api(payload,false);}
   throw e;
 }
}
async function refresh(){
 const data=await api({action:"bootstrap"});
 state.data=data;
 render();return data;
}
async function login(){
 try {
  const data=await authCall("token?grant_type=password",{
    email:el("email").value.trim(),
    password:el("password").value
  });
  state.session={access_token:data.access_token,refresh_token:data.refresh_token};
  state.user=data.user||null;persist();
  await openWorkspace();
 }catch(e){status(e.message,true);}
}
async function signup(){
 if(el("password").value.length<8){status("Mật khẩu cần ít nhất 8 ký tự.",true);return;}
 try{
   const data=await authCall("signup",{
     email:el("email").value.trim(),
     password:el("password").value,
   });
   if(data.access_token){
     state.session={access_token:data.access_token,refresh_token:data.refresh_token};
     state.user=data.user||null;persist();await openWorkspace();
   }else{
     status("Đã gửi yêu cầu tạo tài khoản. Nếu Supabase yêu cầu xác nhận email, hãy xác nhận trước khi đăng nhập.",true);
   }
 }catch(e){status(e.message,true);}
}
async function openWorkspace(){
 el("login").hidden=true;
 try{
   await refresh();
   el("workspace").hidden=false;
   el("username").textContent=text(state.user?.email||"Tài khoản beta");
   el("logout").hidden=false;
   status("Bạn đang ở môi trường beta riêng; không có dữ liệu nào được dùng từ Enna gốc.");
 }catch(e){
   el("login").hidden=false;el("workspace").hidden=true;el("logout").hidden=false;
   status(e.code===423?"Tài khoản đã đăng nhập nhưng chưa được cấp quyền thử nghiệm. Phiên beta chưa mở công khai.":e.message,true);
 }
}
function logout(){
 state.session=null;state.user=null;state.data=null;persist();
 el("login").hidden=false;el("workspace").hidden=true;el("logout").hidden=true;
 el("username").textContent="Chưa đăng nhập";status("Đã đăng xuất.",true);
}
async function loadConversation(){
 const id=el("conversation").value;const log=el("chatlog");log.replaceChildren();
 if(!id){log.appendChild(node("p","Cuộc trò chuyện mới. Hãy gửi một nhiệm vụ thực tế.","empty"));return;}
 try{
  const d=await api({action:"conversation",id});
  for(const m of d.messages)appendMessage(m.role,m.content);
  if(!d.messages.length)log.appendChild(node("p","Chưa có tin nhắn.","empty"));
 }catch(e){status(e.message);}
}
async function send(e){
 e.preventDefault();if(state.busy)return;
 const content=el("message").value.trim();if(!content)return;
 // Preserve an uncertain request ID within this tab for an exact, safe retry.
 // Never silently create a new ID and charge the same request a second time.
 const conversationId=el("conversation").value;
 const agentId=el("chatagent").value,documentId=el("chatdoc").value;
 const pending=state.pendingChat;
 const same=!!pending&&pending.message===content&&
   pending.conversation_id===conversationId&&pending.agent_id===agentId&&
   pending.document_id===documentId;
 const requestId=same?pending.request_id:crypto.randomUUID();
 const payload={
   action:"chat",request_id:requestId,message:content,
   ...(conversationId?{conversation_id:conversationId}:{}),
   ...(agentId?{agent_id:agentId}:{}),
   ...(documentId?{document_id:documentId}:{})
 };
 state.pendingChat={request_id:requestId,message:content,
   conversation_id:conversationId,agent_id:agentId,document_id:documentId};
 state.busy=true;el("send").disabled=true;
 if(!same){
   if(el("chatlog").querySelector(".empty"))el("chatlog").replaceChildren();
   appendMessage("user",content);
 }
 try{
   const data=await api(payload);
   state.pendingChat=null;
   appendMessage("assistant",data.reply);
   el("message").value="";
   // A successful reply is still a success if refreshing the sidebar fails.
   el("conversation").value=data.conversation_id;
   status(data.notice||"Đã hoàn thành bản nháp.");
   try{
     await refresh();
     el("conversation").value=data.conversation_id;
   }catch{
     status("Đã nhận câu trả lời. Lịch sử chưa đồng bộ; có thể tải lại trang.");
   }
 }catch(err){
   status("Không xác nhận được kết quả: "+err.message+
     " Nếu kết nối bị ngắt, gửi lại nguyên văn để tra cứu cùng mã yêu cầu; không tự gọi AI lần hai.");
 }finally{state.busy=false;el("send").disabled=false;}
}
function bindForm(formId,action,fields,after){
 el(formId).addEventListener("submit",async e=>{
   e.preventDefault();
   if(state.busy)return;
   state.busy=true;
   try{
     const payload={action};
     for(const [key,id] of Object.entries(fields))payload[key]=el(id).value;
     if(after)after(payload);
     await api(payload);
     el(formId).reset();
     await refresh();
     status("Đã lưu vào không gian riêng.");
   }catch(err){status("Không thực hiện được: "+err.message);}
   finally{state.busy=false;}
 });
}
document.addEventListener("DOMContentLoaded",async()=>{
 el("authform").addEventListener("submit",e=>{e.preventDefault();void login();});
 el("signupBtn").addEventListener("click",signup);
 el("logout").addEventListener("click",logout);
 for(const b of document.querySelectorAll("[data-tab]"))b.addEventListener("click",()=>{
  if(b.classList.contains("locked")){status("Chức năng này được chuẩn bị cho bản cập nhật tiếp theo.");return;}
  section(b.dataset.tab);
 });
 el("conversation").addEventListener("change",loadConversation);
 el("newchat").addEventListener("click",()=>{el("conversation").value="";void loadConversation();});
 el("chatform").addEventListener("submit",send);
 el("docFile").addEventListener("change",async()=>{
   const file=el("docFile").files?.[0];if(!file)return;
   if(!/\.(txt|csv|tsv|md)$/i.test(file.name)||file.size>12000){
     status("Chỉ hỗ trợ tệp TXT/CSV/TSV/MD dưới 12 KB, không đọc file Excel .xlsx.");return;
   }
   try{
     const content=await file.text();
     if(content.length>12000)throw new Error("Nội dung vượt 12.000 ký tự");
     el("documentTitle").value=file.name.slice(0,120);
     el("documentContent").value=content;
     status("Đã đọc cục bộ. Hãy kiểm tra dữ liệu và bấm Lưu tài liệu để đưa vào kho riêng.");
   }catch{status("Không đọc được file văn bản này.");}
 });
 bindForm("memoryform","memory_add",{note:"memoryInput"});
 bindForm("documentform","document_add",{title:"documentTitle",content:"documentContent"});
 bindForm("agentform","agent_create",{name:"agentName",instructions:"agentInstructions"});
 bindForm("taskform","task_create",{title:"taskTitle",instruction:"taskInstruction",
  frequency:"taskFrequency",next_run_at:"taskDate"},p=>{
   p.next_run_at=new Date(p.next_run_at).toISOString();
  });
 try{
   const value=sessionStorage.getItem("enna_clone_session_v1");
   if(value){
     const s=JSON.parse(value);
     if(typeof s.access_token==="string"&&typeof s.refresh_token==="string"){
       state.session=s;
       try{const u=await authCall("user",undefined,"GET",true);state.user=u;}
       catch{try{await refreshToken();const u=await authCall("user",undefined,"GET",true);state.user=u;}catch{logout();return;}}
       await openWorkspace();
     }
   }
 }catch{logout();}
});
