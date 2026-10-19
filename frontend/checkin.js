/* AI-assisted: one scan -> one request; server remains responsible for uniqueness. */
(() => {
  'use strict'; const {api,$,uuid,message}=window.EventQR;
  let scanner=null, accepted=false, sending=false, scanning=false, starting=false;
  function controls(disabled){$('event-id').disabled=disabled;$('api-key').disabled=disabled;$('start-scan').disabled=disabled;$('manual-checkin').disabled=disabled;}
  async function stop(){if(scanner&&scanning){await scanner.stop();scanning=false;}if(scanner&&!scanning){scanner.clear();scanner=null;}}
  async function submit(payload,eventId,key){
    if(sending)return;sending=true;controls(true);
    try{const data=await api('/checkin',{method:'POST',key,body:{eventId,qrPayload:payload}});message('status','Check-in thành công: '+(data.name||'Khách tham dự')+'\n'+new Date(data.checkedInAt).toLocaleString('vi-VN'),false,true);}
    catch(err){message('status',err.message,true);}finally{sending=false;controls(false);}
  }
  function inputs(){const id=$('event-id').value.trim(),key=$('api-key').value.trim();if(!uuid(id)||!key)throw new Error('Nhập UUID sự kiện và API key trước.');return [id,key];}
  $('start-scan').addEventListener('click',async()=>{
    if(starting||sending)return;starting=true;accepted=false;
    try{const [id,key]=inputs();if(!window.isSecureContext)throw new Error('Camera cần HTTPS hoặc localhost.');if(!window.Html5Qrcode)throw new Error('Thiếu file html5-qrcode.min.js trong bucket web.');
      await stop();controls(true);scanner=new Html5Qrcode('reader');
      message('status','Đang mở camera…');
      await scanner.start({facingMode:'environment'},{fps:8},async text=>{
        if(accepted||starting)return;accepted=true;
        try{await stop();await submit(text,id,key);}catch{message('status','Không dừng được camera. Tải lại trang rồi thử lại.',true);controls(false);}
      },()=>{});
      scanning=true;message('status','Đưa QR vào camera. Sau một lượt, bấm Quét vé tiếp.');
    }catch(err){message('status',err.message||'Không mở được camera; kiểm tra quyền của trình duyệt.',true);controls(false);}
    finally{starting=false;}
  });
  $('stop-scan').addEventListener('click',async()=>{if(starting||sending)return;accepted=true;try{await stop();message('status','Đã tắt camera.');}catch{message('status','Không tắt được camera; đóng trang để giải phóng camera.',true);}controls(false);});
  $('manual-checkin').addEventListener('click',async()=>{try{const [id,key]=inputs();const text=$('manual-payload').value.trim();if(!text)throw new Error('Nhập payload vé thử.');$('manual-payload').value='';await submit(text,id,key);}catch(err){message('status',err.message,true);}});
  window.addEventListener('pagehide',()=>{if(scanner&&scanning)scanner.stop().catch(()=>{});});
})();
