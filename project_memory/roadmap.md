# KẾ HOẠCH CHI TIẾT 4 TUẦN (ROADMAP.MD) — DỰ ÁN EVENTQR

> **Môn:** Cloud Computing (Đợt 1, 2026–2027) — Nhóm Domain Apps — GVHD: TS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:**  
> - Đặng Duy Quang (24110307) — Vai trò A (Lead, Backend dữ liệu, Tài khoản AWS chính)  
> - Trương Hoàng Long (24110273) — Vai trò B (Gửi vé SNS, QR S3, Frontend, CloudWatch)  
> **Thời gian:** 05/10/2026 – 01/11/2026 (4 tuần, $\ge 8$ giờ/người/tuần).

> 📌 **Lưu ý:** Kế hoạch tổng thể chính thức được theo dõi và cập nhật hàng tuần tại file [`docs/plan.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/plan.md).

---

## TỔNG QUAN TIẾN ĐỘ

```
Tuần 1 (05–11/10): Nền tảng, thiết kế & bài thử rủi ro   [100% HOÀN THÀNH]
Tuần 2 (12–18/10): Chức năng lõi & Kiểm thử thành phần     [100% HOÀN THÀNH - SETUP & MÃ NGUỒN XONG]
Tuần 3 (19–25/10): Tích hợp, bảo mật, giám sát            [100% HOÀN THÀNH - ĐỒNG BỘ WORKLOG & ĐÓNG BĂNG]
Tuần 4 (26/10–01/11): Nghiệm thu 21 ca, video demo, báo cáo [CHƯA BẮT ĐẦU - CHUẨN BỊ KỊCH BẢN]
```

---

## TUẦN 1: NỀN TẢNG, THIẾT KẾ & BÀI THỬ RỦI RO (05/10 – 11/10/2026)
*Trạng thái: Hoàn thành 100%. Đã nộp báo cáo và worklog tuần 1.*

- [x] **Công việc của Quang (A) — Tổng: 9.75 giờ:**
  - [x] Thiết kế kiến trúc tổng thể v1 (2.0h)
  - [x] Khởi tạo GitHub repo private `eventqr` + mời cộng tác viên (0.25h)
  - [x] Tạo 2 bảng DynamoDB `eventqr-events` và `eventqr-tickets` On-demand (0.75h)
  - [x] Tạo secret `eventqr-hmac-key` trong AWS Secrets Manager (0.75h)
  - [x] Viết và chạy Lambda test `eventqr-test-secret` với LabRole (0.5h)
  - [x] Viết và chạy Lambda test `eventqr-test-checkin` (0.5h)
  - [x] Kiểm thử điều kiện ghi chống trùng vé (lần đầu 200, lần hai 409) (0.75h)
  - [x] Thảo luận và thống nhất luồng nghiệp vụ với Long (1.0h)
  - [x] Viết mô-đun ký và xác minh HMAC `hmac_utils.py`, kiểm thử 7/7 ca pass (0.25h)
  - [x] Xây dựng bản thảo đặc tả API v0.2 cùng AI (1.0h)
  - [x] Đẩy code lên GitHub (0.5h)
  - [x] Viết báo cáo tuần 1 (1.5h)

- [x] **Công việc của Long (B) — Tổng: 8.2 giờ:**
  - [x] Vẽ sơ đồ kiến trúc và sequence diagrams (1.5h)
  - [x] Cấu hình S3 bucket `eventqr-qr` private, tag `Project=EventQR` (0.5h)
  - [x] Cấu hình S3 bucket `eventqr-web` private, tag `Project=EventQR` (0.5h)
  - [x] Tạo topic SNS `eventqr-ticket-delivery` loại Standard (0.8h)
  - [x] Tạo 2 subscription email kèm filter policy; kiểm thử gửi email nhận diện đúng đích (0.3h)
  - [x] Triển khai Lambda `eventqr-web` đọc HTML từ S3 private (1.0h)
  - [x] Tích hợp API Gateway với Lambda web, kiểm thử HTTPS bật camera trên máy tính (0.5h)
  - [x] Cấu hình CloudWatch Log retention 7 ngày và gắn tags (1.0h)
  - [x] Tạo Presigned URL S3 test 6h (1.0h)
  - [x] Viết báo cáo tuần 1 (1.0h)

---

## TUẦN 2: CHỨC NĂNG LÕI & KIỂM THỬ TỪNG THÀNH PHẦN (12/10 – 18/10/2026)
*Trạng thái: Hoàn thành 100%. Đã ghép 8 Lambda, 4 trang frontend, build 8 gói ZIP, đạt 38/38 unit test local.*

### Phân công theo ngày:

#### Thứ Hai (12/10/2026) — Chốt hợp đồng giao tiếp & Chuẩn bị
- [x] **A (Quang - 1.5h):** Đồng bộ tài liệu [`docs/api.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/api.md) vào repo, chuẩn bị các hàm tiện ích DynamoDB dùng chung.
- [x] **B (Long - 1.5h):** Nghiên cứu thư viện sinh mã QR nhẹ thuần Python (`segno` hoặc `qrcode`), thống nhất hợp đồng gọi giữa `register` và `generate-qr`.

