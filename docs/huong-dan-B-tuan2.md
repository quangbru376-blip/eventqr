# EventQR — Hướng dẫn triển khai tuần 2 cho Long (B)

Người thực hiện: Trương Hoàng Long (24110273). Môi trường: tài khoản chính của Quang, Region `us-east-1`, execution role có sẵn `LabRole`. Hướng dẫn và code có AI hỗ trợ, chuẩn bị ngày 16/10/2026.

**Trạng thái của bộ này:** code đã được chuẩn bị và kiểm thử cục bộ; chưa triển khai AWS trong phiên chat. Kết quả AWS chỉ được ghi hoàn thành sau khi bạn chạy thật và có minh chứng. Không tự cộng giờ AI chạy vào worklog sinh viên.

## 0. Mở bộ mã và kiểm tra nền tảng

1. Giải nén `EventQR_B_Week2_Kit.zip`. Mở thư mục bên trong có `dist`, `frontend`, `lambdas`, `docs`.
2. Mở `docs/huong-dan-B-tuan2.md` bằng VS Code hoặc trình xem Markdown.
3. Đăng nhập phiên AWS Learner Lab của Quang đã được phép sử dụng; Start Lab nếu cần. Chọn `N. Virginia / us-east-1`.
4. Tất cả thao tác sau dùng tài khoản này. Không copy credentials hoặc khóa HMAC vào chat, code, ảnh hoặc Git.
5. Mở DynamoDB → Tables, xác nhận hai bảng: `eventqr-events` (partition key `eventId` String), `eventqr-tickets` (partition key `eventId` String, sort key `ticketId` String), capacity On-demand. Nếu thiếu, phối hợp Quang dựng theo phần A; không tạo bảng khác với tên gần giống.
6. Mở Secrets Manager, xác nhận có `eventqr-hmac-key`. Dùng secret hiện có; không đổi khóa trong khi đang có vé. Cấu trúc cần là JSON có `kid` chuỗi và `key` 64 ký tự hex. Không cần chụp hay gửi nội dung secret.
7. Mở IAM → Roles, kiểm tra có `LabRole`. Không tạo IAM user, role hoặc policy mới. Nếu thao tác AWS bị AccessDenied, lưu tên action/mã lỗi và dừng đúng bước đó; không cố chữa bằng IAM mới.
8. Mở API Gateway → APIs, kiểm tra API chung `eventqr-api` là **REST API, Regional**, stage `v1`. API của A đang có thì dùng tiếp; không xóa hoặc tạo lại.
9. Tài nguyên đã có và đúng cấu hình thì giữ nguyên. Bộ hướng dẫn không xóa hoặc reset tài nguyên của A.

Các file ZIP có sẵn trong `dist/`:

| File upload | Lambda |
|---|---|
| `eventqr-generate-qr.zip` | `eventqr-generate-qr` |
| `eventqr-get-ticket.zip` | `eventqr-get-ticket` |
| `eventqr-resend.zip` | `eventqr-resend` |
| `eventqr-web.zip` | `eventqr-web` |

Đã gói thư viện Segno 1.6.6 vào ZIP sinh QR. Không cần tạo layer hoặc cài Python trên máy nếu chỉ upload gói có sẵn. Các gói còn lại dùng SDK có trong Lambda Python runtime. Khi bảo trì dependencies, xem hướng dẫn AWS về đóng gói SDK trong mục nguồn.

## 1. S3: hai bucket trên tài khoản Quang

Thực hiện cho `eventqr-qr-<AccountID_Quang>` và `eventqr-web-<AccountID_Quang>`; thay phần trong dấu `<...>` bằng thông tin trên console của Quang, không dùng ID tài khoản Long.

1. S3 → Buckets. Nếu bucket đã có, mở bucket đó. Nếu chưa có: Create bucket → General purpose → Region `us-east-1` → nhập tên.
2. Giữ **Block all public access ON**; Object Ownership chọn ACLs disabled theo mặc định. Không bật static website hosting để phục vụ public.
3. Giữ mã hóa SSE-S3 mặc định. Nếu bucket hiện dùng cấu hình khác do Quang thiết lập, đối chiếu trước khi thay đổi; code mẫu sinh QR yêu cầu SSE-S3/AES256.
4. Thêm tags `Project=EventQR`, `Owner=24110273TruongHoangLong` cho tài nguyên mới do Long tạo. Với tài nguyên đã có, giữ Owner của người tạo và thống nhất quy ước nhóm.
5. Chưa bật event notification trên bucket QR: hàm sinh QR được gọi đồng bộ từ register, không phải từ sự kiện S3.
6. Chụp cấu hình private và tags. Không cần bucket policy public, không cần ACL public-read.

