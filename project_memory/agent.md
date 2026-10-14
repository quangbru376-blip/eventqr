# HƯỚNG DẪN DÀNH CHO AI AGENT (AGENT.MD) — DỰ ÁN EVENTQR

> **Dành cho mọi AI Assistant / Agent tiếp quản phiên làm việc mới**  
> Dự án: **EventQR** — Hệ thống quản lý sự kiện và check-in bằng QR code (AWS Serverless)  
> Môn học: Cloud Computing (Đợt 1, 2026–2027) — GVHD: TS. Huỳnh Xuân Phụng  
> Cập nhật lần cuối: 13/10/2026

Tài liệu này là **quy chuẩn bắt buộc** giúp bất kỳ Agent nào khi tham gia vào dự án đều hiểu ngay ngữ cảnh, cách tư duy, phong cách giao tiếp và **giao thức ghi lại nhật ký/trạng thái** để không bị mất thông tin giữa các phiên chat.

---

## 1. Quy trình khởi động (Bootstrapping Protocol)

Mỗi khi bắt đầu một phiên chat mới, Agent **BẮT BUỘC** thực hiện 4 bước sau trước khi đề xuất hoặc viết code:

1. **Bước 1: Đọc tài liệu Memory cốt lõi**
   - Đọc [`project_memory/agent.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/agent.md) (file này) để nắm luật làm việc.
   - Đọc [`project_memory/project-memory.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/project-memory.md) để nắm toàn bộ bức tranh kiến trúc, vai trò, quyết định đã chốt và mục 14 (Trạng thái hiện tại).
   - Đọc [`project_memory/roadmap.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/roadmap.md) để biết kế hoạch 4 tuần và các checklist công việc.

2. **Bước 2: Đối chiếu hiện trạng thực tế trong Workspace**
   - Kiểm tra thư mục `worklog/` của tuần hiện tại để biết task gần nhất đã hoàn thành.
   - Kiểm tra ngày hệ thống hiện tại và xác định dự án đang ở **Tuần mấy, Thứ mấy, mục tiêu trọng tâm là gì**.

3. **Bước 3: Xác định người đang trao đổi**
   - Người dùng trực tiếp là **Đặng Duy Quang (MSSV: 24110307)** — Vai trò **A** (Lead, phụ trách vé, dữ liệu, tài khoản AWS chính).
   - Bạn cùng nhóm là **Trương Hoàng Long (MSSV: 24110273)** — Vai trò **B** (Gửi vé qua SNS, sinh QR ra S3, giao diện web, giám sát CloudWatch).

4. **Bước 4: Báo cáo ngắn gọn điểm tiếp nhận (Quick Sync)**
   - Xác nhận với người dùng: *"Tôi đã đọc memory, xác định dự án đang ở [Tuần X], task tiếp theo là [Tên task]. Chúng ta bắt đầu làm [Nội dung cụ thể] chứ?"*

---

## 2. Quy chuẩn ứng xử và phong cách làm việc

Tuân thủ nghiêm ngặt các nguyên tắc sau (theo thỏa thuận từ đầu dự án):

- **Ngôn ngữ & Hình thức:** Trả lời bằng **tiếng Việt**, văn bản thuần markdown (không dùng widget giả lập, không đồ họa không cần thiết).
- **Phản biện trung thực (Honest Critique):** Người dùng yêu cầu thẳng thắn phản biện. Nếu phát hiện rủi ro kỹ thuật, lỗ hổng bảo mật, cấu hình vượt giới hạn Learner Lab hoặc thiết kế không hợp lý, phải chỉ rõ ngay; tuyệt đối không khen vu vơ, không dễ dãi đồng ý với phương án sai.
- **Ranh giới thực tế vs Giả định:** Luôn phân biệt rõ điều **đã kiểm chứng** trên AWS Learner Lab với điều **chưa kiểm chứng**.
- **Clickable File Links:** Mọi file mã nguồn hoặc tài liệu được nhắc đến trong câu trả lời đều phải tạo link Markdown dạng `file:///absolute/path` (trên Windows dùng dấu `/`, ví dụ: [`naming.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/naming.md)).
- **Minh bạch AI (Bắt buộc theo quy chế môn học):** Mọi đoạn mã, tài liệu hoặc cấu hình do Agent hỗ trợ tạo ra phải được ghi chú rõ ràng để người dùng điền vào Worklog nộp giảng viên.

---

## 3. Ràng buộc kỹ thuật cốt lõi (Non-negotiable Constraints)

Mọi giải pháp kỹ thuật do Agent đưa ra phải tuân thủ tuyệt đối các ràng buộc của môi trường AWS Learner Lab:

1. **Vùng duy nhất:** `us-east-1`.
2. **Quyền hạn:** Chỉ dùng IAM role có sẵn `LabRole`. Tuyệt đối **không tạo IAM User, IAM Role hay IAM Policy mới**.
3. **Ngân sách:** Tối đa **50 USD** mỗi tài khoản sinh viên.
   - Ưu tiên kiến trúc Serverless để giảm thiểu chi phí khi nhàn rỗi.
   - Lambda phải cấu hình timeout hợp lý và reserved concurrency thấp (tránh retry lặp vô tận gây cạn tiền).
   - DynamoDB dùng chế độ **On-demand** (Pay-per-request).
4. **Quy ước đặt tên & Tag:**
   - Tuân thủ nghiêm ngặt [`docs/naming.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/naming.md): Tiền tố `eventqr-`.
   - Tag bắt buộc: `Project=EventQR`, `Owner=<Tên_SV>`.
5. **Bảo mật & Bí mật thông tin:**
   - **Tuyệt đối không lưu ra file, chat, git hay log:** Khóa HMAC bí mật, AWS Access Key, Secret Key, Session Token, Account ID thật.
   - Các biến cấu hình dùng qua Biến môi trường (Environment Variables) của Lambda và `config.js` ở frontend.
6. **Kiến trúc đã chốt:**
   - Web tĩnh: Lưu ở bucket private S3, phân phối qua CloudFront (hoặc Lambda web HTTPS nếu môi trường Lab gặp trở ngại OAC).
   - API: API Gateway REST API (`eventqr-api`, stage `v1`).
   - HMAC QR: Định dạng `v1.<eventId>.<ticketId>.<signature>` (HMAC-SHA256, base64url không padding).
   - Chống check-in trùng: Thực hiện bằng `UpdateItem` có `ConditionExpression` trong DynamoDB, không phụ thuộc vào frontend.

---

## 4. Giao thức ghi nhận thao tác & Đồng bộ Memory (Write-back Protocol)

Để đảm bảo các Agent kế tiếp nắm được diễn biến và công việc không bị trùng lặp, **sau khi hoàn thành một tác vụ lớn hoặc kết thúc phiên làm việc**, Agent phải thực hiện quy trình sau:

### 4.1. Cập nhật Worklog tuần (`worklog/weekX/worklog_markdown.md`)
Mỗi công việc kỹ thuật đã làm phải được thêm vào bảng nhật ký công việc của tuần tương ứng:
- **Người làm:** Đặng Duy Quang hoặc Trương Hoàng Long.
- **Chi tiết công việc:** Mô tả cụ thể chức năng đã làm (kèm tên Lambda / bảng / file).
- **Số giờ:** Số giờ thực tế (mỗi tuần mỗi bạn phải đạt $\ge 8$ giờ).
- **Trạng thái:** `Hoàn thành` hoặc `Đang xử lý`.
- **Ghi chú AI:** Ghi rõ nội dung AI hỗ trợ (ví dụ: *AI sinh khung mã Lambda và viết test case cục bộ*).
- **Link dẫn chứng:** Link tới file trong repo hoặc ảnh chụp trong `docs/evidence/`.

### 4.2. Cập nhật Trạng thái trong `project_memory/project-memory.md`
Agent cập nhật **Mục 14 (Trạng thái hiện tại)**:
- Ghi nhận những phần việc vừa hoàn thành.
- Ghi nhận các lỗi phát sinh vừa xử lý xong hoặc đang chờ kiểm chứng.
- Cập nhật số dư credit AWS (nếu người dùng cung cấp).

### 4.3. Cập nhật Checklist trong `project_memory/roadmap.md`
- Đánh dấu `[x]` vào các đầu việc đã hoàn tất.
- Nếu có điều chỉnh về thứ tự ưu tiên hoặc thời gian, cập nhật trực tiếp vào roadmap.

### 4.4. Tóm tắt bàn giao cuối phiên (Handoff Note)
Trước khi kết thúc câu trả lời cuối cùng của phiên, Agent cần để lại một đoạn tóm tắt bàn giao ngắn:
```markdown
### 📌 BÀN GIAO CHO PHIÊN TIẾP THEO:
- Việc đã xong trong phiên này: ...
- Trạng thái mã nguồn / AWS hiện tại: ...
- Việc cần làm ngay ở phiên tiếp theo: ...
```

---

## 5. Danh mục tài liệu tham chiếu nhanh

- [Kiến trúc hệ thống](file:///c:/Study/CLCO/final_workplace/eventqr/docs/evidence/week1/architecture.md)
- [Đặc tả API v0.2](file:///c:/Study/CLCO/final_workplace/eventqr/docs/api.md)
- [Quy ước đặt tên & Tag](file:///c:/Study/CLCO/final_workplace/eventqr/docs/naming.md)
- [Bản ghi nhớ Memory chính](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/project-memory.md)
- [Lộ trình 4 tuần chi tiết (Roadmap)](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/roadmap.md)
- [Kế hoạch tổng thể cập nhật hằng tuần (Master Plan)](file:///c:/Study/CLCO/final_workplace/eventqr/docs/plan.md)
- [Nhật ký tuần 1](file:///c:/Study/CLCO/final_workplace/eventqr/worklog/week1/worklog_markdown.md)
- [Nhật ký tuần 2](file:///c:/Study/CLCO/final_workplace/eventqr/worklog/week2/worklog_markdown.md)
