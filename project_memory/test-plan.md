# KẾ HOẠCH KIỂM THỬ NGHIỆM THU 21 CA — TUẦN 4 (TEST-PLAN.MD)

> **Dành cho:** AI Assistant / Agent và Nhóm sinh viên (Đặng Duy Quang & Trương Hoàng Long)  
> **Dự án:** EventQR — Hệ thống quản lý sự kiện và check-in bằng QR code (AWS Serverless)  
> **Tài liệu căn cứ:** Mục 10 trong [`docs/api.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/api.md) và Ma trận kiểm thử [`project_memory/test-matrix.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/test-matrix.md)  
> **Thời gian thực hiện:** Tuần 4 (26/10/2026 – 01/11/2026)  
> **Cập nhật:** 31/10/2026

---

## 🎯 1. NGUYÊN TẮC THỰC HIỆN & QUY CHUẨN MINH CHỨNG

1. **Gom nhóm luồng tối ưu (Test Flows):** Không chạy rời rạc 21 ca ngẫu nhiên. Thực hiện theo **4 luồng nghiệp vụ liên hoàn**:
   - **Luồng 1:** Quản trị Sự kiện & Bảo mật API Gateway (TC17, TC20, TC18) $\rightarrow$ Khởi tạo `eventId` mẫu.
   - **Luồng 2:** Đăng ký vé & Xử lý Email SNS (TC03, TC04, TC05, TC06, TC01, TC02, TC07, TC08, TC09).
   - **Luồng 3:** Quét QR & Check-in Chống Trùng (TC16, TC13, TC14, TC15, TC10, TC11, TC12).
   - **Luồng 4:** Thống kê Số liệu & Bền vững Ảnh QR Presigned (TC19, TC21).
2. **Quy chuẩn lưu file ảnh minh chứng:**
   - Tất cả ảnh chụp màn hình được lưu tập trung vào thư mục: [`docs/evidence/week4/`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/).
   - Đặt tên file chuẩn hóa: `tc01.png`, `tc02.png`, ... đến `tc21.png`.
   - **Nội dung bắt buộc thấy trên ảnh:**
     - Mã phản hồi HTTP (Status Code), body JSON hoặc thông báo trực quan trên giao diện web.
     - Nếu chụp AWS Console / Trình duyệt: Thấy rõ Region `us-east-1`, Account ID (menu góc phải), và đồng hồ hệ thống.
     - Nếu chụp Terminal / PowerShell / Postman: Thấy rõ câu lệnh thực hiện, timestamp và kết quả trả về.
3. **Nguyên tắc bảo mật:** Tuyệt đối không để lộ giá trị thật của API Key (`eventqr-organizer-key`), Secret Key HMAC hay AWS credentials trong ảnh chụp công khai đưa lên GitHub.

---

## 🚀 2. KẾ HOẠCH THỰC HIỆN CHI TIẾT THEO 4 LUỒNG

### 🌊 LUỒNG 1: QUẢN TRỊ SỰ KIỆN & BẢO MẬT API GATEWAY (TC17, TC20, TC18)

#### Bước 1.1: Khởi tạo biến môi trường kiểm thử
Mở PowerShell trên máy tính cá nhân và thiết lập:
```powershell
$API_URL = "https://<API_ID>.execute-api.us-east-1.amazonaws.com/v1"
$API_KEY = "<PASTE_API_KEY_ORGANIZER>"
$headers = @{ 'x-api-key' = $API_KEY }
```

#### Bước 1.2: Chạy TC17 — Route BTC từ chối khi thiếu/sai API Key
- **Thao tác:** Gửi request `POST /events` không có header `x-api-key`:
  ```powershell
  Invoke-RestMethod -Method Post -Uri "$API_URL/events" -ContentType 'application/json' -Body '{"name":"Sự kiện thử"}'
  ```
