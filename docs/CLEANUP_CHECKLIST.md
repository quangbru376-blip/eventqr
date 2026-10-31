# CHECKLIST DỌN DẸP TÀI NGUYÊN LAB (CLEANUP CHECKLIST) — EVENTQR

> **Dự án:** EventQR — Quản lý sự kiện và check-in bằng mã QR (AWS Serverless)  
> **Môn học:** Cloud Computing (Đợt 1, 2026–2027) — GVHD: TS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Đặng Duy Quang (24110307) & Trương Hoàng Long (24110273)  
> **Quy định môn học:** Gắn tag đầy đủ; dừng/xóa tài nguyên sau khi kết thúc môn; báo cáo chi phí và lưu minh chứng console sạch sẽ.

---

> [!CAUTION]
> **LƯU Ý QUAN TRỌNG:**  
> Chỉ thực hiện các bước dọn dẹp dưới đây **SAU KHI ĐÃ HOÀN THÀNH QUAY VIDEO DEMO VÀ BẢO VỆ/VẤN ĐÁP MÔN HỌC THÀNH CÔNG**. Không xóa tài nguyên khi Giảng viên chưa chấm xong đồ án.

---

## 📋 1. BẢNG CHECKLIST DỌN DẸP THEO THỨ TỰ TỐI ƯU

Để tránh phát sinh lỗi phụ thuộc tài nguyên (Dependency Violation), thực hiện xóa lần lượt từ Bước 1 đến Bước 7:

- [x] **Bước 1: Amazon S3 (Xóa 2 Buckets)**
  
  - Bucket ảnh QR: `eventqr-qr-<AccountID>`
  - Bucket giao diện web: `eventqr-web-<AccountID>`
  - *Thao tác:*
    1. Vào S3 Console $\rightarrow$ Chọn bucket $\rightarrow$ Bấm nút **Empty** (Xóa sạch toàn bộ objects và versions bên trong).
    2. Sau khi bucket đã rỗng, bấm nút **Delete** $\rightarrow$ Gõ tên bucket để xác nhận xóa vĩnh viễn.

- [x] **Bước 2: Amazon API Gateway (Xóa REST API, Usage Plan & Key)**
  
  - REST API: `eventqr-api` (stage `v1`)
  - Usage Plan: `eventqr-usage-plan`
  - API Key: `eventqr-organizer-key`
  - *Thao tác:*
    1. Vào mục **API Keys** $\rightarrow$ Xóa key `eventqr-organizer-key`.
    2. Vào mục **Usage Plans** $\rightarrow$ Xóa plan `eventqr-usage-plan`.
    3. Vào mục **APIs** $\rightarrow$ Chọn `eventqr-api` $\rightarrow$ Actions $\rightarrow$ **Delete**.

- [x] **Bước 3: AWS Lambda (Xóa 8 hàm Lambda)**
  
  - 8 hàm nghiệp vụ có tiền tố `eventqr-`:
    1. `eventqr-create-event`
    2. `eventqr-register`
    3. `eventqr-generate-qr`
    4. `eventqr-get-ticket`
    5. `eventqr-resend`
    6. `eventqr-checkin`
    7. `eventqr-stats`
    8. `eventqr-web`
  - *Thao tác:* Tích chọn cả 8 hàm trong Lambda Console $\rightarrow$ Bấm **Actions** $\rightarrow$ **Delete** $\rightarrow$ Gõ `delete` để xác nhận.

- [x] **Bước 4: Amazon Simple Notification Service - SNS (Xóa Topic)**
  
  - Topic: `eventqr-ticket-delivery`
  - *Thao tác:* Chọn Topic $\rightarrow$ Bấm **Delete**. Toàn bộ Subscriptions (các email đã đăng ký) bên trong Topic sẽ tự động được giải phóng hoàn toàn.

- [x] **Bước 5: AWS Secrets Manager (Xóa Khóa HMAC)**
  
  - Secret: `eventqr-hmac-key`
  - *Thao tác:* Chọn Secret $\rightarrow$ **Actions** $\rightarrow$ **Delete secret** $\rightarrow$ Chọn chế độ **Delete immediately without recovery** (nếu có) hoặc đặt hạn xóa 7 ngày.
  - *Lý do:* Secrets Manager tính phí $0.40/tháng/secret nên đây là tài nguyên quan trọng cần dọn dẹp để không trừ credit ngầm.

- [x] **Bước 6: Amazon DynamoDB (Xóa 2 Bảng On-demand)**
  
  - Bảng sự kiện: `eventqr-events`
  - Bảng vé tham dự: `eventqr-tickets`
  - *Thao tác:* Chọn từng bảng $\rightarrow$ Bấm **Delete table** $\rightarrow$ Gõ `confirm` để xóa hoàn toàn dữ liệu.

- [x] **Bước 7: Amazon CloudWatch (Dọn dẹp Giám sát & Logs)**
  
  - Dashboard: `eventqr-dashboard` $\rightarrow$ Bấm **Delete**.
  - Alarms: Xóa 2 Alarms cảnh báo lỗi 5xx (`eventqr-*-errors`).
  - Log Groups: Vào mục **Log groups**, tích chọn các nhóm log có tiền tố `/aws/lambda/eventqr-*` $\rightarrow$ **Actions** $\rightarrow$ **Delete log group(s)**.
