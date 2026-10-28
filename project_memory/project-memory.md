# MEMORY DỰ ÁN — EventQR (Cloud, nhóm Domain Apps)

Cập nhật lần cuối: thứ Tư 28/10/2026 (giờ Việt Nam).
Tài liệu hướng dẫn cách đọc memory và ghi nhận thao tác của agent: xem [agent.md](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/agent.md).
Kế hoạch chi tiết 4 tuần dạng checklist: xem [roadmap.md](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/roadmap.md).

Trước khi dùng, hãy kiểm tra mục 14 (trạng thái hiện tại). Không bao giờ ghi vào file này: khóa HMAC, Access Key, Secret Key, session token, mật khẩu, Account ID, API key thật, link vé thật.

## 0. Cách trợ lý nên làm việc với người dùng

- Trả lời bằng tiếng Việt, văn bản thuần (không dùng thẻ widget từng bước, không đồ họa không cần thiết), thẳng thắn, phản biện trung thực, không tô vẽ hay chỉ khen. Người dùng đã yêu cầu rõ phải phản biện.
- Phân biệt rõ điều đã kiểm chứng với điều chưa kiểm chứng, nhất là về giới hạn của AWS Learner Lab. Không đoán yêu cầu của giảng viên; việc gì chưa có thông tin thì nói rõ và đề xuất câu hỏi gửi thầy.
- Hướng dẫn thao tác trên AWS Console theo từng bước, đúng tên mục; nếu người dùng thấy giao diện khác thì hỏi tên mục họ đang thấy.
- Người dùng giữ tài khoản chính. Kế hoạch giữ trong chat; người dùng sẽ yêu cầu xuất file khi cần.
- Mọi sản phẩm AI hỗ trợ phải được ghi nhận trong worklog theo yêu cầu của đề.

## 1. Đề tài (nguyên văn từ đề)

Hệ thống quản lý sự kiện và check-in bằng QR code (Nhóm: Domain Apps). Môn Cloud, Đợt 1, 2026–2027. GVHD: Huỳnh Xuân Phụng.

Xây dựng hệ thống đăng ký sự kiện, phát hành vé QR và check-in tại cổng.

Sản phẩm dự kiến: API đăng ký; Lambda sinh QR (lưu S3, gửi link qua SNS email); trang check-in quét QR (camera web) gọi API; DynamoDB chống check-in trùng; thống kê.

Yêu cầu riêng: Dịch vụ: API Gateway, Lambda, DynamoDB, S3, SNS. QR chứa mã ký HMAC (khóa trong Secrets Manager).

Kế hoạch 4 tuần (mỗi SV ≥ 8 giờ/tuần):
- Tuần 1: tìm hiểu dịch vụ, thiết kế kiến trúc, vẽ sơ đồ, dựng nền tảng (VPC/IAM LabRole/S3...), gắn tag.
- Tuần 2: triển khai các chức năng lõi trên AWS, kiểm thử từng thành phần.
- Tuần 3: tích hợp, bảo mật, giám sát (CloudWatch), tự động hóa/IaC nếu có.
- Tuần 4: kiểm thử tổng thể, tối ưu chi phí, dọn dẹp tài nguyên, viết báo cáo và demo.

Yêu cầu chung:
- Nhóm tối đa 2 SV; hoàn thành trong 4 tuần; nộp nhật ký công việc (worklog) hằng tuần ghi rõ phân công và số giờ của từng SV.
- Được dùng LLM/AI (ChatGPT, Claude, Amazon Q Developer...) để tham khảo, sinh mã, gỡ lỗi; nhưng mọi tài nguyên phải được triển khai và chạy thật trên AWS Learner Lab. Ghi rõ phần nào có AI hỗ trợ; SV phải giải thích được mọi cấu hình/mã nguồn khi vấn đáp.
- Chỉ dùng Region us-east-1/us-west-2; dùng LabRole/LabInstanceProfile (không tạo IAM user/role); EC2 chỉ loại nano→large, ≤ 9 instance và ≤ 32 vCPU chạy đồng thời mỗi Region; EBS ≤ 100 GB (gp2/gp3).
- Gắn tag Project/Owner cho tài nguyên; dừng/xóa tài nguyên sau mỗi buổi; báo cáo chi phí sử dụng cuối kỳ.
- Minh chứng: ảnh chụp console/CLI (có Account ID, Region, thời gian), mã nguồn/template trên Git, báo cáo + sơ đồ kiến trúc, video demo ≤ 10 phút.

