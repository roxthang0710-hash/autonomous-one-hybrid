const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.join(__dirname,"..");
const html=fs.readFileSync(path.join(root,"docs/enna/desk.html"),"utf8");
const js=fs.readFileSync(path.join(root,"docs/enna/desk.js"),"utf8");
const home=fs.readFileSync(path.join(root,"docs/enna/index.html"),"utf8");
const main=fs.readFileSync(path.join(root,".github/workflows/enna-desk-monitor.yml"),"utf8");
const monitors=fs.readFileSync(path.join(root,"growth/enna_desk_monitor.py"),"utf8");
test("Owner desk is reachable from public Enna dashboard",()=>{
 assert.match(home,/href="desk\.html"/);
 assert.match(html,/<script type="module" src="\.\/desk\.js"/);
 assert.match(html,/id="task-form"/);
 assert.match(html,/id="sign-in-hero"/);
 assert.match(html,/KẾT NỐI ENNA BẰNG GITHUB/);
 assert.match(html,/id="research-form"/);
 assert.match(html,/id="copy-profile-bio"/);
 assert.match(html,/id="profile-bio-copy"/);
 assert.match(js,/navigator\.clipboard\.writeText/);
 assert.match(js,/bio-copy-result/);

 assert.match(html,/id="growth-sprint"/);
 assert.match(js,/renderSprint/);
 assert.match(js,/follower_source/);
 assert.match(html,/id="research-list"/);
});
test("Desk supports independent signed-in task submission",()=>{
 assert.match(js,/supabase\.auth\.signInWithOAuth/);
 assert.match(js,/sign-in-hero/);
 assert.match(js,/beginOwnerSignIn/);
 assert.match(js,/provider:"github"/);
 assert.match(js,/request_key:key/);
 assert.match(js,/action:"run_research"/);
 assert.match(js,/renderResearch\(\)/);
 assert.match(js,/functions\/v1\/enna-desk/);
 assert.doesNotMatch(js,/REQUEST_BASE64URL|issues\/new|github-actions\[bot\]/);
});
test("DOM uses safe text nodes for untrusted model and task content",()=>{
 assert.match(js,/node\.textContent=/);
 assert.doesNotMatch(js,/\.innerHTML\s*=/);
});
test("Link-in-bio clearly invites real following before any affiliate catalog",()=>{
 const page=fs.readFileSync(path.join(root,"docs/enna/links/index.html"),"utf8");
 assert.match(page,/Theo dõi Đồ Hay Đi Làm trên Threads/);
 assert.match(page,/https:\/\/www\.threads\.com\/@dohay_dilam/);
 assert.match(page,/Lấy bộ mẫu miễn phí/);
 const follow=page.indexOf("Theo dõi Đồ Hay Đi Làm trên Threads");
 const products=page.indexOf('id="approved-items"');
 assert.ok(follow>0 && products>follow);
});
test("Desk cannot contain private GitHub access or service role tokens",()=>{
 assert.doesNotMatch(js,/ghp_[a-zA-Z0-9]{15,}|sb_secret_|DB_SERVICE_KEY|SUPABASE_SERVICE_ROLE_KEY/);
 assert.doesNotMatch(html,/ghp_[a-zA-Z0-9]{15,}|sb_secret_|DB_SERVICE_KEY/);
});
test("Scheduled monitor is proactive, owner-only, bounded and deduplicated",()=>{
 assert.match(main,/schedule:/);
 assert.match(main,/python -m growth\.enna_desk_monitor/);
 assert.match(monitors,/on_conflict/);
 assert.match(monitors,/owner_id/);
 assert.match(monitors,/follower/i);
});
