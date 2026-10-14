# Đặc tả API — EventQR

Phiên bản: 0.2 — ngày 10/10/2026.
Đề tài: Hệ thống quản lý sự kiện và check-in bằng QR code.

## Thay đổi so với v0.1

| # | Thay đổi | Mục |
|---|---|---|
| 1 | Đổi thứ tự tạo vé: sinh QR và lưu S3 trước, ghi DynamoDB sau, publish SNS cuối cùng. Lỗi trước khi ghi DB thì không có vé nào; bỏ mã `QR_NOT_READY` | 3, 7, 8, 9 |
| 2 | Cách nhận biết subscription SNS đang pending hay đã xác nhận, và quy tắc chỉ publish khi đã xác nhận (hướng dự kiến, phải kiểm chứng ở bài thử 3) | 3, 8, 9 |
| 3 | `GET /ticket` có chế độ dự phòng trả ảnh QR trực tiếp (base64) nếu bài thử presigned URL cho kết quả xấu | 7 |
| 4 | Throttle cho stage, ghi rõ nguy cơ lạm dụng `/register` | 2.5, 12 |
| 5 | Bảng biến môi trường dùng chung (có `WEB_BASE_URL`) | 2.6 |
| 6 | Làm rõ 403/429 do API Gateway sinh ra khác envelope của ứng dụng | 2.4 |

Các thay đổi ở mục 3 (register) do A yêu cầu. Các thay đổi chạm đến phần của B (generate-qr, ticket, resend, gửi email) chỉ là đề xuất, chờ B xác nhận.

## 1. Trạng thái và phạm vi

- A phụ trách đặc tả và triển khai register, checkin, stats. Các lựa chọn trong ba route này đã được A đồng ý (kể cả các chỉnh sửa của v0.2).
- B phụ trách đặc tả events, ticket, resend và giao diện. Nội dung các route này là đề xuất để B rà soát, chưa coi là đã được B xác nhận.
- Đây là hợp đồng API để triển khai tuần 2, không phải minh chứng các API đã chạy thật.
- Region: us-east-1. API: eventqr-api. Stage: v1.
- Lambda Python dùng LabRole; bảng eventqr-events và eventqr-tickets; secret eventqr-hmac-key.
- Phạm vi tối thiểu: cho phép một email đăng ký nhiều vé; chưa triển khai đăng nhập, phân quyền người dùng hoặc chống đăng ký trùng email.

## 2. Quy tắc chung

### 2.1. URL và cấu hình

Base URL dự kiến: `https://<api-id>.execute-api.us-east-1.amazonaws.com/v1`.
Các đường dẫn trong tài liệu là đường dẫn tương đối với base URL. Frontend lấy `API_BASE_URL` và `WEB_BASE_URL` từ `config.js`; không hardcode Account ID, ARN hoặc khóa HMAC. Backend lấy cấu hình từ biến môi trường (mục 2.6).

### 2.2. Định dạng

- Request có body dùng JSON với `Content-Type: application/json`.
- Response của ứng dụng dùng JSON UTF-8. Tên trường dùng camelCase.
- Thời gian dùng ISO 8601 theo UTC, ví dụ `2026-10-10T02:00:00Z`. Frontend đổi sang giờ Việt Nam để hiển thị.
- `eventId` và `ticketId` là chuỗi UUID do backend tạo cho dữ liệu thật; không chứa dấu chấm. Mã `TEST-WEEK1` chỉ dùng trong bài thử nền tảng.
- Vé có hai trạng thái: `ISSUED` và `CHECKED_IN`.
- QR có dạng `v1.<eventId>.<ticketId>.<signature>`; signature là HMAC-SHA256 dạng base64url không có padding.
- QR là dữ liệu nhạy cảm vì có thể dùng để check-in; không chứa tên hay email trong payload.

### 2.3. Phản hồi thành công

```json
{"ok": true, "data": {}}
```

### 2.4. Phản hồi lỗi

```json
{
  "ok": false,
  "error": {
    "code": "TICKET_ALREADY_CHECKED_IN",
    "message": "Vé đã được check-in",
    "details": {"checkedInAt": "2026-10-10T02:00:00Z"}
  }
}
```

