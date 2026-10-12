<!-- codegraph:start -->
# CodeGraph — Code Intelligence

This project is indexed by **CodeGraph** (indexed in `.codegraph/`).

## Always Do

- **CodeGraph First for Search & Architecture:**
  - Before editing, searching, or exploring the codebase, use CodeGraph CLI or MCP tools:
    - Search symbols & call paths: `codegraph explore "<query>"`
    - Find callers: `codegraph callers <symbol>`
    - Find callees: `codegraph callees <symbol>`
    - Analyze blast radius (impact analysis): `codegraph impact <symbol>`
    - Read a symbol or file with dependencies: `codegraph node <symbol_or_path>`
- **Sync index after changes:**
  - Run `codegraph sync` after non-trivial file changes, or `codegraph status` to check status.
- **MUST run impact analysis before editing or refactoring shared code:**
  - Run `codegraph impact <symbol>` to inspect all callers and dependents before modifying any function, class, or method.

## Never Do

- NEVER edit a shared function, class, or method before running `codegraph impact <symbol>`.
- NEVER substitute full-repo brute-force grep for graph analysis when searching for symbols and call chains.
- NEVER rename symbols blindly across the codebase without checking call paths with `codegraph callers <symbol>`.

## CLI Reference

| Task | Command |
| --- | --- |
| Explore area & call paths | `codegraph explore "<query>"` |
| Blast radius / Impact analysis | `codegraph impact <symbol>` |
| Find callers of a function | `codegraph callers <symbol>` |
| Find callees of a function | `codegraph callees <symbol>` |
| Inspect symbol node or file | `codegraph node <symbol_or_file>` |
| Check index status & stats | `codegraph status` |
| Sync updated files into index | `codegraph sync` |
| Rebuild index from scratch | `codegraph index` |

<!-- codegraph:end -->

---

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
- **`regex-vs-llm-structured-text`**: Áp dụng triết lý phân tầng xử lý dữ liệu (Ưu tiên Regex Part-Number chính xác 100% → sau đó mới dùng Levenshtein / Fuzzy Matching cho cấu hình RAM/ROM).
- **`python-patterns`**: Tuân thủ chuẩn PEP 8, loại bỏ dead code, không để import rác, viết type hint rõ ràng.
- **`ai-regression-testing` & `python-testing`**: Viết và chạy test chống lỗi hồi quy, kiểm tra tính toàn vẹn của dữ liệu cào và thuật toán so khớp SKU.
- **`tdd-workflow`**: Phát triển tính năng mới theo chu trình Test-Driven Development (Red → Green → Refactor).
- **`search-first`**: Nghiên cứu và tận dụng các giải pháp, thư viện có sẵn trước khi tự viết code mới.

---

## 3. CHUẨN MỰC CHẤT LƯỢNG MÃ NGUỒN (CODE QUALITY & HYGIENE)
- Tuyệt đối không để lại `import` rác (unused imports).
- Không hardcode các nhãn giả lập (như fallback nhãn nguồn `"CELLPHONES"` trong module dùng chung).
- Giữ các hàm có trách nhiệm đơn nhất (Single Responsibility Principle).

---

## 4. BỘ KỸ NĂNG NÂNG CAO SUPERPOWERS (obra/superpowers) — QUY TẮC CƯỠNG CHẾ
Dự án đã tích hợp bộ kỹ năng **Superpowers** trong `.agents/skills/`.

👉 **BẮT BUỘC 1: KÍCH HOẠT ĐẦU PHIÊN (SKILL INVOCATION)**
Ở đầu mỗi phiên mới hoặc khi nhận tác vụ mới từ người dùng, AI BẮT BUỘC phải dùng `view_file` đọc file `.agents/skills/using-superpowers/SKILL.md` trước tiên để thiết lập workflow tiếp cận.

👉 **BẮT BUỘC 2: TUYÊN BỐ CÔNG KHAI (TRANSPARENT ANNOUNCEMENT)**
Trước khi bắt đầu bất kỳ hành động hoặc phản hồi nào, AI PHẢI thông báo rõ ràng cho người dùng theo cú pháp chuẩn:
> `"Using [tên-skill] to [mục đích cụ thể]"`
(Ví dụ: `Using using-superpowers to establish workflow`, `Using systematic-debugging to diagnose bug`, `Using test-driven-development to implement feature`).

👉 **BẮT BUỘC 3: QUẢN LÝ TIẾN ĐỘ BẰNG TASK ARTIFACT (TASK TRACKING)**
Với các tác vụ từ 2 bước trở lên, AI BẮT BUỘC phải tạo một **Task Artifact** (checklist markdown với `ArtifactType: "task"`) theo dõi từng đầu việc và cập nhật trạng thái `- [x]` ngay sau khi hoàn thành mỗi bước.

