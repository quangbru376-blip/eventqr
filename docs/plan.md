# KẾ HOẠCH TRIỂN KHAI 4 TUẦN (MASTER PLAN) — EVENTQR

> **Tiếp nhận 19/10/2026:** đã sang tuần 3, đang hoàn tất phạm vi tuần 2. Mã từ kit A/B bên ngoài đã ghép vào repo local; đây là kết quả chuẩn bị mã/kiểm thử cục bộ. Checklist AWS lịch sử bên dưới chỉ được đánh hoàn thành khi có kết quả thật. Tiếp tục Lambda web + API Gateway theo handoff; tổng 8 Lambda nếu tính cả web. Xem [báo cáo ghép mã](WEEK2-STATUS.md).

## Tiến độ mã và kiểm chứng ngày 19/10

- [x] Kết hợp source phần A/B, thống nhất ticket_mail, giữ HMAC; build lại 8 ZIP local.
- [x] Kiểm thử local 38/38 unittest, 7/7 HMAC; kiểm tra cú pháp JS và package/source.
- [x] Đồng bộ worklog đã xác nhận: tuần 2 A 8,25h/B 10,50h, ngày 19/10 tính tuần 3 A 1,25h/B 1,00h.
- [ ] Kiểm kê triển khai AWS, xác nhận API key/usage plan và retention 7 ngày trên tài khoản chính.
- [ ] Có bằng chứng luồng create-event → register → QR/email → checkin 200/409 → stats, camera điện thoại và presigned qua phiên lab.

Các checklist AWS lịch sử chỉ được đánh hoàn thành theo kết quả thật; source/ZIP và mock test là kết quả local. Tổng giờ lấy từ [worklog tuần 2](../worklog/week2/worklog_markdown.md) và [tuần 3](../worklog/week3/worklog_markdown.md), không cộng lặp 4 mục ngày 19/10.

> **Đồ án:** Hệ thống quản lý sự kiện và check-in bằng QR code (EventQR)
> **Môn:** Cloud Computing (Đợt 1, 2026–2027) — Nhóm: Domain Apps — GVHD: TS. Huỳnh Xuân Phụng
> **Nhóm sinh viên thực hiện:**
> - **Đặng Duy Quang (MSSV: 24110307)** — Vai trò **A** (Lead, Vé & Dữ liệu, Tài khoản AWS chính)
> - **Trương Hoàng Long (MSSV: 24110273)** — Vai trò **B** (Gửi vé qua SNS, Sinh QR ra S3, Giao diện Web, Giám sát CloudWatch)
>
> **Môi trường:** AWS Learner Lab (`us-east-1`, `LabRole`, ≤ 50 USD/tài khoản). Hai tài khoản Learner Lab **không liên kết được với nhau** (xem mục "Cách ghép hai tài khoản").
> **Quy định thời gian:** mỗi sinh viên ≥ 8 giờ/tuần; nộp worklog và báo cáo hằng tuần; báo cáo nộp **không đính kèm file**, nội dung và link nằm trên GitHub.

---

## BẢNG THEO DÕI TIẾN ĐỘ TỔNG THỂ

*Cập nhật vào cuối mỗi tuần hoặc khi có điều chỉnh quan trọng. Số giờ lấy từ worklog; nếu lệch thì sửa worklog trước.*