#### Thứ Ba (13/10/2026) — Sự kiện & Sinh QR
- [x] **A (Quang - 2.0h):** Viết Lambda `eventqr-create-event`:
  - Input: `{name, startTime, venue}` (yêu cầu header `x-api-key`).
  - Sinh `eventId` UUID, ghi vào `eventqr-events`.
  - Viết test payload kiểm tra phản hồi 201 và các mã lỗi 400.
- [x] **B (Long - 2.0h):** Viết Lambda `eventqr-generate-qr`:
  - Input: `{eventId, ticketId}` (Invoke đồng bộ từ `register`).
  - Đọc khóa HMAC từ Secrets Manager (cache vào bộ nhớ).
  - Ký chuỗi `v1.<eventId>.<ticketId>`, sinh ảnh QR PNG và đẩy vào bucket `eventqr-qr`. Trả về `{qrKey}`.

#### Thứ Tư (14/10/2026) — Đăng ký & Giao diện xem vé
- [x] **A (Quang - 2.0h):** Viết mô-đun `ticket_mail.py` và bắt đầu Lambda `eventqr-register`:
  - Input: `{eventId, name, email}`.
  - Kiểm tra sự kiện tồn tại trong DynamoDB `eventqr-events`.
  - Sinh `ticketId` UUID, gọi đồng bộ `generate-qr`.
- [x] **B (Long - 2.0h):** Thiết kế giao diện HTML/CSS/JS thuần:
  - `register.html`: Form đăng ký sự kiện, hiển thị thông báo và link vé trực tiếp.
  - `ticket.html`: Trang hiển thị chi tiết vé và hình ảnh mã QR.

#### Thứ Năm (15/10/2026) — Ghi nhận vé, Check-in & Lấy vé
- [x] **A (Quang - 2.0h):** Hoàn thiện Lambda `eventqr-register` và viết Lambda `eventqr-checkin`:
  - `register`: Ghi item vào `eventqr-tickets` (`status=ISSUED`, `attribute_not_exists`), kích hoạt gửi vé qua SNS.
  - `checkin`: Nhận `{payload, eventId}`, xác thực HMAC (`compare_digest`), cập nhật DynamoDB `status=ISSUED -> CHECKED_IN`.
- [x] **B (Long - 2.0h):** Viết Lambda `eventqr-get-ticket` và `eventqr-resend`:
  - `get-ticket`: Nhận `eventId`, `ticketId`, kiểm tra DB, trả presigned URL ảnh QR (hoặc ảnh inline base64).
  - `resend`: Gửi lại email vé qua SNS khi người dùng yêu cầu.

#### Thứ Sáu (16/10/2026) — Thống kê & Giao diện Check-in
- [x] **A (Quang - 1.5h):** Viết Lambda `eventqr-stats`:
  - `GET /stats/{eventId}`: Query các vé trong `eventqr-tickets` theo `eventId`, đếm tổng vé, đã check-in, chưa check-in.
  - Cấu hình 6 route lên API Gateway cá nhân của Quang.
- [x] **B (Long - 1.5h):** Hoàn thiện giao diện:
  - `checkin.html`: Tích hợp camera quét QR (dùng thư viện nhẹ `html5-qrcode` qua CDN/local JS), gọi API check-in kèm `x-api-key`.
  - `stats.html`: Dashboard hiển thị số lượng vé trực quan.

#### Thứ Bảy (17/10/2026) — Kiểm thử thành phần độc lập
- [x] **A (Quang - 1.0h):** Test trọn vẹn 6 route qua Postman/curl trên API Gateway của A, lưu kết quả response làm minh chứng.
- [x] **B (Long - 1.0h):** Test giao diện web trên môi trường localhost nối với API Gateway của B, kiểm tra hiển thị QR trên điện thoại.

#### Chủ Nhật (18/10/2026) — Giải thích chéo, Đồng bộ Git & Báo cáo
- [x] **A (Quang - 1.5h):** Giải thích chéo mã nguồn cho Long (30–45p). Cập nhật `worklog/week2/worklog_markdown.md`, viết Báo cáo tuần 2.
- [x] **B (Long - 1.5h):** Giải thích chéo frontend và SNS cho Quang (30–45p). Push toàn bộ mã lên GitHub. Cập nhật worklog tuần 2, viết Báo cáo tuần 2.