- **Kết quả mong đợi:** HTTP `403 Forbidden`, body: `{"message":"Forbidden"}`.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal hiện mã lỗi 403 $\rightarrow$ Lưu thành [`docs/evidence/week4/tc17.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc17.png).

#### Bước 1.3: Tạo Sự kiện mẫu chuẩn (Dữ liệu nền tảng)
- **Thao tác:** Gửi request `POST /events` kèm API Key hợp lệ:
  ```powershell
  $eventBody = @{
      name = "EventQR Demo 2026"
      startTime = "2026-11-01T08:00:00+07:00"
      venue = "Hội trường Trụ sở chính"
  } | ConvertTo-Json

  $resEvent = Invoke-RestMethod -Method Post -Uri "$API_URL/events" -Headers $headers -ContentType 'application/json' -Body $eventBody
  $EVENT_ID = $resEvent.data.eventId
  Write-Host "EVENT_ID chuẩn: $EVENT_ID" -ForegroundColor Cyan
  ```
- **Kết quả mong đợi:** HTTP `201 Created`, trả về `eventId` (UUID). Lưu lại giá trị `$EVENT_ID` này.

#### Bước 1.4: Chạy TC20 — Thống kê sự kiện vừa tạo rỗng (Chưa có vé)
- **Thao tác:** Gọi `GET /stats/{eventId}` của sự kiện vừa tạo:
  ```powershell
  Invoke-RestMethod -Method Get -Uri "$API_URL/stats/$EVENT_ID" -Headers $headers
  ```
- **Kết quả mong đợi:** HTTP `200 OK`, `totalTickets: 0, checkedInTickets: 0, notCheckedInTickets: 0`.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal hiện response `0/0/0` $\rightarrow$ Lưu thành [`docs/evidence/week4/tc20.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc20.png).

#### Bước 1.5: Chạy TC18 — Vượt ngưỡng tải API (Throttling Test / 429)
- **Thao tác:** Bắn burst 120 request liên tiếp trong 1 giây để vượt Burst 100 của Usage Plan:
  ```powershell
  1..120 | ForEach-Object -Parallel {
      try {
          Invoke-RestMethod -Method Get -Uri "$using:API_URL/stats/$using:EVENT_ID" -Headers $using:headers -ErrorAction Stop
          Write-Host "Req $_: 200 OK" -ForegroundColor Green
      } catch {
          if ($_.Exception.Response.StatusCode.value__ -eq 429) {
              Write-Host "Req $_: 429 Too Many Requests (THROTTLED)" -ForegroundColor Yellow
          }
      }
  } -ThrottleLimit 30
  ```
- **Kết quả mong đợi:** Xuất hiện các phản hồi HTTP `429 Too Many Requests`, body: `{"message":"Too Many Requests"}`.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal thấy rõ các dòng `429 Too Many Requests` màu vàng $\rightarrow$ Lưu thành [`docs/evidence/week4/tc18.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc18.png).

---

### 🌊 LUỒNG 2: ĐĂNG KÝ VÉ & XỬ LÝ EMAIL SNS (TC03 $\rightarrow$ TC09)

#### Bước 2.1: Chạy TC03 — Đăng ký thiếu trường bắt buộc
- **Thao tác:** Gọi `POST /register` thiếu tên hoặc email:
  ```powershell
  Invoke-RestMethod -Method Post -Uri "$API_URL/register" -ContentType 'application/json' -Body (@{ eventId=$EVENT_ID; name="" } | ConvertTo-Json)
  ```
- **Kết quả mong đợi:** HTTP `400 Bad Request`, mã lỗi: `INVALID_INPUT`. Không có vé ghi vào DB.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal lỗi 400 $\rightarrow$ Lưu thành [`docs/evidence/week4/tc03.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc03.png).

#### Bước 2.2: Chạy TC04 — Đăng ký sự kiện không tồn tại
- **Thao tác:** Gọi `POST /register` với `eventId` giả mạo (`00000000-0000-4000-8000-000000000000`):
  ```powershell
  Invoke-RestMethod -Method Post -Uri "$API_URL/register" -ContentType 'application/json' -Body (@{ eventId="00000000-0000-4000-8000-000000000000"; name="Test"; email="test@gmail.com" } | ConvertTo-Json)
  ```