| Tuần | Mốc thời gian | Trọng tâm | Trạng thái | Giờ thực tế A (Quang) | Giờ thực tế B (Long) | Báo cáo & minh chứng |
| :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **Tuần 1** | 05/10 – 11/10 | Nền tảng, kiến trúc, bài thử rủi ro | **Xong, còn 3 tồn đọng** (xem mục Tuần 1) | 9.75 h | 9.2 h | Báo cáo T1 bị từ chối lần đầu, **đang nộp lại** (body + link GitHub); số ảnh minh chứng: kiểm đếm lại |
| **Tuần 2** | 12/10 – 18/10 | 7 Lambda, 4 trang web, ghép hai tài khoản, thử CloudFront và camera điện thoại | **Ngày/giờ đã được người dùng xác nhận; AWS còn chờ minh chứng** | 8.25 h *(A01–A10)* | 10.50 h *(B01–B12)* | [Worklog tuần 2](../worklog/week2/worklog_markdown.md); source local; AWS cần đối chiếu |
| **Tuần 3** | 19/10 – 25/10 | Triển khai tài khoản chính, HTTPS, bảo mật, giám sát; đóng băng 25/10 | Đã bắt đầu; có giờ xác nhận ngày 19/10 | Đã ghi 1.25 h; dự kiến cả tuần 11.5 h | Đã ghi 1.00 h; dự kiến cả tuần 12.0 h | [Worklog tuần 3](../worklog/week3/worklog_markdown.md); A11–A12/B13–B14 tính tuần này |
| **Tuần 4** | 26/10 – 01/11 | Nghiệm thu 21 ca, video demo, báo cáo, dọn dẹp | Chưa bắt đầu | Dự kiến 11.0 h | Dự kiến 11.0 h | Video, báo cáo cuối, bảng nghiệm thu |
| **TỔNG** | 4 tuần | | | Dự kiến ~44 h | Dự kiến ~44 h | Chuẩn ≥ 32 h/người |

---

## CÁCH GHÉP HAI TÀI KHOẢN (quyết định cần cho Tuần 2–3)

Vấn đề: `register` gọi đồng bộ `generate-qr`, nhưng Lambda của A và B nằm ở hai tài khoản khác nhau; không có cách gọi chéo, không chia sẻ credentials.

Cách làm đã chọn:

1. **Mọi mã nằm trong Git** (`lambdas/<tên-hàm>/`). Mỗi người viết và test trong tài khoản của mình.
2. **Từ Thứ 4 (14/10), Quang deploy mã của Long** (`generate-qr`, rồi `get-ticket`, `resend`) vào tài khoản của Quang để ghép với `register`, `checkin`, `stats`. Hệ thống đầu-cuối chạy trong **một** tài khoản (của Quang) ngay từ Tuần 2.
3. Long cần một **secret HMAC thử riêng** trong tài khoản của mình để test `generate-qr` (khóa khác khóa của Quang cũng được; không đưa khóa thật vào Git/chat).
4. Việc cần bấm trên console tài khoản Quang (bucket, SNS, CloudFront): **Quang bấm, Long hướng dẫn qua chia sẻ màn hình**. Không chia sẻ credentials.
5. **Triển khai lặp lại được:** thử dựng một template SAM/CloudFormation tối thiểu (1 bucket + 1 Lambda) trong Learner Lab vào Thứ 6 tuần 2. *Chưa kiểm chứng CloudFormation chạy được với `LabRole`.* Nếu chạy được thì dùng cho Tuần 3; nếu không thì dùng quy trình thủ công có checklist.
6. Frontend dùng `config.js` trỏ về API Gateway của Quang. Khi cần cho Long thử, dùng **API key tạm** (tạo riêng cho tuần 2, gửi riêng tư, xóa sau tuần 2). Không đưa key vào Git, ảnh chụp, báo cáo.

---

## LỊCH TRÌNH TỔNG QUAN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TUẦN 1 (05–11/10): Nền tảng & bài thử rủi ro  [XONG, còn 3 tồn đọng]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ TUẦN 2 (12–18/10): 7 Lambda + 4 trang web, ghép lên tài khoản của Quang     │
│  + thử CloudFront + thử camera điện thoại + thử CloudFormation tối thiểu    │
├─────────────────────────────────────────────────────────────────────────────┤
│ TUẦN 3 (19–25/10): Tài khoản chính, HTTPS, API key, throttle, CloudWatch    │
│  -> ĐÓNG BĂNG 25/10                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ TUẦN 4 (26/10–01/11): Nghiệm thu 21 ca, video, báo cáo, dọn dẹp             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### TUẦN 1 (05/10 – 11/10): NỀN TẢNG, THIẾT KẾ & BÀI THỬ RỦI RO
*Trạng thái: hoàn thành phần lớn. Báo cáo Tuần 1 lần đầu bị GVHD từ chối (nộp PDF đính kèm, body chỉ có link repo gốc); đang nộp lại theo quy định.*

