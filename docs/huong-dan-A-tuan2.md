# EventQR — Hoàn thành phần A và ghép với phần B

Chuẩn bị ngày 19/10/2026. Theo lịch dự án đã sang tuần 3; tài liệu này giúp hoàn thành các đầu việc lõi của tuần 2 còn thiếu trước khi làm dashboard/alarm hoặc IaC.

**Phạm vi:** bốn Lambda `create-event`, `register`, `checkin`, `stats`, API Gateway và kiểm thử đầu-cuối. Dùng tài khoản Quang, `us-east-1`, `LabRole`. Giữ phần B đã triển khai. Không tạo IAM user/role/policy mới, không đổi secret HMAC đang sử dụng.

**Thực tế/giả định:** người dùng báo đã làm phần B đến bước 8. Trợ lý chưa xem Console, chưa xác minh mọi bài thử phần B đều PASS. Code A trong bộ này đã được kiểm thử cục bộ với AWS giả lập; chưa được triển khai lên lab trong phiên AI. Các ảnh kết quả thật và giờ sinh viên phải bổ sung sau khi thao tác.

## 0. Mở bộ mã và ghi lại cấu hình hiện có

1. Giải nén `EventQR_A_Week2_Kit.zip`, mở thư mục có `dist`, `lambdas`, `docs`, `tools`, `tests`.
2. Start Lab của tài khoản chính Quang. Mở AWS Console, chọn N. Virginia (`us-east-1`).
3. Xác nhận các tài nguyên sau, ghi tên/URL vào ghi chú cục bộ, không push credentials hoặc secret lên Git:

| Thành phần | Giá trị cần dùng |
|---|---|
| DynamoDB | `eventqr-events`, `eventqr-tickets` |
| Secrets Manager | `eventqr-hmac-key`, đang dùng cho Lambda sinh QR |
| Lambda B | `eventqr-generate-qr`, `eventqr-get-ticket`, `eventqr-resend`, `eventqr-web` |
| SNS | ARN của `eventqr-ticket-delivery` |
| Web | URL trang register đang mở được trên tài khoản chính |
| API | REST API `eventqr-api`, stage `v1` |
| IAM | `LabRole` có sẵn |

4. `WEB_BASE_URL` là địa chỉ thư mục web. Với phương án Lambda web:

```text
API_BASE_URL = https://<api-id>.execute-api.us-east-1.amazonaws.com/v1
WEB_BASE_URL = https://<api-id>.execute-api.us-east-1.amazonaws.com/v1/web
```

Lấy api-id thật từ API Gateway → APIs → eventqr-api → Stages → v1 → Invoke URL. Không nhập nguyên `<api-id>`. WEB_BASE_URL không thêm `register.html` hoặc `ticket.html`. Vì bạn đã làm phần web của B, dùng URL hiện có, không tạo API mới để lấy URL khác.

5. Nếu API/web chưa có thật, hoàn thành route GET `/web/{page}` và Deploy v1 bằng phần B trước khi test register có tạo link vé. Không dùng URL giả để ép test PASS.
6. Nếu Lambda nào cùng tên đã có mã thật mới hơn, tải/lưu mã hiện tại hoặc so sánh trước khi thay ZIP. Không xóa hàm để làm lại từ đầu.

## 1. Kiểm tra DynamoDB và secret

### 1.1. Hai bảng DynamoDB

Vào DynamoDB → Tables → chọn bảng → Overview/General information.

| Bảng | Partition key | Sort key | Capacity |
|---|---|---|---|
| eventqr-events | eventId, String | Không có | On-demand |
| eventqr-tickets | eventId, String | ticketId, String | On-demand |

- Đã đúng thì giữ nguyên dữ liệu.
- Nếu chưa có: Create table → nhập đúng key như bảng → Table settings/Customize settings → On-demand → tags `Project=EventQR`, `Owner=24110307DangDuyQuang` → Create table → chờ ACTIVE.
- Nếu bảng hiện có sai key schema, không xóa bảng đang dùng. Ghi vấn đề để xử lý trước khi triển khai; không thể đổi primary key bằng cách thêm thuộc tính item.
- Không cần secondary index cho các API tối thiểu này.