**Tổng kết giờ Tuần 2:** Quang: 8.25h | Long: 10.50h (Đạt chuẩn $\ge 8$h).

---

## TUẦN 3: TÍCH HỢP TOÀN HỆ THỐNG, BẢO MẬT & GIÁM SÁT (19/10 – 25/10/2026)
*Trạng thái: Đang thực hiện. Mục tiêu: Chạy toàn bộ trên tài khoản chính của Quang; Đóng băng tính năng vào 23:59 ngày 25/10.*

### Phân công theo ngày:

#### Thứ Hai (19/10/2026) — Triển khai hạ tầng Tài khoản chính
- [x] **A (Quang - 2.0h):** Đồng bộ tạo toàn bộ tài nguyên trên tài khoản AWS chính: 2 bảng DynamoDB, secret HMAC, 7 hàm Lambda (lấy code từ Git).
- [x] **B (Long - 1.5h):** Dựng 2 S3 bucket trên tài khoản chính (`eventqr-qr-<AccountID>`, `eventqr-web-<AccountID>`), topic SNS `eventqr-ticket-delivery`.

#### Thứ Ba (20/10/2026) — Cấu hình API Gateway & Hosting Web
- [x] **A (Quang - 2.0h):** Dựng API Gateway `eventqr-api` (stage `v1`) trên tài khoản chính: ánh xạ 6 route tới 6 Lambda, cấu hình CORS chuẩn.
- [x] **B (Long - 2.0h):** Triển khai giao diện web lên S3/Lambda web HTTPS. Thiết lập file `config.js` động trỏ về API Gateway chính.

#### Thứ Tư (21/10/2026) — Bảo mật & Throttling
- [x] **A (Quang - 1.5h):** Cấu hình bảo mật API: Tạo API Key `eventqr-organizer-key`, Usage Plan gắn throttling (Rate: 50, Burst: 100), khóa bảo vệ route `/events`, `/checkin`, `/stats`.
- [ ] **B (Long - 2.0h):** Tích hợp quét camera trên điện thoại thật qua HTTPS của hệ thống chính; kiểm thử truyền API Key trong header `x-api-key`. [ĐANG THỰC HIỆN]

#### Thứ Năm (22/10/2026) — Kiểm thử tích hợp luồng đầu - cuối (End-to-End)
- [ ] **A (Quang - 1.5h):** Kiểm tra dữ liệu ghi nhận trong DynamoDB và Secrets Manager khi luồng đăng ký -> gửi email -> check-in chạy thật.
- [ ] **B (Long - 2.0h):** Thiết lập CloudWatch: Đổi retention 7 ngày, tạo dashboard `eventqr-dashboard` giám sát invocations/lỗi Lambda, tạo 2 CloudWatch Alarms cảnh báo lỗi 5xx. [ĐANG THỰC HIỆN]

#### Thứ Sáu (23/10/2026) — Rà soát phi chức năng & IaC
- [ ] **A (Quang - 1.5h):** Kiểm tra giới hạn reserved concurrency của Lambda, rà soát tránh lỗi retry vô tận gây cạn kinh phí 50 USD.
- [ ] **B (Long - 1.5h):** Soạn thảo template IaC (SAM/CloudFormation) nếu kịp; nếu không kịp thì viết tài liệu quy trình thao tác tay.

#### Thứ Bảy (24/10/2026) — Hoàn thiện UX & Xử lý ngoại lệ
- [ ] **A (Quang - 1.5h):** Xử lý triệt để mã lỗi CORS từ Gateway Responses (lỗi 403 khi sai API key, lỗi 429 khi quá tải).
- [ ] **B (Long - 1.5h):** Tinh chỉnh thông báo lỗi trên UI: hiển thị rõ vé đã check-in lúc mấy giờ, âm thanh quét thành công/thất bại.

#### Chủ Nhật (25/10/2026) — Giải thích chéo, Báo cáo Tuần 3 & ĐÓNG BĂNG MÃ NGUỒN
- [ ] **A (Quang - 1.5h):** Giải thích chéo cho Long. Chụp minh chứng tài khoản chính. Viết báo cáo tuần 3. **CHỐT ĐÓNG BĂNG TÍNH NĂNG (FEATURE FREEZE).**
- [ ] **B (Long - 1.5h):** Giải thích chéo cho Quang. Hoàn tất tài liệu vận hành. Viết báo cáo tuần 3.

**Mục tiêu giờ Tuần 3:** Quang: 11.5h | Long: 12.0h (Đạt chuẩn $\ge 8$h).

---