**Tồn đọng chuyển sang Tuần 2:** (1) presigned URL 6 giờ chưa hoàn thành; (2) retention 7 ngày cần xác nhận đã lưu; (3) camera mới thử trên máy tính, chưa thử trên điện thoại.

- **Thành viên A (Đặng Duy Quang) — 9.75 giờ:**
  - [x] Thiết kế kiến trúc v1 (`docs/evidence/week1/architecture.md`) (2.0h)
  - [x] Tạo repo GitHub `eventqr` (hiện đang **public**), thêm thành viên còn lại (0.25h)
  - [x] Tạo 2 bảng DynamoDB `eventqr-events`, `eventqr-tickets` (On-demand) (0.75h)
  - [x] Tạo secret `eventqr-hmac-key` trong Secrets Manager (0.75h)
  - [x] Lambda `eventqr-test-secret` (LabRole, biến môi trường `SECRET_NAME`) (0.5h)
  - [x] Lambda `eventqr-test-checkin` (cập nhật có điều kiện `ISSUED -> CHECKED_IN`, `TICKETS_TABLE`) (0.5h)
  - [x] Thử check-in: lần 1 trả 200, lần 2 trả 409 (0.75h)
  - [x] Thảo luận thống nhất đặc tả register, checkin, stats (1.0h)
  - [x] Mô-đun ký/xác minh HMAC, test cục bộ 7/7 PASS (`lambdas/common/`) (0.25h)
  - [x] Dự thảo đặc tả API cùng AI (1.0h)
  - [x] Đẩy mã lên Git (0.5h) và viết báo cáo Tuần 1 (1.5h)

- **Thành viên B (Trương Hoàng Long) — 9.2 giờ** *(bảng cũ ghi 8.2 h do tính nhầm dòng cuối)*:
  - [x] Vẽ sơ đồ kiến trúc (1.5h)
  - [x] Bucket S3 `eventqr-qr` và `eventqr-web`: private, kiểm tra Block public access, gắn tag Project/Owner (1.0h)
  - [x] SNS topic `eventqr-ticket-delivery`, filter policy theo email, gửi thử hai email thành công (1.1h)
  - [x] Lambda `eventqr-web` đọc HTML từ S3 private; tích hợp API Gateway phục vụ HTTPS; camera chạy trên **máy tính** (1.5h)
  - [x] Kiểm tra log `WEB_PAGE_SERVED`, gắn tag CloudWatch; chọn retention 7 ngày (1.0h) — *cần xác nhận đã lưu*
  - [ ] **Presigned URL S3 hạn 6 giờ, lưu kết quả HTTP 200 (1.0h) — ĐANG LÀM.** Chỉ đánh `[x]` khi có ảnh kết quả trong `docs/evidence/week1/Long/`
  - [x] Được thêm vào repo (0.1h), họp đặc tả (1.0h), viết báo cáo Tuần 1 (1.0h) = 2.1h

---

### TUẦN 2 (12/10 – 18/10): CHỨC NĂNG LÕI, GHÉP TÀI KHOẢN & KIỂM CHỨNG RỦI RO
*Mục tiêu: 7 Lambda chạy được và ghép đầu-cuối trên tài khoản của Quang; 4 trang web; có kết quả CloudFront, camera điện thoại, CloudFormation.*

