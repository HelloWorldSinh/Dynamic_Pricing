# WORKSPACE RULES & AGENT WORKFLOW ENFORCEMENT

## 1. QUY TẮC BẮT BUỘC: SỬ DỤNG CODEGRAPH TRƯỚC TIÊN (CODEGRAPH FIRST)
Kho mã nguồn này đã được lập chỉ mục bởi CodeGraph (có thư mục `.codegraph/` tại root).
Khi người dùng có bất kỳ câu hỏi nào về:
- Tìm kiếm hàm, class, cấu trúc file, luồng xử lý
- Quan hệ phụ thuộc, luồng gọi hàm (Call Paths / Callers / Callees)
- Đánh giá mức độ ảnh hưởng trước khi sửa hoặc xóa code (Blast Radius)
- Tìm lỗi (debugging) hoặc khảo sát kiến trúc

👉 **BẮT BUỘC**: Phải gọi công cụ MCP `codegraph_explore` (hoặc lệnh shell `codegraph explore "<query>"`) TRƯỚC TIÊN.  
👉 **NGHIÊM CẤM**: Không dùng `grep_search` hay đọc file `view_file` thủ công khi chưa chạy CodeGraph để định vị ngữ cảnh. Kết quả từ CodeGraph đã chứa mã nguồn kèm số dòng chính xác, hãy dùng trực tiếp mà không cần mở lại file nhiều lần.

---

## 2. KÍCH HOẠT VÀ TUÂN THỦ CÁC SKILL TRONG CODEBASE (.agents/skills/)
Trước khi thực hiện tác vụ, AI PHẢI chủ động đọc và áp dụng hướng dẫn từ file `SKILL.md` tương ứng trong `.agents/skills/`:
- **`regex-vs-llm-structured-text`**: Áp dụng triết lý phân tầng xử lý dữ liệu (Ưu tiên Regex Part-Number chính xác 100% $\rightarrow$ sau đó mới dùng Levenshtein / Fuzzy Matching cho cấu hình RAM/ROM).
- **`python-patterns`**: Tuân thủ chuẩn PEP 8, loại bỏ dead code, không để import rác, viết type hint rõ ràng.
- **`ai-regression-testing` & `python-testing`**: Viết và chạy test chống lỗi hồi quy, kiểm tra tính toàn vẹn của dữ liệu cào và thuật toán so khớp SKU.
- **`tdd-workflow`**: Phát triển tính năng mới theo chu trình Test-Driven Development (Red $\rightarrow$ Green $\rightarrow$ Refactor).
- **`search-first`**: Nghiên cứu và tận dụng các giải pháp, thư viện có sẵn trước khi tự viết code mới.

---

## 3. CHUẨN MỰC CHẤT LƯỢNG MÃ NGUỒN (CODE QUALITY & HYGIENE)
- Tuyệt đối không để lại `import` rác (unused imports).
- Không hardcode các nhãn giả lập (như fallback nhãn nguồn `"CELLPHONES"` trong module dùng chung).
- Giữ các hàm có trách nhiệm đơn nhất (Single Responsibility Principle).

---

## 4. BỘ KỸ NĂNG NÂNG CAO SUPERPOWERS (obra/superpowers)
Dự án đã tích hợp bộ kỹ năng **Superpowers** trong `.agents/skills/`:
- **`using-superpowers`**: Kích hoạt trước mỗi cuộc hội thoại, phân định quy trình tiếp cận trước khi code.
- **`brainstorming`**: Khảo sát yêu cầu, thiết kế giải pháp và phản biện ý tưởng trước khi lập kế hoạch.
- **`writing-plans` & `executing-plans`**: Lập kế hoạch chi tiết từng bước (task-by-task) và thực thi theo checklist.
- **`systematic-debugging`**: Quy trình 4 bước chẩn đoán gốc rễ lỗi (Root Cause Analysis) trước khi sửa code.
- **`test-driven-development`**: Luôn viết test kiểm thử trước khi bổ sung code tính năng.
- **`verification-before-completion`**: Chạy kiểm thử và chứng minh bằng bằng chứng thực tế trước khi tuyên bố hoàn thành task.

---

