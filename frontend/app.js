/* AI-assisted Week 2 UI. Never store API keys in config/localStorage or log tickets. */
(() => {
  'use strict';
  const cfg = window.EVENTQR_CONFIG || {};
  const pathname = location.pathname;
  const marker = pathname.lastIndexOf('/web/');
  const inferred = marker >= 0 ? location.origin + pathname.slice(0, marker) : '';
  const base = (cfg.API_BASE_URL || inferred).replace(/\/$/, '');
  const $ = id => document.getElementById(id);
  const uuid = v => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v);
  const message = (id, text, bad = false, good = false) => {
    $(id).textContent = text; $(id).className = 'status' + (bad ? ' bad' : good ? ' good' : '');
  };
  async function api(path, {method = 'GET', body, key} = {}) {
    if (!base || !/^https?:\/\//.test(base)) throw new Error('Cần đặt API_BASE_URL trong config.js.');
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (key) headers['x-api-key'] = key;
    let res;
    try { res = await fetch(base + path, {method, headers, cache: 'no-store', referrerPolicy: 'no-referrer', body: body === undefined ? undefined : JSON.stringify(body)}); }
    catch { throw new Error('Không kết nối được API. Kiểm tra URL, CORS và kết nối mạng; chưa xác định thao tác đã thành công hay chưa.'); }
    let result;
    try { result = await res.json(); } catch { throw new Error(`API trả nội dung không hợp lệ (HTTP ${res.status}).`); }
    if (!res.ok || result.ok !== true) {
      const code = result.error?.code;
      let text = result.error?.message || `Yêu cầu thất bại (HTTP ${res.status}).`;
      if (code === 'TICKET_ALREADY_CHECKED_IN') text = 'Vé đã check-in lúc ' + (result.error.details?.checkedInAt ? new Date(result.error.details.checkedInAt).toLocaleString('vi-VN') : 'trước đó') + '.';
      if (!code && res.status === 403) text = 'API Gateway từ chối. Kiểm tra API key, URL và cấu hình route.';
      if (res.status === 429) text = 'Đang vượt giới hạn yêu cầu. Chờ rồi thao tác lại.';
      const err = new Error(text); err.code = code; throw err;
    }
    return result.data;
  }
  window.EventQR = {api, $, uuid, message};
  const query = new URLSearchParams(location.search);
  if ($('event-id') && query.get('e')) $('event-id').value = query.get('e');
  if (document.body.dataset.page === 'register') {
    $('register-form').addEventListener('submit', async e => {
      e.preventDefault(); $('submit-register').disabled = true; $('ticket-link-wrap').hidden = true;
      message('status', 'Đang đăng ký…');
      try {
        const eventId = $('event-id').value.trim(); if (!uuid(eventId)) throw new Error('Mã sự kiện phải là UUID.');
        const data = await api('/register', {method:'POST', body:{eventId, name:$('full-name').value.trim(), email:$('email').value.trim().toLowerCase()}});
        const link = new URL(data.ticketUrl, location.href);
        if (!['http:', 'https:'].includes(link.protocol)) throw new Error('API trả link vé không hợp lệ.');
        $('ticket-link').href = link.href; $('ticket-link-wrap').hidden = false;
        const texts = {PENDING_CONFIRMATION:'Cần xác nhận email SNS rồi mở vé và bấm gửi lại.', PUBLISHED:'SNS đã chấp nhận gửi email; hãy kiểm tra hộp thư.', FAILED:'Chưa gửi được email. Bạn vẫn mở được vé bằng link bên dưới.'};
        message('status', 'Đăng ký thành công. ' + (texts[data.emailDeliveryStatus] || 'Mở link để xem vé.'), false, true);
      } catch (err) { message('status', err.message, true); }
      finally { $('submit-register').disabled = false; }
    });
  }
  if (document.body.dataset.page === 'ticket') {
    const eventId = query.get('e'), ticketId = query.get('t');
    const valid = () => { if (!uuid(eventId || '') || !uuid(ticketId || '')) throw new Error('Link vé thiếu hoặc sai e/t.'); };
    async function loadTicket() {
      $('refresh-ticket').disabled = true; $('qr').hidden = true;
      message('status', 'Đang tải vé…');
      try {
        valid(); const data = await api('/ticket?' + new URLSearchParams({e:eventId,t:ticketId}));
        const src = data.qrImageDataUrl || data.qrImageUrl || '';
        if (!src.startsWith('data:image/png;base64,') && !src.startsWith('https://')) throw new Error('Ảnh QR không hợp lệ.');
        $('qr').src = src; $('qr').hidden = false;
        message('status', data.status === 'CHECKED_IN' ? 'Vé đã được check-in.' : 'Vé sẵn sàng. Đưa QR này cho ban tổ chức.', false, true);
      } catch (err) { message('status', err.message, true); }
      finally { $('refresh-ticket').disabled = false; }
    }
    $('qr').addEventListener('error', () => { $('qr').hidden=true; message('status','Ảnh chưa tải được hoặc URL đã hết hạn. Bấm tải lại ảnh QR.',true); });
    $('refresh-ticket').addEventListener('click', loadTicket);
    $('resend-ticket').addEventListener('click', async () => {
      $('resend-ticket').disabled = true; message('mail-status','Đang yêu cầu gửi lại…');
      try { valid(); await api('/resend',{method:'POST',body:{eventId,ticketId}}); message('mail-status','SNS đã chấp nhận gửi. Kiểm tra hộp thư và thư rác.',false,true); }
      catch(err) { message('mail-status',err.message,true); }
      finally { $('resend-ticket').disabled=false; }
    });
    loadTicket();
  }
  if (document.body.dataset.page === 'stats') {
    $('stats-form').addEventListener('submit',async e=>{
      e.preventDefault(); $('load-stats').disabled=true; ['total','checked','remaining'].forEach(id=>$(id).textContent='—');
      try { const id=$('event-id').value.trim();if(!uuid(id))throw new Error('Mã sự kiện phải là UUID.');
        const data=await api('/stats/'+encodeURIComponent(id),{key:$('api-key').value.trim()});
        const counts=[data.totalTickets,data.checkedInTickets,data.notCheckedInTickets];
        if(counts.some(n=>!Number.isInteger(n)||n<0)||counts[0]!==counts[1]+counts[2])throw new Error('API trả số liệu thống kê không hợp lệ.');
        ['total','checked','remaining'].forEach((id,i)=>$(id).textContent=counts[i]);message('status','Đã cập nhật lúc '+new Date().toLocaleTimeString('vi-VN'),false,true);
      }catch(err){message('status',err.message,true);}finally{$('load-stats').disabled=false;}
    });
  }
})();