| Ngày | A (Quang) — Vé & Dữ liệu | Giờ | B (Long) — Gửi vé & Web UI | Giờ |
| :--- | :--- | :---: | :--- | :---: |
| **T2 12/10** | [x] Chốt đặc tả API v0.2; đưa [`docs/api.md`](api.md) vào repo; chuẩn bị helper DynamoDB. | 1.5 | [x] Nghiên cứu thư viện sinh QR (segno/qrcode); thống nhất hợp đồng `register` ↔ `generate-qr`. | 1.5 |
| **T3 13/10** | [ ] Lambda `eventqr-create-event`: validate, sinh UUID, ghi `eventqr-events`; test payload. | 2.0 | [ ] Lambda `eventqr-generate-qr`: nhận `{eventId, ticketId}`, đọc secret, ký HMAC, sinh PNG, lưu S3 `eventqr-qr`. Tạo **secret thử** trong tài khoản của Long. | 2.0 |
| **T4 14/10** | [ ] Mô-đun `ticket_mail.py`; bắt đầu `eventqr-register`; **deploy `generate-qr` (từ Git) vào tài khoản Quang** để `register` gọi được. | 2.0 | [ ] **Hoàn tất bài thử presigned URL (chốt dùng `presigned` hay `inline`)**; `register.html` và `ticket.html`. | 2.0 |
| **T5 15/10** | [ ] Hoàn thiện `register` (`attribute_not_exists`, SNS); Lambda `eventqr-checkin`. | 2.0 | [ ] Lambda `eventqr-get-ticket` theo chế độ đã chốt; Lambda `eventqr-resend`. Xác nhận retention 7 ngày. | 2.0 |
| **T6 16/10** | [ ] Lambda `eventqr-stats`; deploy `get-ticket`, `resend` (từ Git); 6 route API Gateway + CORS ở tài khoản Quang. | 2.0 | [ ] `checkin.html` (quét QR) và `stats.html`; **thử CloudFront + OAC** (tạo distribution tối thiểu, ghi lại thành công/thất bại); thử SAM/CloudFormation tối thiểu cùng Quang. | 2.0 |
| **T7 17/10** | [ ] Test 6 route bằng Postman/curl; chụp response và CloudWatch log. Tạo API key tạm cho Long. | 1.0 | [ ] **Thử camera trên điện thoại thật** (qua HTTPS Lambda web hiện có) quét QR do hệ thống của Quang sinh; chụp ảnh. | 1.0 |
| **CN 18/10** | [ ] **Giải thích chéo 45 phút** (DynamoDB & HMAC). Worklog, báo cáo Tuần 2. Xóa API key tạm. | 1.5 | [ ] **Giải thích chéo** (S3 QR & Frontend). Push code. Worklog, báo cáo Tuần 2. | 1.5 |
| **TỔNG** | | **12.0 h** | | **12.0 h** |

**Cổng kiểm tra cuối Tuần 2:** `POST /register` → có QR + link vé → `POST /checkin` trả 200 rồi 409, chạy trên **một** tài khoản. Nếu chưa đạt, Tuần 3 ưu tiên sửa việc này trước mọi thứ khác.

---

### TUẦN 3 (19/10 – 25/10): TÀI KHOẢN CHÍNH, BẢO MẬT & GIÁM SÁT
*Mục tiêu: hệ thống chạy thông suốt trên tài khoản chính của Quang; đóng băng chức năng 25/10.*