## 5. BỘ KỸ NĂNG KỸ THUẬT THỰC CHIẾN (mattpocock/skills)
Dự án đã tích hợp đầy đủ bộ kỹ năng từ **[mattpocock/skills](https://github.com/mattpocock/skills)** vào `.agents/skills/`:

### Agent Skills Configuration
- **Issue tracker**: Lưu trữ local markdown tại `.scratch/<feature-slug>/`. Chi tiết xem [docs/agents/issue-tracker.md](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/docs/agents/issue-tracker.md).
- **Triage labels**: 5 nhãn vai trò chuẩn (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). Chi tiết xem [docs/agents/triage-labels.md](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/docs/agents/triage-labels.md).
- **Domain docs**: Thiết lập đơn ngữ cảnh (single-context: `GLOSSARY.md` và `docs/adr/` tại root). Chi tiết xem [docs/agents/domain.md](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/docs/agents/domain.md).

### Các kỹ năng chủ đạo sẵn sàng sử dụng:
- **`ask-matt`**: Router hướng dẫn lựa chọn skill phù hợp nhất cho bài toán đang gặp.
- **`grill-with-docs` / `grill-me`**: Phỏng vấn sâu, thử thách mọi giả định thiết kế trước khi bắt đầu code và tự động cập nhật tài liệu ADR & GLOSSARY.
- **`domain-modeling`**: Xây dựng ngôn ngữ chung (ubiquitous language) trong `GLOSSARY.md` và lưu quyết định kiến trúc trong `docs/adr/`.
- **`codebase-design`**: Thiết kế deep modules, giảm độ phức tạp bề mặt giao diện, tăng tính độc lập và khả năng test.
- **`to-spec` & `to-tickets`**: Chuyển cuộc hội thoại thành đặc tả (spec) và các ticket theo mô hình tracer-bullet trong `.scratch/`.
- **`implement` / `implement-spec`**: Triển khai giải pháp theo các ticket / spec đã định hình.
- **`diagnosing-bugs`**: Vòng lặp điều tra lỗi sâu và hồi quy hiệu năng.
- **`improve-codebase-architecture`**: Quét cấu trúc module, tìm cơ hội làm sâu (deepening) và xuất báo cáo HTML.
- **`code-review`**: Đánh giá code theo 2 tiêu chí song song: Coding Standards và Specification.
- **`wayfinder`**: Điều phối tác vụ lớn vượt quá dung lượng 1 phiên làm việc thành bản đồ quyết định.

---

## 6. QUY TRÌNH PHÁT TRIỂN THEO ĐẶC TẢ SPEC KIT (github/spec-kit)
Dự án đã tích hợp bộ công cụ **[GitHub Spec Kit (Spec-Driven Development)](https://github.com/github/spec-kit)** vào hệ thống Agent qua cấu hình `.specify/` và các kỹ năng `speckit-*` trong `.agents/skills/`:

### Cấu hình và Cơ sở hạ tầng
- **Spec Kit root**: `.specify/` (lưu trữ templates, workflows, memory, scripts).
- **Specs directory**: `specs/<feature-slug>/` (lưu trữ spec, plan, tasks cho từng tính năng).
- **Project Constitution**: `.specify/memory/constitution.md` (Hiến chương quy chuẩn kỹ thuật và nguyên tắc kiến trúc cốt lõi).

### Chu trình phát triển Spec-Driven Development (SDD):
1. **`speckit-constitution`**: Thiết lập/cập nhật nguyên tắc kỹ thuật, ràng buộc kiến trúc cốt lõi của dự án.
2. **`speckit-specify`**: Sinh đặc tả tính năng (`spec.md`) từ mô tả tự nhiên của người dùng, xác định scope, scenarios và tiêu chuẩn thành công.
3. **`speckit-clarify`** *(Tuỳ chọn)*: Đặt câu hỏi cấu trúc để giải tỏa các điểm rủi ro/mơ hồ trước khi lập kế hoạch (giới hạn tối đa 3 câu hỏi trọng tâm).
4. **`speckit-plan`**: Chuyển spec thành bản thiết kế kỹ thuật và kiến trúc chi tiết (`plan.md`).
5. **`speckit-checklist`** *(Tuỳ chọn)*: Tạo checklist đánh giá độ hoàn thiện và tính khả thi của yêu cầu.
6. **`speckit-tasks`**: Bẻ nhỏ plan thành danh sách task hành động cụ thể (`tasks.md`) có dependency và thứ tự phase rõ ràng.
7. **`speckit-analyze`** *(Tuỳ chọn)*: Kiểm tra đối chiếu tính nhất quán giữa spec, plan và tasks trước khi code.
8. **`speckit-implement`**: Thực thi code và test theo từng task.
9. **`speckit-converge`**: Rà soát độ hội tụ giữa mã nguồn thực tế và spec, phát hiện các task còn sót để hoàn thành 100%.
10. **`speckit-taskstoissues`**: Xuất các tasks sang hệ thống issue tracker (hỗ trợ cả `.scratch/` và GitHub Issues).