### 1.2. Secret HMAC

- Secrets Manager → tìm `eventqr-hmac-key` đang được B sử dụng.
- Dùng cùng secret đó cho register/checkin; không tạo khóa mới và không bật rotation giữa buổi test.
- Secret có JSON `kid` là chuỗi, `key` là 64 ký tự hex. Code chuyển bằng `bytes.fromhex`, giống module HMAC cũ của Quang và bộ QR B.
- Có thể chạy lại Lambda test-secret tuần 1 để xác nhận quyền/định dạng; kết quả chỉ hiện kid và thông báo, không hiện khóa.
- Chỉ khi toàn bộ môi trường thực sự chưa có secret mới phối hợp tạo trước phần QR. Không thay khóa để chữa lỗi INVALID_SIGNATURE của vé đã phát hành.

## 2. Quy trình tạo/cập nhật một Lambda

Thực hiện bốn lần theo bảng:

| Function name | ZIP trong dist | Memory | Timeout |
|---|---|---|---|
| eventqr-create-event | eventqr-create-event.zip | 128 MB | 10 giây |
| eventqr-register | eventqr-register.zip | 128 MB | 25 giây |
| eventqr-checkin | eventqr-checkin.zip | 128 MB | 10 giây |
| eventqr-stats | eventqr-stats.zip | 128 MB | 10 giây |

1. Lambda → Functions → mở hàm đã có, hoặc Create function → Author from scratch.
2. Function name theo bảng; Runtime Python 3.12 nếu được lab hỗ trợ; architecture x86_64.
3. Change default execution role → Use an existing role → **LabRole** → Create function. Không để mặc định tạo role mới.
4. Code → Upload from → .zip file → chọn ZIP tương ứng → Save. Nếu có thay đổi chưa deploy thì bấm Deploy.
5. Runtime settings → Edit → Handler: `lambda_function.lambda_handler`.
6. Configuration → General configuration → Memory/Timeout như bảng → Save.
7. Configuration → Permissions → Execution role là LabRole; không gắn Lambda vào VPC.
8. Configuration → Tags → Project/Owner cho hàm mới bạn tạo.
9. Environment variables theo từng mục dưới đây. Các ZIP có sẵn helper đúng vị trí gốc; không chỉ dán riêng lambda_function.py rồi bỏ thiếu module phụ.

## 3. Lambda tạo sự kiện — eventqr-create-event

### 3.1. Cấu hình

Upload ZIP theo mục 2, thêm environment variable:

```text
EVENTS_TABLE = eventqr-events
```

Nếu frontend gọi API khác origin thì thêm CORS_ORIGIN theo mục 8. Web/API cùng origin có thể để trống biến này.

### 3.2. Test

Lambda → Test → Create new event → tên `a-create-event` → Private nếu có lựa chọn:

```json
{
  "httpMethod": "POST",
  "body": "{\"name\":\"EventQR Demo\",\"startTime\":\"2026-10-25T08:00:00+07:00\",\"venue\":\"Hoi truong\"}"
}
```

1. Test, mong đợi statusCode **201**. Trong body có `ok=true`, `data.eventId`, `name`, `startTime`, `venue`, `createdAt`.
2. startTime được chuẩn hóa thành `2026-10-25T01:00:00Z` (08:00 giờ Việt Nam).
3. Copy **eventId backend vừa tạo**, lưu cục bộ để dùng cho mọi bước sau. Không dùng một UUID mẫu chưa được ghi vào bảng.
4. DynamoDB → Explore items → eventqr-events → tìm eventId vừa nhận, kiểm tra item tồn tại.
5. Test thiếu venue hoặc name rỗng: phải trả 400 INVALID_INPUT; không tạo item mới.
6. Test startTime thiếu múi giờ: phải trả 400. Ngày mẫu là ngày sự kiện giả lập, có thể thay cho phù hợp demo.