Lưu ý về quy định "dừng/xóa tài nguyên sau mỗi buổi": đề viết "sau mỗi buổi" (mỗi buổi làm việc), là "dừng hoặc xóa", không bắt buộc xóa hết. Việc giữ tài nguyên serverless giữa các buổi có được chấp nhận hay không chưa được thầy xác nhận (xem mục 12). Nếu thầy bắt xóa sau mỗi buổi thì đóng gói SAM/CloudFormation sớm và có script nạp dữ liệu mẫu.

## 2. Bối cảnh người dùng và nhóm

- Sinh viên đại học ở Việt Nam. Nhóm 2 người đã chốt, trình độ ngang nhau:
  + **Đặng Duy Quang (MSSV: 24110307)** — Vai trò **A** (Lead, phụ trách vé & dữ liệu: DynamoDB, Secrets Manager, HMAC, `create-event`, `register`, `checkin`, `stats`).
  + **Trương Hoàng Long (MSSV: 24110273)** — Vai trò **B** (Phụ trách gửi vé & giao diện: S3, SNS, CloudFront, CloudWatch, `generate-qr`, `get-ticket`, `resend`, frontend web).
- Mỗi người có một tài khoản Learner Lab riêng, ngân sách 50 USD mỗi tài khoản. Hai tài khoản không liên kết được với nhau và tài nguyên không tự chia sẻ cho nhau.
- **Tài khoản của Quang là tài khoản chính** (chạy hệ thống cuối, quay demo).
- **Cách ghép hai tài khoản:** 
  + Mọi mã nguồn nằm trên Git (`lambdas/<tên-hàm>/`). Repo GitHub hiện đang là **public**.
  + Mỗi người viết và test độc lập trên tài khoản riêng.
  + **Từ Thứ 4 (14/10), Quang deploy mã của Long (`generate-qr`, rồi `get-ticket`, `resend`) vào tài khoản của Quang** để ghép với `register`, `checkin`, `stats`. Hệ thống đầu-cuối chạy trong **một tài khoản duy nhất** ngay từ Tuần 2.
  + Long có một secret HMAC thử riêng trong tài khoản của mình để test `generate-qr`.
  + Thao tác console trên tài khoản Quang: Quang thao tác, Long hỗ trợ hướng dẫn qua chia sẻ màn hình. Không chia sẻ credentials.
  + Frontend dùng `config.js` trỏ về API Gateway của Quang. Khi cho Long thử, dùng **API key tạm** (xóa sau Tuần 2).
- Mốc thời gian: 4 tuần tính từ 05/10/2026. Tuần 1: 05–11/10 (xong, còn 3 tồn đọng); tuần 2: 12–18/10 (đang thực hiện); tuần 3: 19–25/10; tuần 4: 26/10–01/11.
- Mỗi người dành từ 8 giờ trở lên mỗi tuần (kế hoạch dự trù khoảng 11–12 giờ mỗi tuần).
- Quy định nộp bài: Báo cáo nộp **không đính kèm file**, nội dung và link minh chứng nằm trên GitHub.

## 3. Các quyết định đã chốt

1. Gửi vé qua SNS theo phương án A: lúc đăng ký, subscribe email người dùng vào SNS kèm filter policy theo email; người dùng bấm xác nhận một lần rồi nhận link vé. Link vé luôn được hiển thị trên web sau khi đăng ký (email chỉ là kênh phụ).
2. Trang web host trên AWS qua CloudFront (HTTPS) với origin là S3 web tĩnh, vì camera trình duyệt chỉ chạy trên HTTPS hoặc localhost. Bám sát thiết kế ban đầu; nếu CloudFront gặp trở ngại OAC thì giữ giải pháp dự phòng Lambda web + API Gateway.
3. Dịch vụ ngoài danh sách đề: tối thiểu, chỉ thêm CloudFront, CloudWatch, và SAM/CloudFormation nếu kịp.
4. Công nghệ: Lambda Python; frontend HTML/JS thuần kèm một thư viện quét QR; mã trên GitHub (repo `eventqr`, public); làm tay trên console trước rồi đóng gói IaC ở tuần 3 nếu còn thời gian.
5. Region duy nhất: us-east-1. Tag mọi tài nguyên hỗ trợ tag: `Project=EventQR`, `Owner=<tên người tạo>` (khóa phân biệt hoa thường, giá trị Project giống hệt nhau).
6. Không đặt Lambda vào VPC (sẽ mất đường ra SNS, Secrets Manager, DynamoDB trừ khi có NAT Gateway hoặc VPC endpoint; NAT Gateway tính phí theo giờ, đáng kể so với 50 USD). Chụp VPC mặc định và giải thích trong báo cáo vì sao serverless không cần VPC. Giảng viên đã đồng ý với hiện trạng này.
7. Giảng viên hướng dẫn (TS. Huỳnh Xuân Phụng) đã đồng ý với hiện trạng triển khai và tiến độ hiện tại của nhóm.
8. API Gateway dùng REST API (để có API key và usage plan).
9. Thứ tự tạo vé (v0.2): sinh QR và lưu S3 trước, ghi DynamoDB sau, publish SNS cuối cùng; lỗi trước khi ghi DB thì không có vé nào.
10. Quản lý tên và tag theo `naming.md`. Tài liệu API v0.2 đã được đồng bộ vào file `docs/api.md` trong repo. Kế hoạch tổng thể 4 tuần nằm tại `docs/plan.md`.

