# GITHUB COPILOT INSTRUCTIONS — EVENTQR

Tất cả các gợi ý mã nguồn và hỗ trợ kỹ thuật phải tuân theo bộ nhớ dự án và quy chuẩn sau:
- Tham khảo hướng dẫn chính tại: [`AGENTS.md`](../AGENTS.md)
- Tham khảo hướng dẫn chi tiết: [`project_memory/agent.md`](../project_memory/agent.md)
- Tham khảo kiến trúc và trạng thái: [`project_memory/project-memory.md`](../project_memory/project-memory.md)
- Tham khảo kế hoạch triển khai: [`docs/plan.md`](../docs/plan.md)

Các ràng buộc kỹ thuật cốt lõi:
- AWS Learner Lab (`us-east-1`, chỉ dùng `LabRole`, không tạo IAM mới, ngân sách <= 50 USD/tài khoản).
- Tiền tố `eventqr-`, tag `Project=EventQR`, `Owner=<Tên_SV>`.
- Không hardcode secret/credentials vào mã nguồn.
- Chống check-in trùng bằng DynamoDB `UpdateItem` có `ConditionExpression`.
- Tuân thủ Write-back Protocol để cập nhật worklog và memory sau mỗi tác vụ lớn.
