# KẾT QUẢ NGHIỆM THU 21 CA KIỂM THỬ — EVENTQR (AWS SERVERLESS)

> **Môn học:** Cloud Computing (Đợt 1, 2026–2027) — GVHD: TS. Huỳnh Xuân Phụng  
> **Đề tài:** EventQR — Hệ thống quản lý sự kiện và check-in bằng mã QR  
> **Căn cứ đặc tả:** Mục 10 trong [`docs/api.md`](api.md)  
> **Thời gian nghiệm thu:** Tuần 4 (26/10/2026 – 01/11/2026)  
> **Repository GitHub:** [https://github.com/quangbru376-blip/eventqr](https://github.com/quangbru376-blip/eventqr)  
> **Nhóm sinh viên thực hiện:**
> - **Đặng Duy Quang (MSSV: 24110307)** — Vai trò A (Lead, Backend dữ liệu & API)
> - **Trương Hoàng Long (MSSV: 24110273)** — Vai trò B (Gửi vé SNS, S3, Web UI & CloudWatch)

---

## 📊 BẢNG MA TRẬN KẾT QUẢ NGHIỆM THU 21 CA KIỂM THỬ

Toàn bộ 21/21 ca kiểm thử dưới đây đã được thực thi và nghiệm thu thực tế 100% trên môi trường AWS Learner Lab (Region `us-east-1`, IAM `LabRole`). Mỗi ca đều có đường dẫn trực tiếp đến ảnh chụp màn hình minh chứng trên GitHub:

| Mã TC | Nhóm chức năng | Tình huống kiểm thử | Thao tác thực hiện | Kết quả mong đợi & Kết quả thực tế | Trạng thái | Link ảnh minh chứng trên GitHub |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **TC01** | Đăng ký & QR | Đăng ký vé hợp lệ thành công | Gửi `POST /register` với tên và email hợp lệ | HTTP 201 Created; sinh `ticketId`, lưu DynamoDB `status: ISSUED`; S3 sinh ảnh QR; web hiển thị vé | **PASS** | [Xem ảnh tc01.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc01.png) |
| **TC02** | Đăng ký & QR | Cùng email đăng ký lần 2 | Gửi `POST /register` lần 2 với cùng thông tin | HTTP 201 Created; sinh `ticketId` thứ hai độc lập, không ghi đè vé cũ | **PASS** | [Xem ảnh tc02.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc02.png) |
| **TC03** | Đăng ký & QR | Đăng ký thiếu trường bắt buộc | Gửi `POST /register` thiếu `name` hoặc `email` | HTTP 400 Bad Request; mã lỗi `INVALID_INPUT`; không ghi nhận vé nào vào DynamoDB | **PASS** | [Xem ảnh tc03.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc03.png) |
| **TC04** | Đăng ký & QR | Đăng ký sự kiện không tồn tại | Gửi `POST /register` với `eventId` là UUID giả | HTTP 404 Not Found; mã lỗi `EVENT_NOT_FOUND` | **PASS** | [Xem ảnh tc04.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc04.png) |
| **TC05** | Đăng ký & QR | Lỗi sinh QR / ghi S3 (Không tạo vé rác) | Kiểm tra thứ tự logic: gọi `generate-qr` trước khi ghi DB | HTTP 500 nếu lỗi S3; cơ chế Fail-safe by ordering đảm bảo không sinh vé mồ côi trong DynamoDB | **PASS** | [Xem ảnh tc05.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc05.png) |
| **TC06** | SNS Email | Email chưa xác nhận SNS Subscription | Gửi `POST /register` với email mới tinh | HTTP 201 Created; `emailDeliveryStatus: "PENDING_CONFIRMATION"`; chưa gửi email vé; web vẫn có vé | **PASS** | [Xem ảnh tc06.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc06.png) |
| **TC07** | SNS Email | Gửi lại vé sau khi đã Confirm SNS | Bấm "Confirm subscription" trong Gmail rồi gọi `POST /resend` | HTTP 200 OK; `emailDeliveryStatus: "PUBLISHED"`; SNS gửi thư vé thật về hộp thư Gmail | **PASS** | [Xem ảnh tc07.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc07.png) |
| **TC08** | SNS Email | Cách ly Filter Policy SNS giữa 2 email | Đăng ký 2 email; phát hành vé cho email A | Chỉ email A nhận được vé; email B hoàn toàn không nhận được thư của A (Filter Policy theo MessageAttribute) | **PASS** | [Xem ảnh tc08.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc08.png) |
| **TC09** | SNS Email | Bền vững khi SNS lỗi sau khi lưu DB | Khảo sát lỗi khi publish SNS sau khi DB đã ghi | HTTP 201 Created; `emailDeliveryStatus: "FAILED"`; khách vẫn nhận được link vé và mở được vé trên web | **PASS** | [Xem ảnh tc09.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc09.png) |
| **TC10** | Check-in cổng | Check-in vé hợp lệ lần đầu | Quét QR vé hợp lệ qua Camera trên `checkin.html` | HTTP 200 OK; vé cập nhật `status: "CHECKED_IN"`, lưu `checkedInAt`; giao diện báo xanh, **Beep 880Hz** | **PASS** | [Xem ảnh tc10.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc10.png) |
| **TC11** | Check-in cổng | Quét lại cùng 1 vé (Chống trùng vé) | Đưa lại mã QR vừa check-in ở TC10 vào quét lần 2 | HTTP 409 Conflict; mã lỗi `TICKET_ALREADY_CHECKED_IN`; giữ nguyên giờ check-in cũ; **Beep trầm 330Hz** | **PASS** | [Xem ảnh tc11.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc11.png) |
| **TC12** | Check-in cổng | Hai thiết bị check-in cùng vé đồng thời | 2 cửa sổ cùng quét và gửi check-in tại cùng 1 tích tắc | Đúng 1 thiết bị nhận HTTP 200 (xanh); thiết bị kia nhận HTTP 409 (đỏ); DynamoDB atomic | **PASS** | [Xem ảnh tc12.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc12.png) |
| **TC13** | Bảo mật HMAC | Quét mã QR bị sửa chữ ký (HMAC tamper) | Thay đổi 1 ký tự cuối cùng của chuỗi signature | HTTP 403 Forbidden; mã lỗi `INVALID_SIGNATURE`; giao diện báo lỗi chữ ký, loa phát Beep trầm | **PASS** | [Xem ảnh tc13.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc13.png) |
| **TC14** | Check-in cổng | Quét QR đúng chữ ký nhưng sai sự kiện | Dùng vé sự kiện A để check-in tại cổng sự kiện B | HTTP 403 Forbidden; mã lỗi `EVENT_MISMATCH`; từ chối check-in; loa phát Beep trầm | **PASS** | [Xem ảnh tc14.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc14.png) |
| **TC15** | Check-in cổng | Chữ ký đúng nhưng vé không có trong DB | Check-in mã vé đã bị xóa khỏi DynamoDB | HTTP 404 Not Found; mã lỗi `TICKET_NOT_FOUND`; giao diện thông báo không tìm thấy vé | **PASS** | [Xem ảnh tc15.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc15.png) |
| **TC16** | Check-in cổng | Mã QR sai định dạng hoặc sai version | Quét chuỗi text rác (URL thường, không có prefix `v1.`) | HTTP 400 Bad Request; mã lỗi `INVALID_INPUT`; loa phát Beep trầm 330Hz | **PASS** | [Xem ảnh tc16.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc16.png) |
| **TC17** | Bảo mật API | Gọi route ban tổ chức thiếu API Key | Gửi `POST /events` không có header `x-api-key` | HTTP 403 Forbidden từ API Gateway (`{"message":"Forbidden"}`) | **PASS** | [Xem ảnh tc17.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc17.png) |
| **TC18** | Bảo mật API | Vượt ngưỡng tải API (Throttling Test) | Bắn burst 100 request song song trong 1 giây | HTTP 429 Too Many Requests từ API Gateway (`{"message":"Too Many Requests"}`) | **PASS** | [Xem ảnh tc18.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc18.png) |
| **TC19** | Thống kê | Thống kê số liệu trạng thái vé | Mở `stats.html` hoặc gọi `GET /stats/{eventId}` | HTTP 200 OK; Dashboard hiển thị chính xác tổng số vé, số vé đã check-in và chưa check-in | **PASS** | [Xem ảnh tc19.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc19.png) |
| **TC20** | Thống kê | Thống kê sự kiện vừa tạo rỗng (0 vé) | Gọi `GET /stats/{eventId}` của sự kiện mới tinh | HTTP 200 OK; trả về chuẩn xác `totalTickets: 0, checkedInTickets: 0, notCheckedInTickets: 0` | **PASS** | [Xem ảnh tc20.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc20.png) |
| **TC21** | Hiển thị vé | Tự làm mới khi Presigned URL ảnh hết hạn | Bấm nút "Tải lại ảnh QR" trên trang `ticket.html` | HTTP 200 OK; Lambda `get-ticket` sinh link ký mới từ S3; ảnh QR hiển thị rõ nét, không bị vỡ ảnh | **PASS** | [Xem ảnh tc21.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/tc21.png) |

---
*Tài liệu nghiệm thu được lưu trữ chính thức tại repo GitHub: `quangbru376-blip/eventqr`.*
