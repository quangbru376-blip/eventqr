# EventQR — Hệ thống quản lý sự kiện và check-in bằng QR code

Đồ án môn **Cloud** (Đợt 1, 2026–2027) — nhóm **Domain Apps** — GVHD: TS. Huỳnh Xuân Phụng.

EventQR cho phép người dùng đăng ký một sự kiện và nhận vé là một mã QR. Tại cổng, ban tổ chức quét QR bằng camera trên trang web; hệ thống xác minh vé thật bằng chữ ký HMAC và chỉ cho vào **một lần**. Ban tổ chức xem được thống kê số vé đã đăng ký và đã vào.

Toàn bộ hệ thống chạy trên **AWS Learner Lab** theo hướng serverless, Region `us-east-1`, dùng `LabRole` (không tạo IAM user hoặc role).

> **Trạng thái local 19/10/2026:** đã ghép mã tuần 2 từ hai kit A/B và handoff bên ngoài: 7 Lambda nghiệp vụ + web Lambda, 4 trang web và test/build. 38/38 mock test và 7/7 ca HMAC đạt. AWS tuần 2 chưa được xác nhận độc lập; handoff ghi người dùng báo B đến bước 8. Xem [báo cáo ghép mã và mức bằng chứng](docs/WEEK2-STATUS.md). Sơ đồ bên dưới phản ánh source và phương án Lambda web + API Gateway theo handoff; deployment thực tế cần kiểm chứng riêng.

## Chạy bản nguồn đã ghép

Chạy từ thư mục repo `eventqr`. Hướng dẫn AWS: [phần A](docs/huong-dan-A-tuan2.md), [phần B](docs/huong-dan-B-tuan2.md). Các hướng dẫn này được chuẩn bị ở môi trường khác; kết quả triển khai phải được ghi riêng.

```powershell
python -B tools/package_a.py
python -m pip download --no-deps --only-binary=:all: segno==1.6.6 -d local/dependencies
$segnoWheel = Get-ChildItem local/dependencies/segno-1.6.6-*.whl | Select-Object -First 1
python -B tools/package_b_week2.py --segno-archive $segnoWheel.FullName
python -B -m unittest discover -s tests -v
python -B lambdas/common/test_hmac.py
node --check frontend/app.js
node --check frontend/checkin.js
node --check frontend/config.js
```

Build B lấy Segno 1.6.6 từ wheel đã tải ở bước trên; cũng có thể dùng ZIP generate-qr gốc làm archive đầu vào khi đã có sẵn. Thư mục `local/` được Git ignore.

`dist/` chứa 8 gói Lambda sinh lại, được Git ignore. SDK boto3 có trong Lambda runtime; test local dùng fake AWS và Segno trong ZIP. API key nhập trong phiên giao diện tổ chức. `frontend/config.js` để URL công khai trống nhằm suy ra stage khi web/API cùng origin; khi khác origin cần cấu hình URL thực tế. Source import và tài liệu có AI hỗ trợ; xem [worklog tiếp nhận](worklog/week3/worklog_markdown.md).

## Chức năng

- Tạo sự kiện (ban tổ chức).
- Đăng ký tham dự và phát hành vé QR; link vé luôn hiển thị ngay trên web, đồng thời gửi qua email (SNS).
- Xem lại vé và gửi lại link vé.
- Check-in bằng cách quét QR qua camera trình duyệt; chống làm giả (HMAC) và chống check-in trùng (cập nhật có điều kiện trong DynamoDB).
- Thống kê theo sự kiện: tổng vé, đã check-in, chưa check-in.

Phạm vi được giữ ở mức tối thiểu: một email có thể đăng ký nhiều vé, chưa có đăng nhập hay phân quyền người dùng, chưa chống đăng ký trùng email.

## Kiến trúc

