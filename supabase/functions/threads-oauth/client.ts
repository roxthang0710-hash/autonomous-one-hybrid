export const JS = "const SB='https://gjdvdohylvsauphhkutw.supabase.co';"+
"const KEY='sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H';"+
"document.getElementById('connect').addEventListener('submit',async e=>{"+
"e.preventDefault();const button=document.getElementById('submit'),status=document.getElementById('status');button.disabled=true;"+
"status.textContent='Đang xác minh quyền chủ sở hữu...';"+
"try{"+
"const email=document.getElementById('email').value.trim();"+
"const password=document.getElementById('password').value;"+
"const login=await fetch(SB+'/auth/v1/token?grant_type=password',{method:'POST',headers:{'apikey':KEY,'Content-Type':'application/json'},body:JSON.stringify({email,password}),cache:'no-store'});"+
"document.getElementById('password').value='';"+
"if(!login.ok)throw Error('Đăng nhập không thành công. Dùng tài khoản Supabase Auth đã được cấp quyền điều hành.');"+
"const session=await login.json();"+
"const response=await fetch(SB+'/functions/v1/threads-oauth/start',{method:'POST',headers:{'Authorization':'Bearer '+session.access_token,'apikey':KEY,'Content-Type':'application/json'},body:JSON.stringify({appId:document.getElementById('appId').value.trim(),appSecret:document.getElementById('appSecret').value,enableReplies:document.getElementById('replies').checked}),cache:'no-store'});"+
"document.getElementById('appSecret').value='';"+
"const data=await response.json();"+
"if(!response.ok||typeof data.authorizeUrl!=='string')throw Error(data.error||'Không khởi tạo được kết nối Meta.');"+
"status.style.color='#176748';status.textContent='Đã xác thực. Chuyển sang Threads để cấp quyền...';"+
"window.location.assign(data.authorizeUrl);"+
"}catch(err){status.textContent=err.message||'Đã gặp lỗi khi kết nối.';button.disabled=false;}"+
"});";