**Đạt:** sự kiện được tạo bởi Lambda, không phải nhập item tay; có eventId và item tương ứng.

Lưu ý Test trực tiếp trong Lambda không kiểm tra API key. Yêu cầu API key sẽ do API Gateway thực thi ở mục 7.

## 4. Lambda đăng ký vé — eventqr-register

### 4.1. Environment variables

| Key | Value |
|---|---|
| EVENTS_TABLE | eventqr-events |
| TICKETS_TABLE | eventqr-tickets |
| GENERATE_QR_FUNCTION | eventqr-generate-qr |
| SECRET_NAME | eventqr-hmac-key |
| SNS_TOPIC_ARN | ARN topic SNS đã tạo ở tài khoản chính |
| WEB_BASE_URL | URL thật đến `/v1/web` |

Register đọc kid từ cùng secret, vì vậy bản triển khai này cần SECRET_NAME trên register bên cạnh generate-qr/checkin. Không nhập giá trị khóa HMAC vào biến môi trường.

### 4.2. Test bằng email bạn kiểm soát

```json
{
  "httpMethod": "POST",
  "body": "{\"eventId\":\"THAY_EVENT_ID_VUA_TAO\",\"name\":\"Khach thu\",\"email\":\"THAY_EMAIL_CUA_BAN\"}"
}
```

Thay hai placeholder thật trong body trước khi Test. Giữ body là chuỗi JSON, không bỏ các dấu escape nếu copy ví dụ nguyên khối.

1. Test một lần. Mong đợi **201**, `data.ticketId`, `ticketUrl`, `status=ISSUED`, `emailDeliveryStatus`.
2. Copy link ticketUrl và ticketId để kiểm thử; không đưa link vé còn hiệu lực hoặc payload lên Git/chat công khai.
3. DynamoDB → Tickets → tìm đúng cặp eventId/ticketId, kiểm tra status=ISSUED, qrKey, email chuẩn hóa chữ thường, kid, createdAt.
4. S3 → bucket QR → object key đúng `qr/<eventId>/<ticketId>.png`.
5. Mở ticketUrl trên trình duyệt: trang vé của B phải lấy được ảnh QR từ GET /ticket.

### 4.3. Email mới: hệ thống tự Subscribe

- Register tự dùng `ticket_mail.send_ticket` để bảo đảm subscription và gắn filter email; người quản trị không thêm từng Gmail bằng tay.
- Email mới chưa confirmed: trả 201 với `PENDING_CONFIRMATION`; SNS gửi thư xác nhận. Khách bấm Confirm subscription, quay lại trang vé rồi bấm Gửi lại email vé.
- Email đã confirmed và filter đúng: `PUBLISHED` khi SNS chấp nhận publish. Phải kiểm tra hộp thư để xác nhận giao email thật.
- Nếu SNS lỗi: register vẫn **201 với FAILED**, vé và QR vẫn còn, link vé vẫn dùng được. Xử lý SNS rồi resend, không đăng ký lại chỉ để gửi email.
- Filter thay đổi có thể cần đến 15 phút để có hiệu lực. Chỉ test bằng email mình kiểm soát và dùng topic đã rà soát: subscription thử không có filter có thể nhận thư không dành cho nó.
- Module email trong bộ A giữ hợp đồng bộ B; bổ sung timeout ngắn cho SDK. Không bắt buộc thay Lambda resend đang chạy chỉ để triển khai A; khi đồng bộ Git, so sánh bản module đang dùng.

### 4.4. Thứ tự quan trọng và giới hạn

1. Validate → đọc Events → tạo ticketId.
2. Invoke generate-qr đồng bộ → kiểm tra FunctionError và qrKey.
3. PutItem Tickets có điều kiện không ghi đè vé.
4. Subscribe/publish SNS → trả 201 và link vé.

AWS Invoke trả HTTP 200 chưa đủ kết luận hàm con chạy thành công; code đã kiểm tra FunctionError riêng.

