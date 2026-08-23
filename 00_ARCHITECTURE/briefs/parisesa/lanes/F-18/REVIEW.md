---
lane: F-18
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: INCOMPLETE-RETURN
ratified_by: ratifier-2
ratified_by: ratifier-3
---

## Method

Read: PROTOCOL.md, F-18/SPEC.md (revision 2), F-18/DIAGNOSIS.md, F-18/ADAPTS.md, F-17/SPEC.md, F-17/REVIEW.md (pool-2 DRAFT, INCOMPLETE-RETURN), F-18/REVIEW.md (existing pool-1/ratified, INCOMPLETE-RETURN).

Source verified at `/Users/Dev/par-night/main-ro/platform-mcp/src/tools/register_p1_aliases.ts`:
- `dualOutput` function definition: confirmed at line 183 (`function dualOutput(data: unknown, toolName = 'unknown_tool')`). SPEC R2 cites 183. ✓
- Bare call at line 652: `return dualOutput(data)` inside `bodha_graph_traverse_get` handler, confirmed. SPEC R2 cites 652. ✓
- Line 1794: `// RC-04 drill-crawl (2026-07-23): dualOutput(data) with no toolName arg was` — comment line, starts with `//`, NOT `return`. Anchored regex `^\s*return\s+dualOutput\(data\)` correctly excludes it. ✓
- Exit test file `platform-mcp/src/tools/__tests__/dual_output_tool_name.test.ts`: does not yet exist in main-ro (new file to be created by builder). ✓
- vitest.config.ts confirmed: `globals: true`, `"test": "vitest run"` (runs from `platform-mcp/` package root), no CWD override. ✓
- Codebase test pattern verified: `deprecated_tool_gate.test.ts` uses `new URL('../../../platform/src/lib/retrieval/registry/canonical_faces.json', import.meta.url)`. `kala_sky_pattern.test.ts` imports `fileURLToPath` from `node:url`. No existing test uses a bare `'platform-mcp/...'` path to read cross-package source. ✓

F-18 is a fold lane — no independent diff. This second review assesses whether SPEC R2 resolved the two first-pass deficiencies (pool-1/ratifier-1), and whether F-17's newly-surfaced path bug (F-17 pool-2 DRAFT) is inherited by F-18.

First-pass deficiency 1 (line citation drift 657→652, 188→183): RESOLVED in R2. ✓
First-pass deficiency 2 (regex not anchored): RESOLVED in R2 — now `/^\s*return\s+dualOutput\(data\)/gm`. ✓
New deficiency from F-17 pool-2 DRAFT (path bug): INHERITED — F-18/SPEC R2 §3 carries the identical bare-path `readFileSync` call. ✗

## Q1 — Mechanism vs. symptom

PASS. SPEC R2 §1 names the exact mechanism: `dualOutput`'s second argument defaults to `'unknown_tool'` (confirmed at register_p1_aliases.ts:183), and the bare call inside `bodha_graph_traverse_get` omits it (confirmed at :652), so `recover_via.instrument` receives the placeholder verbatim. Mechanism-level, not symptom-level. ✓

## Q2 — Every DIAGNOSIS sub-claim maps to a spec element

PASS. F-18/DIAGNOSIS has one core claim: `recover_via.instrument` reads `'unknown_tool'` at the `bodha_graph_traverse_get` handler (DIAGNOSIS cites :657, actual :652 — off-by-5 DIAGNOSIS error, acknowledged in SPEC R2). F-18/SPEC R2 §7 maps it to F-17 §2 (line 652 explicit in F-17's call-site list) and F-17 §3 (zero-bare-sites assertion covers :652 by construction). Nothing unmapped. ✓

## Q3 — Exit test genuinely fails on today's code

FAIL — test throws ENOENT, not a red assertion; cannot go green post-fix.

The shared exit test (F-18/SPEC R2 §3) reads:
```ts
const src = fs.readFileSync('platform-mcp/src/tools/register_p1_aliases.ts', 'utf8')
```
`npm test` invokes `vitest run` from the `platform-mcp/` package root (confirmed via package.json `"test": "vitest run"`, vitest.config.ts no CWD override). With CWD = `platform-mcp/`, the path `'platform-mcp/src/tools/register_p1_aliases.ts'` resolves to `platform-mcp/platform-mcp/src/tools/register_p1_aliases.ts` — does not exist. Test throws `ENOENT` today, and throws `ENOENT` post-fix too: it can never go green.

Every existing source-reading test in this codebase uses `new URL(..., import.meta.url)` or equivalent (deprecated_tool_gate.test.ts, kala_sky_pattern.test.ts). The correct path from this test's location is `'src/tools/register_p1_aliases.ts'` (CWD-relative from package root) or `new URL('../../register_p1_aliases.ts', import.meta.url)` (relative to test file at `src/tools/__tests__/`). Deficiency is blocking and inherited identically from F-17.

## Q4 — All sibling sites covered or excluded with reason

PASS. F-17/SPEC §2 lists all 21 bare call sites including :652. F-43 explicitly scoped as sibling spec. No site silently excluded. ✓

## Q5 — Recurrence guard

FAIL (inherited). Guard logic is sound — anchored regex `^\s*return\s+dualOutput\(data\)` correctly excludes the :1794 comment (confirmed: comment starts with `//`, not `return`). However the path bug (Q3) renders the guard inoperative as a CI gate: the test crashes with ENOENT rather than executing the regex assertion, so future regressions would not be caught by the intended check. ✓ (logic) / ✗ (path bug makes guard non-functional)

## Q7 — Every file:line citation verified against current source

PASS (for SPEC R2).
- SPEC R2 §1: `dualOutput` at line 183 — source confirmed. ✓
- SPEC R2 §2: bare call at line 652 (`bodha_graph_traverse_get`) — source confirmed. ✓
- SPEC R2 note: line 1794 is a `//` comment excluded by `^\s*return` anchor — source confirmed. ✓
- F-17/SPEC §2 call-site list (652 included) — consistent with source per F-17 pool-2 trace. ✓
- ADAPTS.md references "line 657" (stale, pre-R2) — cosmetic inconsistency, no practical impact (F-18 has no independent diff; F-17/SPEC §2 authoritative at 652). Non-blocking.

No writer_asset, data_delta, or RS-A fields apply — pure TypeScript call-site fix, no data-generation layer.

## Named deficiencies (INCOMPLETE-RETURN)

1. **Exit test path bug (blocking, inherited from F-17)**: `fs.readFileSync('platform-mcp/src/tools/register_p1_aliases.ts', 'utf8')` in F-18/SPEC R2 §3 (shared test file) resolves to a non-existent path when vitest runs from `platform-mcp/` package root. Test throws `ENOENT` both before and after fix — can never go green. Fix: change to `'src/tools/register_p1_aliases.ts'` (CWD-relative) or `new URL('../../register_p1_aliases.ts', import.meta.url)` (matching codebase pattern in deprecated_tool_gate.test.ts etc.). One-line change in F-17/SPEC §3; F-18/SPEC §3 inherits the fix.

## Verdict: INCOMPLETE-RETURN
