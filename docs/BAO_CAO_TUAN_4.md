# BÁO CÁO NGHIỆM THU ĐỒ ÁN MÔN HỌC — TUẦN 4

> **Môn học:** Điện toán đám mây (Cloud Computing) — Đợt 1, Năm học 2026–2027  
> **Giảng viên hướng dẫn:** TS. Huỳnh Xuân Phụng  
> **Tên đề tài:** EventQR — Hệ thống quản lý sự kiện và check-in bằng mã QR (AWS Serverless)  
> **Thời gian thực hiện Tuần 4:** 26/10/2026 – 01/11/2026  
> **Repository GitHub (Public):** [https://github.com/quangbru376-blip/eventqr](https://github.com/quangbru376-blip/eventqr)  

### THÔNG TIN NHÓM SINH VIÊN:

1. **Đặng Duy Quang (MSSV: 24110307)** — **Vai trò A (Lead)**: Phụ trách cấu trúc vé, DynamoDB, Secrets Manager HMAC, API tạo sự kiện, đăng ký vé, check-in, thống kê, tài khoản AWS chính và nghiệm thu hệ thống.
2. **Trương Hoàng Long (MSSV: 24110273)** — **Vai trò B**: Phụ trách lưu trữ ảnh S3, gửi vé SNS Email, giao diện web HTML/JS, giám sát CloudWatch, âm thanh Web Audio Beep và Video Demo.

---

## I. CÁC ĐƯỜNG DẪN HỒ SƠ NỘP BÀI CHÍNH THỨC

- **Link Video Demo ($\le$ 10 phút):** [https://youtu.be/smI9ZXoDlLg](https://youtu.be/smI9ZXoDlLg)
- **Bảng ma trận 21 ca kiểm thử có link ảnh GitHub:** [docs/TEST_RESULTS.md](https://github.com/quangbru376-blip/eventqr/blob/main/docs/TEST_RESULTS.md)
- **Checklist dọn dẹp tài nguyên (Cleanup):** [docs/CLEANUP_CHECKLIST.md](https://github.com/quangbru376-blip/eventqr/blob/main/docs/CLEANUP_CHECKLIST.md)
- **Thư mục lưu trữ 21 ảnh minh chứng thực tế:** [docs/evidence/week4/](https://github.com/quangbru376-blip/eventqr/tree/main/docs/evidence/week4)

---

## II. BÁO CÁO CHI PHÍ AWS THỰC TẾ (CREDIT BILLING)

- **Hạn mức tài khoản sinh viên được cấp (Budget):** `50.00 USD`
- **Chi phí thực tế tiêu thụ ghi nhận trên Vocareum:** **`0.30 USD`**
- **Số dư tín chỉ khả dụng còn lại:** **`49.70 USD`** (Tiêu tốn **0.6%** tổng ngân sách).
- **Minh chứng ảnh chụp màn hình Credit:** [docs/evidence/week4/credit_billing.png](https://github.com/quangbru376-blip/eventqr/blob/main/docs/evidence/week4/credit_billing.png)

---

## III. TỔNG KẾT NGHIỆM THU 21 CA KIỂM THỬ (MỤC 10 ĐẶC TẢ API)

Nhóm đã hoàn thành nghiệm thu **21/21 ca kiểm thử đạt kết quả PASS 100%** trên môi trường AWS thật:

- **Luồng 1 — API Gateway & Bảo vệ API (3 ca):** Chặn 403 khi thiếu API Key (TC17), thống kê sự kiện rỗng 0/0/0 (TC20), kích hoạt Throttling 429 Too Many Requests khi DoS 100 request (TC18).
- **Luồng 2 — Đăng ký vé & SNS Email (9 ca):** Validation thiếu trường 400 (TC03), sự kiện không tồn tại 404 (TC04), an toàn thứ tự S3 trước DB sau không sinh vé mồ côi (TC05), hoãn gửi SNS khi email chưa confirm 201 PENDING_CONFIRMATION (TC06), đăng ký thành công (TC01), đăng ký vé thứ 2 cùng email (TC02), gửi lại vé sau khi confirm (TC07), phân tách Filter Policy SNS giữa 2 email (TC08), xử lý bền vững khi SNS lỗi (TC09).
- **Luồng 3 — Soát vé Camera & Chống trùng HMAC (7 ca):** Chặn QR sai version/format 400 (TC16), chặn sửa chữ ký HMAC 403 (TC13), chặn check-in sai sự kiện 403 (TC14), vé không tồn tại trong DB 404 (TC15), check-in vé hợp lệ lần đầu kèm tiếng **Beep cao 880Hz** (TC10), quét lại chặn trùng vé 409 kèm tiếng **Beep trầm 330Hz** (TC11), hai thiết bị check-in đồng thời Race Condition: 1 máy xanh 200, 1 máy đỏ 409 (TC12).
- **Luồng 4 — Thống kê & S3 Presigned URL (2 ca):** Thống kê số liệu trạng thái vé theo thời gian thực (TC19), tự động làm mới Presigned URL ảnh S3 sau khi hết hạn (TC21).

*(Chi tiết từng ca và đường dẫn ảnh minh chứng xem tại file [`docs/TEST_RESULTS.md`](TEST_RESULTS.md)).*

---

## IV. KẾ HOẠCH DỌN DẸP TÀI NGUYÊN (CLEANUP CHECKLIST)

Sau khi hoàn tất bảo vệ và vấn đáp đồ án với Giảng viên, nhóm sẽ thực thi quy trình dọn dẹp 7 bước:

1. **Amazon S3:** Empty toàn bộ objects trong 2 bucket `eventqr-qr-*` và `eventqr-web-*`, sau đó xóa bucket.
2. **API Gateway:** Xóa API Key `eventqr-organizer-key`, Usage Plan `eventqr-usage-plan` và REST API `eventqr-api`.
3. **AWS Lambda:** Xóa 8 hàm Lambda có tiền tố `eventqr-`.
4. **Amazon SNS:** Xóa Topic `eventqr-ticket-delivery`.
5. **AWS Secrets Manager:** Xóa Secret `eventqr-hmac-key` (Force delete without recovery).
6. **Amazon DynamoDB:** Xóa 2 bảng `eventqr-events` và `eventqr-tickets`.
7. **Amazon CloudWatch:** Xóa Dashboard `eventqr-dashboard`, 2 Alarms 5xx và các Log groups.

*(Chi tiết quy trình và script tự động xem tại file [`docs/CLEANUP_CHECKLIST.md`](CLEANUP_CHECKLIST.md)).*

---

## V. NHẬT KÝ CÔNG VIỆC CHI TIẾT TUẦN 4 (WORKLOG)

*(Định dạng chuẩn theo cấu trúc báo cáo Report.docx của các tuần trước)*

### 1. Thống kê tổng hợp Tuần 4

| Nhân sự               | Vai trò                                        | Số tác vụ | Hoàn thành | Đang xử lý | Tỷ lệ HT | Tổng số giờ | Giờ TB/Tác vụ |
|:--------------------- |:---------------------------------------------- |:---------:|:----------:|:----------:|:--------:|:-----------:|:-------------:|
| **Đặng Duy Quang**    | A (Lead, Backend, Nghiệm thu 21 ca & Báo cáo)  | 8         | 8          | 0          | 100%     | **11,00 h** | 1,38 h        |
| **Trương Hoàng Long** | B (Web UI, Audio Beep, Tái lập hạ tầng & Demo) | 8         | 8          | 0          | 100%     | **11,50 h** | 1,44 h        |
| **Tổng cộng**         |                                                | **16**    | **16**     | **0**      | **100%** | **22,50 h** | **1,41 h**    |

---

### 2. Vai trò A — Backend, Nghiệm thu 21 ca & Báo cáo chi phí (Đặng Duy Quang)

| Mã        | Ngày thực hiện | Chi tiết công việc                                                                                                                                                                                                                      | Kết quả và mức xác nhận cập nhật                                                                                 | Giờ thực tế | Ghi chú và dẫn chứng                                                                                                                                                                                                       |
|:---------:|:--------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:---------------------------------------------------------------------------------------------------------------- |:-----------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A4-01** | 26/10/2026     | Rà soát toàn bộ 21 tình huống kiểm thử trong Mục 10 đặc tả `docs/api.md`; xây dựng kế hoạch kiểm thử 4 luồng chi tiết (`test-plan.md`) và bảng ma trận nghiệm thu (`test-matrix.md`).                                                   | Ban hành kế hoạch kiểm thử chi tiết 4 luồng, quy chuẩn tên ảnh `tc01.png` - `tc21.png`.                          | 1,50h       | [`test-plan.md`](../project_memory/test-plan.md); [`test-matrix.md`](../project_memory/test-matrix.md)                                                                                                                     |
| **A4-02** | 27/10/2026     | Nghiệm thu Luồng 1 (Bảo mật API Gateway & Throttling): kiểm thử chặn 403 thiếu key (TC17), khởi tạo sự kiện cơ sở, kiểm tra thống kê ban đầu 0/0/0 (TC20), và chạy kiểm thử DoS kích hoạt 429 Too Many Requests (TC18).                 | Hoàn thành 3/3 ca Luồng 1; nâng `DefaultConnectionLimit` PowerShell lên 100 để kích hoạt thành công 429.         | 2,00h       | [Minh chứng TC17](evidence/week4/tc17.png); [Minh chứng TC18](evidence/week4/tc18.png); [Minh chứng TC20](evidence/week4/tc20.png)                                                                                         |
| **A4-03** | 28/10/2026     | Nghiệm thu Luồng 2 (Đăng ký vé & Xử lý SNS): kiểm thử validation thiếu trường 400 (TC03), sự kiện không tồn tại 404 (TC04), cơ chế fail-safe không sinh vé mồ côi (TC05), và đăng ký vé mới với trạng thái PENDING_CONFIRMATION (TC06). | Hoàn thành 4 ca đầu Luồng 2; kiểm chứng thành công logic an toàn thứ tự S3 trước DynamoDB sau.                   | 1,50h       | [Minh chứng TC03](evidence/week4/tc03.png); [Minh chứng TC04](evidence/week4/tc04.png); [Minh chứng TC05](evidence/week4/tc05.png); [Minh chứng TC06](evidence/week4/tc06.png)                                             |
| **A4-04** | 29/10/2026     | Tiếp tục nghiệm thu Luồng 2: kiểm thử đăng ký vé hợp lệ (TC01), cùng email đăng ký vé thứ 2 (TC02), gửi lại vé sau khi confirm SNS (TC07), kiểm tra phân tách Filter Policy SNS (TC08), và cơ chế bền vững khi SNS lỗi (TC09).          | Hoàn thành toàn bộ 9/9 ca Luồng 2; xác nhận email vé thật nhận trong hộp thư Gmail từ AWS Notifications.         | 1,50h       | [Minh chứng TC01](evidence/week4/tc01.png); [Minh chứng TC02](evidence/week4/tc02.png); [Minh chứng TC07](evidence/week4/tc07.png); [Minh chứng TC08](evidence/week4/tc08.png); [Minh chứng TC09](evidence/week4/tc09.png) |
| **A4-05** | 30/10/2026     | Nghiệm thu Luồng 3 (Soát vé & Chống trùng HMAC): kiểm thử chặn QR sai định dạng 400 (TC16), chặn QR bị sửa chữ ký 403 (TC13), chặn QR sai sự kiện 403 (TC14), và kiểm tra vé không có trong DB 404 (TC15).                              | Backend phát hiện chính xác mọi hành vi gian lận mã QR; chữ ký HMAC-SHA256 bảo vệ toàn vẹn tuyệt đối dữ liệu vé. | 1,50h       | [Minh chứng TC13](evidence/week4/tc13.png); [Minh chứng TC14](evidence/week4/tc14.png); [Minh chứng TC15](evidence/week4/tc15.png); [Minh chứng TC16](evidence/week4/tc16.png)                                             |
| **A4-06** | 31/10/2026     | Hoàn tất Luồng 3 & 4: check-in vé lần đầu (TC10), quét lại báo trùng 409 (TC11), hai thiết bị check-in đồng thời Race Condition (TC12), thống kê sự kiện (TC19) và làm mới Presigned URL ảnh S3 sau khi hết hạn (TC21).                 | Đạt mốc **21/21 ca kiểm thử PASS 100%**; lưu trữ đầy đủ 21 ảnh chụp màn hình minh chứng trong repo GitHub.       | 1,50h       | [Minh chứng TC10](evidence/week4/tc10.png); [Minh chứng TC11](evidence/week4/tc11.png); [Minh chứng TC12](evidence/week4/tc12.png); [Minh chứng TC19](evidence/week4/tc19.png); [Minh chứng TC21](evidence/week4/tc21.png) |
| **A4-07** | 31/10/2026     | Tổng hợp và trích xuất số liệu chi phí thực tế trên Vocareum: đối chiếu chi phí thực tế (0.30 USD) với hạn mức 50 USD; phân tích hiệu quả kinh tế của kiến trúc Serverless (không NAT Gateway, DynamoDB On-demand).                     | Xác nhận chi phí thực tế cực thấp: chỉ tiêu tốn 0.6% ngân sách lab được cấp (0.30$/50.00$).                      | 0,75h       | Vocareum hiển thị: `Cloud Credits: $49.70 Remaining / $50.00 Budget`. [Minh chứng credit](evidence/week4/credit_billing.png)                                                                                               |
| **A4-08** | 01/11/2026     | Soạn thảo kịch bản Video Demo solo $\le$ 10 phút chi tiết từng mốc thời gian; tổng hợp Báo cáo nghiệm thu Tuần 4 và checklist dọn dẹp tài nguyên sau vấn đáp.                                                                           | Kịch bản video 9 phút 15 giây bao quát toàn bộ đề tài; tài liệu dọn dẹp sẵn sàng thực thi sau buổi bảo vệ.       | 0,75h       | [`BAO_CAO_TUAN_4.md`](BAO_CAO_TUAN_4.md); [`CLEANUP_CHECKLIST.md`](CLEANUP_CHECKLIST.md)                                                                                                                                   |

---

### 3. Vai trò B — Web UI, Audio Beep, Tái lập hạ tầng & Video Demo (Trương Hoàng Long)

| Mã        | Ngày thực hiện | Chi tiết công việc                                                                                                                                                                                     | Kết quả và mức xác nhận cập nhật                                                                                                       | Giờ thực tế | Ghi chú và dẫn chứng                                                                                                   |
|:---------:|:--------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |:-------------------------------------------------------------------------------------------------------------------------------------- |:-----------:|:---------------------------------------------------------------------------------------------------------------------- |
| **B4-01** | 26/10/2026     | Tích hợp âm thanh phản hồi (Audio Beep) vào `frontend/checkin.js` bằng Web Audio API thuần: tạo sóng âm tần số cao 880Hz (thành công) và sóng tần số trầm 330Hz (thất bại/trùng vé).                   | Phát âm thanh trực tiếp trên trình duyệt mà không cần file MP3 hay thư viện ngoài; hỗ trợ nhân viên soát vé nhận biết tức thì kết quả. | 1,50h       | Tối ưu `AudioContext.resume()` và `setValueAtTime` chống ngắt âm trên Chromium. [`checkin.js`](../frontend/checkin.js) |
| **B4-02** | 27/10/2026     | Kiểm thử giao diện web trên thiết bị di động thật: kiểm tra hiển thị responsive của 4 trang HTML, kiểm tra quyền camera HTTPS trên trình duyệt điện thoại.                                             | Giao diện hiển thị rõ ràng trên mobile; camera quét mã QR nhạy bén dưới các điều kiện ánh sáng khác nhau.                              | 1,50h       | [Giao diện Web](../frontend/)                                                                                          |
| **B4-03** | 28/10/2026     | Phối hợp cùng Quang kiểm thử nghiệm thu các ca SNS Email (TC06, TC07, TC08): xác nhận đăng ký email thật, bấm confirm subscription và kiểm tra tính năng gửi lại vé (`POST /resend`).                  | Email thông báo từ AWS Notifications đến đúng hộp thư; bộ lọc Filter Policy hoạt động chính xác giữa 2 email của nhóm.                 | 1,50h       | [Minh chứng TC07](evidence/week4/tc07.png); [Minh chứng TC08](evidence/week4/tc08.png)                                 |
| **B4-04** | 29/10/2026     | Rà soát cấu hình CloudWatch: kiểm tra thời gian lưu log 7 ngày, kiểm tra tính chính xác của các widget trên Dashboard `eventqr-dashboard` và trạng thái hoạt động của 2 CloudWatch Alarms.             | Dashboard phản ánh đầy đủ lưu lượng gọi API và thời gian thực thi; không có lỗi 5xx vượt ngưỡng cảnh báo.                              | 1,50h       | [Minh chứng Dashboard](evidence/week3/dashboard.png); [Minh chứng Alarms](evidence/week3/alarm.png)                    |
| **B4-05** | 30/10/2026     | Tái lập toàn bộ hạ tầng Serverless trên tài khoản dự phòng B (Long) từ mã nguồn Git để phục vụ quay Live Demo và dự phòng sự cố session lab: tạo DynamoDB, S3, Secrets Manager, Lambda, API Gateway.   | Toàn bộ hệ thống chạy live thông suốt trên tài khoản B; chứng minh khả năng tái lập và tính di động của mã nguồn đồ án.                | 2,00h       | Dùng `LabRole` có sẵn; kiểm tra chéo API URL và các route hoạt động 100%.                                              |
| **B4-06** | 31/10/2026     | Thực hiện kiểm thử Race Condition (TC12) và Thống kê (TC19): sử dụng 2 thiết bị gửi đồng thời yêu cầu check-in để đối chiếu phản hồi 200 vs 409; kiểm tra hiển thị số liệu thống kê trên `stats.html`. | Minh chứng 2 thiết bị đặt cạnh nhau phản ánh trung thực tính atomic của DynamoDB; Dashboard hiển thị đúng số liệu vé.                  | 1,50h       | [Minh chứng TC12](evidence/week4/tc12.png); [Minh chứng TC19](evidence/week4/tc19.png)                                 |
| **B4-07** | 01/11/2026     | Hỗ trợ chuẩn bị phòng quay, kiểm tra chất lượng âm thanh Desktop Audio và hình ảnh phục vụ quay video demo; phối hợp chạy thử kịch bản demo 9 phút cùng Quang.                                         | Âm thanh tiếng beep 880Hz và 330Hz thu rõ nét; các bước demo diễn ra nhịp nhàng đúng thời lượng quy định $\le$ 10 phút.                | 1,00h       | [Kịch bản Video Demo](BAO_CAO_TUAN_4.md#i-các-đường-dẫn-hồ-sơ-nộp-bài-chính-thức)                                      |
| **B4-08** | 01/11/2026     | Rà soát toàn bộ tài nguyên đã tạo trên cả 2 tài khoản, chuẩn bị lệnh AWS CLI và các bước xóa bucket S3 để sẵn sàng dọn dẹp tài nguyên sau buổi vấn đáp.                                                | Hoàn thiện tài liệu hướng dẫn dọn dẹp an toàn; đảm bảo không phát sinh chi phí ngầm sau khi kết thúc môn học.                          | 1,00h       | [`CLEANUP_CHECKLIST.md`](CLEANUP_CHECKLIST.md)                                                                         |
