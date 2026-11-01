(function(root){
'use strict';
const headers=['ngay','don_vi','kenh','chu_de','noi_dung','keu_goi','trang_thai','het_han_uu_dai'];
function parseCSV(text){
 if(new TextEncoder().encode(text).length>2000000)throw Error('Giới hạn 2 MB mỗi lần kiểm tra.');
 text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],cell='',quoted=false,closed=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=c;continue;}
 if(closed&&c!==','&&c!=='\r'&&c!=='\n')throw Error('CSV không hợp lệ: ký tự sau dấu ngoặc kép.');
 if(c==='"'){if(cell)throw Error('CSV không hợp lệ: dấu ngoặc kép trong ô chưa được bao.');quoted=true;}
 else if(c===','){row.push(cell);cell='';closed=false;}
 else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()))rows.push(row);row=[];cell='';closed=false;}
 else cell+=c;
 }
 if(quoted)throw Error('CSV thiếu dấu ngoặc kép đóng.');row.push(cell);if(row.some(x=>x.trim()))rows.push(row);
 if(rows.length<2)throw Error('Cần một hàng tiêu đề và ít nhất một dòng nội dung.');
 if(rows.length>1001)throw Error('Giới hạn 1.000 bài mỗi lần kiểm tra.');
 const keys=rows.shift().map(s=>s.trim().toLowerCase());if(new Set(keys).size!==keys.length)throw Error('Tên cột bị trùng.');
 for(const key of headers.slice(0,7))if(!keys.includes(key))throw Error('Thiếu cột: '+key);
 return rows.map((r,i)=>{if(r.length!==keys.length)throw Error('Số ô không khớp ở dòng dữ liệu '+(i+1)+'.');return Object.fromEntries(keys.map((k,j)=>[k,r[j].trim()]));});
}
function date(value){let m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(value);let y,mo,d;if(m){[,y,mo,d]=m;}else{m=/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(value);if(!m)return null;[,d,mo,y]=m;}y=+y;mo=+mo;d=+d;if(y<1900||y>2100)return null;const n=new Date(Date.UTC(y,mo-1,d));if(n.getUTCFullYear()!==y||n.getUTCMonth()!==mo-1||n.getUTCDate()!==d)return null;return n.toISOString().slice(0,10);}
const norm=s=>String(s||'').normalize('NFC').toLowerCase().replace(/\s+/g,' ').trim();
function check(rows){const findings=[],seen=new Map();const add=(i,level,code,message)=>findings.push({dong:i+1,don_vi:rows[i].don_vi,chu_de:rows[i].chu_de,muc_do:level,ma:code,can_sua:message});
 rows.forEach((r,i)=>{const when=date(r.ngay);if(!when)add(i,'Lỗi','DATE','Ngày không hợp lệ. Dùng YYYY-MM-DD hoặc DD/MM/YYYY.');
 for(const [key,label] of [['don_vi','đơn vị'],['kenh','kênh'],['chu_de','chủ đề'],['noi_dung','nội dung']])if(!r[key])add(i,'Lỗi','MISSING_'+key,'Thiếu '+label+'.');
 if(!r.keu_goi)add(i,'Cần xem','CTA','Chưa có lời kêu gọi hành động; xác nhận có cần cho bài này không.');
 if(norm(r.trang_thai)!=='da_duyet'&&norm(r.trang_thai)!=='đã duyệt')add(i,'Cần xem','APPROVAL','Chưa ghi nhận trạng thái đã duyệt.');
 if(r.het_han_uu_dai){const end=date(r.het_han_uu_dai);if(!end)add(i,'Lỗi','EXPIRY_DATE','Hạn ưu đãi không phải ngày hợp lệ.');else if(when&&when>end)add(i,'Lỗi','EXPIRED','Ngày đăng nằm sau hạn ưu đãi.');}
 if(when&&r.don_vi&&r.kenh&&r.noi_dung){const key=[when,norm(r.don_vi),norm(r.kenh),norm(r.noi_dung)].join('\u0000');if(seen.has(key))add(i,'Lỗi','DUPLICATE','Trùng ngày, đơn vị, kênh và nội dung với dòng '+(seen.get(key)+1)+'.');else seen.set(key,i);}
 });return {rows:rows.length,errors:findings.filter(f=>f.muc_do==='Lỗi').length,warnings:findings.filter(f=>f.muc_do==='Cần xem').length,affected:new Set(findings.map(f=>f.dong)).size,findings};}
function csv(rows,keys){const safe=v=>{let s=String(v??'');if(/^[\s]*[=+@-]/.test(s)||/^[\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};return '\uFEFF'+[keys,...rows.map(r=>keys.map(k=>r[k]))].map(r=>r.map(safe).join(',')).join('\r\n');}
const api={parseCSV,date,check,csv,headers};if(typeof module!=='undefined')module.exports=api;else root.CalendarCheck=api;
})(typeof globalThis!=='undefined'?globalThis:this);