`details` luôn là object, dùng `{}` nếu không có chi tiết. Frontend xử lý theo `error.code`, không phân tích `message`. Không trả stack trace, khóa secret hoặc AWS credentials cho frontend.

HTTP status là mã trạng thái thật của response, không chỉ là trường bên trong body. Với Lambda proxy integration, Lambda phải đóng gói `statusCode`, `headers` và `body` (chuỗi JSON) đúng định dạng của API Gateway.

**Lỗi do API Gateway sinh ra không theo envelope.** Khi lỗi xảy ra trước khi gọi Lambda, body thường là dạng `{"message": "..."}`. Hai trường hợp frontend phải xử lý riêng:
- **403** do thiếu hoặc sai `x-api-key`: body kiểu `{"message":"Forbidden"}` (không có `ok`/`error`). Trong khi đó 403 do ứng dụng (`INVALID_SIGNATURE`, `EVENT_MISMATCH`) luôn có envelope. Quy tắc: có `error.code` thì xử lý theo code; body không có envelope thì hiểu là lỗi API key và yêu cầu người dùng nhập lại key.
- **429** do vượt throttle: body kiểu `{"message":"Too Many Requests"}`. Frontend báo "thử lại sau", không tự retry liên tục.

Cấu hình Gateway Responses (DEFAULT_4XX, DEFAULT_5XX) để các lỗi này cũng có header CORS; nếu không cấu hình được thì trình duyệt có thể báo lỗi CORS thay cho 403/429. Frontend cần thông báo dự phòng cho trường hợp request thất bại mà không đọc được response.

### 2.5. Quyền truy cập, CORS và throttle

| Route | Quyền | Lambda |
|---|---|---|
| POST /events | BTC, yêu cầu x-api-key | eventqr-create-event |
| POST /register | Công khai | eventqr-register |
| GET /ticket | Có link vé chứa eventId và ticketId | eventqr-get-ticket |
| POST /resend | Có eventId và ticketId | eventqr-resend |
| POST /checkin | BTC, yêu cầu x-api-key | eventqr-checkin |
| GET /stats/{eventId} | BTC, yêu cầu x-api-key | eventqr-stats |

Theo phương án API key/usage plan, dự kiến dùng API Gateway REST API; phải kiểm chứng khả năng tạo trong Learner Lab. API key `eventqr-organizer-key` và usage plan `eventqr-usage-plan`.

API key chỉ là hạn chế truy cập của bản demo, không phải đăng nhập hoặc phân quyền an toàn. Không nhúng sẵn giá trị key vào repo/`config.js`; trang BTC cho người thao tác nhập key trong phiên làm việc. Key vẫn có thể bị người có quyền truy cập trình duyệt lấy được.

CORS cho origin CloudFront thực tế và localhost dùng khi phát triển; cho phép GET, POST, OPTIONS và header `Content-Type`, `x-api-key`. OPTIONS không yêu cầu API key. CORS không thay thế kiểm soát truy cập.

**Throttle.** Đặt giới hạn rate/burst thấp cho stage `v1` (con số cụ thể chốt khi tích hợp, đủ cho bản demo và test 5–10 email). Hai route công khai `/register` và `/resend` là nơi cần giới hạn chặt nhất (xem mục 12).

### 2.6. Biến môi trường dùng chung

| Biến | Ý nghĩa | Dùng bởi |
|---|---|---|
| `EVENTS_TABLE` | Tên bảng sự kiện (`eventqr-events`) | create-event, register, checkin, stats, get-ticket, resend |
| `TICKETS_TABLE` | Tên bảng vé (`eventqr-tickets`) | register, checkin, stats, get-ticket, resend |
| `SECRET_NAME` | Tên secret HMAC (`eventqr-hmac-key`) | generate-qr, checkin |
| `QR_BUCKET` | Bucket ảnh QR (`eventqr-qr-<AccountID>`) | generate-qr, get-ticket |
| `SNS_TOPIC_ARN` | ARN topic gửi vé | register, resend |
| `WEB_BASE_URL` | Domain web (CloudFront) để tạo `ticketUrl` trong response và trong email | register, resend |
| `GENERATE_QR_FUNCTION` | Tên hàm generate-qr để gọi nội bộ | register |
| `QR_DELIVERY_MODE` | `presigned` (mặc định) hoặc `inline`, xem mục 7 | get-ticket |