| Ngày | A (Quang) | Giờ | B (Long) | Giờ |
| :--- | :--- | :---: | :--- | :---: |
| **T2 19/10** | [ ] Dựng phần còn thiếu trên tài khoản chính theo checklist/template: bảng, secret HMAC chính, 7 Lambda (từ Git). | 2.0 | [ ] **Hướng dẫn qua chia sẻ màn hình** để Quang dựng 2 bucket, SNS topic + subscription; chuẩn bị `config.js`, template/checklist. | 1.5 |
| **T3 20/10** | [ ] API Gateway `eventqr-api` (stage `v1`): CORS mọi route, ánh xạ 6 Lambda. | 2.0 | [ ] Triển khai web: **CloudFront nếu Tuần 2 thử được, ngược lại Lambda web + API Gateway** (ghi lý do vào kiến trúc); `config.js` trỏ về API chính. | 2.0 |
| **T4 21/10** | [ ] API key `eventqr-organizer-key`, usage plan (50 req/s, burst 100), gắn bảo vệ route ban tổ chức. | 1.5 | [ ] Thử camera điện thoại thật qua HTTPS của hệ thống chính, có header `x-api-key`. | 2.0 |
| **T5 22/10** | [ ] Kiểm thử đầu-cuối: tạo sự kiện → đăng ký → SNS → check-in bằng điện thoại. | 1.5 | [ ] CloudWatch dashboard `eventqr-dashboard`; 2 alarm lỗi. | 2.0 |
| **T6 23/10** | [ ] Kiểm tra giới hạn `POST /register` công khai (throttle, spam email); thử reserved concurrency *nếu Learner Lab cho phép*. | 1.5 | [ ] Hoàn thiện template SAM/CloudFormation nếu Tuần 2 chạy được; nếu không, viết checklist triển khai thủ công. | 1.5 |
| **T7 24/10** | [ ] Gateway Responses: CORS cho 403 (sai API key) và 429 (throttle). | 1.5 | [ ] Hoàn thiện UI: hiển thị thời gian check-in, âm báo thành công/thất bại. | 1.5 |
| **CN 25/10** | [ ] **Giải thích chéo 45 phút.** Ảnh minh chứng tài khoản chính. Báo cáo Tuần 3. **ĐÓNG BĂNG.** | 1.5 | [ ] **Giải thích chéo.** Tài liệu vận hành. Báo cáo Tuần 3. **ĐÓNG BĂNG.** | 1.5 |
| **TỔNG** | | **11.5 h** | | **12.0 h** |

---

### TUẦN 4 (26/10 – 01/11): NGHIỆM THU, VIDEO, BÁO CÁO & DỌN DẸP
*Sau đóng băng chỉ sửa lỗi, không thêm chức năng. Hỏi thầy hạn nộp chính xác và hình thức demo (trực tiếp hay video) trước ngày 26/10.*

| Ngày | A (Quang) | Giờ | B (Long) | Giờ |
| :--- | :--- | :---: | :--- | :---: |
| **T2 26/10** | [ ] Nghiệm thu backend: vé hợp lệ, quét trùng 2 máy, sửa chữ ký, sai eventId, vé không tồn tại. | 2.0 | [ ] Nghiệm thu frontend & SNS: email mới, email chưa confirm, resend, camera góc nghiêng. | 2.0 |
| **T3 27/10** | [ ] Điền bảng 21 ca nghiệm thu; **sửa lỗi phát hiện** (thời gian đệm). | 1.5 | [ ] Kịch bản video demo (≤ 10 phút) theo phân đoạn; hỗ trợ sửa lỗi frontend. | 1.5 |
| **T4 28/10** | [ ] Dữ liệu mẫu sạch: 1 sự kiện, 5–10 email thật; tổng hợp phần AI hỗ trợ. | 1.5 | [ ] Tổng duyệt kịch bản cùng Quang; test micro, màn hình, camera điện thoại. | 1.5 |
| **T5 29/10** | [ ] **Quay video demo** (màn hình + điện thoại). Soạn báo cáo cuối kỳ. | 2.0 | [ ] **Hậu kỳ video** (≤ 10 phút), xuất link dự phòng. | 2.0 |
| **T6 30/10** | [ ] Cost Explorer/Billing, phân tích chi phí so với 50 USD; hoàn thiện báo cáo cuối. | 1.5 | [ ] Hoàn thiện phần báo cáo của Long; bảng phân bổ công việc và tự đánh giá. | 1.5 |
| **T7 31/10** | [ ] Rà soát hồ sơ: báo cáo, link video, bảng nghiệm thu, worklog 4 tuần. | 1.5 | [ ] Kiểm tra chéo link GitHub, repo không lộ secret/token. | 1.5 |
| **CN 01/11** | [ ] **Dọn dẹp tài nguyên chỉ sau khi đã nộp đủ và có đủ ảnh minh chứng.** Nếu hạn nộp trùng 01/11, dọn sau giờ nộp. Chụp ảnh console trống. | 1.0 | [ ] Dọn tài khoản B, chụp ảnh console trống; hoàn tất worklog Tuần 4. | 1.0 |
| **TỔNG** | | **11.0 h** | | **11.0 h** |