**Đạt:** có hai bucket đúng tài khoản/Region, private. Ghi tên bucket vào ghi chú cục bộ để nhập biến môi trường.

## 2. SNS: tạo topic và kiểm thử filter

1. SNS → Topics. Dùng topic `eventqr-ticket-delivery` đã có hoặc Create topic → Standard → tên `eventqr-ticket-delivery` → tags Project/Owner → Create.
2. Mở topic, copy ARN chỉ để nhập vào biến môi trường Lambda trên console. Không hardcode ARN trong Git.
3. Create subscription → Protocol Email → nhập email do bạn/Quang kiểm soát. Mở email SNS, bấm Confirm subscription. Làm tương tự cho email thứ hai.
4. Mỗi subscription → Edit → Subscription filter policy → chọn **Message attributes**. Với email thứ nhất nhập:

```json
{"email":["email-thu-nhat@example.com"]}
```

Thay bằng email thật viết thường; subscription thứ hai dùng đúng email thứ hai.

5. Save. Đợi filter có hiệu lực, AWS nêu có thể mất tới **15 phút**. Kiểm tra cả subscription cũ cùng topic: subscription không filter có thể nhận mọi vé; cần phối hợp người sở hữu sửa/xóa subscription thử dư, hoặc gắn filter phù hợp trước khi gửi vé thật.
6. Topic → Publish message. Subject `EventQR TEST 1`, body `Thu SNS email 1`. Message attributes: Name `email`, Type `String`, Value email thứ nhất. Publish.
7. Kiểm tra chỉ email thứ nhất nhận; làm ngược lại cho email thứ hai. Có thể thử value `unmatched@example.invalid`, không email nào được nhận.
8. Chụp trạng thái Confirmed, hai filter, thông điệp đã nhận và Message ID. `Publish` thành công chỉ cho biết SNS nhận thông điệp, không phải biên nhận giao email.

**Đạt:** hai email được lọc đúng. Module `ticket_mail.py` kèm theo từ chối publish nếu không xác minh được filter/confirmation; đây là cách tránh gửi vé khi cấu hình chưa đúng, không phải cơ chế bảo đảm filter đã hết thời gian propagation.

## 3. Sinh QR: Lambda eventqr-generate-qr

### 3.1. Tạo/cập nhật hàm

1. Lambda → Functions. Nếu có `eventqr-generate-qr`, kiểm tra và cập nhật hàm đó. Nếu thiếu: Create function → Author from scratch.
2. Function name `eventqr-generate-qr`; Runtime Python 3.12 nếu lab hỗ trợ; architecture x86_64.
3. Change default execution role → **Use an existing role → LabRole**. Create function.
4. Code → Upload from → `.zip file` → chọn `dist/eventqr-generate-qr.zip` → Save. Nếu trình soạn thảo báo thay đổi chưa deploy thì bấm Deploy.
5. Runtime settings → Edit → Handler `lambda_function.lambda_handler`.
6. Configuration → General configuration → Memory 128 MB, Timeout 10 seconds → Save.
7. Configuration → Permissions → Execution role phải là LabRole. Configuration → VPC: không gắn VPC.
8. Configuration → Environment variables → Edit → thêm:

| Key | Value |
|---|---|
| `SECRET_NAME` | `eventqr-hmac-key` |
| `QR_BUCKET` | Tên bucket QR của Quang |

9. Configuration → Tags: thêm Project/Owner nếu bạn tạo hàm mới.

### 3.2. Kiểm thử độc lập

Test → Create new event → tên `b-generate-qr` → dùng:

```json
{"eventId":"11111111-1111-4111-8111-111111111111","ticketId":"22222222-2222-4222-8222-222222222222"}
```

1. Test, mong đợi:

```json
{"qrKey":"qr/11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222.png"}
```

2. S3 → bucket QR → mở các prefix `qr/111.../` → chọn PNG → Download. Không mở S3 Object URL public; private thì AccessDenied là đúng.
3. Mở PNG trên máy, kiểm tra ảnh QR vuông rõ nét. Payload có HMAC, không có tên/email. Quét bằng trang check-in sau bước 7 để kiểm chứng chữ ký với backend A.
4. Chạy lại cùng input: phải trả cùng `qrKey`, ghi đè cùng object. Nếu bucket có versioning thì có thể tạo thêm version, không có thêm tên key khác.
5. Thử thay `eventId` thành `sai-id`: Lambda phải báo lỗi `QR_GENERATION_FAILED`, không ghi object sai. Đây là Lambda nội bộ nên không trả envelope HTTP.
6. Monitor → View CloudWatch logs → tìm `QR_CREATED`. Không log secret, payload QR hay link vé.

