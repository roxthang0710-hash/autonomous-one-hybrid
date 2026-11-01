import { createClient } from "npm:@supabase/supabase-js@2.57.0";
import { PAGE } from "./page.ts";
import { JS } from "./client.ts";

const SB = Deno.env.get("SUPABASE_URL") || "https://gjdvdohylvsauphhkutw.supabase.co";
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const ROOT = "/functions/v1/threads-oauth";
const CALLBACK = SB + ROOT + "/callback";
const API = "https://graph.threads.net";
const EXPECTED = "dohay_dilam";
const scopes = ["threads_basic", "threads_content_publish",
                "threads_manage_insights", "threads_read_replies",
                "threads_manage_replies", "threads_keyword_search"];
const service = SERVICE ? createClient(SB,SERVICE,{auth:{persistSession:false,autoRefreshToken:false}}) : null;

function headers(type="text/html; charset=utf-8") {
 return {"Content-Type":type,"Cache-Control":"no-store, max-age=0",
 "Referrer-Policy":"no-referrer","X-Content-Type-Options":"nosniff",
 "X-Frame-Options":"DENY","Strict-Transport-Security":"max-age=31536000",
 "Content-Security-Policy":"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' "+SB+"; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"};
}
const json = (data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:headers("application/json; charset=utf-8")});
const html = (data:string,status=200)=>new Response(data,{status,headers:headers()});
const endPage = (success:boolean,detail:string,status=200)=>html(
 "<!doctype html><html lang='vi'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Kết nối Threads</title>"+
 "<style>body{font:17px system-ui;background:#eef4f0;color:#183528}main{max-width:630px;background:white;padding:40px;margin:7vh auto;border-radius:15px}a{color:#176943}</style>"+
 "<main><h1>"+(success?"Đã kết nối Threads thành công":"Chưa kết nối được Threads")+"</h1><p>"+detail+"</p>"+
 "<p><a href='"+ROOT+"'>Trở lại trang kết nối</a></p></main></html>",status);