## TUẦN 4: NGHIỆM THU 21 CA, VIDEO DEMO, BÁO CÁO TỔNG KẾT & DỌN DẸP (26/10 – 01/11/2026)
*Trạng thái: Chưa bắt đầu. Mục tiêu: Nghiệm thu toàn bộ hệ thống, quay video $\le 10$ phút, hoàn thiện báo cáo và dọn dẹp tài nguyên.*

### Phân công theo ngày:

#### Thứ Hai (26/10/2026) — Nghiệm thu 21 ca kiểm thử (Test Cases 1–11)
- [ ] **A (Quang - 2.0h):** Chạy nghiệm thu các ca backend: vé hợp lệ, quét trùng đồng thời 2 thiết bị, QR bị sửa signature, QR sai eventId, vé không tồn tại.
- [ ] **B (Long - 2.0h):** Chạy nghiệm thu các ca frontend & SNS: đăng ký email mới, email chưa confirm SNS, resend vé, quét trong điều kiện camera mờ.

#### Thứ Ba (27/10/2026) — Nghiệm thu 21 ca kiểm thử (Test Cases 12–21) & Kịch bản Demo
- [ ] **A (Quang - 1.5h):** Hoàn thiện bảng kết quả nghiệm thu 21 test cases (ghi rõ Pass/Fail, thời gian, response). Tối ưu chi phí Lambda.
- [ ] **B (Long - 1.5h):** Soạn thảo kịch bản chi tiết cho Video Demo ($\le 10$ phút) theo đúng yêu cầu giảng viên.

#### Thứ Tư (28/10/2026) — Dữ liệu mẫu & Tổng hợp đóng góp AI
- [ ] **A (Quang - 1.5h):** Chuẩn bị dữ liệu mẫu sạch trên tài khoản chính: 1 sự kiện chuẩn, chuẩn bị sẵn 5–10 email sinh viên thật để demo. Tổng hợp phần đóng góp của AI trong toàn dự án.
- [ ] **B (Long - 1.5h):** Tổng duyệt kịch bản video demo cùng Quang; test âm thanh, ánh sáng, góc quay camera quét vé trên điện thoại.

#### Thứ Năm (29/10/2026) — Quay và Dựng Video Demo
- [ ] **A (Quang - 2.0h):** Phối hợp quay video demo chính thức: thao tác tạo sự kiện, đăng ký, nhận vé, quét QR bằng điện thoại, xem dashboard thống kê. Soạn Báo cáo cuối kỳ.
- [ ] **B (Long - 2.0h):** Hậu kỳ video demo: cắt ghép, bổ sung chú thích các bước kỹ thuật, kiểm soát thời lượng $\le 10$ phút, xuất bản link dự phòng.

#### Thứ Sáu (30/10/2026) — Báo cáo Chi phí & Hoàn thiện tài liệu
- [ ] **A (Quang - 1.5h):** Chụp ảnh AWS Cost Explorer / Billing của tài khoản chính; phân tích chi phí tiêu thụ so với hạn mức 50 USD; hoàn thiện chương Kiến trúc & Bảo mật trong Báo cáo cuối kỳ.
- [ ] **B (Long - 1.5h):** Hoàn thiện chương Frontend, SNS, Giám sát trong Báo cáo cuối kỳ; tổng hợp bảng phân bổ công việc và tự đánh giá thành viên.

#### Thứ Bảy (31/10/2026) — Kiểm tra chéo toàn diện (Final Review)
- [ ] **A (Quang - 1.5h):** Rà soát toàn bộ hồ sơ nộp môn học: Báo cáo cuối kỳ (PDF), Video demo link, Bảng nghiệm thu, Worklog 4 tuần.
- [ ] **B (Long - 1.5h):** Kiểm tra chéo link GitHub, đảm bảo repo không chứa thông tin nhạy cảm, README đầy đủ thông tin nhóm và hướng dẫn.

#### Chủ Nhật (01/11/2026) — DỌN DẸP TÀI NGUYÊN (CLEANUP)
- [ ] **A (Quang - 1.0h):** **Chỉ sau khi đã có đầy đủ video và minh chứng:** Xóa toàn bộ tài nguyên trên tài khoản chính (DynamoDB, S3, Lambda, Secrets Manager, API Gateway). Chụp ảnh console trống làm minh chứng.
- [ ] **B (Long - 1.0h):** Xóa tài nguyên trên tài khoản phụ của Long. Chụp ảnh console trống làm minh chứng dọn dẹp. Cập nhật worklog tuần 4 kết thúc dự án.

**Mục tiêu giờ Tuần 4:** Quang: 11.0h | Long: 11.0h (Đạt chuẩn $\ge 8$h).