Nếu function/API timeout hoặc mất kết nối sau khi ghi, kết quả request có thể chưa rõ dù vé đã tồn tại. API v0.2 chưa có idempotency key cho register; không tự lặp POST liên tục. Xem CloudWatch và dữ liệu trước khi thử lại. Ảnh QR mồ côi sau lỗi ghi DB không tự trở thành vé hợp lệ.

## 5. Lambda check-in — eventqr-checkin

### 5.1. Cấu hình

Upload ZIP theo mục 2, thêm:

```text
EVENTS_TABLE = eventqr-events
TICKETS_TABLE = eventqr-tickets
SECRET_NAME = eventqr-hmac-key
```

Code nhận **qrPayload**, khớp frontend B và docs/api.md. Một số roadmap cũ viết payload, không dùng tên trường cũ đó.

### 5.2. Test đầu vào sai trước

```json
{
  "httpMethod": "POST",
  "body": "{\"eventId\":\"THAY_EVENT_ID_VUA_TAO\",\"qrPayload\":\"QR-GIA\"}"
}
```

Thay eventId thật; mong đợi **400 INVALID_INPUT**. Không thay status vé để tạo bài thử này.

### 5.3. Test vé thật

Cách dễ nhất là nối route ở mục 7 rồi dùng trang checkin.html của B với điện thoại (mục 9). Nếu muốn Test trực tiếp Lambda:

1. Dùng công cụ đọc QR trên thiết bị bạn kiểm soát để đọc PNG của **vé thử** thành chuỗi `v1.<eventId>.<ticketId>.<signature>`.
2. Dán chuỗi đó vào qrPayload của Test event Private. Không dán link ticket.html hoặc presigned URL vào qrPayload; backend cần nội dung bên trong QR.
3. Test lần đầu: 200 CHECKED_IN, có name và checkedInAt.
4. Test lại **đúng cùng payload**: 409 TICKET_ALREADY_CHECKED_IN, details.checkedInAt bằng lần đầu.
5. DynamoDB status thành CHECKED_IN, checkedInAt không bị đổi bởi lần thứ hai.
6. Đổi một ký tự hợp lệ ở giữa phần signature: 403 INVALID_SIGNATURE, không cập nhật dữ liệu.
7. Giữ payload hợp lệ nhưng đổi eventId BTC đang chọn sang một UUID khác: 403 EVENT_MISMATCH.

Không nhờ gửi khóa HMAC hoặc vé thật lên chat để sinh payload hộ. Vé sau khi check-in giữ nguyên trạng thái; muốn bài thử thành công mới thì đăng ký vé thử khác.

### 5.4. Vì sao chống trùng hoạt động

UpdateItem dùng điều kiện `attribute_exists(eventId) AND attribute_exists(ticketId) AND status=ISSUED` rồi đổi thành CHECKED_IN trong cùng thao tác ghi. Khi điều kiện thất bại, GetItem ConsistentRead giúp phân biệt vé không tồn tại và vé đã check-in. Không dùng quy trình đọc status rồi ghi vô điều kiện.

Hai lượt quét đồng thời phải chỉ có một lượt thành công. Bài mock hai luồng đã chạy, nhưng bài hai thiết bị trên AWS vẫn phải thực hiện và chụp kết quả thật.

## 6. Lambda thống kê — eventqr-stats

Upload ZIP theo mục 2, thêm:

```text
EVENTS_TABLE = eventqr-events
TICKETS_TABLE = eventqr-tickets
```

Test event:

```json
{
  "httpMethod": "GET",
  "pathParameters": {"eventId": "THAY_EVENT_ID_VUA_TAO"}
}
```

1. Thay đúng eventId thật; Test → 200.
2. Body có `totalTickets`, `checkedInTickets`, `notCheckedInTickets`.
3. Với một sự kiện mới có đúng một vé vừa check-in: mong đợi **1, 1, 0**. Nếu đã đăng ký nhiều lần, tổng vé phải tính đủ; không ép kết quả về 1 bằng cách xóa dữ liệu.
4. Sự kiện tồn tại chưa có vé: **0, 0, 0**.
5. UUID hợp lệ nhưng sự kiện không tồn tại: 404 EVENT_NOT_FOUND; ID sai định dạng: 400.
6. Code Query theo eventId và đọc hết LastEvaluatedKey, không Scan toàn bảng. Thống kê là kết quả lượt đọc, không phải snapshot giao dịch trong khi nhiều vé đang được cập nhật.