**Đạt:** có PNG thật trong S3 và log, upload lại không đổi đường dẫn key. Module dùng `bytes.fromhex(secret['key'])` giống bài thử của Quang; bên check-in phải dùng cùng cách chuyển khóa và cùng `hmac_utils.py`.

### 3.3. Bàn giao cho phần register của A

- Quang đặt `GENERATE_QR_FUNCTION=eventqr-generate-qr` trên hàm register.
- Invoke kiểu đồng bộ `RequestResponse`, input chỉ `{eventId,ticketId}`. Phải kiểm tra `FunctionError` và JSON output có `qrKey`; một lời gọi Invoke được AWS nhận chưa chứng minh hàm con thành công.
- Sau khi sinh QR thành công mới PutItem vé có điều kiện; email gửi sau bước ghi vé. Không đổi khóa HMAC đã có để chữa lỗi chữ ký.
- Hàm sinh QR không tạo item DynamoDB và không publish SNS. Quy trình email dùng chung được đề xuất ở bước 5; Quang cần đồng bộ khi viết register.

## 4. Xem vé: Lambda eventqr-get-ticket

### 4.1. Triển khai

Lặp lại cách tạo Lambda ở bước 3 với tên `eventqr-get-ticket`, ZIP `dist/eventqr-get-ticket.zip`, LabRole, Python 3.12, handler `lambda_function.lambda_handler`, Memory 128 MB, Timeout 10 giây. Thêm biến:

| Key | Value |
|---|---|
| `EVENTS_TABLE` | `eventqr-events` |
| `TICKETS_TABLE` | `eventqr-tickets` |
| `QR_BUCKET` | Tên bucket QR của Quang |
| `QR_DELIVERY_MODE` | `presigned` |
| `CORS_ORIGIN` | Có thể bỏ trống khi web/API cùng stage; xem bước 6 nếu khác origin |

`presigned` tạo URL mới 300 giây mỗi lần mở vé; `inline` đọc PNG và trả base64. Có thể đổi biến sang inline để thử phương án dự phòng, không cần sửa frontend.

### 4.2. Chuẩn bị dữ liệu thử nếu register chưa sẵn sàng

1. Ưu tiên tạo vé bằng register thật nếu A đã triển khai. Khi đó dùng eventId/ticketId thật của vé thử; không dùng các ID mẫu sau.
2. Nếu A chưa xong: DynamoDB → Explore items → bảng events → Create item → JSON view. Chọn chế độ DynamoDB JSON nếu console có lựa chọn; dùng nội dung `docs/week2-b-fixture-event.json`.
3. Làm tương tự cho bảng tickets, dùng `docs/week2-b-fixture-ticket.json`. **Thay email placeholder bằng email bạn kiểm soát, nhập tại console; không sửa email thật rồi push fixture lên Git.** `kid` phải khớp secret hiện tại; mặc định mẫu là `1`.
4. Chỉ dùng fixture trong trường hợp item mẫu chưa tồn tại. Nếu đã có item cùng key, kiểm tra và dùng tiếp; không ghi đè vé đã CHECKED_IN về ISSUED.
5. Các timestamp fixture là dữ liệu mẫu, không phải thời điểm triển khai thực tế. Nếu cần, thay bằng UTC lúc bạn chạy trên console.

Đây là dữ liệu kiểm thử thủ công, không được ghi rằng register đã chạy thành công chỉ vì đã có item fixture.

### 4.3. Test Lambda

```json
{"httpMethod":"GET","queryStringParameters":{"e":"11111111-1111-4111-8111-111111111111","t":"22222222-2222-4222-8222-222222222222"}}
```

- Có sự kiện, vé và PNG từ bước 3: `statusCode=200`; `body` là chuỗi JSON có `ok=true`, `data.qrImageUrl`.
- Tạm đổi `QR_DELIVERY_MODE=inline`, Save và test lại: có `data.qrImageDataUrl` bắt đầu `data:image/png;base64,`; sau đó chọn mode phù hợp.
- ID sai định dạng: 400 `INVALID_INPUT`.
- UUID hợp lệ nhưng không tồn tại: 404 đúng `EVENT_NOT_FOUND` hoặc `TICKET_NOT_FOUND`.
- Thử nội dung JSON test trong console không cần API Gateway. API sẽ nối ở bước 6.