Mọi giá trị được đặt khi deploy ở từng tài khoản, không có giá trị nào nằm trong mã nguồn.

## 3. POST /register — A đã đồng ý

### Request

```json
{"eventId": "<event-uuid>", "name": "Nguyễn Văn A", "email": "example@gmail.com"}
```

- Cả ba trường bắt buộc và phải là chuỗi.
- Bỏ khoảng trắng đầu/cuối. `name` dài 1–100 ký tự sau chuẩn hóa.
- `email` kiểm tra định dạng cơ bản, tối đa 254 ký tự. Chuẩn hóa về chữ thường cho bản demo ở cả subscribe, filter policy và publish.
- Sự kiện phải tồn tại. `ticketId` do backend sinh, không nhận từ client.
- Không chặn nhiều vé cùng email. Gửi lại request đăng ký có thể tạo vé mới; frontend khóa nút khi đang gửi và không tự retry POST khi chưa biết kết quả.

### Thứ tự xử lý (v0.2)

1. Kiểm tra đầu vào và chuẩn hóa.
2. Đọc bảng Events, xác nhận sự kiện tồn tại.
3. Sinh `ticketId` (UUID).
4. Gọi `generate-qr` đồng bộ với `{eventId, ticketId}`: ký HMAC, tạo PNG, lưu S3, trả `qrKey`. Hàm này không ghi DynamoDB và không publish SNS. Lỗi ở đây: trả 500, chưa có gì trong DynamoDB.
5. Ghi vé vào Tickets (`status = ISSUED`, `createdAt`, `email`, `name`, `qrKey`, `kid`) với điều kiện `attribute_not_exists(ticketId)`. Lỗi ở đây: trả 500; ảnh QR đã lưu trong S3 trở thành ảnh mồ côi, vô hại.
6. Chạy quy trình email dùng chung (mục 9): bảo đảm subscription, xác định pending/confirmed, chỉ publish khi đã xác nhận. Lỗi ở bước này không làm mất vé: vẫn trả 201 với `emailDeliveryStatus = FAILED`.

Nhờ thứ tự này, một vé tồn tại trong DynamoDB thì QR của nó đã có trong S3, và link trong email mở được ngay khi người dùng nhận được.

### Thành công — 201

```json
{
  "ok": true,
  "data": {
    "eventId": "<event-uuid>",
    "ticketId": "<ticket-uuid>",
    "status": "ISSUED",
    "ticketUrl": "https://<domain>/ticket.html?e=<event-uuid>&t=<ticket-uuid>",
    "emailDeliveryStatus": "PENDING_CONFIRMATION"
  }
}
```

Frontend luôn hiển thị `ticketUrl` để người dùng nhận vé ngay cả khi email chưa đến.

| emailDeliveryStatus | Ý nghĩa |
|---|---|
| PENDING_CONFIRMATION | Subscription email chưa xác nhận; chưa publish. Người dùng cần xác nhận SNS rồi dùng resend |
| PUBLISHED | Subscription đã xác nhận và SNS chấp nhận publish; không khẳng định email đã đến hộp thư |
| FAILED | Vé/QR đã sẵn sàng nhưng thao tác subscribe/publish lỗi; người dùng vẫn mở được `ticketUrl` |

Đăng ký thành công không đồng nghĩa email đã được giao. `emailDeliveryStatus` là kết quả tại thời điểm xử lý request, không phải biên nhận giao email.

### Lỗi

| HTTP | error.code | Trường hợp |
|---|---|---|
| 400 | INVALID_INPUT | Body/JSON sai, thiếu trường hoặc dữ liệu không hợp lệ |
| 404 | EVENT_NOT_FOUND | Không có sự kiện |
| 500 | INTERNAL_ERROR | Không tạo được QR hoặc không ghi được vé (không có vé nào được tạo) |

## 4. POST /checkin — A đã đồng ý

### Request

Header `x-api-key` bắt buộc.

```json
{"eventId": "<event-uuid>", "qrPayload": "v1.<event-uuid>.<ticket-uuid>.<signature>"}
```

`eventId` là sự kiện BTC đang chọn. Không chỉ lấy `eventId` từ QR, vì sẽ có nguy cơ nhận vé của sự kiện khác.