## 7. API Gateway: ghép bốn route A vào API đang có

API Gateway → REST API `eventqr-api` → Resources. Dùng cùng API/stage với B. Không xóa `/ticket`, `/resend`, `/web/{page}` đang hoạt động.

| Resource | Method | Lambda | API key required |
|---|---|---|---|
| /events | POST | eventqr-create-event | True |
| /register | POST | eventqr-register | False |
| /checkin | POST | eventqr-checkin | True |
| /stats/{eventId} | GET | eventqr-stats | True |

### 7.1. Tạo resource và integration

1. Chọn `/` → Create resource → nhập `events`, Create. Tương tự register/checkin/stats nếu chưa có.
2. Chọn `/stats` → Create resource → nhập `{eventId}`. Đây là path parameter, giữ dấu ngoặc nhọn.
3. Chọn resource cần method → Create method → Method type POST/GET theo bảng.
4. Integration type Lambda → **Lambda proxy integration ON** → Region us-east-1 → chọn đúng function → Create.
5. Console yêu cầu cho API Gateway invoke Lambda: chấp nhận thêm resource-based invoke permission cho hàm; đây không phải tạo IAM role/user. Nếu bị AccessDenied, ghi lỗi/action, không tạo IAM mới để vượt chặn.
6. Nếu method đã có: mở Integration request/Integration settings để kiểm tra function và proxy; dùng Edit thay vì tạo method trùng.
7. Method request → Edit → Authorization NONE cho cấu hình demo hiện tại, API key required theo bảng → Save. Không bật key cho OPTIONS hoặc register.
8. Deploy API → chọn stage v1 → Deploy. Sau mỗi thay đổi resource/method/integration phải redeploy API.

### 7.2. API key/usage plan — kiểm tra hoặc tạo khi chưa có

Bạn đã được hướng dẫn tạo key ở phần B. Có rồi thì kiểm tra lại liên kết, không tạo thêm key không cần thiết.

1. API Gateway → API keys → mở `eventqr-organizer-key`; nếu thiếu, Create API key → Auto generate → Enabled.
2. Usage plans → mở/tạo `eventqr-usage-plan`. Theo kế hoạch nhóm: Rate 50, Burst 100; quota có thể để chưa áp dụng trong bài thử. Đây là cấu hình dự kiến của demo, không phải giới hạn chi phí tuyệt đối.
3. Associated stages → Add stage → API eventqr-api, Stage v1.
4. Associated API keys → Add existing key → eventqr-organizer-key.
5. Kiểm tra API key source của REST API là HEADER nếu có mục này; gọi bằng header `x-api-key`.
6. Copy **giá trị API key**, không phải Key ID, để nhập vào trang BTC. Không ghi vào config.js, Git, ảnh hoặc chat.
7. Chờ cập nhật liên kết nếu vừa thêm, rồi kiểm thử method qua Invoke URL. Test trực tiếp Lambda không kiểm tra key; không dùng kết quả Lambda Test để kết luận Gateway đã được bảo vệ.

API key/usage plan chỉ là cơ chế quản lý sử dụng trong demo, không thay hệ thống xác thực/phân quyền hoàn chỉnh. Mọi tài nguyên mới vẫn dùng LabRole, không cần IAM mới.

## 8. Web config và CORS

### Cùng API Gateway cho web và API

- Web là `https://<api-id>.../v1/web/register.html`, API là `https://<api-id>.../v1/register`: cùng origin. Bộ frontend B có thể tự suy ra base URL nếu API_BASE_URL để trống.
- Kiểm tra CORS_ORIGIN không bắt buộc ở cấu hình này. Giữ WEB_BASE_URL trên register/resend cùng URL thư mục web thật.