**Đạt:** cả mode bạn chọn và lỗi đầu vào đều đúng. Không chụp toàn bộ presigned URL còn hiệu lực làm minh chứng công khai.

## 5. Gửi lại vé: Lambda eventqr-resend

### 5.1. Triển khai

Tạo/cập nhật Lambda `eventqr-resend` bằng ZIP `dist/eventqr-resend.zip`, cùng runtime/handler/LabRole/128 MB/10 giây. Thêm biến:

| Key | Value |
|---|---|
| `EVENTS_TABLE` | `eventqr-events` |
| `TICKETS_TABLE` | `eventqr-tickets` |
| `SNS_TOPIC_ARN` | ARN topic của Quang, lấy từ SNS console |
| `WEB_BASE_URL` | `https://<api-id>.execute-api.us-east-1.amazonaws.com/v1/web` |
| `CORS_ORIGIN` | Bỏ trống nếu cùng origin; khác origin thì đặt đúng origin web |

Chưa biết api-id thì hoàn thành bước 6 rồi quay lại nhập WEB_BASE_URL. Không dùng URL `/v1/web/index.html`, không thêm `ticket.html` vào biến này. Email được ghép thành `<WEB_BASE_URL>/ticket.html?e=...&t=...`.

### 5.2. Test

```json
{"httpMethod":"POST","body":"{\"eventId\":\"11111111-1111-4111-8111-111111111111\",\"ticketId\":\"22222222-2222-4222-8222-222222222222\"}"}
```

1. Dùng vé thử của bạn. Email lấy từ item DynamoDB, không từ client.
2. Nếu email đã subscribe, confirmed và filter đúng, Lambda trả 200 với `emailDeliveryStatus=PUBLISHED`. Mở hộp thư để xác minh nhận thư thật và mở link.
3. Nếu chưa subscribe, module tạo subscription với filter theo email. Lần đầu dự kiến trả 409 `EMAIL_CONFIRMATION_REQUIRED`. Xác nhận email SNS, đợi filter ổn định rồi Test lại.
4. Nếu trả 503, xem log `TICKET_EMAIL_FAILED`: kiểm tra ARN topic, quyền LabRole, trạng thái subscription, filter scope `MessageAttributes` và policy chính xác. Code cố ý từ chối publish khi filter thiếu/sai hoặc không xác minh được; không bỏ kiểm tra này để ép email đi.
5. Sau gửi lại, kiểm tra DynamoDB vẫn cùng ticketId, status và checkedInAt; không tạo vé mới và không reset check-in.
6. Đưa `lambdas/common/ticket_mail.py` và `api_utils.py` cho Quang đóng gói cùng register. Hàm `send_ticket(email,eventId,ticketId,event_name='EventQR')` trả `PENDING_CONFIRMATION`, `PUBLISHED` hoặc `FAILED`. Đây là mã chung được đề xuất, phải thống nhất với register của A trước khi thay thế mã A đang dùng.

**Đạt:** pending không publish, confirmed nhận đúng email, gửi lại giữ nguyên vé. Việc Subscribe/GetSubscriptionAttributes trong LabRole vẫn phải kiểm chứng thật; mock cục bộ không chứng minh được quyền trên lab.

## 6. Nối API Gateway và phục vụ web HTTPS

### 6.1. Upload giao diện

1. S3 → bucket web của Quang → Upload → Add files.
2. Chọn các file HTML, JS, CSS ở ngay thư mục `frontend/`; upload **từng file ở gốc bucket**, không tạo prefix `frontend/`. Có thể upload kèm file license.
3. Các file chính: index.html, register.html, ticket.html, checkin.html, stats.html, config.js, app.js, checkin.js, styles.css, html5-qrcode.min.js.
4. `config.js` mặc định để trống API_BASE_URL: frontend tự nhận stage từ URL `/v1/web/...` khi web và API nghiệp vụ cùng API Gateway. Nếu dùng API khác, điền base URL đầy đủ đến `/v1`, không có `/register` hoặc `/web` ở cuối. Chỉ có URL công khai, không chứa API key/credentials.

### 6.2. Lambda web

1. Tạo/cập nhật `eventqr-web`, LabRole, bằng `dist/eventqr-web.zip`; handler và runtime như trên.
2. Environment variable `WEB_BUCKET` = bucket web của Quang. Memory 128 MB, Timeout 10 giây.
3. Test:

