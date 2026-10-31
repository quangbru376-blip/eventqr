/* AI-assisted: one scan -> one request; server remains responsible for uniqueness. */
(() => {
  'use strict'; const {api,$,uuid,message}=window.EventQR;
  let scanner=null, accepted=false, sending=false, scanning=false, starting=false;
  function controls(disabled){$('event-id').disabled=disabled;$('api-key').disabled=disabled;$('start-scan').disabled=disabled;$('manual-checkin').disabled=disabled;}
  function beep(success=true){
    try{
      const AudioCtx=window.AudioContext||window.webkitAudioContext;
      if(!AudioCtx)return;
      const ctx=new AudioCtx();
      if(ctx.state==='suspended'){ctx.resume();}
      const osc=ctx.createOscillator(),gain=ctx.createGain();
      osc.type=success?'sine':'triangle';
      osc.frequency.setValueAtTime(success?880:330,ctx.currentTime);
      gain.gain.setValueAtTime(0.3,ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001,ctx.currentTime+(success?0.2:0.35));
      osc.connect(gain);gain.connect(ctx.destination);
      osc.start();osc.stop(ctx.currentTime+(success?0.2:0.35));
    }catch(err){console.warn('Beep error:',err);}
  }
  async function stop(){if(scanner&&scanning){await scanner.stop();scanning=false;}if(scanner&&!scanning){scanner.clear();scanner=null;}}
  async function submit(payload,eventId,key){
    if(sending)return;sending=true;controls(true);
    try{const data=await api('/checkin',{method:'POST',key,body:{eventId,qrPayload:payload}});beep(true);message('status','Check-in thành công: '+(data.name||'Khách tham dự')+'\n'+new Date(data.checkedInAt).toLocaleString('vi-VN'),false,true);}
    catch(err){beep(false);message('status',err.message,true);}finally{sending=false;controls(false);}
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