## 4. Kiến trúc

```
Trình duyệt / điện thoại
   |
   v
CloudFront (HTTPS) --> S3 (web tĩnh: register, ticket, checkin, stats)
   |
   v
API Gateway (REST API eventqr-api, stage v1, CORS)
   POST /events          (BTC, API key)  -> Lambda create-event
   POST /register                        -> Lambda register
   GET  /ticket          (có e, t)       -> Lambda get-ticket
   POST /resend                          -> Lambda resend
   POST /checkin         (BTC, API key)  -> Lambda checkin
   GET  /stats/{eventId} (BTC, API key)  -> Lambda stats

register -> generate-qr (nội bộ, Invoke đồng bộ) -> ghi Tickets -> email qua SNS
DynamoDB: Events, Tickets    S3 (private): ảnh QR    Secrets Manager: khóa HMAC
CloudWatch: log, dashboard, alarm
```

### Luồng chính
1. Đăng ký: `POST /register` → kiểm tra đầu vào → đọc Events → sinh `ticketId` (UUID) → gọi generate-qr (ký HMAC, tạo PNG, lưu S3, trả `qrKey`) → ghi Tickets (`ISSUED`, điều kiện `attribute_not_exists(ticketId)`) → quy trình email (subscribe, kiểm tra xác nhận, chỉ publish khi đã xác nhận) → trả 201 kèm `ticketUrl`.
2. Nhận vé: link trong email hoặc trên web mở `ticket.html?e=<eventId>&t=<ticketId>`, trang gọi `GET /ticket` để lấy ảnh QR mới mỗi lần mở.
3. Check-in: trang quét QR bằng camera, gọi `POST /checkin`; Lambda verify HMAC rồi `UpdateItem` có điều kiện.
4. Thống kê: `GET /stats/{eventId}` truy vấn vé theo `eventId` và đếm theo trạng thái.

### Dữ liệu
- Bảng `eventqr-events`: khóa `eventId` (S). Thuộc tính: `name`, `startTime`, `venue`, `createdAt`.
- Bảng `eventqr-tickets`: khóa phân vùng `eventId` (S), khóa sắp xếp `ticketId` (S, UUID ngẫu nhiên). Thuộc tính: `email`, `name`, `status` (`ISSUED` hoặc `CHECKED_IN`), `createdAt`, `checkedInAt`, `qrKey`, `kid`.
- Cả hai bảng On-demand. Tùy chọn (có thể bỏ ở mức tối thiểu): chống một email đăng ký hai lần bằng `TransactWriteItems` với item `EMAIL#<email>`; nếu thêm thì stats phải loại item này.

### QR và HMAC
- Payload: `v1.<eventId>.<ticketId>.<signature>`; `signature` là HMAC-SHA256 của chuỗi `v1.<eventId>.<ticketId>`, base64url không padding. UUID không chứa dấu chấm nên không phá định dạng. QR không chứa tên hay email, và là dữ liệu nhạy cảm vì có thể dùng để check-in.
- Secret `eventqr-hmac-key` trong Secrets Manager, dạng JSON `{"kid":"1","key":"<64 ký tự hex>"}`, đọc một lần rồi cache trong biến toàn cục của Lambda. Sinh khóa bằng `python3 -c "import secrets;print(secrets.token_hex(32))"`. Không lưu khóa ra file, Git, chat hay báo cáo; không bấm hiện giá trị khi chụp ảnh.
- Verify bằng `hmac.compare_digest`.

### Check-in chống trùng
`UpdateItem` theo khóa `eventId` + `ticketId` với điều kiện vé tồn tại và `status = ISSUED`; đặt `CHECKED_IN` và `checkedInAt`. Nếu điều kiện thất bại thì đọc lại bằng `ConsistentRead` để phân biệt không tồn tại với đã check-in. So `eventId` trong QR với `eventId` ban tổ chức đang chọn. Không đọc rồi ghi vô điều kiện.

### SNS
Một topic Standard `eventqr-ticket-delivery`. Mỗi email là một subscription giao thức email với filter policy `{"email": ["<địa chỉ>"]}` (lọc theo message attributes). Publish kèm message attribute `email` (String). Email xác nhận của SNS hay vào mục spam. Email vé publish trước khi người dùng xác nhận sẽ mất, nên chỉ publish khi subscription đã xác nhận, và luôn có link vé trên web cùng route resend.