### Xử lý

1. Kiểm tra trường bắt buộc, định dạng QR và version `v1`.
2. Verify HMAC bằng `hmac.compare_digest`; không ghi payload/secret vào log.
3. Kiểm tra `eventId` trong QR khớp `eventId` BTC chọn và sự kiện tồn tại.
4. `UpdateItem` theo khóa `eventId` + `ticketId`, với điều kiện vé tồn tại và `status = ISSUED`; đặt `CHECKED_IN` và `checkedInAt`.
5. Nếu conditional update thất bại, đọc lại vé bằng `ConsistentRead` để phân biệt không tồn tại và đã check-in.

Không dùng cách đọc status rồi cập nhật vô điều kiện. Lần quét trùng không thay đổi `checkedInAt` của lần đầu.

### Thành công — 200

```json
{
  "ok": true,
  "data": {
    "eventId": "<event-uuid>",
    "ticketId": "<ticket-uuid>",
    "name": "Nguyễn Văn A",
    "status": "CHECKED_IN",
    "checkedInAt": "2026-10-10T02:00:00Z"
  }
}
```

### Lỗi

| HTTP | error.code | Trường hợp |
|---|---|---|
| 400 | INVALID_INPUT | Thiếu trường, JSON sai hoặc QR sai định dạng/version |
| 403 | INVALID_SIGNATURE | HMAC không hợp lệ |
| 403 | EVENT_MISMATCH | Vé thuộc sự kiện khác |
| 404 | EVENT_NOT_FOUND | Sự kiện không tồn tại |
| 404 | TICKET_NOT_FOUND | Vé không tồn tại |
| 409 | TICKET_ALREADY_CHECKED_IN | Vé đã check-in; `details` chứa `checkedInAt` |
| 500 | INTERNAL_ERROR | Lỗi hệ thống hoặc trạng thái dữ liệu ngoài hai trạng thái đã quy định |

Lưu ý: 403 do thiếu/sai API key không có envelope, xem mục 2.4.

## 5. GET /stats/{eventId} — A đã đồng ý

Header `x-api-key` bắt buộc. Không có request body.

### Thành công — 200

```json
{
  "ok": true,
  "data": {
    "eventId": "<event-uuid>",
    "totalTickets": 10,
    "checkedInTickets": 6,
    "notCheckedInTickets": 4
  }
}
```

- Sự kiện tồn tại nhưng chưa có vé: trả ba số 0.
- Query theo `eventId`, đọc hết các trang qua `LastEvaluatedKey`; không Scan toàn bảng.
- `totalTickets = checkedInTickets + notCheckedInTickets` với mô hình hai trạng thái hiện tại.
- Chỉ đếm item vé. Nếu sau này thêm item `EMAIL#` để chặn trùng email, phải loại item đánh dấu khỏi thống kê.
- Thống kê là kết quả của lượt đọc, không cam kết snapshot giao dịch khi nhiều vé đang được cập nhật.

### Lỗi

| HTTP | error.code | Trường hợp |
|---|---|---|
| 400 | INVALID_INPUT | eventId không hợp lệ |
| 404 | EVENT_NOT_FOUND | Không có sự kiện |
| 500 | INTERNAL_ERROR | Lỗi đọc dữ liệu |

## 6. POST /events — Đề xuất, chờ B xác nhận

Header `x-api-key` bắt buộc.

```json
{"name": "Ngày hội CNTT", "startTime": "2026-10-25T01:00:00Z", "venue": "Hội trường"}
```

`name`: 1–100 ký tự; `venue`: 1–200 ký tự; `startTime`: thời gian ISO 8601 có múi giờ, backend chuẩn hóa UTC. Các trường bắt buộc. Backend sinh `eventId` UUID và `createdAt`.

Thành công 201:

```json
{
  "ok": true,
  "data": {
    "eventId": "<event-uuid>",
    "name": "Ngày hội CNTT",
    "startTime": "2026-10-25T01:00:00Z",
    "venue": "Hội trường",
    "createdAt": "2026-10-10T02:00:00Z"
  }
}
```