---

## RỦI RO VÀ ĐIỂM CHƯA KIỂM CHỨNG

| Điểm | Cách kiểm | Hạn | Nếu thất bại |
| :--- | :--- | :---: | :--- |
| Presigned URL sống đúng hạn | Bài thử của Long | 14/10 | Dùng chế độ `inline` |
| CloudFront + OAC trong Learner Lab | Thử tối thiểu | 16/10 | Giữ Lambda web + API Gateway, ghi vào kiến trúc |
| Camera trên điện thoại qua HTTPS | Thử với QR thật | 17/10 | Sửa thư viện quét/giao diện trong Tuần 3 |
| SAM/CloudFormation với `LabRole` | Template tối thiểu | 16/10 | Triển khai thủ công theo checklist |
| LabRole đọc Secrets Manager | Đã thử ở Tuần 1 (Lambda test-secret); xác nhận lại trong `generate-qr` | 14/10 | — |
| Reserved concurrency | Thử nếu còn thời gian | 23/10 | Bỏ, dựa vào throttle |
| Phát hiện subscription SNS đang chờ xác nhận | Thử với email thật | 15/10 | Luôn hiển thị link vé trên web |

## QUY TRÌNH CẬP NHẬT HÀNG TUẦN

1. **Thời điểm:** tối Chủ nhật, sau buổi giải thích chéo.
2. **Bước 1:** đổi `[ ]` thành `[x]` cho việc đã xong; việc **chưa xong thì giữ `[ ]` và ghi lý do**.
3. **Bước 2:** cập nhật số giờ từ **worklog** (nguồn chuẩn); cộng lại để số trong plan và worklog khớp nhau.
4. **Bước 3:** cập nhật trạng thái tuần; không ghi "100%" nếu còn tồn đọng.
5. **Bước 4:** nếu có thay đổi kỹ thuật hoặc yêu cầu từ GVHD, sửa đầu việc tuần tới ngay trong file này.
6. **Bước 5:** đồng bộ trạng thái mã, kiểm thử và minh chứng vào [trạng thái tuần 2](WEEK2-STATUS.md).

## NHẬT KÝ THAY ĐỔI SO VỚI BẢN TRƯỚC

- Tuần 1: sửa giờ Long 8.2 → 9.2 h; presigned URL đổi về chưa xong; ghi báo cáo bị từ chối và đang nộp lại; sửa "repo private" thành public; bỏ "tiến độ 30%".
- Thêm mục "Cách ghép hai tài khoản" và ghép đầu-cuối trên tài khoản Quang ngay trong Tuần 2.
- Dời thử CloudFront, camera điện thoại, CloudFormation về Tuần 2; chốt presigned URL trước khi viết `get-ticket`.
- Tuần 3: Long hướng dẫn bằng chia sẻ màn hình thay vì tự dựng trong tài khoản Quang; thay mục "retry vô tận" bằng kiểm tra spam `POST /register`.
- Tuần 4: thêm thời gian sửa lỗi; dọn dẹp sau khi nộp; hỏi hạn nộp và hình thức demo.
- Đổi link `file:///c:/...` thành đường dẫn tương đối.
