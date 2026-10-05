# Dynamic Pricing System Constitution

## Core Principles

### I. CodeGraph First & Impact Analysis
CodeGraph is the primary intelligence tool for this codebase (`.codegraph/`).
- Before modifying shared functions, services, or models, developers and AI
  agents MUST run `codegraph impact <symbol>` or use `codegraph_explore` to
  evaluate the blast radius.
- No editing or refactoring shared code without prior caller/callee analysis.
- Run `codegraph sync` after non-trivial file changes.

### II. Deep Modules & Clean Architecture
Modules MUST hide internal implementation complexity behind simple, clean
interfaces.
- Separate layers strictly: Scraping Strategies (`app/services/scrapers/`),
  SKU Matching Engine (`app/services/matching/`), Pricing Rules
  (`app/services/pricing/`), and API Routes (`app/api/`).
- Strategy Pattern mandatory for multi-source crawlers (CellphoneS, Hoang Ha,
  FPT Shop).
- Domain logic MUST NOT directly depend on raw HTTP frameworks or external
  web scraping implementations.

### III. Test-Driven Development & Anti-Regression (NON-NEGOTIABLE)
All new features, bug fixes, and matching algorithms MUST follow strict TDD
principles.
- Write failing unit/integration tests before writing implementation code
  (Red → Green → Refactor).
- SKU matching engine MUST maintain >90% precision and include regression
  test coverage for edge-case product titles/RAM/ROM specifications.
- Maintain overall pytest suite pass rate and test coverage >= 80%.

### IV. Two-Tiered Data Matching Protocol (Regex + Fuzzy)
SKU and product matching MUST strictly follow two-tiered processing:
- **Tier 1 (Deterministic):** Exact Regex extraction for Model Code, Part
  Numbers, RAM, and Storage variants. This tier MUST achieve 100% precision
  on structured identifiers.
- **Tier 2 (Probabilistic):** RapidFuzz / Levenshtein scoring for remaining
  string similarity only when Tier 1 succeeds or validates bounds.
- MUST NOT rely purely on fuzzy string matching for critical hardware
  specifications.

### V. Code Quality & Zero Waste
- Strict PEP 8 compliance, proper Python type hints (`typing`), and explicit
  return types on all public functions.
- Zero unused imports or dead code permitted in production commits.
- Absolute prohibition of hardcoded secrets (API keys, tokens, DB passwords)
  or environment fallback hacks in shared modules.
- No hardcoded source labels (e.g., fallback `"CELLPHONES"`) in shared
  matching/pricing modules.

## Technology Stack & Constraints

- **Runtime:** Python 3.11+
- **Web Framework:** FastAPI with Pydantic v2 for request/response models.
- **ORM & Migrations:** SQLAlchemy 2.x (async-ready) + Alembic for schema
  versioning. All schema changes MUST go through Alembic migrations.
- **Database:** PostgreSQL (production) / SQLite (local development & CI).
- **Scraping:** httpx + BeautifulSoup4 via Strategy Pattern. All scrapers
  MUST extend `BaseScraper`.
- **SKU Matching:** RapidFuzz + custom Regex extractors in
  `app/services/matching/`.
- **Testing:** pytest + pytest-cov. No unittest-style test classes unless
  integrating with existing test infrastructure.
- **Dependency Management:** `requirements.txt` (pip). Pin major versions.

## Development Workflow & Quality Gates

1. **Research & Reuse First:** Check existing libraries and codebase patterns
   (via CodeGraph) before writing new code.
2. **Plan Before Code:** For features spanning >1 file, create a spec
   (`speckit-specify`) and plan (`speckit-plan`) first.
3. **TDD Cycle:** Write failing tests → implement minimum code to pass →
   refactor. No implementation PR without corresponding test coverage.
4. **Code Review Gate:** All PRs MUST pass linting (`ruff`), type checking,
   and full pytest suite before merge.
5. **Conventional Commits:** All commits MUST follow the format
   `<type>: <description>` where type is one of: `feat`, `fix`, `refactor`,
   `docs`, `test`, `chore`, `perf`, `ci`.
6. **Security:** No secrets in code or git history. Use `.env` files
   (gitignored) for all sensitive configuration.

## Governance

This Constitution supersedes all ad-hoc practices. All Pull Requests,
commits, and AI-generated code changes MUST comply with these principles.

- Amendments require: documented rationale, updated test suites, and version
  bump following semantic versioning (MAJOR: principle removal/redefinition,
  MINOR: new principle added, PATCH: clarification/wording).
- All PRs and code reviews MUST verify compliance with this Constitution.
- Complexity MUST be justified; default to the simplest solution (YAGNI).

**Version**: 1.0.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-01