## 5. Đặc tả API (tóm tắt, bản v0.2)

Bản đầy đủ: tài liệu "Đặc tả API — EventQR" (Claude Docs, link ở mục 13) và file `api.md`. Tóm tắt:

- Phản hồi thành công: `{"ok": true, "data": {...}}`. Lỗi: `{"ok": false, "error": {"code", "message", "details"}}`; frontend xử lý theo `error.code`. Thời gian ISO 8601 UTC. camelCase.
- 403 do thiếu hoặc sai `x-api-key` và 429 do vượt throttle là lỗi của API Gateway, body kiểu `{"message": "..."}`, không theo envelope; frontend phân biệt bằng việc body có `error.code` hay không. Cần cấu hình Gateway Responses để các lỗi này có header CORS.
- API key chỉ là hạn chế của bản demo; không nhúng key vào repo hoặc `config.js` (trang ban tổ chức cho nhập key trong phiên).

| Route | Quyền | Thành công | Lỗi chính |
| --- | --- | --- | --- |
| `POST /register` | Công khai | 201: `ticketId`, `ticketUrl`, `emailDeliveryStatus` (`PENDING_CONFIRMATION`, `PUBLISHED`, `FAILED`) | 400 `INVALID_INPUT`, 404 `EVENT_NOT_FOUND`, 500 `INTERNAL_ERROR` |
| `POST /checkin` | API key | 200: vé `CHECKED_IN` kèm `checkedInAt` | 400, 403 `INVALID_SIGNATURE`, 403 `EVENT_MISMATCH`, 404 `EVENT_NOT_FOUND`, 404 `TICKET_NOT_FOUND`, 409 `TICKET_ALREADY_CHECKED_IN`, 500 |
| `GET /stats/{eventId}` | API key | 200: `totalTickets`, `checkedInTickets`, `notCheckedInTickets` | 400, 404 `EVENT_NOT_FOUND`, 500 |
| `POST /events` | API key | 201: `eventId`, `name`, `startTime`, `venue`, `createdAt` | 400, 500 |
| `GET /ticket?e=&t=` | Có link vé | 200: `qrImageUrl` (presigned, dự kiến 300 giây) hoặc `qrImageDataUrl` (chế độ `inline`) | 400, 404 `EVENT_NOT_FOUND`, 404 `TICKET_NOT_FOUND`, 500 |
| `POST /resend` | Có `eventId` và `ticketId` | 200: `emailDeliveryStatus = PUBLISHED` | 400, 404, 409 `EMAIL_CONFIRMATION_REQUIRED`, 503 `EMAIL_DELIVERY_FAILED`, 500 |

Trạng thái thiết kế: register, checkin, stats do A đồng ý; events, ticket, resend là đề xuất chờ B xác nhận.

### Hợp đồng nội bộ generate-qr
Chỉ được gọi từ register bằng Invoke đồng bộ. Input `{eventId, ticketId}` (kiểm tra UUID, không chứa dấu chấm). Việc làm: đọc secret (cache), ký, tạo PNG, lưu S3 key `qr/<eventId>/<ticketId>.png`. Output `{qrKey}`. Không ghi DynamoDB, không publish SNS. Gọi lại cùng input cho cùng chữ ký, ghi đè cùng key, an toàn khi retry.

### Mô-đun email dùng chung `ticket_mail` (đặt trong `lambdas/common/`, dùng cho register và resend)
- `ensure_subscription(email)`: Subscribe (protocol `email`, endpoint là email chuẩn hóa chữ thường, FilterPolicy theo email, `ReturnSubscriptionArn = true`), rồi `GetSubscriptionAttributes` đọc `PendingConfirmation`. Dự phòng: duyệt `ListSubscriptionsByTopic` (có phân trang) xem ARN có là `PendingConfirmation` không. **Đây là hướng dự kiến, chưa kiểm chứng.**
- `send_ticket(email, eventId, ticketId)`: chỉ publish khi đã xác nhận; nội dung gồm tên sự kiện và `ticketUrl`.
- Trả về `PENDING_CONFIRMATION`, `PUBLISHED` hoặc `FAILED`; nếu đang pending thì không publish.

### Chế độ ảnh QR của `GET /ticket`
Mặc định `presigned` (URL ngắn hạn, tạo mới mỗi lần mở trang). Dự phòng `inline` (`QR_DELIVERY_MODE=inline`, trả PNG base64) nếu bài thử presigned URL cho kết quả xấu. Lý do không dùng presigned URL cố định trong email: theo hiểu biết (chưa kiểm chứng), URL ký bằng credentials tạm của LabRole chết khi credentials hết hạn dù đặt hạn dài hơn.

