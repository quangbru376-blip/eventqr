# EventQR — Trạng thái tuần 2, cập nhật 19/10/2026

## Mã nguồn

Repo đã kết hợp mã phần A và B: 7 Lambda nghiệp vụ (`create-event`, `register`, `generate-qr`, `get-ticket`, `resend`, `checkin`, `stats`) và Lambda `web`; 4 trang đăng ký, xem vé, check-in và thống kê cùng assets.

- HMAC giữ định dạng `v1.<eventId>.<ticketId>.<signature>`, dùng cùng secret và cách chuyển hex sang bytes.
- `register` và `resend` dùng chung `ticket_mail.py` có timeout SNS. `PUBLISHED` chỉ nghĩa SNS chấp nhận publish, không chứng minh email đã vào hộp thư.
- `register` gọi QR đồng bộ, kiểm tra FunctionError/qrKey, ghi vé có điều kiện rồi xử lý email. Chưa có idempotency để chống mọi lần đăng ký lặp.
- `checkin` nhận `qrPayload`, kiểm tra chữ ký và cập nhật DynamoDB có điều kiện để chống check-in trùng.
- `stats` Query có phân trang. Web phục vụ file trong allowlist từ S3 private qua API Gateway + Lambda, theo phương án đang tiếp tục sau hạn chế OAC/OAI.
- Build sinh 8 ZIP trong `dist/` (Git ignore); xem lệnh build/test trong [README](../README.md). API key không nằm trong frontend/config hoặc Git.

## Kiểm thử local

- 38/38 unittest đạt: 23 ca A + 15 regression test B có mã trong repo. Báo cáo B trước đây có 15 mock test là kết quả lịch sử riêng, không cộng thành 53 ca hiện tại.
- 7/7 ca HMAC đạt; JavaScript qua kiểm tra cú pháp. Các ZIP build khớp source/helper đi kèm; Segno 1.6.6 và thư viện quét có license.
- Test dùng fake boto3/DynamoDB/S3/SNS/Secrets Manager/Lambda. Mã QR + Segno thật tạo PNG trong bộ nhớ; kiểm tra local không chứng minh quyền LabRole, AWS concurrency, email, browser hoặc camera thật.
- Luồng tích hợp local gồm register → QR → lưu vé → checkin 200 rồi 409 → stats; có ca QR sửa chữ ký, sai sự kiện, thiếu vé, phân trang và lỗi gửi email.

Mã kiểm thử: [A](../tests/test_a.py), [B](../tests/test_b.py), [HMAC](../lambdas/common/test_hmac.py). Kết quả local được giữ tách khỏi kết quả triển khai AWS.

## AWS và mức bằng chứng

| Nội dung | Trạng thái được ghi nhận |
|---|---|
| Tuần 1 | Có ảnh lịch sử đọc secret thành công và camera máy tính qua HTTPS; worklog ghi thử DynamoDB chống trùng/SNS filter. Không xác nhận lại tài nguyên live ngày 19/10 |
| Phần B | Người thực hiện báo đã làm đến bước 8 và đã tạo hai bucket; còn đối chiếu từng cấu hình và kết quả bằng minh chứng |
| API và luồng thật | Chưa có bộ minh chứng đầy đủ cho create-event 201 → đăng ký → QR/email → check-in 200/409 → thống kê |
| API key/usage plan | Chưa được xác nhận đầy đủ trên tài khoản chính |
| CloudWatch | Cần ảnh đủ các log group liên quan có retention 7 ngày; ảnh web tuần 1 không bao quát toàn bộ |
| Browser/điện thoại | Chưa có kết quả được xác nhận độc lập cho UI/email/camera điện thoại và quét QR thật |
| Presigned dài hạn | Bài thử qua phiên lab vẫn cần chốt; URL 300 giây trong get-ticket là hạng mục khác |

Phiên kết hợp source và kiểm thử local không triển khai AWS hoặc gửi email thật. Lỗi `503 EMAIL_DELIVERY_FAILED` từng được báo chưa có nguyên nhân thực tế được xác nhận là đã sửa.

## Worklog đã xác nhận

| Thành viên | 12–18/10: giờ tuần 2 | 19/10: giờ tuần 3 | Tổng theo phạm vi công việc |
|---|---:|---:|---:|
| Đặng Duy Quang | 8,25h | 1,25h | 9,50h |
| Trương Hoàng Long | 10,50h | 1,00h | 11,50h |
| **Tổng** | **18,75h** | **2,25h** | **21,00h** |

26 hạng mục gồm 22 mục ngày 12–18/10 và 4 mục ngày 19/10. Tuần 2 cả hai đã ghi đủ ≥8h/người; 4 mục bổ sung chỉ tính tuần 3. Xem [worklog tuần 2](../worklog/week2/worklog_markdown.md) và [tuần 3](../worklog/week3/worklog_markdown.md). Giờ theo xác nhận của người thực hiện; không suy thành toàn bộ ca AWS đã hoàn thành.

## Tiếp theo

1. Đối chiếu source/config với các Lambda và tài nguyên hiện có trên tài khoản chính, giữ secret và trạng thái vé.
2. Lưu minh chứng luồng create-event → register → QR/vé → Confirm SNS/resend/email → check-in 200/409 → stats, rồi thử điện thoại HTTPS.
3. Xác nhận API key/usage plan, retention, presigned và lỗi email bằng log/kết quả thật trước khi đánh hoàn thành checklist AWS.

Giữ các ràng buộc `us-east-1`, `LabRole`, S3 private, không tạo IAM mới hoặc gắn Lambda vào VPC. Các bộ source/hướng dẫn có AI hỗ trợ; phần hỗ trợ kỹ thuật đã được ghi trong worklog.
