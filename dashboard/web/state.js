'use strict';
(function(root){
function derive(s,now=Date.now()) {
 if(!s)return {key:'offline',label:'Chưa kết nối dữ liệu',detail:'Đăng nhập để xem trạng thái thật của Enna.'};
 const r=s.runs?.[0], started=Date.parse(r?.started_at), age=now-started;
 if(!s.account||s.account.status!=='active'||!(Date.parse(s.account.expires_at)>now))return {key:'attention',label:'Cần kiểm tra kết nối',detail:'Thông tin kết nối Threads không còn đủ điều kiện.'};
 if(r?.status==='running' && Number.isFinite(age)&&age>=0&&age<15*60000)return {key:'working',label:'Đang xử lý lượt nghiên cứu',detail:'Có lượt chạy đang mở trong cơ sở dữ liệu. Làm mới mỗi 30 giây.'};
 if(r?.status==='running')return {key:'attention',label:'Lượt chạy cần kiểm tra',detail:'Lượt chạy mở quá lâu hoặc có thời gian không hợp lệ; chưa xác nhận còn hoạt động.'};
 if(r?.status==='failed')return {key:'attention',label:'Lượt gần nhất gặp lỗi',detail:'Xem nhật ký để xác định bước bị lỗi.'};
 if(!r||!Number.isFinite(age)||age<0||age>36*3600000)return {key:'attention',label:'Cần kiểm tra lịch chạy',detail:'Chưa thấy lượt nghiên cứu hợp lệ trong 36 giờ gần nhất.'};
 if(['empty_keyword_results','own_posts_only_possible_app_review','not_authorized','source_unavailable','no_relevant_recent_public_posts'].includes(r.discovery))return {key:'waiting',label:'Đang chờ hội thoại phù hợp',detail:'Lượt quét đã kết thúc. Chưa có bằng chứng tìm được hội thoại đủ điều kiện để phản hồi.'};
 return {key:'ready',label:'Sẵn sàng cho lượt tiếp theo',detail:'Lượt gần nhất đã kết thúc. Enna hoạt động theo lịch, không chạy liên tục.'};
}
function nextSchedule(now=new Date()){
 const times=[[2,15,'Quét chủ đề'],[7,15,'Quét chủ đề'],[12,15,'Quét chủ đề'],[2,45,'Kiểm tra nội dung'],[5,45,'Kiểm tra nội dung'],[11,45,'Kiểm tra nội dung']];
 const slots=[];for(let day=0;day<2;day++)for(const[h,m,label]of times){const d=new Date(now);d.setUTCDate(d.getUTCDate()+day);d.setUTCHours(h,m,0,0);if(d>now)slots.push({at:d.toISOString(),label});}return slots.sort((a,b)=>a.at.localeCompare(b.at)).slice(0,3);
}
const api={derive,nextSchedule};if(typeof module!=='undefined')module.exports=api;else root.EnnaState=api;
})(globalThis);