```json
{"httpMethod":"GET","pathParameters":{"page":"register.html"}}
```

Phải trả 200, `Content-Type: text/html; charset=utf-8`. Đổi page `config.js`: 200, Content-Type JavaScript. Đổi page `secret.json`: 404.

4. Bản week1 chỉ cho index.html; ZIP mới mở rộng allowlist chính xác cho các trang/asset, không phục vụ một object tùy ý.

### 6.3. Resources và methods

API Gateway → `eventqr-api` → Resources. Nếu API chưa có, phối hợp Quang tạo **REST API / Regional**; dùng chung API cho cả web và nghiệp vụ để đơn giản hóa cấu hình.

| Resource | Method | Lambda | API key required |
|---|---|---|---|
| `/web/{page}` | GET | eventqr-web | False |
| `/ticket` | GET | eventqr-get-ticket | False |
| `/resend` | POST | eventqr-resend | False |
| `/register` | POST | eventqr-register (A) | False |
| `/events` | POST | eventqr-create-event (A) | True khi API key/usage plan sẵn sàng |
| `/checkin` | POST | eventqr-checkin (A) | True khi API key/usage plan sẵn sàng |
| `/stats/{eventId}` | GET | eventqr-stats (A) | True khi API key/usage plan sẵn sàng |

Không tạo route cho generate-qr. Tổng là 6 route nghiệp vụ và 1 route web.

Cách tạo một method:

1. Chọn resource cha → Create resource. `/web/{page}` tạo `web` dưới root rồi `{page}` dưới web; stats tương tự với `{eventId}`. Những resource đã có thì dùng tiếp.
2. Chọn resource → Create method → chọn GET/POST theo bảng.
3. Integration type Lambda function → **Lambda proxy integration ON** → Lambda Region us-east-1 → chọn đúng hàm → Create/Save.
4. Cho phép console thêm resource-based invoke permission cho API Gateway gọi Lambda. Đây không phải tạo IAM role mới. Nếu bị chặn, ghi lỗi và phối hợp Quang/thầy; không đổi sang role mới.
5. Method request: Authorization NONE cho cấu hình demo hiện tại; API key required theo bảng. API key không phải cơ chế đăng nhập an toàn; không nhúng key vào frontend.
6. Deploy API → stage `v1` → Deploy. Đã có stage thì chọn lại stage đó.
7. Stages → v1 → copy Invoke URL, mở:

```text
https://<api-id>.execute-api.us-east-1.amazonaws.com/v1/web/register.html
```

8. Quay lại resend và register, đặt WEB_BASE_URL đúng `.../v1/web`.

Nếu A chưa triển khai register/checkin/stats, B vẫn kiểm thử get-ticket và resend bằng fixture. Chưa được ghi luồng đầu-cuối đã hoàn thành.

### 6.4. Khi web và API khác origin hoặc test localhost

Web/API cùng origin thì trình duyệt không cần CORS. Nếu khác origin:

1. Origin chỉ gồm `https://host` (hoặc `http://localhost:8000`), không có `/v1/web` ở cuối.
2. Đặt `CORS_ORIGIN` trên get-ticket/resend bằng đúng origin của web; các Lambda A cần trả header tương tự, kể cả phản hồi lỗi.
3. Tạo OPTIONS trên các resource được frontend gọi, Authorization NONE, API key required False. Có thể dùng Enable CORS của console với Allow-Headers `Content-Type,x-api-key`, Allow-Methods `GET,POST,OPTIONS`, Allow-Origin đúng origin.
4. Với Lambda proxy, header CORS của GET/POST do Lambda trả; không chỉ dựa vào nút Enable CORS.
5. Gateway Responses DEFAULT_4XX/DEFAULT_5XX cũng cần Access-Control-Allow-Origin cho 403/429 do Gateway sinh ra. Không dùng `*` để chữa vấn đề route/private bucket.
6. Deploy API lại. Mở F12 → Network để kiểm tra OPTIONS và GET/POST. Không chụp API key hoặc link vé thật trong Network.

## 7. Kiểm thử lần lượt bốn trang

### register.html

1. Mở `.../v1/web/register.html?e=<eventId_thu>`.
2. Nhập họ tên và email kiểm soát được, bấm Đăng ký một lần.
3. Có link vé ngay sau thành công. Nếu pending thì hiển thị yêu cầu xác nhận email; nếu gửi email lỗi vẫn có link vé.
4. Kiểm tra DynamoDB có vé và S3 có ảnh. A chịu trách nhiệm backend register; lỗi register chưa deploy không phải lỗi form của B.