```mermaid
flowchart TB
  U["Trình duyệt / điện thoại"]
  S3W["S3 web private"]
  APIGW["API Gateway<br/>eventqr-api, stage v1"]
  subgraph L["Lambda (Python, LabRole)"]
    F1["create-event"]
    F2["register"]
    F3["generate-qr"]
    F4["get-ticket"]
    F5["resend"]
    F6["checkin"]
    F7["stats"]
    FW["web: allowlist HTML/JS/CSS"]
  end
  DDB[("DynamoDB<br/>Events, Tickets")]
  SM["Secrets Manager<br/>khóa HMAC"]
  S3Q["S3 ảnh QR (private)"]
  SNS["SNS<br/>gửi link vé"]
  CW["CloudWatch"]

  U -->|GET /web/page qua HTTPS| APIGW --> FW --> S3W
  U -->|gọi API| APIGW
  APIGW --> F1 & F2 & F4 & F5 & F6 & F7
  F2 -->|Invoke đồng bộ| F3
  F1 & F2 & F4 & F5 & F6 & F7 --> DDB
  F3 & F6 --> SM
  F3 & F4 --> S3Q
  F2 & F5 --> SNS
  L -.-> CW
```

| Dịch vụ AWS | Vai trò |
| --- | --- |
| API Gateway + Lambda web + S3 private | Phục vụ HTML/JS/CSS qua HTTPS; tiếp tục phương án handoff sau hạn chế OAC/OAI |
| API Gateway (REST API) | Cổng vào cho sáu route, CORS, API key và throttle |
| Lambda (Python) | Bảy hàm nghiệp vụ và một hàm web, dùng `LabRole` |
| DynamoDB | Bảng `eventqr-events`, `eventqr-tickets`; chống check-in trùng |
| S3 (ảnh QR) | Lưu ảnh PNG của QR, bucket private |
| Secrets Manager | Giữ khóa HMAC để ký và kiểm tra QR |
| SNS | Gửi link vé qua email, mỗi email một subscription có filter policy |
| CloudWatch | Log, một dashboard, vài alarm lỗi |

Mô hình dữ liệu và thiết kế nền nằm trong [`docs/architecture.md`](docs/architecture.md) (bản lịch sử còn CloudFront); trạng thái ghép hiện tại ở [báo cáo 19/10](docs/WEEK2-STATUS.md). Sơ đồ sequence tuần 1: [đăng ký và gửi vé](docs/evidence/week1/sequence-register.png), [check-in](docs/evidence/week1/sequence-checkin.png).

### Cách QR hoạt động

Nội dung QR là `v1.<eventId>.<ticketId>.<signature>`, trong đó `signature` là HMAC-SHA256 của chuỗi `v1.<eventId>.<ticketId>` (base64url, không padding). QR không chứa tên hay email. Khi check-in, Lambda kiểm tra chữ ký bằng so sánh hằng thời gian, rồi cập nhật vé từ `ISSUED` sang `CHECKED_IN` bằng một thao tác có điều kiện; nếu hai thiết bị quét cùng lúc thì chỉ một bên thành công, bên còn lại nhận `409`.

## API

Base URL dự kiến: `https://<api-id>.execute-api.us-east-1.amazonaws.com/v1`.

| Route | Quyền | Chức năng |
| --- | --- | --- |
| `POST /events` | Ban tổ chức (`x-api-key`) | Tạo sự kiện |
| `POST /register` | Công khai | Đăng ký, phát hành vé QR, gửi link vé |
| `GET /ticket?e=&t=` | Người có link vé | Lấy ảnh QR của vé |
| `POST /resend` | Có `eventId` và `ticketId` | Gửi lại link vé qua email |
| `POST /checkin` | Ban tổ chức (`x-api-key`) | Check-in bằng QR |
| `GET /stats/{eventId}` | Ban tổ chức (`x-api-key`) | Thống kê vé của sự kiện |
| `GET /web/{page}` | Công khai | Phục vụ các file frontend theo allowlist |

Phản hồi thành công có dạng `{"ok": true, "data": {...}}`, lỗi có dạng `{"ok": false, "error": {"code", "message", "details"}}`. Đặc tả đầy đủ (request, mã lỗi, quy tắc xử lý, 21 tình huống nghiệm thu): [`docs/api.md`](docs/api.md).

## Cấu trúc repo

```
lambdas/              mỗi hàm một thư mục; lambdas/common/ cho mã dùng chung (ví dụ ticket_mail)
frontend/             trang đăng ký, vé, check-in, thống kê; config.js
docs/
  architecture.md     kiến trúc, luồng xử lý, dữ liệu, bảo mật, quyết định thiết kế
  api.md              đặc tả API
  naming.md           quy ước đặt tên và tag tài nguyên
  services.md         vai trò và cấu hình từng dịch vụ (sẽ bổ sung)
  diagrams/           sơ đồ dạng ảnh
  evidence/           ảnh minh chứng theo tuần (week1 ... week4)
  worklog/            nhật ký công việc hằng tuần
README.md
```

