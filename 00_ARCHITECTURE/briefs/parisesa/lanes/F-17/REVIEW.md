---
lane: F-17
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

Read: PROTOCOL.md, F-17/SPEC.md (R2), F-17/DIAGNOSIS.md. No REVIEW_LEADS.md found.

Source verified at `/Users/Dev/par-night/main-ro/platform-mcp/src/tools/register_p1_aliases.ts`:
- `dualOutput` function definition: actual line 183 (SPEC §1 cites 183 correctly; DIAGNOSIS §3 cited 188 — off by +5, DIAGNOSIS error not SPEC). ✓
- All 21 SPEC-cited call-site lines verified by grep — exact match: 601, 652, 1150, 1202, 1244, 1363, 1494, 1517, 1553, 1565, 1577, 1589, 1601, 1613, 1625, 1665, 1776, 1839, 1855, 1869, 1966. ✓
- Known-good fix pattern at line 1800 (`return dualOutput(data, 'phala_outlook_get')`). ✓
- Comment-only line 1794: `// RC-04 drill-crawl (2026-07-23): dualOutput(data) with no toolName arg was` — does NOT begin with `return`; regex anchor correctly excludes it. ✓
- Verified `vitest.config.ts` (test runner is vitest, not Jest; `globals: true`; includes `src/**/*.test.ts`; no CWD override) and `package.json` (`"type": "module"`, `"test": "vitest run"`). Read existing source-reading tests: every `readFileSync` targeting cross-directory source files uses either `import.meta.url`-relative URLs or a `ROOT = join(dirname(fileURLToPath(import.meta.url)), ...)` constant — none use a bare `'platform-mcp/...'` path.

Exit test traced line-by-line against current source (Q3).

## Q1 — Mechanism vs symptom

SPEC addresses mechanism: the `toolName = 'unknown_tool'` default parameter at line 183 and 21 call sites that omit the second argument, not merely the symptom (`recover_via.instrument` reads placeholder). ✓

## Q2 — D sub-claims mapped

| DIAGNOSIS claim | SPEC element |
|---|---|
| §1 live reproduction: `recover_via.instrument = 'unknown_tool'` | §2 fix at line 1244 (F-17 own site) + §3 exit test asserts zero remaining bare sites |
| §3 mechanism: default param at line 183 (DIAGNOSIS wrongly cites 188), call site at 1244 (DIAGNOSIS wrongly cites 1249) | §1 root cause, §2 file:line list — SPEC uses correct line numbers independently |
| §4 sibling census: 21 bare call sites, F-18=line 652, F-43=19 remaining | §2 all 21 lines listed; §4 sibling relationship declared |
| §5 blast radius: CL-00 doesn't catch this today | §5 recurrence guard via exit test + follow-up flagged |

All D sub-claims mapped. ✓

## Q3 — Exit test fails today (traced against current source)

Regex `/^\s*return\s+dualOutput\(data\)/gm` vs. current source → 21 matches confirmed by grep → `expect(21).toBe(0)` FAILS. Correct signal, correct reason.

**Hard path deficiency — test can never go green**: `fs.readFileSync('platform-mcp/src/tools/register_p1_aliases.ts', 'utf8')` uses a plain relative path. vitest is invoked via `npm test` inside `platform-mcp/` (npm script convention changes CWD to package dir); `process.cwd()` = `platform-mcp/`. The path resolves to `platform-mcp/platform-mcp/src/tools/register_p1_aliases.ts`, which does not exist. The test throws `ENOENT` both before and after the fix — it can never go green post-fix. Every existing cross-directory `readFileSync` in this codebase (deprecated_tool_gate.test.ts, resources.test.ts, kala_sky_pattern.test.ts, etc.) uses `import.meta.url`-based resolution, not bare relative paths. This deficiency is blocking. ✗

## Q4 — Sibling coverage

All 21 sites listed in SPEC §2; F-18 (line 652) and F-43 (19 remaining) declared as replications, not independent specs. No site excluded without stated reason. ✓

## Q5 — Recurrence guard

The exit test itself is the permanent guard. The `return` anchor correctly excludes comment-only lines (line 1794 verified: comment text contains `dualOutput(data)` but not `return dualOutput(data)`). Secondary weakness (different variable names) documented as known limitation with follow-up flagged. Guard logic is sound; however the path deficiency (Q3) renders it non-functional as written. ✓ (logic) / ✗ (path bug makes guard inoperative post-fix)

## Q7 — Source citations accurate

- SPEC §1 `dualOutput` at "line 183": actual line 183. ✓
- All 21 call-site lines in SPEC §2: exact grep match to current source. ✓
- SPEC §6 "line 1800" known-good pattern: actual line 1800 (`return dualOutput(data, 'phala_outlook_get')`). ✓
- DIAGNOSIS §3 line 188 / §4 lines all +5 from actual: DIAGNOSIS errors, not SPEC errors. SPEC independently verified and corrected all line numbers. ✓
- No unverified assumptions in SPEC. ✓

## Named deficiencies (INCOMPLETE-RETURN)

1. **Exit test path wrong** — `platform-mcp/src/tools/__tests__/dual_output_tool_name.test.ts` (SPEC §3): `fs.readFileSync('platform-mcp/src/tools/register_p1_aliases.ts', 'utf8')` resolves to a non-existent path when vitest runs from the `platform-mcp/` package root. The test throws `ENOENT` always — it cannot go green after the fix. Fix: change to `'src/tools/register_p1_aliases.ts'` (CWD-relative from package root), or use `new URL('../../tools/register_p1_aliases.ts', import.meta.url)` consistent with the codebase pattern (deprecated_tool_gate.test.ts, kala_sky_pattern.test.ts, etc.). One-line fix in the spec.

## Verdict: INCOMPLETE-RETURN