### Biến môi trường dùng chung (không hardcode Account ID hay ARN)
`EVENTS_TABLE`, `TICKETS_TABLE`, `SECRET_NAME`, `QR_BUCKET`, `SNS_TOPIC_ARN`, `WEB_BASE_URL` (để tạo `ticketUrl`), `GENERATE_QR_FUNCTION`, `QR_DELIVERY_MODE`. Frontend đọc `API_BASE_URL` và `WEB_BASE_URL` từ `config.js`.

## 6. Quy ước đặt tên và tag (tóm tắt, chi tiết trong `naming.md`)

- Tiền tố `eventqr-`, chữ thường, gạch ngang, không dấu cách.
- DynamoDB: `eventqr-events`, `eventqr-tickets`. Secret: `eventqr-hmac-key`. SNS topic: `eventqr-ticket-delivery`.
- S3: `eventqr-qr-<AccountID>` và `eventqr-web-<AccountID>` (bucket phải duy nhất toàn cầu), Block all public access luôn bật.
- Lambda: `eventqr-create-event`, `eventqr-register`, `eventqr-generate-qr`, `eventqr-get-ticket`, `eventqr-resend`, `eventqr-checkin`, `eventqr-stats`. Execution role: `LabRole` (không tạo role mới).
- API Gateway: `eventqr-api`, stage `v1`, API key `eventqr-organizer-key`, usage plan `eventqr-usage-plan`. CloudFront: Description `eventqr-web`. CloudWatch: dashboard `eventqr-dashboard` (chỉ 1), alarm `eventqr-<hàm>-errors`. Stack IaC: `eventqr-stack`.
- Tag `Project=EventQR`, `Owner=<tên>` gắn ngay lúc tạo ở mục Tags của form; tài nguyên con không hỗ trợ tag thì bỏ qua. Kiểm tra bằng Resource Groups & Tag Editor (chưa chắc Learner Lab cho phép đầy đủ).

## 7. Cấu trúc repo GitHub (`eventqr`, private; mời bạn nhóm làm collaborator)

```
lambdas/            (mỗi hàm một thư mục; lambdas/common/ cho mã dùng chung như ticket_mail)
frontend/           (register, ticket, checkin, stats; config.js)
docs/               (api.md, naming.md, services.md, sơ đồ, worklog)
docs/evidence/week1/ ... week4/   (ảnh minh chứng đặt tên có thứ tự)
.gitignore          (ít nhất: .env, *.zip, *.pem, .aws/, __pycache__/)
```

## 8. Phân công A và B

Hai người đều phải giải thích được toàn bộ hệ thống khi vấn đáp; mỗi tuần dành khoảng 30–45 phút để giải thích chéo code và cấu hình cho nhau.

**A, vé và dữ liệu:**
- DynamoDB (hai bảng), Secrets Manager (secret HMAC), module ký và verify HMAC dùng chung.
- Lambda `register`, `checkin`, `stats`; đặc tả các route này.
- `services.md`: DynamoDB, Secrets Manager, Lambda, API Gateway.

**B, gửi vé và giao diện:**
- S3 (hai bucket), SNS, CloudFront, CloudWatch.
- Lambda `create-event`, `generate-qr`, `get-ticket`, `resend`; trang đăng ký, trang vé, trang check-in, trang thống kê.
- `services.md`: S3, SNS, CloudFront, CloudWatch; đặc tả events, ticket, resend.

**Chung:** repo, `naming.md`, sơ đồ kiến trúc (một người vẽ, người kia kiểm tra với kết quả bài thử), worklog, báo cáo, test tổng thể, demo. Việc còn mở: chọn người viết mô-đun `ticket_mail`.

Hai tài khoản riêng: mỗi người dựng phần của mình ở tài khoản của mình để thực hành và có ảnh minh chứng (Account ID của chính mình); tuần 3 deploy toàn bộ vào tài khoản chính từ Git. Nếu một người đã dựng sẵn tài nguyên ở tài khoản chính thì giữ lại.

## 9. Kế hoạch 4 tuần

### Tuần 1 (05–11/10): nền tảng và bài thử rủi ro
- Chung: repo, `naming.md`, cấu hình AWS CLI (nếu dùng: dán khối AWS CLI từ AWS Details kèm session token; mỗi lần Start Lab credentials đổi), sơ đồ v1, `docs/api.md`, `docs/services.md`, worklog, buổi giải thích chéo.
- A: hai bảng DynamoDB, secret HMAC, bài thử 1 và 2, hàm HMAC kèm test cục bộ.
- B: hai bucket S3, topic SNS, distribution CloudFront (tạo sớm vì deploy mất vài phút đến mười mấy phút), bài thử 3 đến 5.
- Lịch gợi ý: thứ Sáu 09/10 tạo tài nguyên nền; thứ Bảy 10/10 bài thử 1 đến 3; Chủ nhật 11/10 bài thử 4 và 5, chốt sơ đồ, chụp minh chứng, buổi giải thích chéo, worklog.