### ticket.html

1. Dùng link register trả về hoặc `.../v1/web/ticket.html?e=<eventId>&t=<ticketId>` của fixture.
2. QR hiện rõ. Bấm Tải lại ảnh QR: gọi GET /ticket, không sinh vé mới.
3. Xác nhận email SNS rồi bấm Gửi lại email vé. Kiểm tra hộp thư và link. Nếu vừa sửa filter, chờ tối đa 15 phút trước khi kết luận lỗi.
4. Sửa t sang UUID không tồn tại: trang phải báo vé không tồn tại, không giữ ảnh cũ.

### checkin.html

1. Xác nhận API checkin của A dùng đúng payload field `qrPayload` (không phải `payload`) và cùng secret/signature.
2. API key/usage plan do A chuẩn bị. Nhập key vào ô password của trang; key chỉ dùng trong phiên, không lưu trong config hoặc localStorage.
3. Mở trang trên **điện thoại thật qua HTTPS**, nhập eventId đang kiểm vé và key. Mở vé trên màn hình máy tính để điện thoại quét; một điện thoại không thể đồng thời dùng camera sau để quét QR đang hiển thị trên chính màn hình của nó.
4. Bấm Bật camera, cho phép quyền. Đưa QR vào khung; sau một lượt camera dừng và trang gửi một request.
5. Lần đầu 200: hiện tên và thời gian. Bấm Quét vé tiếp, quét lại: 409 và thời gian check-in đầu tiên.
6. Trong F12/Network trên máy tính có thể kiểm tra header x-api-key khi phát triển; không chụp hoặc đưa key lên Git. Backend DynamoDB có điều kiện mới là lớp chống trùng; frontend khóa nút chỉ tránh gửi lặp ngoài ý muốn.
7. Nếu camera lỗi: HTTPS, quyền trang, app khác đang chiếm camera, file html5-qrcode.min.js có tải 200 không. Không dùng URL S3 HTTP hoặc browser nhúng trong app chat để kết luận camera không hoạt động.

### stats.html

1. Nhập cùng eventId và API key → Xem thống kê.
2. Tổng vé = đã check-in + chưa check-in. Với fixture, thống kê sẽ tính cả vé thử đó.
3. Sau check-in quay lại refresh để thấy số đã check-in tăng.
4. Thử sai API key: có thông báo bị từ chối; không giữ số liệu cũ như dữ liệu mới. Không khẳng định đây là hệ thống phân quyền đăng nhập hoàn chỉnh.

## 8. CloudWatch và ba tồn đọng tuần 1

### Log retention và tags

1. Gọi từng Lambda ít nhất một lần để sinh log group.
2. CloudWatch → Logs → Log groups → chọn từng `/aws/lambda/eventqr-...` → Actions → Edit retention setting → **1 week (7 days)** → Save.
3. Kiểm tra ở Log group details phải hiện 7 days rồi chụp ảnh. Hộp thoại đang chọn 7 days chưa chứng minh đã Save.
4. Tags → Manage tags → Project/Owner nếu quyền cho phép. AccessDenied thì lưu minh chứng, không sửa IAM.
5. Mở log stream mới nhất, filter `QR_CREATED` hoặc `WEB_PAGE_SERVED`. Dashboard và hai alarm thuộc tuần 3; chưa ghi chúng đã xong trong tuần 2.

### Presigned URL

1. Link thử từ 09–10/10 đến hôm nay 16/10 đã quá TTL 6 giờ; lỗi của link đó lúc này không phân biệt được do TTL hay credentials. Ghi đúng giới hạn này.
2. Nếu cần chạy bài thử mới, upload một ảnh thử private. AWS CLI phải dùng credentials tạm của Quang và profile cục bộ đúng tài khoản; không dùng profile cũ của Long. Kiểm tra bằng `aws sts get-caller-identity --profile eventqr-main --region us-east-1`, không đưa credentials lên chat.
3. Thử TTL 60 giây để chứng minh hết hạn theo TTL, rồi thử TTL dài qua phiên lab nếu còn cần kiểm chứng credentials. Không tạo lại link giữa các lượt probe.

Ví dụ PowerShell (thay tên bucket thực tế):