Lỗi: 400 `INVALID_INPUT`, 500 `INTERNAL_ERROR`. Chưa thêm API danh sách/sửa/xóa sự kiện; bản tối thiểu dùng `eventId` do BTC cung cấp để mở trang đăng ký/check-in.

## 7. GET /ticket — Đề xuất, chờ B xác nhận

Query parameters: `e=<eventId>&t=<ticketId>`, thống nhất với link `ticket.html`.

Không yêu cầu API key. Bộ đôi eventId/ticketId trong link đóng vai trò thông tin truy cập vé; `ticketId` phải ngẫu nhiên và khó đoán. Người có link có thể lấy QR, nên không ghi link đầy đủ vào log hoặc công khai ảnh vé thật.

Thành công 200 (chế độ mặc định `presigned`):

```json
{
  "ok": true,
  "data": {
    "eventId": "<event-uuid>",
    "ticketId": "<ticket-uuid>",
    "status": "ISSUED",
    "qrImageUrl": "<fresh-presigned-s3-url>"
  }
}
```

Chỉ tạo presigned URL mới cho PNG đã lưu, không sinh lại vé hoặc QR mỗi lần mở trang. URL ảnh dự kiến có hạn ngắn (300 giây); không khẳng định thời gian thực tế trước khi kiểm chứng credentials tạm (bài thử 5). Response đặt `Cache-Control: no-store`. Frontend mở lại `GET /ticket` khi URL ảnh hết hạn.

**Chế độ dự phòng `inline`.** Nếu bài thử 5 cho thấy presigned URL chết sớm hơn hạn đã đặt, hoặc gây khó khăn khi tích hợp, chuyển sang `QR_DELIVERY_MODE=inline`: Lambda đọc PNG từ S3 và trả `qrImageDataUrl` (`data:image/png;base64,...`) thay cho `qrImageUrl`. Ảnh QR chỉ vài KB nên nằm gọn trong response. Ảnh vẫn được lưu S3 như đề yêu cầu. Frontend dùng `data.qrImageDataUrl || data.qrImageUrl` để hiển thị, nên chuyển chế độ không phải sửa frontend. Quyết định chế độ nào là mặc định được chốt sau bài thử 5.

S3 ảnh QR giữ private. Email chứa link trang `ticket.html`, không chứa presigned URL cố định. Không trả email hoặc dữ liệu cá nhân không cần thiết trong route công khai.

Lỗi: 400 `INVALID_INPUT`, 404 `EVENT_NOT_FOUND`, 404 `TICKET_NOT_FOUND`, 500 `INTERNAL_ERROR` (bao gồm trường hợp vé có trong DynamoDB nhưng không đọc được ảnh trong S3; với thứ tự tạo vé ở mục 3, tình huống này không xảy ra trong luồng bình thường).

## 8. POST /resend — Đề xuất, chờ B xác nhận

```json
{"eventId": "<event-uuid>", "ticketId": "<ticket-uuid>"}
```

Không nhận email đích từ client; lấy email đã lưu trong vé để tránh gửi vé đến địa chỉ tùy ý. Không sinh vé mới, không reset check-in. Chưa thêm trường hợp đăng ký lại bằng email để tìm vé.

Xử lý: đọc vé, rồi chạy quy trình email dùng chung (mục 9). Subscription đã xác nhận và SNS chấp nhận publish: HTTP 200.

```json
{"ok": true, "data": {"emailDeliveryStatus": "PUBLISHED"}}
```

Chưa xác nhận subscription: HTTP 409, code `EMAIL_CONFIRMATION_REQUIRED`. Frontend yêu cầu người dùng xác nhận email SNS (kiểm tra spam), sau đó gửi lại. Có nên để resend gọi lại thao tác subscribe để gửi lại email xác nhận hay không phụ thuộc kết quả bài thử 3 (mục 11).

Lỗi khác: 400 `INVALID_INPUT`, 404 `EVENT_NOT_FOUND`, 404 `TICKET_NOT_FOUND`, 503 `EMAIL_DELIVERY_FAILED`, 500 `INTERNAL_ERROR`. Frontend không tự retry liên tục; B đề xuất giới hạn gửi lại (kết hợp throttle ở mục 2.5) trước khi tích hợp.

## 9. Phối hợp backend/frontend