👉 **NGHIÊM CẤM**:
- Tuyệt đối không được tự ý thực thi "ngầm" quy trình trong đầu mà không gọi `view_file` nạp `SKILL.md`.
- Tuyệt đối không được bỏ qua câu lệnh tuyên bố `Using [skill]...` trước người dùng.
- Không được rationalizing (ngụy biện) rằng tác vụ đơn giản để bỏ qua skill.

### Danh mục kỹ năng Superpowers cốt lõi:
- **`using-superpowers`**: Kích hoạt đầu mỗi phiên, phân định quy trình tiếp cận trước khi code.
- **`brainstorming`**: Khảo sát yêu cầu, thiết kế giải pháp và phản biện ý tưởng trước khi lập kế hoạch.
- **`writing-plans` & `executing-plans`**: Lập kế hoạch chi tiết từng bước (task-by-task) và thực thi theo checklist Task Artifact.
- **`systematic-debugging`**: Quy trình 4 bước chẩn đoán gốc rễ lỗi (Root Cause Analysis) trước khi sửa code.
- **`test-driven-development`**: Luôn viết test kiểm thử trước khi bổ sung code tính năng.
- **`verification-before-completion`**: Chạy kiểm thử và chứng minh bằng bằng chứng thực tế trước khi tuyên bố hoàn thành task.

---