```powershell
New-Item -ItemType Directory -Force local
aws s3 presign "s3://<bucket-qr-cua-Quang>/test.png" --expires-in 60 --profile eventqr-main --region us-east-1 | Set-Content -Encoding ascii local/presigned-short.txt
py tools/probe_presigned.py local/presigned-short.txt
```

Đợi trên 60 giây rồi chạy lại đúng lệnh probe. Thử dài dùng `--expires-in 21600` và file khác. End Lab không chứng minh credentials hết hiệu lực ngay; `ExpiredToken` trước TTL là bằng chứng cụ thể hơn. Không xóa object/đổi policy giữa bài thử. Thư mục `local/` không đưa lên Git.

4. URL ký bằng credentials tạm bị giới hạn bởi thời hạn credentials là hành vi AWS đã tài liệu hóa. Kết quả xấu với link 6 giờ không tự động chứng minh GET /ticket tạo URL mới 300 giây bị hỏng. Kiểm thử mode sử dụng thật; inline là lựa chọn dự phòng có sẵn.

### Camera điện thoại

Hoàn thành bằng bài thử checkin ở bước 7. Ảnh camera máy tính không thay thế ảnh/video điện thoại thật; bật được camera cũng chưa chứng minh đã giải mã QR và check-in.

## 9. CloudFront/IaC trong kế hoạch: kiểm chứng có điều kiện

### CloudFront

- CloudFront không bắt buộc trong danh sách dịch vụ đề bài. Luồng Lambda web + API Gateway HTTPS là phương án hiện có.
- Lỗi OAC/OAI bạn gặp ở tài khoản Long không tự chứng minh tài khoản Quang cũng bị chặn. Nếu kế hoạch nhóm yêu cầu thử tài khoản chính, chỉ thử tối thiểu khi core đã chạy.
- Nếu tiếp tục gặp AccessDenied ở OAC/OAI trên tài khoản Quang, lưu ảnh và dừng bài thử đó; không bật public bucket hay thay đổi IAM để vượt chặn. Giữ web HTTPS hiện tại, cập nhật kiến trúc đúng thực tế.
- Chưa có bài thử CloudFront thành công trong phiên chuẩn bị code này. Không ghi CloudFront đã hoàn tất.

### CloudFormation tối thiểu (tùy chọn sau khi core đã chạy)

1. File `infra/probe-labrole.yaml` chỉ tạo 1 bucket private trống và 1 Lambda thử; không có AWS::IAM::*.
2. Console IAM → Roles → LabRole → copy ARN vào **tham số trên console** của stack, không vào mã Git.
3. CloudFormation → Create stack → With new resources (standard) → Template is ready → Upload template file → chọn file probe.
4. Stack name `eventqr-iac-probe`, tham số ExistingLabRoleArn là ARN LabRole hiện có, Owner theo tên Long. Không chọn tạo role mới hoặc cấp policy mới.
5. Giữ các cấu hình khác mặc định, xem lại changes → Create stack. Nếu có CREATE_COMPLETE, test Lambda `eventqr-iac-probe` và lưu ảnh. Nếu AccessDenied thì ghi action/error và dùng checklist triển khai thủ công.
6. Probe này không thuộc hạ tầng demo: sau khi chụp đủ minh chứng, chỉ xóa stack probe bằng CloudFormation → chọn đúng `eventqr-iac-probe` → Delete. Bucket probe để trống; không dùng để chứa dữ liệu dự án. Không xóa stack hoặc bucket thật của nhóm.

Đây là bài thử được đề xuất, chưa kiểm chứng quyền CloudFormation/PassRole trong Learner Lab. Có thể bỏ qua nếu chưa hoàn thành luồng đăng ký/check-in.

## 10. Git, minh chứng, worklog và bàn giao