## Triển khai

Chưa có script triển khai. Dự kiến: làm tay trên AWS Console ở tuần 1–2 để hiểu từng dịch vụ, đóng gói SAM/CloudFormation ở tuần 3 nếu còn thời gian. Nếu không kịp, báo cáo sẽ ghi rõ là triển khai thủ công.

Quy tắc khi triển khai:

- Chỉ dùng Region `us-east-1`, Lambda dùng `LabRole`.
- Đặt tên và gắn tag theo [`docs/naming.md`](docs/naming.md): `Project=EventQR`, `Owner=<tên người tạo>`.
- Không hardcode Account ID hay ARN. Cấu hình qua biến môi trường: `EVENTS_TABLE`, `TICKETS_TABLE`, `SECRET_NAME`, `QR_BUCKET`, `WEB_BUCKET`, `SNS_TOPIC_ARN`, `WEB_BASE_URL`, `GENERATE_QR_FUNCTION`, `QR_DELIVERY_MODE`, `CORS_ORIGIN` khi khác origin. Frontend đọc `API_BASE_URL` và `WEB_BASE_URL` từ `config.js`.
- Mỗi thành viên có tài khoản Learner Lab riêng; tài nguyên không chia sẻ giữa hai tài khoản nên hệ thống cuối được deploy từ Git vào tài khoản chính.
- Credentials của Learner Lab đổi mỗi lần Start Lab; nhớ cập nhật lại cho AWS CLI và Postman.


## Tiến độ

Kế hoạch 4 tuần, tính từ 05/10/2026.

| Tuần | Thời gian | Nội dung | Trạng thái |
| --- | --- | --- | --- |
| 1 | 05–11/10 | Nền tảng và bài thử rủi ro | Xong phần lớn; còn tồn đọng theo plan |
| 2 | 12–18/10 | Chức năng lõi | Mã A/B đã ghép local ngày 19/10; mock test đạt; AWS chờ xác nhận |
| 3 | 19–25/10 | Tích hợp, bảo mật, giám sát, IaC nếu kịp; đóng băng chức năng 25/10 | Đã tiếp nhận/ghép mã 19/10; ưu tiên xác nhận luồng thật |
| 4 | 26/10–01/11 | Kiểm thử tổng thể, tối ưu chi phí, báo cáo, demo, dọn tài nguyên | Chưa bắt đầu |

## Nhóm thực hiện

| Thành viên | Phụ trách |
| --- | --- |
| _(Đặng Duy Quang, 24110307)_ — A | Vé và dữ liệu: `create-event`, `register`, `checkin`, `stats`, DynamoDB, Secrets Manager, HMAC |
| _(Trương Hoàng Long, 24110273)_ — B | Gửi vé và giao diện: `generate-qr`, `get-ticket`, `resend`, `web`, S3, SNS, CloudWatch, các trang web |

Cả hai thành viên đều phải giải thích được toàn bộ cấu hình và mã nguồn khi vấn đáp.

## Hỗ trợ AI

Theo quy định của đề, phần có AI hỗ trợ được ghi rõ: các tài liệu kiến trúc, đặc tả API, quy ước đặt tên và README này được soạn với sự hỗ trợ của Claude (Anthropic); nhóm chịu trách nhiệm về nội dung. Chi tiết theo từng tuần nằm trong worklog.

Ngày 19/10, Codex ghép mã/hướng dẫn do B và các agent chuẩn bị bên ngoài, bổ sung kiểm thử B, build lại ZIP và cập nhật ngữ cảnh. Xem [worklog tuần 3](worklog/week3/worklog_markdown.md); chưa gán giờ sinh viên hoặc đánh hoàn thành triển khai AWS từ công việc AI.

## Tài liệu

- [Kiến trúc](docs/architecture.md)
- [Đặc tả API](docs/api.md)
- [Quy ước đặt tên và tag](docs/naming.md)
- [Kế hoạch 4 tuần (Master Plan)](docs/plan.md)
