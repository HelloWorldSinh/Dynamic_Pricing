# Tools & Skills Enforcement Rules

## 1. CodeGraph First Enforcement
In this repository, CodeGraph index is maintained in `.codegraph/`.
- For locating symbols, tracing call paths, examining callers/callees, checking blast radius before refactoring/deleting code: **Always invoke `codegraph_explore` MCP tool or `codegraph explore "<query>"` before reading files or using grep**.
- Use the line-numbered source returned by CodeGraph directly without redundant file reads.

## 2. Project Skills Utilization
Always check `.agents/skills/` and adopt established patterns:
- `regex-vs-llm-structured-text`: Tier 1 Part-Number Regex -> Tier 2 Fuzzy Attribute Matching.
- `python-patterns`: Idiomatic Python, PEP 8, strict type hints, clean imports.
- `ai-regression-testing`: Automated verification against data schema regressions.
- `tdd-workflow`: Write test assertions before implementing logic.