### Khác origin (CloudFront hoặc localhost)

1. `frontend/config.js`: API_BASE_URL là URL API thật đến `/v1`; không phải URL Lambda, không thêm /web, không kèm key.
2. Trên bốn Lambda A đặt `CORS_ORIGIN` bằng origin của trang, ví dụ `https://<domain-cloudfront>` hoặc `http://localhost:8000`. Origin không có `/v1/web` hoặc tên file ở cuối. B get-ticket/resend cần cùng cấu hình.
3. Trên từng resource API: thêm OPTIONS, Authorization NONE, API key required False. Có thể tích hợp OPTIONS proxy cùng Lambda A vì code đã xử lý OPTIONS; cấu hình đúng invoke permission và redeploy.
4. Lambda A trả header Allow-Origin/Methods/Headers khi có CORS_ORIGIN. Với Lambda proxy, chỉ bấm Enable CORS ở Gateway chưa đủ nếu response thực không có header.
5. Gateway Responses DEFAULT_4XX và DEFAULT_5XX: thêm Access-Control-Allow-Origin bằng origin web (giá trị tĩnh trong console có thể cần dấu nháy đơn theo form), để 403/429 do Gateway sinh ra cũng đọc được từ trình duyệt. Kiểm tra lại response thật thay vì chỉ nhìn cấu hình đã Save.
6. Deploy lại v1. CORS không sửa được backend 500 hay thiếu route; xem Network/CloudWatch để tách nguyên nhân.

## 9. Kiểm thử đầu-cuối bằng giao diện B

Làm từng bước trên một sự kiện thử mới để dễ đếm.

1. Tạo sự kiện bằng Lambda create-event Test hoặc POST /events có API key. Copy eventId mới.
2. Mở `.../v1/web/register.html?e=<eventId_moi>`.
3. Nhập tên và Gmail bạn kiểm soát → Đăng ký một lần.
4. Kiểm tra trang hiện link vé; DynamoDB có item ISSUED; S3 có PNG.
5. Mở link vé trên máy tính, QR hiển thị.
6. Với email mới, bấm Confirm subscription trong thư SNS; quay lại trang vé → Gửi lại email vé; kiểm tra thư nhận được và link.
7. Mở `.../v1/web/checkin.html?e=<eventId_moi>` trên điện thoại Chrome/Safari qua HTTPS.
8. Nhập giá trị API key ở ô ban tổ chức, bấm bật camera → cho phép quyền. Quét QR đang mở trên máy tính.
9. Lần đầu phải 200; quét lại cùng QR phải 409, cùng checkedInAt.
10. Mở `.../v1/web/stats.html?e=<eventId_moi>`, nhập key → Xem thống kê. Nếu có đúng một vé thì 1/1/0; tổng luôn bằng đã check-in + chưa check-in.
11. Thử key sai/thiếu ở route BTC qua API thật: phải bị Gateway từ chối. Route register/ticket/resend/web không được tự yêu cầu key.
12. Khi log lỗi, chỉ gửi mã lỗi/timestamp/request ID đã bỏ thông tin nhạy cảm để gỡ; không gửi secret/key/payload/link vé còn dùng được.

Nếu B mới chỉ triển khai màn hình mà A chưa có backend, màn hình có thể từng báo lỗi API; hoàn thành bốn hàm A và route mới giúp kiểm chứng đầy đủ. Không cần upload lại toàn bộ frontend nếu URL/config đã đúng.

## 10. Thử REST API từ PowerShell (tùy chọn)

Không cần AWS Access Key để gọi API công khai/API key; chỉ cần base URL và API key demo. Các lệnh dưới gửi request thật, dùng email của bạn.