**Năm bài thử rủi ro nền tảng:**
1. Lambda Python dùng LabRole đọc được secret qua `GetSecretValue` (tên secret từ biến môi trường, cache toàn cục). Nếu AccessDenied thì chụp lỗi và báo thầy.
2. Lambda ghi một vé vào Tickets rồi `UpdateItem` đặt `CHECKED_IN` với điều kiện `status = ISSUED`; lần hai phải ra `ConditionalCheckFailedException`.
3. SNS: subscribe hai email với hai filter policy, xác nhận cả hai (kiểm tra spam), publish với attribute `email` của email thứ nhất, chỉ email đó nhận; làm lại với email thứ hai. Đồng thời kiểm chứng: `Subscribe` với `ReturnSubscriptionArn` rồi `GetSubscriptionAttributes` có cho biết `PendingConfirmation` không; `Subscribe` lại với email đã có (pending hoặc đã xác nhận) cho kết quả gì và có gửi lại email xác nhận không; thời hạn của subscription pending.
4. CloudFront phục vụ một trang HTML bật được camera qua HTTPS trên điện thoại (thử OAC; nếu bị chặn thì dùng bucket website làm custom origin).
5. Presigned URL của một file trong bucket QR với hạn dài: kiểm tra ngay, rồi kiểm tra lại sau khi phiên lab hết hạn và Start Lab lại.

Trang thử camera (`index.html` trong bucket web):

```html
<!doctype html>
<meta charset="utf-8">
<title>Camera test</title>
<button id="b">Bật camera</button>
<p id="s"></p>
<video id="v" autoplay playsinline style="width:100%;max-width:480px"></video>
<script>
document.getElementById('b').onclick = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    document.getElementById('v').srcObject = stream;
    document.getElementById('s').textContent = 'Camera OK';
  } catch (e) { document.getElementById('s').textContent = 'Lỗi: ' + e.name; }
};
</script>
```

Hướng dẫn thao tác tuần 1 (đã đưa): Start Lab, mở console, kiểm tra Region N. Virginia, ghi Account ID và credit còn lại; tạo bảng DynamoDB On-demand (capacity mode chọn Customize settings), secret loại "Other type of secret" (`kid=1`, `key=<chuỗi>`, bỏ rotation), bucket S3 (giữ Block all public access), topic SNS Standard; CloudFront với origin là bucket web, Origin access control, Redirect HTTP to HTTPS, Default root object `index.html`, không bật WAF, price class North America và Europe, rồi dán bucket policy mà console đề xuất vào bucket web; chờ trạng thái Deployed.

**Minh chứng tuần 1:** ảnh toàn màn hình thấy đồng hồ hệ thống, Account ID (menu tài khoản góc trên bên phải) và Region cho: hai bảng, secret (che giá trị), hai bucket với Block public access, topic SNS cùng hai subscription Confirmed và filter policy kèm ảnh email đúng người nhận, distribution Deployed và ảnh điện thoại xin quyền camera, kết quả ba bài thử Lambda, tab Tags của vài tài nguyên chính, commit đầu tiên trên Git, sơ đồ v1.

### Tuần 2 (12–18/10): chức năng lõi, test từng thành phần
- A: register, checkin, stats. B: generate-qr, create-event, get-ticket, resend, trang đăng ký, trang check-in (camera chạy trên localhost trước). API Gateway nối các route, test bằng Postman hoặc curl.
- Minh chứng: ảnh Postman hoặc curl, item DynamoDB, ảnh QR trong S3, log CloudWatch.

### Tuần 3 (19–25/10): tích hợp, bảo mật, giám sát
- Deploy toàn bộ vào tài khoản chính; CloudFront, HTTPS, CORS; quét QR bằng điện thoại qua địa chỉ CloudFront; route resend.
- Bảo mật: bucket private, API key cho route ban tổ chức, cache secret, kiểm tra đầu vào, throttle cho stage, reserved concurrency thấp cho Lambda.
- CloudWatch: thời gian giữ log, 1 dashboard, 2–3 alarm; SAM/CloudFormation nếu kịp (nếu không thì ghi rõ trong báo cáo là làm tay).
- **Đóng băng chức năng 25/10**, sau đó chỉ sửa lỗi.

