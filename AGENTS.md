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