- **Kết quả mong đợi:** HTTP `404 Not Found`, mã lỗi: `EVENT_NOT_FOUND`.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal lỗi 404 $\rightarrow$ Lưu thành [`docs/evidence/week4/tc04.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc04.png).

#### Bước 2.3: Chạy TC05 — Lỗi sinh QR/S3 rollback không tạo vé mồ côi
- **Thao tác:** Kiểm tra logic bảo vệ thứ tự: Hàm con `generate-qr` được gọi trước khi ghi item vào bảng `eventqr-tickets`. (Đối chiếu ca kiểm thử tự động hoặc log giả lập).
- **Kết quả mong đợi:** HTTP `500 Internal Server Error`, không xuất hiện vé rác mồ côi trong DynamoDB.
- 📸 **CHỤP MINH CHỨNG:** Chụp log kiểm tra tính nguyên vẹn dữ liệu $\rightarrow$ Lưu thành [`docs/evidence/week4/tc05.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc05.png).

#### Bước 2.4: Chạy TC06 — Email chưa xác nhận SNS (`PENDING_CONFIRMATION`)
- **Thao tác:** Đăng ký vé với một email sinh viên hoàn toàn mới chưa từng xác nhận subscription:
  ```powershell
  $emailMoi = "sinhvien_moi_clco@gmail.com" # thay bằng email thật của bạn
  $regMoi = Invoke-RestMethod -Method Post -Uri "$API_URL/register" -ContentType 'application/json' -Body (@{ eventId=$EVENT_ID; name="Sinh Vien Moi"; email=$emailMoi } | ConvertTo-Json)
  $regMoi
  ```
- **Kết quả mong đợi:** HTTP `201 Created`, trả về `emailDeliveryStatus: "PENDING_CONFIRMATION"`. Chưa gửi thư vé; trang web vẫn cung cấp link vé.
- 📸 **CHỤP MINH CHỨNG:** Chụp phản hồi `PENDING_CONFIRMATION` $\rightarrow$ Lưu thành [`docs/evidence/week4/tc06.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc06.png).

#### Bước 2.5: Chạy TC01 — Đăng ký vé hợp lệ thành công
- **Thao tác:** Đăng ký vé cho khách tham dự chuẩn:
  ```powershell
  $reg1 = Invoke-RestMethod -Method Post -Uri "$API_URL/register" -ContentType 'application/json' -Body (@{ eventId=$EVENT_ID; name="Nguyen Van A"; email="khach_a@gmail.com" } | ConvertTo-Json)
  $TICKET_ID_1 = $reg1.data.ticketId
  $reg1.data
  ```
- **Kết quả mong đợi:** HTTP `201 Created`, trả `ticketId` và `ticketUrl`. Item vé được ghi vào DynamoDB với `status: ISSUED`, S3 có ảnh QR `qr/<eventId>/<ticketId>.png`.
- 📸 **CHỤP MINH CHỨNG:** Chụp trang web `ticket.html` hiển thị mã QR $\rightarrow$ Lưu thành [`docs/evidence/week4/tc01.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc01.png).

#### Bước 2.6: Chạy TC02 — Đăng ký cùng 1 email 2 lần
- **Thao tác:** Gửi lại đúng thông tin của TC01 một lần nữa.
- **Kết quả mong đợi:** HTTP `201 Created`, sinh ra vé thứ 2 với `ticketId` mới độc lập.
- 📸 **CHỤP MINH CHỨNG:** Chụp terminal nhận vé thứ 2 $\rightarrow$ Lưu thành [`docs/evidence/week4/tc02.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc02.png).

#### Bước 2.7: Chạy TC07 — Gửi vé sau khi đã Confirm SNS (`PUBLISHED`)
- **Thao tác:** Người dùng mở hộp thư, bấm "Confirm subscription" trong email của AWS SNS. Sau đó bấm nút "Gửi lại vé" (`POST /resend`) trên trang vé.
- **Kết quả mong đợi:** HTTP `200 OK`, `emailDeliveryStatus: "PUBLISHED"`. Email chứa link vé được gửi thành công vào hộp thư.
- 📸 **CHỤP MINH CHỨNG:** Chụp ảnh màn hình hộp thư Gmail nhận được email vé $\rightarrow$ Lưu thành [`docs/evidence/week4/tc07.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc07.png).

