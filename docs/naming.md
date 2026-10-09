# Quy ước đặt tên và gắn tag — EventQR

Đồ án: Hệ thống quản lý sự kiện và check-in bằng QR code (nhóm Domain Apps).
Region duy nhất: `us-east-1`. Tiền tố chung của mọi tài nguyên: `eventqr-`.

## 1. Tag bắt buộc (mọi tài nguyên hỗ trợ tag)

| Khóa (Key) | Giá trị (Value) | Ghi chú |
|---|---|---|
| `Project` | `EventQR` | Giống hệt nhau cho mọi tài nguyên, đúng hoa thường |
| `Owner` | `<tên người tạo>` | Mỗi người dùng đúng một cách viết tên của mình, không đổi giữa các tài nguyên |

Quy tắc:
- Khóa phân biệt hoa thường: `Project` khác `project`. Chỉ dùng hai khóa ở trên, không thêm khóa khác nếu chưa thống nhất.
- Gắn tag ngay lúc tạo tài nguyên (mục Tags cuối form), đừng để quay lại bổ sung.
- Chỉ gắn cho tài nguyên cấp cao (bảng, bucket, hàm, topic...), không gắn cho từng bản ghi hay từng đối tượng bên trong.

## 2. Bảng đặt tên và tag theo tài nguyên

`<AccountID>` là dãy 12 chữ số của tài khoản chạy tài nguyên đó (bấm vào tên tài khoản ở góc trên bên phải console).

| Dịch vụ | Tài nguyên | Tên | Gắn tag Project/Owner? | Ghi chú |
|---|---|---|---|---|
| DynamoDB | Bảng sự kiện | `eventqr-events` | Có | Khóa: `eventId` (S). On-demand |
| DynamoDB | Bảng vé | `eventqr-tickets` | Có | Khóa: `eventId` (S) + `ticketId` (S). On-demand |
| Secrets Manager | Khóa HMAC | `eventqr-hmac-key` | Có | JSON `{"kid","key"}`. Không bật rotation. Không lưu giá trị ra file, Git, chat |
| S3 | Bucket ảnh QR | `eventqr-qr-<AccountID>` | Có | Private, Block public access bật |
| S3 | Bucket web tĩnh | `eventqr-web-<AccountID>` | Có | Private, truy cập qua CloudFront |
| SNS | Topic gửi vé | `eventqr-ticket-delivery` | Có | Loại Standard |
| SNS | Subscription email | (tự sinh) | Không | Subscription không có tag. Filter policy: `{"email": ["<địa chỉ>"]}` |
| CloudFront | Distribution | (không có trường tên) | Có | Đặt Description = `eventqr-web` để dễ nhận ra |
| CloudFront | Origin access control | `eventqr-web-oac` | Không (theo mình biết) | Tạo cùng distribution |
| Lambda | Tạo sự kiện | `eventqr-create-event` | Có | |
| Lambda | Đăng ký | `eventqr-register` | Có | |
| Lambda | Sinh QR | `eventqr-generate-qr` | Có | |
| Lambda | Lấy vé | `eventqr-get-ticket` | Có | |
| Lambda | Gửi lại vé | `eventqr-resend` | Có | |
| Lambda | Check-in | `eventqr-checkin` | Có | |
| Lambda | Thống kê | `eventqr-stats` | Có | |
| Lambda | Execution role | `LabRole` | Không | Có sẵn, không tạo mới (không tạo IAM user/role) |
| API Gateway | API | `eventqr-api` | Có | Stage: `v1` |
| API Gateway | API key | `eventqr-organizer-key` | Có | Dùng cho các route của ban tổ chức |
| API Gateway | Usage plan | `eventqr-usage-plan` | Có | |
| CloudWatch | Log group | `/aws/lambda/eventqr-<tên hàm>` | Có (nếu cho phép) | Tự sinh theo tên hàm. Đặt Retention (ví dụ 7 ngày) |
| CloudWatch | Dashboard | `eventqr-dashboard` | Không (theo mình biết) | Chỉ tạo 1 dashboard |
| CloudWatch | Alarm | `eventqr-<tên hàm>-errors` | Có | Chỉ tạo vài alarm cần thiết |
| CloudFormation / SAM | Stack (nếu dùng IaC) | `eventqr-stack` | Có | Tag của stack được truyền xuống tài nguyên nó tạo |
| VPC | VPC mặc định | (có sẵn) | Không | Không tạo VPC mới, không sửa VPC mặc định; chụp ảnh và giải thích trong báo cáo |

Các tài nguyên đánh dấu "theo mình biết" có thể khác tùy dịch vụ và phiên bản console. Nếu không thấy mục Tags thì ghi lại và bỏ qua, không cố tìm cách khác.

## 3. Quy ước chung cho tên

- Chữ thường, ngăn cách bằng dấu gạch ngang `-`, không dấu cách, không ký tự có dấu tiếng Việt.
- Tên bucket S3 là duy nhất toàn cầu nên bắt buộc có hậu tố `<AccountID>`.
- Tên bảng, topic, secret, hàm giống hệt nhau giữa hai tài khoản (mỗi tài khoản là một môi trường riêng).
- Mã không hardcode Account ID hay ARN: dùng biến môi trường (`TICKETS_TABLE`, `EVENTS_TABLE`, `SECRET_NAME`, `QR_BUCKET`, `SNS_TOPIC_ARN`...).

## 4. Kiểm tra và dọn dẹp

- Kiểm tra tag: dùng Resource Groups & Tag Editor trên console (Region us-east-1), lọc theo `Project = EventQR`, tìm tài nguyên thiếu tag.
- Dọn dẹp cuối kỳ: lọc theo `Project = EventQR` để chắc không sót tài nguyên. Chỉ dọn sau khi đã quay demo và chụp đủ minh chứng.
- Chụp ảnh tab Tags của các tài nguyên chính làm minh chứng (thấy Account ID, Region, thời gian).