1. Lưu ảnh vào `docs/evidence/week2/Long/`: buckets/tags, SNS filters + email, Lambda QR test, PNG trong S3, get-ticket, resend pending/confirmed, web bốn trang, camera điện thoại, log retention đã Save, E2E 200/409.
2. Ảnh AWS theo đề cần Account ID, Region, thời gian; không hiển thị secret/credentials/API key hoặc link vé còn dùng được. Các ID thật dùng cho triển khai chỉ giữ ở môi trường/console, không hardcode vào source.
3. Bảng nghiệm thu của bạn ghi điều đã làm thật, ví dụ: `Sinh QR trên Lambda → PNG có ở S3 → PASS`, `resend pending → 409, không gửi vé → PASS`. Thời gian từ worklog thực tế, không từ số giờ dự trù của plan.
4. Copy các file mã trong bộ kit vào đúng thư mục repo đang làm của bạn; xem diff trước, đặc biệt `ticket_mail.py`, `api_utils.py`, web Lambda và config.js. Đồng bộ với Quang để không đè code A vừa sửa.
5. Gói dist là sản phẩm build để upload AWS; giữ ngoài Git nếu .gitignore loại *.zip. Git nên chứa source, requirements pin version, hướng dẫn build, thư viện web kèm license và checklist. Nếu cần build lại: `py -m pip download --no-deps segno==1.6.6 -d local` rồi `py tools/package_b_week2.py --segno-wheel local/segno-1.6.6-py3-none-any.whl`.
6. Kiểm tra `.gitignore` có `local/`, `.aws/`, `.env`, `__pycache__/`, `dist/`; không thêm key thật. Dùng `git status`, `git diff`, rồi stage đúng file cần commit. Không push file ZIP, credentials hoặc config chứa key.
7. Worklog ghi: AI hỗ trợ code mẫu, hướng dẫn, mock tests; sinh viên thực hiện deploy, test AWS, ghi nhận lỗi và kết quả. Mã chuẩn bị không có nghĩa hạ tầng đã chạy.
8. Sau khi chạy thật, cập nhật `docs/plan.md` và Mục 14–15 của project-memory; chưa đạt thì giữ pending. Bộ kit có note bàn giao riêng, không tự đánh dấu các đầu việc AWS đã hoàn thành.
9. Cuối buổi lưu code, ảnh và ngân sách. Không xóa nền tảng EventQR đang dùng chỉ vì kết thúc hướng dẫn; áp dụng yêu cầu dọn tài nguyên với thầy và nhóm. Việc giữ serverless giữa các buổi vẫn cần thống nhất, không tự diễn giải là đã được miễn yêu cầu.

## 11. Bảng lỗi thường gặp

| Hiện tượng | Kiểm tra |
|---|---|
| `No module named segno` | Upload ZIP generate-qr có sẵn, không chỉ dán lambda_function.py |
| `Unable to import module` / thiếu api_utils | Handler phải lambda_function.lambda_handler; dùng đúng ZIP với helper ở gốc |
| QR_GENERATION_FAILED | CloudWatch QR_CREATE_FAILED: SECRET_NAME, QR_BUCKET, key hex, quyền LabRole |
| QR quét được nhưng INVALID_SIGNATURE | Cùng secret, cùng bytes.fromhex, cùng module HMAC ở A/B; đừng đổi secret bừa |
| get-ticket 404 | Item fixture/real có đúng eventId + ticketId, cùng Region/tài khoản không |
| get-ticket 500 | qrKey lưu trong vé đúng đường dẫn; ảnh S3 tồn tại; QR_DELIVERY_MODE đúng |
| resend 409 | Xác nhận email SNS rồi thử lại |
| resend 503 | ARN topic, quyền đọc subscription/publish, filter, scope và propagation; xem mã lỗi an toàn trong log |
| Link email mở 404 | WEB_BASE_URL đúng đến /v1/web; có ticket.html ở bucket và allowlist |
| Missing Authentication Token | Sai method/URL/resource, chưa Deploy API; root /v1 không có trang chủ |
| Trang trắng, JS không chạy | Upload đủ app.js/config.js/styles.css; Content-Type JS đúng; xem Network 404 |
| API 502 | Proxy response đúng format; handler/import/environment variables; xem CloudWatch |
| Camera chạy nhưng không quét | Có html5-qrcode.min.js; thử QR trên màn hình khác, ánh sáng/góc chụp |
| Camera không có quyền | HTTPS, quyền trình duyệt, ứng dụng khác, mở Chrome/Safari trực tiếp |
| 403 từ Gateway | API key/usage plan/resource/deployment; không tự kết luận mọi 403 là sai key |

## Nguồn kỹ thuật

- AWS Lambda Python ZIP: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
- API Gateway Lambda proxy: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
- CORS REST API: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html
- SNS filter propagation: https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html
- SNS Subscribe: https://docs.aws.amazon.com/sns/latest/api/API_Subscribe.html
- SNS GetSubscriptionAttributes: https://docs.aws.amazon.com/sns/latest/api/API_GetSubscriptionAttributes.html
- S3 presigned URL lifetime: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
- API key limitations: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
- Segno PNG: https://segno.readthedocs.io/en/stable/serializers.html
- Html5Qrcode: https://scanapp.org/html5-qrcode-docs/docs/intro
