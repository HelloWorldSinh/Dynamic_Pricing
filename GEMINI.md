# Gemini / Antigravity Agent Rules

> **Toàn bộ quy tắc dự án đã được gộp vào file `AGENTS.md`** — file chuẩn chung cho
> mọi AI agent (Claude, Gemini, Copilot, Cursor...).
>
> File này được giữ lại để Antigravity/Gemini nhận diện workspace.
> Nếu cần thêm quy tắc **chỉ dành riêng cho Gemini**, hãy viết bên dưới.

Xem: [AGENTS.md](./AGENTS.md)

---

## Cấu Hình & Quy Tắc Riêng Cho Antigravity / Gemini

### 1. Tự Động Đọc File & Tránh Terminal Popup Prompt
- **NGHIÊM CẤM:** Không dùng `run_command` chạy các lệnh shell (`Get-ChildItem`, `dir`, `cat`, `type`, `ls`) chỉ để đọc file hoặc liệt kê thư mục, vì sẽ kích hoạt popup yêu cầu người dùng xác nhận cấp quyền.
- **BẮT BUỘC:** Luôn sử dụng công cụ đọc gốc **`view_file`** hoặc MCP **`codegraph_explore`** để đọc và khám phá codebase. Các công cụ này chạy ngầm tự động 100%, không yêu cầu người dùng bấm Approve.