### Tuần 4 (26/10–01/11): kiểm thử, báo cáo, demo, dọn dẹp
- Kiểm thử: hai điện thoại quét cùng một vé gần như đồng thời, QR bị sửa một ký tự, QR giả, sự kiện không tồn tại, người dùng chưa xác nhận email, thử với 5–10 email thật (bảng 21 tình huống nghiệm thu nằm trong tài liệu API).
- Tối ưu chi phí và chụp báo cáo chi phí; hoàn thiện báo cáo và sơ đồ cuối, ghi rõ phần AI hỗ trợ.
- Quay video demo ≤ 10 phút theo kịch bản viết trước (có video dự phòng dù demo trực tiếp).
- Dọn tài nguyên chỉ sau khi đã quay xong và chụp đủ minh chứng, rồi chụp lại console trống.

### Worklog
Mỗi dòng: ngày, người làm, việc đã làm, số giờ thật, có AI hỗ trợ không và hỗ trợ phần nào. Mỗi người từ 8 giờ trở lên mỗi tuần; ghi đúng số giờ thật (không cần bằng nhau). Mẫu worklog và mẫu báo cáo của thầy chưa có.

## 10. Chi phí

- 50 USD mỗi tài khoản là dư dả. Ước tính thô (chưa kiểm chứng với giá hiện hành): cả 4 tuần khoảng 1–5 USD nếu không có lỗi vòng lặp. Khoản đáng chú ý: Secrets Manager (khoảng 0,40 USD mỗi secret mỗi tháng), CloudWatch (log nhiều, alarm, dashboard vượt mức miễn phí).
- Số credit đã dùng trên trang lab cập nhật trễ vài giờ; kiểm tra sau mỗi buổi làm. Nếu một ngày tiêu hao bất thường (vài USD) thì dừng lại tìm nguyên nhân.
- Rủi ro lớn nhất về tiền: Lambda tự kích hoạt lại chính nó (ví dụ S3 event trên bucket mà Lambda đó ghi vào), hoặc retry vô hạn. Đặt reserved concurrency thấp và timeout hợp lý.
- Phiên lab thường kéo dài khoảng 4 giờ rồi hết hạn; credentials đổi mỗi lần Start Lab nên phải cập nhật cho CLI và Postman. Learner Lab có thể thay đổi chính sách theo từng khóa; đối chiếu với trang lab.

## 11. Điều đã kiểm chứng vs Chưa kiểm chứng (Cập nhật Tuần 3)

### Đã kiểm chứng (Cập nhật 28/10/2026):
- LabRole đọc được Secrets Manager qua `GetSecretValue` (đã test thành công với `eventqr-test-secret`).
- DynamoDB `UpdateItem` có điều kiện chống trùng vé hoạt động chính xác (200 lần đầu, 409 `ConditionalCheckFailedException` lần hai).
- SNS topic Standard + filter policy theo email gửi đúng người nhận.
- Module HMAC-SHA256 chuẩn (`hmac_utils.py`) pass 7/7 ca kiểm thử.
- Camera điện thoại mở được qua giao thức HTTPS.
- Giảng viên đồng ý với kiến trúc serverless không cần VPC và hiện trạng của dự án.
- Đã chọn thư viện sinh mã QR: `segno` (1.6.6) đóng gói kèm ZIP `dist/eventqr-generate-qr.zip`.
- Giao diện web: Đã hoàn thiện 4 trang thuần HTML/JS (`register.html`, `ticket.html`, `checkin.html`, `stats.html`) kèm `config.js` động, kiểm tra cú pháp JS pass.
- Đã build 8 gói ZIP Lambda hoàn chỉnh trong `dist/`, kiểm thử giả lập đạt 38/38 unit tests (23 bộ A + 15 bộ B) và 7/7 HMAC.
- Người dùng đã hoàn thành toàn bộ các thiết lập (setup) tài nguyên và triển khai của Tuần 2 trên AWS Console.

### Chưa kiểm chứng hoặc đang hoàn tất trong Tuần 3:
- Presigned URL ngắn hạn 300 giây đã được chọn trong `get-ticket` để tránh URL chết khi phiên lab hết hạn; bài thử URL 6 giờ của tuần 1 chỉ giữ tính tham khảo.
- Cấu hình API Key `eventqr-organizer-key` & Usage Plan bảo vệ 3 route ban tổ chức (`/events`, `/checkin`, `/stats`) và Gateway Responses (CORS cho lỗi 403, 429).
- Kiểm chứng thực tế camera quét QR trên điện thoại thật (iOS Safari / Android Chrome) qua HTTPS của hệ thống chính.
- Kiểm chứng dứt điểm luồng gửi email vé SNS thật khi người dùng Confirm và Resend.
- CloudWatch: Log retention 7 ngày cho toàn bộ 8 log groups, tạo Dashboard `eventqr-dashboard` và 2 Alarms (`eventqr-checkin-errors`, `eventqr-register-errors`).

