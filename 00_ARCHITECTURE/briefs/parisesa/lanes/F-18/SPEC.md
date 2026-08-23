---
finding: F-18
stream: S1 DVARA
class: CL-11 — dead recover_via pointer ('unknown_tool' placeholder)
stage: S COMPLETE — folded into F-17; builds and review ride on F-17's REVIEW.md
authority: /Users/Dev/par-night/coord-wt/00_ARCHITECTURE/briefs/parisesa/lanes/F-17/SPEC.md
revision: 3 (reviser cycle 2 — corrected exit-test readFileSync path: bare package-relative path → CWD-relative 'src/tools/register_p1_aliases.ts')
---

## 1. Root cause (one sentence, mechanism-level)

`register_p1_aliases.ts`'s `dualOutput` helper (definition at line 183) defaults `toolName` to
`'unknown_tool'` when the second argument is omitted; the bare call at line 652 (the
`bodha_graph_traverse_get` handler, `mode:'paths'` response path) is one of 21 such omissions,
so every trimmed response from that tool carries `recover_via.instrument: 'unknown_tool'` instead
of the real tool name.

## 2. Files to change

This finding's only change site is already listed in F-17's §2:
- `platform-mcp/src/tools/register_p1_aliases.ts` **line 652** — `dualOutput(data)` →
  `dualOutput(data, 'bodha_graph_traverse_get')` (the literal name of the enclosing
  `server.tool(...)` block).

No other file changes. F-17's PR diff covers this line; F-18 has no independent diff.

NOTE: Line 1794 in the file is a COMMENT (`// RC-04 drill-crawl (2026-07-23): dualOutput(data)
with no toolName arg was …`) — not a fix target; it must not be modified and must not cause any
regex-based test to treat it as a bare call site.

## 3. Exit test

Same file as F-17 — `platform-mcp/src/tools/__tests__/dual_output_tool_name.test.ts`:
```ts
// FAILS today (line 652 is a bare dualOutput(data) site); PASSES after F-17's fix lands.
import * as fs from 'fs'
test('every dualOutput(data) call site in register_p1_aliases.ts passes an explicit toolName', () => {
  // CWD when 'npm test' runs is platform-mcp/ (package root, per package.json "test": "vitest run"
  // with no CWD override in vitest.config.ts).  Path is relative to that root.
  const src = fs.readFileSync('src/tools/register_p1_aliases.ts', 'utf8')
  // Anchored to 'return' so comment-only lines (e.g. line 1794) are NOT matched.
  const bare = [...src.matchAll(/^\s*return\s+dualOutput\(data\)/gm)]
  expect(bare.length).toBe(0)
})
```

**Pre-fix count (current source):** the anchored regex matches all 21 live `return dualOutput(data)`
statements and zero comment lines → `bare.length === 21` → test is correctly RED today.

**Post-fix count (after all 21 sites fixed):** `bare.length === 0` → test is GREEN.
The comment at :1794 (`//`) is NOT matched by `^\s*return\s+dualOutput`, so it does not
cause a permanent false-fail. This lane closes when F-17's build makes the count reach 0.
No separate test file is created for F-18.

## 4. Sibling sites covered

All 21 bare-call sites (including **line 652**, this finding) are covered by F-17's §4 and §2
line list. No site silently excluded — F-43 is explicitly scoped as a sibling spec, not an
omission. The anchored regex in §3 correctly enumerates all 21 live sites and none of the
comment lines.

## 5. Recurrence guard

Identical to F-17 §5 — the permanent CI test (`dual_output_tool_name.test.ts`) uses the
anchored `/^\s*return\s+dualOutput\(data\)/gm` regex, which is NOT fooled by comment lines
(confirmed: line 1794 is a `//` comment, excluded by the `return` anchor). The test file path
is now `'src/tools/register_p1_aliases.ts'` (CWD-relative from `platform-mcp/` package root),
which resolves correctly under `npm test` → `vitest run`. Any future `return dualOutput(data)`
call added without a name will fail CI immediately. This lane adds no second guard; inheriting
F-17's corrected test is sufficient.

## 6. Dependencies and rollback

**Depends on F-17 completing its full D→S→R→B→V cycle and merging.** F-18 may not be built or
verified independently — its single change site lives in F-17's diff. Once F-17 merges, F-18 is
automatically closed (the exit test's zero-bare-sites assertion covers line 652 by construction).
No migration. Rollback = revert F-17's commit.

## 7. Sub-claim coverage table

| F-18 diagnosis sub-claim | Spec element that closes it |
|---|---|
| `recover_via.instrument` reads `'unknown_tool'` at **line 652** (`bodha_graph_traverse_get`) | F-17 §2 — line 652 is explicit in F-17's call-site list; fix is `dualOutput(data, 'bodha_graph_traverse_get')` |
| Same mechanism as F-17 (same helper, same default at line 183) | F-17 §1 root-cause statement covers the mechanism for all 21 sites |
| Part of the 21-site sibling census from F-17 §4 | F-17 §4 — F-18 named explicitly as a covered replication lane |
| Exit test asserts zero bare `return dualOutput(data)` sites remain (comment at :1794 excluded by anchored regex) | F-17 §3 (corrected) — anchored regex `/^\s*return\s+dualOutput\(data\)/gm`, zero remaining matches = line 652 is fixed |