### Hợp đồng nội bộ generate-qr (đề xuất, chờ B xác nhận)

- Không có route công khai; chỉ được gọi từ register (`Invoke` đồng bộ).
- Input: `{"eventId": "<uuid>", "ticketId": "<uuid>"}`. Kiểm tra cả hai là UUID, không chứa dấu chấm.
- Việc làm: đọc secret (cache), ký `v1.<eventId>.<ticketId>`, tạo PNG, lưu S3 với key `qr/<eventId>/<ticketId>.png`.
- Output: `{"qrKey": "qr/<eventId>/<ticketId>.png"}`. Lỗi: ném lỗi để register trả 500.
- Không ghi DynamoDB, không publish SNS. Gọi lại với cùng input cho cùng chữ ký và ghi đè cùng một key, nên an toàn khi retry.
- Lưu ý khi viết báo cáo: đề nêu "Lambda sinh QR (lưu S3, gửi link qua SNS email)". Việc gửi email vẫn thực hiện bằng Lambda và SNS, nhưng nằm ở bước sau khi vé đã ghi DB (mô-đun email dưới đây), để link trong email luôn mở được.

### Quy trình email dùng chung (mô-đun `ticket_mail`, dùng cho register và resend)

Đặt trong `lambdas/common/` của repo, đóng gói cùng từng Lambda cần dùng. Hướng dự kiến (phải kiểm chứng ở bài thử 3):

1. `ensure_subscription(email)`: gọi Subscribe với protocol `email`, endpoint là email đã chuẩn hóa, `FilterPolicy = {"email": ["<email>"]}`, `ReturnSubscriptionArn = true`; sau đó gọi `GetSubscriptionAttributes` và đọc `PendingConfirmation` để biết đã xác nhận hay chưa. Phương án dự phòng nếu cách trên không dùng được: duyệt `ListSubscriptionsByTopic` (có phân trang) và xem ARN của endpoint có là `PendingConfirmation` không.
2. `send_ticket(email, eventId, ticketId)`: chỉ publish khi subscription đã xác nhận, kèm message attribute `email` (String). Nội dung email gồm tên sự kiện và link `ticketUrl`, không chứa dữ liệu cá nhân khác.
3. Trả về một trong ba trạng thái: `PENDING_CONFIRMATION`, `PUBLISHED`, `FAILED`. Nếu pending thì không publish, vì thư gửi tới subscription chưa xác nhận sẽ mất.

### Quy tắc phía frontend

- Khóa nút đăng ký/gửi lại khi request đang chạy. Trang scanner tránh gửi nhiều request liên tiếp cho cùng lần quét.
- Scanner vẫn phải xử lý 409; khóa nút/quét phía frontend không thay thế conditional update trong DynamoDB.
- Khi đăng ký trả `PENDING_CONFIRMATION`, hiển thị link vé và hướng dẫn xác nhận SNS rồi nhấn gửi lại.
- Khi đăng ký trả `FAILED`, vẫn hiển thị link vé và thông báo email chưa được gửi.
- stats hiển thị rõ tổng vé, đã check-in, chưa check-in.
- Xử lý lỗi không theo envelope (403 key, 429) theo mục 2.4.
- Không commit secret, AWS credentials, presigned URL còn hiệu lực hoặc API key thật.

## 10. Kiểm thử nghiệm thu