async function digest(value:string) {
 const b=new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(value)));
 return [...b].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function owner(req:Request) {
 if (!service) return null;
 const jwt=(req.headers.get("Authorization")||"").replace(/^Bearer /,"");
 if(jwt.length<30) return null;
 const {data,error}=await service.auth.getUser(jwt);
 if(error||!data.user) return null;
 const {data:role,error:e}=await service.from("agent_reviewers").select("user_id").eq("user_id",data.user.id).limit(1);
 if(e||!role?.length) return null;
 return data.user.id;
}
async function meta(url:string,options:RequestInit={}) {
 const r=await fetch(url,{...options,cache:"no-store",signal:AbortSignal.timeout(20000)});
 if(!r.ok) throw Error("Meta HTTP "+r.status);
 const data=await r.json();
 if(!data||typeof data!=="object") throw Error("Malformed Meta response");
 return data as Record<string,unknown>;
}
async function handler(req:Request):Promise<Response> {
 const url=new URL(req.url),path=url.pathname;
 if(req.method==="GET"&&(path===ROOT||path===ROOT+"/"))return html(PAGE);
 if(req.method==="GET"&&path===ROOT+"/client.js")return new Response(JS,{headers:headers("application/javascript; charset=utf-8")});
 if(req.method==="POST"&&path===ROOT+"/start"){
   const userId=await owner(req);
   if(!userId)return json({error:"Chỉ tài khoản chủ sở hữu Autonomous One mới được phép kết nối."},401);
   if(!service)return json({error:"Thiếu cấu hình máy chủ."},503);
   let body:Record<string,unknown>;
   try{body=await req.json()}catch{return json({error:"Dữ liệu không hợp lệ."},400)}
   const appId=String(body.appId||"");
   const appSecret=String(body.appSecret||"");
   if(!/^[0-9]{8,30}$/.test(appId)||appSecret.length<16||appSecret.length>400)
      return json({error:"Threads App ID hoặc App Secret không hợp lệ."},400);
   const state=[...crypto.getRandomValues(new Uint8Array(32))]
         .map(x=>x.toString(16).padStart(2,"0")).join("");
   const {error}=await service.rpc("threads_begin_oauth",{
     p_owner_user_id:userId,p_state_hash:await digest(state),
     p_app_id:appId,p_app_secret:appSecret,p_redirect_uri:CALLBACK,
     p_enable_replies:body.enableReplies===true,
   });
   if(error)return json({error:"Không lưu được phiên cấp quyền. Kiểm tra App ID và Meta settings."},500);
   const params=new URLSearchParams({client_id:appId,redirect_uri:CALLBACK,
      scope:scopes.join(","),response_type:"code",state});
   return json({authorizeUrl:"https://threads.net/oauth/authorize?"+params.toString()});
 }
 if(req.method==="GET"&&path===ROOT+"/callback"){
   if(url.searchParams.has("error"))return endPage(false,"Bạn đã hủy hoặc từ chối cấp quyền Meta.",400);
   const code=url.searchParams.get("code")||"";
   const state=url.searchParams.get("state")||"";
   if(!/^[a-f0-9]{64}$/.test(state)||code.length<10||code.length>3000||!service)
      return endPage(false,"Thiếu mã, phiên không hợp lệ hoặc máy chủ chưa cấu hình.",400);
   const {data,error}=await service.rpc("threads_claim_oauth",{p_state_hash:await digest(state)});
   const grant=data?.[0];
   if(error||!grant)return endPage(false,"Phiên đã hết hạn hoặc được sử dụng. Hãy bắt đầu lại.",400);
   try{
     const short=await meta(API+"/oauth/access_token",{
       method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},
       body:new URLSearchParams({client_id:grant.app_id,client_secret:grant.app_secret,
         grant_type:"authorization_code",code,redirect_uri:grant.redirect_uri}),
     });
     if(typeof short.access_token!=="string"||short.access_token.length<40)
       throw Error("Missing short Meta token");
     const long=await meta(API+"/access_token?"+new URLSearchParams({
       grant_type:"th_exchange_token",client_secret:grant.app_secret}),{
       headers:{"Authorization":"Bearer "+short.access_token},
     });
     if(typeof long.access_token!=="string"||typeof long.expires_in!=="number")
       throw Error("Missing long Meta token");
     const seconds=Number(long.expires_in);
     if(seconds<86400||seconds>70*86400)throw Error("Bad Meta token lifetime");
     const profile=await meta(API+"/v1.0/me?fields=id,username",{
       headers:{"Authorization":"Bearer "+long.access_token},
     });
     if(String(profile.username||"").toLowerCase()!==EXPECTED||!profile.id)
       return endPage(false,"Meta đang đăng nhập tài khoản khác @dohay_dilam. Không có quyền nào được kích hoạt.",422);
     const {error:e}=await service.rpc("threads_finish_oauth",{
       p_owner_user_id:grant.owner_user_id,p_app_id:grant.app_id,
       p_app_secret_ref:grant.app_secret_ref,p_access_token:long.access_token,
       p_username:EXPECTED,p_platform_user_id:String(profile.id),
       p_expires_at:new Date(Date.now()+seconds*1000).toISOString(),
       p_enable_replies:grant.enable_replies===true,
     });
     if(e)throw Error("Vault save rejected");
     return endPage(true,"Đã xác nhận @dohay_dilam và lưu token an toàn trong Supabase Vault. Lịch đăng trực tiếp của Agent sẽ chỉ bắt đầu sau giai đoạn Metricool.");
   }catch{
     // Never print or reflect authorization code, token or app secret.
     return endPage(false,"Meta chưa xác thực được hoặc quyền ứng dụng chưa đầy đủ. Kiểm tra Threads App ID, Secret, quyền Tester và Redirect URL rồi thử lại.",422);
   }
 }
 return json({error:"Not found"},404);
}
Deno.serve(req=>handler(req).catch(()=>json({error:"Có lỗi máy chủ. Vui lòng thử lại."},500)));