## 5. BỘ KỸ NĂNG KỸ THUẬT THỰC CHIẾN (mattpocock/skills)
Dự án đã tích hợp đầy đủ bộ kỹ năng từ **[mattpocock/skills](https://github.com/mattpocock/skills)** vào `.agents/skills/`:

### Agent Skills Configuration
- **Issue tracker**: Lưu trữ local markdown tại `.scratch/<feature-slug>/`.
- **Triage labels**: 5 nhãn vai trò chuẩn (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
- **Domain docs**: Thiết lập đơn ngữ cảnh (single-context: `GLOSSARY.md` và `docs/adr/` tại root).

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

### 👉 QUY TẮC BẮT BUỘC: ĐỌC CONSTITUTION TRƯỚC KHI PHÁT TRIỂN TÍNH NĂNG
Trước khi thực thi **bất kỳ** skill `speckit-*` nào (specify, plan, tasks, implement...), AI **BẮT BUỘC** phải:
1. Đọc file `.specify/memory/constitution.md` bằng `view_file`.
2. Sử dụng các nguyên tắc trong Constitution làm ràng buộc khi sinh spec, plan, code và test.
3. Không được vi phạm bất kỳ nguyên tắc nào trong Constitution (CodeGraph First, Clean Architecture, TDD, Two-Tiered Matching, Code Quality).

### Nguyên tắc cốt lõi trong Constitution (tóm tắt để tham chiếu nhanh):
- **I. CodeGraph First**: PHẢI chạy `codegraph impact` trước khi sửa shared code.
- **II. Deep Modules & Clean Architecture**: Tách biệt Scrapers / Matching / Pricing / API. Strategy Pattern cho crawlers.
- **III. TDD (NON-NEGOTIABLE)**: Viết test trước → code sau → refactor. Coverage >= 80%.
- **IV. Two-Tiered Matching**: Regex Tier 1 (100% precision) → Fuzzy Tier 2 (RapidFuzz). KHÔNG dùng fuzzy đơn lẻ.
- **V. Code Quality**: PEP 8, type hints, zero dead code, zero hardcoded secrets.

### Technology Stack (từ Constitution):
- **Python 3.11+** | **FastAPI** + Pydantic v2 | **SQLAlchemy 2.x** + **Alembic**
- **PostgreSQL** (production) / **SQLite** (dev & CI)
- **httpx** + BeautifulSoup4 (scraping) | **RapidFuzz** (matching) | **pytest** + pytest-cov (testing)

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

---

## 7. QUY TẮC TÍCH HỢP OBSIDIAN VAULT (KNOWLEDGE BASE & SECOND BRAIN)
Dự án đã được liên kết trực tiếp 2 chiều với **Obsidian Vault** của lập trình viên:
- **Thư mục Vault gốc:** `C:\Users\nguye\OneDrive\Tài liệu\Obsidian Vault`
- **Điểm cầu nối trong Repo (Bridge Junction):** `docs/obsidian-notes/` ↔ `Obsidian Vault/02_Projects/Dynamic-Pricing/`

👉 **QUY TẮC BẮT BUỘC ĐỐI VỚI AI AGENT:**
1. **Tra cứu Ngữ cảnh Nghiệp vụ (Domain Context First):**
   - Trước khi viết code tính năng mới liên quan đến định giá, cào dữ liệu, đối soát SKU hoặc thiết kế DB, AI PHẢI ưu tiên đọc các tài liệu tại `docs/obsidian-notes/`:
     - `Khám phá Dữ liệu & Ma trận Định giá.md` (Ma trận 9 kịch bản, công thức Composite Score)
     - `Product Backlog – Dynamic Pricing.md` & `Sprint Plan – Dynamic Pricing System.md`
     - `Thiết kế Cơ sở Dữ liệu Toàn diện.md` & `Giải thích Kiến trúc Backend và Chi tiết Codebase.md`
     - `Hiểu code cào dữ liệu và map sku.md`
2. **Chuẩn mực Lưu trữ Tài liệu & Quyết định Kiến trúc:**
   - Khi sinh tài liệu kỹ thuật, kiến trúc (ADR), hướng dẫn vận hành (Runbook) hoặc phân tích lỗi: Lưu trực tiếp vào `docs/obsidian-notes/` hoặc thư mục chuyên mục tương ứng trong Vault.
   - Luôn duy trì cú pháp **Wikilinks hai chiều** `[[Tên Note]]` và YAML Frontmatter (`title`, `tags`, `date`, `status`) để đảm bảo tính liên kết trong Graph View của Obsidian.
3. **Nhật ký & Báo cáo Tiến độ (Daily Notes):**
   - Khi người dùng yêu cầu tóm tắt công việc ngày hoặc chuẩn bị Standup, AI hỗ trợ tạo/cập nhật trực tiếp vào `Obsidian Vault/01_Daily/` theo template chuẩn `Daily Note Template.md`.

---

## 8. QUY TẮC CƯỠNG CHẾ BỘ RULES TẠI `.agents/rules/` (DEVELOPMENT & GIT WORKFLOW)
AI BẮT BUỘC phải đọc và áp dụng nghiêm ngặt các quy tắc kỹ thuật tại `.agents/rules/`:

### 8.1. Quy trình Git & Chuẩn Commit
- **Định dạng Commit Chuẩn (Conventional Commits):**
  ```text
  <type>: <description>

  <optional body explaining why, context, or issue reference>
  ```
  - `type` BẮT BUỘC thuộc một trong các nhãn: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
  - Giữ commit mang tính nguyên tử (Atomic Commit): Không gộp nhiều thay đổi logic không liên quan vào 1 commit.
- **Quy chuẩn Tạo Pull Request (PR):**
  - Luôn kiểm tra toàn bộ lịch sử thay đổi qua `git diff [base-branch]...HEAD`.
  - Soạn tóm tắt PR toàn diện và kèm checklist kiểm thử (Test Plan with TODOs).

### 8.2. Chu trình Phát triển Tính năng
1. **Research & Reuse First:** Tra cứu thư viện và mẫu thiết kế có sẵn trước khi tự viết code mới từ đầu.
2. **Plan First:** Lập kế hoạch chi tiết, đánh giá dependency và rủi ro trước khi đụng vào code.
3. **TDD Approach:**
   - Viết test trước khi code tính năng (Red → Green → Refactor).
   - Đảm bảo độ bao phủ kiểm thử (test coverage) đạt ít nhất 80%.
4. **Code Review & Security Check:**
   - Rà soát mã nguồn ngay sau khi viết xong, xử lý dứt điểm các lỗi Critical & High.
   - Tuyệt đối không hardcode bí mật (API keys, token, mật khẩu DB) vào code hoặc git commit.

---

## 9. NGUYÊN TẮC THIẾT KẾ GIAO DIỆN (UI DESIGN - NGHIÊM CẤM DÙNG ICON / EMOJI)
👉 **QUY TẮC BẮT BUỘC: TUYỆT ĐỐI KHÔNG DÙNG ICON, EMOJI TRONG GIAO DIỆN**

Khi thiết kế, xây dựng hoặc chỉnh sửa bất kỳ giao diện nào (HTML, CSS, JavaScript, React/Vue/Svelte, Python Web/Streamlit/Qt):
1. **Nghiêm cấm tuyệt đối Emoji & Icon trang trí:**
   - Không chèn emoji hay icon vào nhãn, nút bấm, tiêu đề, menu, badge, thẻ trạng thái, thông báo, modal hay tooltip.
   - Giữ phong cách thiết kế tối giản, tinh tế, sạch sẽ (clean, minimal, modern typography & color accents) và chuẩn mực doanh nghiệp (enterprise-grade).
2. **Thể hiện trạng thái và phân cấp thông tin:**
   - Sử dụng màu sắc tinh tế (color coding: viền/nền/chữ) và phân cấp kiểu chữ (typography: font-weight, size, spacing) để biểu đạt trực quan trạng thái thay vì dùng biểu tượng minh họa.
   - Sử dụng ngôn ngữ chuẩn xác, súc tích.

