---
canonical_id: R10_X_S10
version: 1.0
status: CURRENT
session_id: X-S10
title: Interactive tables — sortable headers + CSV download
depends_on: [X-S9]
blocked_on: []
flag: MARSYS_FLAG_R10_INTERACTIVE_TABLES
flag_default: true
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES"
authored: 2026-05-20
---

# X-S10 — Interactive Tables (Sort + CSV)

## Context

The synthesis pipeline sometimes emits Markdown tables (planetary positions, dasha timelines, event comparisons). Currently these render as static HTML tables. This session wraps tables with ≥3 data rows in an `InteractiveTable` component that adds: (1) sortable column headers (click to sort asc/desc), (2) a CSV download button.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block.

**Amendment 3:** FLAGGED — loads sort/CSV behavior; risk-managed rollout.

**Amendment 2:** Visible component (InteractiveTable replacing static table) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/messages/InteractiveTable.tsx` (new)
- `platform/src/components/chat-v2/messages/MarkdownContent.tsx` — route `table` handler to `InteractiveTable` when flag enabled and row count ≥3
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=true`
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side pipeline code
- Phase 4C files
- Any file outside `platform/src/components/chat-v2/messages/` and `platform/tests/` (beyond deploy.yml)

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=true`. Session is NOT complete until present.
2. **Client-side classification (Amendment 1):** Executor confirms via grep: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES" platform/src --include="*.ts*"` — confirms usage in a `'use client'` component.
3. **click-path (Amendment 2):** User path: Chat V2 response containing a Markdown table with ≥3 data rows → table headers are clickable → clicking a header sorts rows by that column ascending → clicking again sorts descending → a "Download CSV" button above/below table downloads a `.csv` file of the table data. Document in commit body.
4. **Row count guard:** `InteractiveTable` only replaces the default `<table>` handler when `rows >= 3`. Tables with <3 data rows render as the standard static table.
5. **Sort behavior:** Clicking a column header sorts all rows by that column. Numeric strings ("3.14", "42") sort numerically. Other strings sort lexicographically. A sort direction indicator (▲/▼) appears in the active header cell.
6. **CSV download:** "Download CSV" button triggers a client-side download of the table data as `table-export.csv` (or `marsys-table-<timestamp>.csv`). No server round-trip.
7. **Flag guard:** When `NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=false`, all tables render as standard `<table>` elements (existing behavior).
8. **Parent-context integration test (Amendment 2):** At least one test mounts `MarkdownContent` within its real parent provider chain (ChatShell or message list context) with flag=true and a ≥3-row table input, and asserts: (a) `InteractiveTable` renders, (b) clicking a header sorts rows. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 — HARD GATE
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES" .github/workflows/deploy.yml && echo "PASS: deploy.yml has flag" || echo "FAIL: HARD GATE"

grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES" platform/src --include="*.ts*" && echo "PASS: client-side usage confirmed" || echo "FAIL: no usage found"

npx jest --testPathPattern="InteractiveTable|interactive.*table|table.*sort" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): interactive tables — sortable headers + CSV download

InteractiveTable.tsx wraps Markdown tables with ≥3 data rows when
MARSYS_FLAG_R10_INTERACTIVE_TABLES=true. Click headers to sort (asc/desc,
numeric-aware). CSV download button. MarkdownContent table handler
routes to InteractiveTable. NEXT_PUBLIC + deploy.yml build-arg per Amendment 1.

Click-path: response with table → click header → rows sort → Download CSV.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
