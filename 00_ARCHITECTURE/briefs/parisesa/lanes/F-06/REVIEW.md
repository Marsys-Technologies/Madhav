---
lane: F-06
stream: S5 MULA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-06/SPEC.md, F-06/DIAGNOSIS.md, F-06/repro_raw.json.
Verified against current source at /Users/Dev/par-night/main-ro:
- register_d7_channel.ts lines 1430–1526 (full queryRemediesForChartCapability block)
- register_p1_aliases.ts lines 1554–1570 (ref_remedies_chart_get server.tool block)
Traced exit test assertions line-by-line against current source; no worktree run (TIER2-HONESTY, non-writer layer — no shadow run required per PROTOCOL §Level 0).

## Q1 — Mechanism vs symptom

PASS. The spec removes the decorative `chart_id` field from `queryRemediesForChartCapability.input_schema` entirely (Change 1), rewrites the capability description to state global-only scope (Change 2), and drops the handler variable and echo (Change 3). Separately, File B corrects the MCP alias description string. This targets the structural mismatch (field declared in schema, never bound in SQL WHERE; alias description promises chart-scoping the implementation cannot provide), not just a surface reword.

## Q2 — Diagnosis claims → spec elements

PASS. Coverage table §7 is complete:
- Claim a (alias description false): → §2 File B, description string corrected.
- Claim b (Zod schema has no chart_id, hard-rejected): → §2 File A Change 1 removes server-side chart_id from input_schema, closing even the server-side implication.
- Claim c (handler provenance-only, never in WHERE): → §2 File A Changes 1–3 (field removed, handler variable dropped, echo removed).
- Sibling census 0: → §4, with explicit enumeration of all genuine WHERE-bound chart_id usages (lines 979, 1039, 1061, 1072, 1188, 1190, 1250–1251, 1294).
- S1 lease on register_p1_aliases.ts: → §2 File B dependency note and §6.
- Two remediation shapes (minimal vs build-out): → §2 explicitly chooses minimal/honest, defers chart join as future backlog.
- brahma_remedy_corpus L0 global (no chart_id column even in principle): → §2 rationale and §5 guard comment.
No unmapped claims.

## Q3 — Exit test genuinely fails today

PASS. Traced both tests against current source:

Test 1 (register_d7_channel.ts block, bounded by LIMIT \$2 at line 1503):
- `expect(block).not.toMatch(/'chart_id'/)` — FAILS today: `args['chart_id']` at line 1487 is within the block, and `'chart_id'` appears literally there.
- `expect(block).not.toMatch(/"chart_id"/)` — PASSES today (no double-quoted form in block; not a false negative — the single-quoted catch at line 1487 is the correct catch).
- `expect(block).not.toMatch(/provenance only/)` — FAILS today: line 1448 description string contains "Optional: chart_id (provenance only, not used for data filtering)" and line 1487 contains `// optional — provenance only`.
Overall: Test 1 RED today on assertions 1 and 3. After all three File A changes (Change 2 rewrites description removing line 1448 text; Change 3 removes line 1487): all assertions GREEN.

Test 2 (register_p1_aliases.ts):
- `expect(src).not.toMatch(/Chart-specific remedy suggestions/)` — FAILS today: string present at line 1560. GREEN after File B fix.

## Q4 — Sibling sites

PASS. DIAG §4 enumerates all 46 chart_id occurrences in register_d7_channel.ts and traces each to genuine WHERE-bound predicates (lines 979, 1039, 1061, 1072, 1188, 1190, 1250–1251, 1294). The three "provenance only" comments (lines 1448/1456/1487) are all within queryRemediesForChartCapability only. Independently verified: no other capability in the file carries the provenance-only pattern. In register_p1_aliases.ts, all sibling remedy aliases (ref_remedies_get, ref_remedies_by_category_list, ref_remedy_get, ref_tantric_remedies_get, ref_remedies_by_planet_get, ref_mantras_get, ref_remedies_search) make no chart-specificity claim. Zero siblings, no exclusion needed.

## Q5 — Recurrence guard

PASS. Exit test catches re-introduction of `'chart_id'` (via args bracket-access pattern) or "provenance only" text anywhere in the queryRemediesForChartCapability block. Guard comment codifies that brahma_remedy_corpus has no chart_id column and directs future editors to open a separate finding if chart scoping is ever wanted. Guard detects the defect class, not a weak proxy.

## Q7 — File:line citation accuracy

TWO MINOR INACCURACIES (non-blocking):

1. SPEC §2 File B states "line 1565 (alias description string)". Current source: the description string is at line 1560. Line 1565 is `return dualOutput(data)` — five lines below the description, still within the same server.tool block. DIAG claims "audit said 1563-1573; matches" and "Line numbers confirmed exact" — actual block is lines 1558–1568. The discrepancy is ~5 lines; the file is correct; the content is findable by text search; the exit test is line-number-independent. Non-blocking for the builder.

2. SPEC Change 3 pseudocode: "Replace `const { affliction, top_k, chart_id } = input;` with `const { affliction, top_k } = input;`". Actual code uses bracket-access style: `const chart_id = args['chart_id'] as string | undefined  // optional — provenance only` (line 1487), not destructuring. The fix intent (remove chart_id variable and its echo) is clear; the pseudocode is schematic. Non-blocking for a competent builder.

No unverified assumptions about SQL structure (SQL at lines 1495–1504 confirmed, no chart_id bind var, only $1=affliction and $2=topK). No assumptions about brahma_remedy_corpus schema (confirmed global L0 lookup, no chart_id column referenced anywhere in the SQL or table definition comments). writer_asset/data_delta/RS-A: SPEC §6 correctly classifies as non-writer-layer (retrieval/MCP registration only), no shadow run required, no rebuild required. CONFIRMED.

## Verdict: COMPLETE

Spec is sound. Both exit tests trace correctly to RED-today / GREEN-after-fix. All DIAG claims are mapped. Sibling census is accurate. The two Q7 citation inaccuracies (P1 line number off by 5; Change 3 pseudocode style mismatch) are non-blocking — the builder will find the correct lines by text search and the exit test will validate correctness. The S1 lease dependency on register_p1_aliases.ts is correctly flagged; File A is independently actionable now.