| Tình huống | Kết quả mong đợi |
|---|---|
| Đăng ký hợp lệ | 201, `ticketId` và `ticketUrl`; QR mở được |
| Đăng ký cùng email hai lần | Có thể có hai vé, phù hợp phạm vi tối thiểu |
| Đăng ký thiếu tên/email | 400 INVALID_INPUT |
| Đăng ký sự kiện không tồn tại | 404 EVENT_NOT_FOUND |
| Lỗi khi sinh QR hoặc ghi S3 | 500; không có vé nào trong DynamoDB |
| Email chưa xác nhận SNS | 201 với `PENDING_CONFIRMATION`, không có thư vé; web vẫn có link vé; resend trả EMAIL_CONFIRMATION_REQUIRED |
| Email đã xác nhận SNS | 201 với `PUBLISHED`; chỉ email đó nhận thư, email khác không nhận |
| Hai email khác nhau, hai filter | Mỗi email chỉ nhận thư của mình |
| Publish/subscribe lỗi sau khi vé đã ghi | register vẫn trả vé, `emailDeliveryStatus = FAILED` |
| QR hợp lệ, đúng sự kiện, lần đầu | 200 CHECKED_IN |
| Quét lại cùng vé | 409, `checkedInAt` lần đầu giữ nguyên |
| Hai thiết bị check-in cùng vé đồng thời | Một 200, một 409 nếu cả hai request đến backend và không có lỗi khác |
| Sửa chữ ký hoặc mã vé trong QR | 403 INVALID_SIGNATURE nếu cấu trúc vẫn hợp lệ |
| QR đúng chữ ký nhưng khác sự kiện BTC chọn | 403 EVENT_MISMATCH |
| QR đúng chữ ký nhưng vé không có trong DB | 404 TICKET_NOT_FOUND |
| QR sai cấu trúc/version | 400 INVALID_INPUT |
| Gọi route BTC thiếu hoặc sai API key | 403 không có envelope; frontend báo nhập lại key, không báo lỗi QR |
| Gọi vượt throttle | 429 không có envelope; frontend báo thử lại sau |
| Sự kiện có 10 vé, 6 đã check-in | stats trả 10/6/4 |
| Sự kiện tồn tại nhưng chưa có vé | stats trả 0/0/0 |
| URL ảnh hết hạn | `GET /ticket` lại để nhận URL mới |

## 11. Các điểm phải chốt với B trước tuần 2

1. Xác nhận route events, ticket, resend và tên trường trong mục 6–8.
2. Kết quả bài thử SNS (bài thử 3), gồm ba việc: filter với hai email hoạt động đúng; `Subscribe` với `ReturnSubscriptionArn = true` rồi `GetSubscriptionAttributes` có cho biết được `PendingConfirmation` không (nếu không thì dùng `ListSubscriptionsByTopic`); gọi `Subscribe` lại với email đã có (đang pending hoặc đã xác nhận) cho kết quả gì và có gửi lại email xác nhận không. Ghi thêm thời hạn của subscription đang pending nếu quan sát được.
3. Chấp nhận hợp đồng generate-qr và mô-đun `ticket_mail` ở mục 9, và ai viết mô-đun (đặt trong `lambdas/common/`).
4. Domain CloudFront, API base URL, origin CORS thực tế và kết quả camera HTTPS.
5. Kết quả thử presigned URL qua thời điểm credentials hết hạn (bài thử 5); chốt `QR_DELIVERY_MODE` mặc định.
6. Khả năng cấu hình REST API, API key, usage plan, throttle và Gateway Responses trong Learner Lab.
7. Giới hạn resend phù hợp bản demo và con số throttle cho `/register`, `/resend`.

Đã giải quyết bằng thay đổi thứ tự ở mục 3 (so với v0.1): xử lý vé đã ghi nhưng QR chưa tạo được. Khi B đồng ý, cập nhật trạng thái mục 6–8, ghi ngày chốt và người xác nhận; giữ tài liệu đồng bộ với implementation khi có thay đổi.

## 12. Hạn chế đã biết (ghi trong báo cáo, không giấu)

- API key cho route BTC nằm trong trình duyệt nên chỉ là mức bảo vệ tối thiểu.
- Mọi Lambda dùng chung LabRole nên không áp dụng được quyền tối thiểu theo từng hàm.
- `POST /register` công khai và nhận email tùy ý, nên có thể bị dùng để làm hệ thống subscribe email của người khác vào topic và gây ra thư xác nhận SNS gửi tới họ. Biện pháp trong phạm vi tối thiểu: throttle ở stage, kiểm tra sự kiện tồn tại; chưa có CAPTCHA hay xác thực.
- `GET /ticket` và `POST /resend` dựa vào việc `eventId`/`ticketId` khó đoán; ai có link thì lấy được QR của vé đó.
- Chưa chống đăng ký trùng email, chưa ràng buộc thời gian check-in với thời gian sự kiện, chưa có xoay vòng khóa HMAC (QR `v1` không chứa `kid`).
- Gửi email phụ thuộc người dùng xác nhận subscription SNS (thư xác nhận hay vào spam); vì vậy link vé luôn được hiển thị trên web.