#### Bước 2.8: Chạy TC08 — Cách ly Filter Policy giữa 2 email
- **Thao tác:** Đăng ký vé cho Email A và Email B (đều đã Confirm). Publish vé của Email A.
- **Kết quả mong đợi:** Hộp thư A nhận thư; Hộp thư B hoàn toàn không nhận được thư của A (chứng minh bộ lọc filter policy hoạt động chính xác).
- 📸 **CHỤP MINH CHỨNG:** Chụp đối chiếu 2 hộp thư $\rightarrow$ Lưu thành [`docs/evidence/week4/tc08.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc08.png).

#### Bước 2.9: Chạy TC09 — Xử lý khi SNS lỗi sau khi đã lưu vé
- **Thao tác:** Khảo sát trường hợp Publish SNS gặp lỗi kết nối sau khi DynamoDB đã ghi vé thành công.
- **Kết quả mong đợi:** API vẫn trả HTTP 201 kèm link vé, `emailDeliveryStatus: "FAILED"`. Khách không mất quyền xem vé trên web.
- 📸 **CHỤP MINH CHỨNG:** Chụp phản hồi trả link vé khi SNS lỗi $\rightarrow$ Lưu thành [`docs/evidence/week4/tc09.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc09.png).

---

### 🌊 LUỒNG 3: QUÉT QR & CHECK-IN CHỐNG TRÙNG VÉ (TC10 $\rightarrow$ TC16)

#### Bước 3.1: Chạy TC16 — Mã QR sai định dạng / Sai version
- **Thao tác:** Mở mục "Nhập payload thủ công" trên `checkin.html`, nhập chuỗi URL website thông thường hoặc text rác (không có prefix `v1.`).
- **Kết quả mong đợi:** HTTP `400 Bad Request`, mã lỗi: `INVALID_INPUT`. Loa phát tiếng beep trầm (330Hz).
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện báo lỗi định dạng $\rightarrow$ Lưu thành [`docs/evidence/week4/tc16.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc16.png).

#### Bước 3.2: Chạy TC13 — Quét QR bị sửa chữ ký (HMAC Tamper)
- **Thao tác:** Lấy payload QR hợp lệ `v1.<eventId>.<ticketId>.<sig>`, thay đổi 1 ký tự cuối cùng của chuỗi signature và bấm Check-in thử.
- **Kết quả mong đợi:** HTTP `403 Forbidden`, mã lỗi: `INVALID_SIGNATURE`. Loa phát tiếng beep trầm (330Hz).
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện báo lỗi chữ ký không hợp lệ $\rightarrow$ Lưu thành [`docs/evidence/week4/tc13.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc13.png).

#### Bước 3.3: Chạy TC14 — Quét QR đúng chữ ký nhưng sai sự kiện (Event Mismatch)
- **Thao tác:** Lấy vé của Sự kiện X nhưng nhập `eventId` của Sự kiện Y vào ô kiểm vé và quét.
- **Kết quả mong đợi:** HTTP `403 Forbidden`, mã lỗi: `EVENT_MISMATCH`. Loa phát tiếng beep trầm (330Hz).
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện báo lỗi sai sự kiện $\rightarrow$ Lưu thành [`docs/evidence/week4/tc14.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc14.png).

#### Bước 3.4: Chạy TC15 — Chữ ký đúng nhưng vé không có trong DB
- **Thao tác:** Gửi payload có chữ ký hợp lệ nhưng `ticketId` là UUID không tồn tại trong bảng `eventqr-tickets`.
- **Kết quả mong đợi:** HTTP `404 Not Found`, mã lỗi: `TICKET_NOT_FOUND`. Loa phát tiếng beep trầm (330Hz).
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện báo vé không tồn tại $\rightarrow$ Lưu thành [`docs/evidence/week4/tc15.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc15.png).

