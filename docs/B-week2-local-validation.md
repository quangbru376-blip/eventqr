# Kiểm thử chuẩn bị phần B — 16/10/2026

AI hỗ trợ sinh mã và kiểm thử. Không có AWS credentials trong phiên, không gọi tài khoản AWS thật.

## Đã chạy

- 15 kiểm thử backend PASS, dùng fake boto3/DynamoDB/S3/Secrets Manager/SNS:
  - PNG tạo được và định dạng hợp lệ; module HMAC dùng cùng khóa bytes.
  - Retry cùng key, cache secret một lần.
  - UUID không hợp lệ không upload.
  - get-ticket inline/presigned; thiếu sự kiện/vé; qrKey sai; không trả email trong response.
  - pending hoặc subscription mới không publish; filter sai không publish.
  - publish có message attribute email đúng.
  - resend bỏ qua email đích trong request, không sửa item vé.
  - JSON body sai trả 400.
  - web chỉ phục vụ allowlist và trả đúng Content-Type JS.
- `node --check` cho app.js/checkin.js PASS.
- Gói ZIP chứa handler/helpers ở gốc; Segno 1.6.6 nằm trong gói sinh QR.

## Chưa chạy / giới hạn

- Không deploy hoặc test trên AWS Learner Lab; mock không chứng minh được quyền LabRole.
- Chưa chạy browser UI/camera thật. Runtime thiếu browser executable; tải browser để QA không thành công, vì vậy không báo đã test UI.
- PNG đã được PIL kiểm tra cấu trúc, chưa giải mã ngược bằng camera trong phiên này.
- Module SNS và CloudFormation cần xác nhận quyền/behavior trên tài khoản Quang.
- Throttle, API key/usage plan, CORS, HMAC check-in của A và luồng register thật chưa được kiểm thử trong phiên.

Sinh viên thực hiện các bước AWS trong hướng dẫn và lưu kết quả thật vào worklog/evidence.