## 12. Việc còn mở

- **Hạ tầng & Giám sát Tuần 3:**
  - Hoàn tất cấu hình CloudWatch (đổi retention 7 ngày cho 8 log groups, dashboard `eventqr-dashboard`, 2 alarms).
  - Thu thập trọn bộ ảnh minh chứng có Account ID, Region `us-east-1`, giờ hệ thống cho luồng quét điện thoại và CloudWatch.
- **Tuần 4 (Nghiệm thu & Đóng gói):**
  - Thực hiện 21 ca kiểm thử nghiệm thu theo [`docs/api.md`](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/api.md).
  - Soạn kịch bản và quay video demo $\le 10$ phút.
  - Báo cáo chi phí AWS Cost Explorer / Billing và hoàn thiện hồ sơ nộp bài.

## 13. Tài liệu đã tạo

- `naming.md`: quy ước đặt tên và tag (tại [docs/naming.md](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/naming.md)).
- `api.md`: đặc tả API v0.2 đầy đủ (tại [docs/api.md](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/api.md)).
- `plan.md`: kế hoạch 4 tuần và bảng theo dõi tiến độ cập nhật hàng tuần (tại [docs/plan.md](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/plan.md)).
- `architecture.md`: kiến trúc hệ thống và sơ đồ (tại [docs/evidence/week1/architecture.md](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/evidence/week1/architecture.md)).
- `worklog/week1/worklog_markdown.md`: nhật ký công việc tuần 1 (Quang 9.75h, Long 9.2h).
- `worklog/week2/worklog_markdown.md`: nhật ký công việc tuần 2 (Quang 8.25h, Long 10.50h — Hoàn thành 100% mục tiêu tuần 2).
- `worklog/week3/worklog_markdown.md`: nhật ký công việc tuần 3 (đã ghi nhận bước đầu ngày 19/10 và đang bổ sung).
- `project_memory/agent.md`: hướng dẫn vận hành và giao thức ghi nhận dành cho AI Agent.
- `project_memory/roadmap.md`: kế hoạch hành động 4 tuần chi tiết từng ngày.
- `docs/WEEK2-STATUS.md`: báo cáo trạng thái hoàn thiện mã nguồn và kiểm thử tuần 2.

## 14. Trạng thái hiện tại (Cập nhật 28/10/2026)

- **Tuần 1 (05–11/10):** Đã hoàn thành 100% (Quang: 9.75h, Long: 9.2h). Báo cáo đã nộp lại theo quy định.
- **Tuần 2 (12–18/10):** **ĐÃ HOÀN THÀNH 100%.**
  - Người dùng đã hoàn thành toàn bộ công việc setup của tuần 2.
  - Mã nguồn 8 hàm Lambda và 4 trang frontend đã hoàn tất trong repo, 38/38 unit test local pass, 7/7 test HMAC pass. Đã build 8 gói ZIP.
  - Giờ làm việc tuần 2: Quang 8.25h, Long 10.50h (cả 2 đều $\ge 8$h).
- **Tuần 3 (19–25/10):** **ĐANG HOÀN TẤT & CHUẨN BỊ ĐÓNG BĂNG.**
  - Trọng tâm còn lại: Cấu hình CloudWatch (Retention 7 ngày, `eventqr-dashboard`, 2 Alarms), kiểm thử camera điện thoại thật qua HTTPS và kiểm chứng gửi email SNS.
  - Sau khi xong các bài thử trên sẽ chốt **Đóng băng tính năng (Feature Freeze)** để chuyển sang Tuần 4.
- **Tuần 4 (26/10–01/11):** Chuẩn bị chạy nghiệm thu 21 test case, quay video demo $\le 10$ phút và hoàn thiện báo cáo chi phí.

## 15. Trợ lý mới nên làm tiếp

1. Đọc [`docs/plan.md`](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/plan.md), [`project_memory/agent.md`](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/project_memory/agent.md) và [`project_memory/project-memory.md`](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/project_memory/project-memory.md).
2. Hướng dẫn và đồng hành cùng người dùng hoàn tất các thao tác CloudWatch (Retention 7 ngày, Dashboard, 2 Alarms) và kiểm thử camera điện thoại thật.
3. Hỗ trợ người dùng rà soát 21 ca nghiệm thu theo [`docs/api.md`](file:///c:/Users/LongHoang/Documents/GitHub/eventqr/docs/api.md) để chuẩn bị kịch bản quay video demo.
4. Cập nhật `worklog/week3/worklog_markdown.md` để đảm bảo số giờ của Quang và Long đạt $\ge 8$h cho tuần 3 theo đúng Write-back Protocol.