#### Bước 3.5: Chạy TC10 — Check-in vé hợp lệ lần đầu
- **Thao tác:** Mở `checkin.html` trên điện thoại hoặc máy tính, bật camera và quét mã QR hợp lệ của vé đã tạo ở TC01.
- **Kết quả mong đợi:** HTTP `200 OK`. Vé đổi trạng thái sang `CHECKED_IN`, lưu `checkedInAt`. Giao diện thông báo thành công kèm tên khách và thời gian check-in. **Loa phát tiếng beep cao (880Hz)**.
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện thông báo check-in thành công màu xanh $\rightarrow$ Lưu thành [`docs/evidence/week4/tc10.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc10.png).

#### Bước 3.6: Chạy TC11 — Quét lại cùng 1 vé (Chống check-in trùng)
- **Thao tác:** Đưa lại chính xác mã QR vừa check-in ở Bước 3.5 vào camera để quét lần 2.
- **Kết quả mong đợi:** HTTP `409 Conflict`, mã lỗi: `TICKET_ALREADY_CHECKED_IN`. Giao diện báo rõ: *"Vé đã check-in lúc [giờ cũ]"*. `checkedInAt` ban đầu được giữ nguyên. **Loa phát tiếng beep trầm (330Hz)**.
- 📸 **CHỤP MINH CHỨNG:** Chụp giao diện thông báo trùng vé màu đỏ $\rightarrow$ Lưu thành [`docs/evidence/week4/tc11.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc11.png).

#### Bước 3.7: Chạy TC12 — Hai thiết bị quét cùng 1 vé đồng thời (Race Condition)
- **Thao tác:** Mở 2 tab trình duyệt hoặc 2 điện thoại, dán cùng 1 payload vé hợp lệ mới và bấm gửi check-in gần như cùng tích tắc.
- **Kết quả mong đợi:** Đúng 1 thiết bị nhận HTTP 200 thành công; thiết bị còn lại nhận HTTP 409 báo trùng (chứng minh tính toàn vẹn của DynamoDB `ConditionExpression`).
- 📸 **CHỤP MINH CHỨNG:** Chụp màn hình 2 thiết bị đặt cạnh nhau (1 xanh 200, 1 đỏ 409) $\rightarrow$ Lưu thành [`docs/evidence/week4/tc12.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc12.png).

---

### 🌊 LUỒNG 4: THỐNG KÊ DASHBOARD & BỀN VỮNG ẢNH S3 (TC19, TC21)

#### Bước 4.1: Chạy TC19 — Thống kê sự kiện có số liệu hỗn hợp (10 vé: 6 check-in, 4 chưa)
- **Thao tác:** Đăng ký tổng cộng 10 vé cho sự kiện, tiến hành check-in 6 vé, để lại 4 vé chưa check-in. Mở `stats.html` (hoặc gọi API `GET /stats/{eventId}`).
- **Kết quả mong đợi:** Giao diện thống kê hiển thị chính xác: Tổng vé: 10, Đã check-in: 6, Chưa check-in: 4.
- 📸 **CHỤP MINH CHỨNG:** Chụp dashboard `stats.html` hiển thị tỷ lệ 10 / 6 / 4 $\rightarrow$ Lưu thành [`docs/evidence/week4/tc19.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc19.png).

#### Bước 4.2: Chạy TC21 — Tự động làm mới khi Presigned URL ảnh S3 hết hạn
- **Thao tác:** Mở trang xem vé `ticket.html?e=...&t=...` sau hơn 5 phút (vượt quá thời hạn 300 giây của link presigned cũ) và tải lại trang.
- **Kết quả mong đợi:** Lambda `get-ticket` sinh presigned URL mới hợp lệ; ảnh mã QR tiếp tục hiển thị rõ nét, không bị lỗi icon ảnh vỡ.
- 📸 **CHỤP MINH CHỨNG:** Chụp trang vé hiển thị ảnh QR sau khi link cũ hết hạn $\rightarrow$ Lưu thành [`docs/evidence/week4/tc21.png`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week4/tc21.png).

---

## 📁 3. DANH MỤC FILE MINH CHỨNG HOÀN CHỈNH (21 ẢNH TUẦN 4)

Sau khi hoàn tất, thư mục `docs/evidence/week4/` phải có đầy đủ 21 file ảnh:
- `tc01.png`, `tc02.png`, `tc03.png`, `tc04.png`, `tc05.png`, `tc06.png`, `tc07.png`, `tc08.png`, `tc09.png`, `tc10.png`
- `tc11.png`, `tc12.png`, `tc13.png`, `tc14.png`, `tc15.png`, `tc16.png`, `tc17.png`, `tc18.png`, `tc19.png`, `tc20.png`, `tc21.png`
