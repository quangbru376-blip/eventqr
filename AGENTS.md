# AGENTS.MD — ENTRY POINT CHO AI ASSISTANT / AGENT

Dự án này sử dụng hệ thống bộ nhớ ngữ cảnh chuyên sâu (**Project Memory**) được lưu trữ tập trung tại thư mục [`project_memory/`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/).

---

## ⚡ QUY TẮC KHỞI ĐỘNG BẮT BUỘC (BOOTSTRAPPING)

Mọi AI Assistant / Agent (Claude, ChatGPT, Cursor, Gemini, Copilot, Antigravity, OpenHands...) khi tham gia vào workspace này **BẮT BUỘC** thực hiện các bước sau trước khi đề xuất giải pháp hoặc viết mã:

1. **Đọc quy chuẩn làm việc & giao thức Agent:**
   - [`project_memory/agent.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/agent.md) — Phong cách phản biện trung thực, phân định rõ thực tế vs giả định, và **Write-back Protocol**.
2. **Đọc bộ nhớ ngữ cảnh toàn diện:**
   - [`project_memory/project-memory.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/project-memory.md) — Toàn bộ kiến trúc, 10 quyết định kỹ thuật đã chốt, điều đã kiểm chứng vs chưa kiểm chứng trên AWS Learner Lab, và **Mục 14 (Trạng thái hiện tại)**.
3. **Đọc kế hoạch 4 tuần & checklist công việc:**
   - [`docs/plan.md`](file:///c:/Study/CLCO/final_workplace/eventqr/docs/plan.md) (Master Plan chính thức) hoặc [`project_memory/roadmap.md`](file:///c:/Study/CLCO/final_workplace/eventqr/project_memory/roadmap.md).
4. **Kiểm tra nhật ký tuần gần nhất:**
   - [`worklog/week2/worklog_markdown.md`](file:///c:/Study/CLCO/final_workplace/eventqr/worklog/week2/worklog_markdown.md) để biết task gần nhất đã xong và tiến độ giờ của từng thành viên.

---

## 📌 TÓM TẮT NHANH VỀ DỰ ÁN

- **Tên dự án:** EventQR — Quản lý sự kiện và check-in bằng QR code (Serverless trên AWS).
- **Môn học:** Cloud Computing (Đợt 1, 2026–2027) — GVHD: TS. Huỳnh Xuân Phụng.
- **Thành viên:**
  - **Đặng Duy Quang (MSSV: 24110307)** — Vai trò **A** (Lead, phụ trách vé & dữ liệu: DynamoDB, Secrets Manager, HMAC, `create-event`, `register`, `checkin`, `stats`, tài khoản AWS chính chạy demo).
  - **Trương Hoàng Long (MSSV: 24110273)** — Vai trò **B** (Phụ trách gửi vé & giao diện: S3, SNS, CloudFront, CloudWatch, `generate-qr`, `get-ticket`, `resend`, frontend web).
- **Ràng buộc kỹ thuật bất khả xâm phạm:**
  1. Chỉ dùng vùng `us-east-1`.
  2. Chỉ dùng IAM role có sẵn `LabRole`. **Tuyệt đối không tạo IAM User, Role hay Policy mới**.
  3. Ngân sách tối đa **50 USD/tài khoản sinh viên**.
  4. DynamoDB dùng chế độ **On-demand** (Pay-per-request).
  5. Mọi tài nguyên có tiền tố `eventqr-` và gắn tag `Project=EventQR`, `Owner=<Tên_SV>`.
  6. **Không hardcode** khóa HMAC, AWS credentials, Account ID hay ARN trong mã nguồn/Git/chat/log.
  7. Không đặt Lambda vào VPC (để tránh chi phí NAT Gateway và giữ kết nối SNS, Secrets Manager, DynamoDB).
  8. Chống check-in trùng bằng `UpdateItem` có `ConditionExpression` trong DynamoDB.
  9. Phản hồi bằng **tiếng Việt**, thẳng thắn phản biện trung thực, phân biệt rõ điều đã kiểm chứng trên lab với điều chưa kiểm chứng.

---

## 🔄 GIAO THỨC ĐỒNG BỘ CUỐI PHIÊN (WRITE-BACK PROTOCOL)

Sau khi hoàn thành tác vụ kỹ thuật hoặc kết thúc phiên làm việc, Agent **bắt buộc** cập nhật lại:
1. `worklog/weekX/worklog_markdown.md`: Thêm dòng nhật ký công việc (nội dung, số giờ, ghi chú hỗ trợ AI).
2. `project_memory/project-memory.md`: Cập nhật **Mục 14 (Trạng thái hiện tại)** và **Mục 15**.
3. `project_memory/roadmap.md` hoặc `docs/plan.md`: Đánh dấu checklist `[x]`.
4. Để lại ghi chú bàn giao (Handoff Note) ở cuối câu trả lời cho phiên tiếp theo.