```powershell
$eventqrApiBase = (Read-Host "API base URL den /v1").TrimEnd('/')
$eventqrSecureKey = Read-Host "API key ban to chuc" -AsSecureString
$eventqrOrganizerKey = [System.Net.NetworkCredential]::new('', $eventqrSecureKey).Password
$eventqrHeaders = @{ 'x-api-key' = $eventqrOrganizerKey }
$eventqrCreateBody = @{ name='EventQR Demo'; startTime='2026-10-25T08:00:00+07:00'; venue='Hoi truong' } | ConvertTo-Json
$eventqrCreated = Invoke-RestMethod -Method Post -Uri "$eventqrApiBase/events" -Headers $eventqrHeaders -ContentType 'application/json' -Body $eventqrCreateBody
$eventqrEventId = $eventqrCreated.data.eventId
$eventqrEmail = Read-Host "Email thu do ban kiem soat"
$eventqrRegisterBody = @{ eventId=$eventqrEventId; name='Khach thu'; email=$eventqrEmail } | ConvertTo-Json
$eventqrRegistered = Invoke-RestMethod -Method Post -Uri "$eventqrApiBase/register" -ContentType 'application/json' -Body $eventqrRegisterBody
Start-Process $eventqrRegistered.data.ticketUrl
```

Lệnh register chỉ chạy một lần cho một vé; không chạy lại cả khối để tải lại ảnh. Dùng trang vé để refresh hoặc resend. Nếu lỗi HTTP làm PowerShell ném exception, đọc response và CloudWatch trước khi lặp request.

Sau khi check-in, lấy thống kê:

```powershell
Invoke-RestMethod -Method Get -Uri "$eventqrApiBase/stats/$eventqrEventId" -Headers $eventqrHeaders
```

Không in hoặc chụp `$eventqrHeaders`, giá trị API key hoặc link vé thật lên minh chứng công khai. Đóng PowerShell khi kết thúc phiên; không lưu chúng vào script/Git.

## 11. Checklist kết quả và lỗi thường gặp

| Hạng mục | Kết quả mong đợi | Minh chứng |
|---|---|---|
| Tạo sự kiện hợp lệ | 201 và item Events | Lambda/API response + DynamoDB |
| Tạo sự kiện thiếu dữ liệu | 400, không thêm item | Response |
| Đăng ký | 201, QR S3 và item Tickets | Response + S3 + DynamoDB |
| Email mới | PENDING_CONFIRMATION, có thư xác nhận | Response + SNS/email |
| Email đã xác nhận | Publish được, thư link vé thật | SNS + hộp thư |
| Check-in lần đầu | 200, CHECKED_IN, checkedInAt | Response + DynamoDB |
| Quét lại | 409, giữ timestamp cũ | Response |
| QR sửa chữ ký | 403 INVALID_SIGNATURE | Response |
| QR khác sự kiện | 403 EVENT_MISMATCH | Response |
| Thống kê | Tổng = đã vào + chưa vào | Response + trang stats |
| Thiếu key route BTC | 403 qua API thật | Response đã che key |

| Lỗi | Kiểm tra |
|---|---|
| Không import được a_common/ticket_mail/api_utils/hmac_utils | Upload đúng ZIP có sẵn; handler ở gốc là lambda_function.lambda_handler |
| CREATE_EVENT_FAILED / ResourceNotFound | EVENTS_TABLE đúng tên/tài khoản/Region, bảng ACTIVE |
| CONFIG_MISSING | Tên biến thiếu được ghi trong log; thêm đúng biến, không thêm khóa bí mật |
| REGISTER_FAILED / RuntimeError | Lambda con generate-qr đã deploy, function name đúng, LabRole InvokeFunction, kết quả qrKey đúng |
| REGISTER_FAILED / ValueError | WEB_BASE_URL thật, Secret JSON/key/kid đúng; không còn placeholder |
| Register 201 nhưng FAILED | Vé đã tạo; xem TICKET_EMAIL_FAILED, kiểm tra SNS/filter/quyền rồi resend |
| Register timeout | Timeout 25 giây, generate-qr 10 giây, quyền/dịch vụ con; kiểm tra DB trước khi đăng ký lại |
| Check-in INVALID_INPUT | Body phải có qrPayload, UUID đúng; không dán URL trang vé vào payload |
| Check-in INVALID_SIGNATURE | Khóa/bytes.fromhex/version/module có đồng nhất với B; không đổi secret của vé cũ |
| Check-in 404 | Chọn đúng sự kiện, cặp eventId/ticketId có trong bảng cùng tài khoản |
| Stats 0 dù có vé | eventId có khớp, TICKETS_TABLE đúng, từng vé là item ISSUED/CHECKED_IN |
| Stats 500 | Item status ngoài mô hình, quyền Query hoặc bảng sai; xem STATS_FAILED |
| Missing Authentication Token | URL/method/resource/stage; đã Deploy API sau thay đổi chưa |
| 502 | Handler, import module, response proxy; xem Lambda log |
| API key không được nhận | Value vs ID; key Enabled; Usage plan có đúng API v1; method required True; redeploy |

## 12. CloudWatch, worklog, Git và bàn giao

1. Sau khi gọi hàm, vào Monitor → View CloudWatch logs; hoặc CloudWatch → Log groups → `/aws/lambda/eventqr-...`.
2. Actions → Edit retention → 1 week (7 days) → Save; kiểm tra Details đã hiện 7 days. Gắn tag nếu quyền cho phép.
3. Lưu minh chứng vào `docs/evidence/week2/Quang/` cho mục tiêu tuần 2; ghi **ngày chạy thực tế 19/10**. Có thể tham chiếu từ báo cáo tuần 3 như việc hoàn thành tồn đọng, không lùi ngày thực hiện.
4. Worklog: nội dung thực tế, ai trực tiếp thao tác, số giờ thực tế, phần AI hỗ trợ. Nếu Long đang làm thay phần A, ghi người thực hiện là Long và ghi task thuộc phần A; không tự ghi giờ cho Quang chỉ vì dùng tài khoản Quang.
5. Bộ này có note bàn giao tại docs/HANDOFF-A-20261019.md. Source ở lambdas/ và tools/package_a.py. Dùng ZIP dist để upload; không bắt buộc đẩy ZIP lên Git.
6. So sánh diff trước khi ghép vào repo. Bộ A không yêu cầu thay code Lambda B đang chạy; shared module được đóng gói độc lập trong register. Không đè các file memory/plan/worklog nhóm vừa cập nhật bằng nguyên bản tham chiếu cũ.
7. Chỉ đánh dấu nhiệm vụ AWS `[x]` sau khi có kết quả thật. Giờ chưa xác nhận thì để trống/chưa xác nhận, không dùng giờ dự kiến hoặc thời gian AI sinh mã thay giờ sinh viên.
8. Cuối buổi lưu code/ảnh và kiểm tra ngân sách. Không xóa bảng/secret/bucket đang cần cho tích hợp chỉ để bắt đầu phần A. Quy định giữ/dọn serverless sau buổi vẫn cần áp dụng theo thầy và nhóm; không coi End Lab là đã dừng mọi chi phí.

## 13. Kiểm thử cục bộ đi kèm

Chạy bằng Python:

```text
py -m unittest discover -s tests -v
```

23 ca đã PASS trong phiên chuẩn bị, gồm ghép với mã generate-qr của B từ bộ trước; dịch vụ AWS giả lập. Fake conditional update dùng khóa để kiểm thử luồng xử lý đồng thời, không thay bài kiểm chứng hai máy trên DynamoDB thật. Không có browser/camera hoặc email thật được kiểm thử trong phiên AI.

Build lại ZIP nếu sửa source:

```text
py tools/package_a.py
```

Không cần cài Segno cho các Lambda A; thư viện sinh QR vẫn nằm trong Lambda B.

## Nguồn kỹ thuật

- Lambda synchronous Invoke và FunctionError: https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html
- DynamoDB conditional UpdateItem: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateItem.html
- DynamoDB read consistency: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html
- DynamoDB Query pagination: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html
- API Gateway API keys: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-setup-api-keys.html
- API Gateway usage plans: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-usage-plans.html
- CORS REST Lambda proxy: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html
- SNS Subscribe: https://docs.aws.amazon.com/sns/latest/api/API_Subscribe.html
- SNS filter policy: https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html
