---
lane: F-93
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read PROTOCOL.md, SPEC.md, DIAGNOSIS.md in full. Read and traced the following source files in `/Users/Dev/par-night/main-ro` directly:
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` — lines 1–60 (header/imports), 120–139 (input_schema.ayanamsha_id), 195–244 (handler open / system default), 530–589 (levelsAvailable sub-query / facets_applied return)
- `platform/src/lib/retrieval/registry/constants.ts` (full, 3 lines)
- `platform/src/lib/pipeline/prashna_ask_synthesis.ts` — lines 80–106 (NO_LIVE_TOOLS_OVERRIDE), 230–282 (formatEvidenceBlock)
- `platform/src/lib/pipeline/compiled_floor_adapter.ts` — lines 370–390 (ensureDashaContextFloor)
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_chart_snapshot.ts` — grep for DEFAULT_AYANAMSHA
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_strength.ts` — grep for DEFAULT_AYANAMSHA
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts` — grep for DEFAULT_AYANAMSHA
- `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas.integration.test.ts` — lines 40–76 (REGRESSION test block)
- `platform/src/lib/pipeline/__tests__/prashna_ask_synthesis.test.ts` — lines 85–103 (existing assertion pattern)

No REVIEW_LEADS.md present in lane directory.

## Q1 — Mechanism vs. symptom

The spec addresses the mechanism at both layers it exists: (1) the tool-dispatch default gap in `get_dashas.ts` (two SQL-building sites, both patched), and (2) the synthesis-prompt disambiguation gap in `prashna_ask_synthesis.ts`. The symptom is wrong dates in the reading; the mechanism is an unfiltered 5-ayanāṁśa evidence dump reaching a model with no disambiguation rule. Both roots are closed. No symptom-only masking.

## Q2 — DIAGNOSIS sub-claim coverage

All DIAGNOSIS claims map to spec elements via the explicit Sub-claim coverage table. Verified each row:
- Claims (a), (c): correctly identified as unaffected (never wrong) — no spec element needed. ✓
- Claim (b) wrong MD dates: Files item 1 + Exit-test-A exact-date assertion. ✓
- Claim (d) AD end-date = Krishnamurti MD end: Files item 1 (structural closure — once single-ayanāṁśa default is in place, no other ayanāṁśa's date can appear in any row). ✓
- Mechanism steps A/B/C: all three have a spec element. ✓
- Attribution caveat (planner transcript not captured): correctly marked "not a spec element to close" with reasoning — the fix closes the gap regardless of which exact caller produced `{}`. ✓
- Blast Radius F-120/F-121: explicitly not unified, stated reason given (different mechanism). ✓
- Sibling census items 1–6: all addressed, none silently dropped. ✓

No unmapped sub-claim found.

## Q3 — Exit test would fail on today's code

**Test A (get_dashas.integration.test.ts):** The SPEC's post-fix assertions are:
- `rows.length === 1` — today's REGRESSION test at lines 53–75 confirms `rows.length > 1` (multiple ayanāṁśas returned). The new assertion inverts this and WOULD FAIL on current source. ✓
- `rows[0].ayanamsha_id === 'lahiri_chitrapaksha'` — current code returns Krishnamurti row (or indeterminate ordering among 5). WOULD FAIL or be indeterminate today. ✓
- `rows[0].start_date === '2010-08-18'` — DIAGNOSIS live repro shows current code returns `'2010-07-07'` (Krishnamurti). WOULD FAIL. ✓
- `levels_available` consistency test: today, omitting ayanamsha_id means `lvlSql` at line 545 has no ayanamsha filter → `MAX(level_n)` scans all 5 ayanāṁśas; passing `lahiri_chitrapaksha` scopes to one. In practice level counts likely differ or may coincide by accident, but the spec's guard is structural — the two call sites are demonstrably not using the same resolved variable today. ✓

**Test B (prashna_ask_synthesis.test.ts):** NO_LIVE_TOOLS_OVERRIDE (lines 90–105) confirmed contains zero mention of "ayanamsha" and no canonical-ayanāṁśa instruction. New regex assertion `/canonical ayan[aā]ṁśa is.*lahiri_chitrapaksha/i` WOULD FAIL today. ✓

The existing REGRESSION test (lines 53–75) is the inverse: it PASSES today (pinning the defect) and will break on merge if not rewritten in the same commit. SPEC explicitly requires this rewrite in the same commit. ✓

## Q4 — Sibling sites coverage

All 6 DIAGNOSIS sibling census items addressed:
1. prashna_ask_synthesis.ts — directly fixed (Files item 2). ✓
2. consult/route.ts — structurally covered by tool-layer fix; no consult-specific test. Stated reason: tool-layer default closes all callers by construction. ✓
3. pariprashna/route.ts — same. ✓
4. register_p1_synthesis.ts — re-verified not vulnerable (independent grep confirmed zero LLM call). ✓
5. query_remedies.ts — same (deterministic, no LLM call). ✓
6. adjudicator.ts / member_runner.ts / summaries/worker.ts — explicitly out-of-scope with stated reason (untraced budget; flagged for follow-up lane). ✓

Two additional exposures found by the SPEC's own file read (compiled_floor_adapter.ts:381, b11_floor.ts:61, bundle_adapters.ts:379) flagged and structurally closed by tool-layer fix. ✓

## Q5 — Recurrence guard

The SPEC's recurrence guard discussion explicitly addresses the §N.7/§N.8 test: does the guard detect the defect class (wrong value silently substituted) or only a proxy (row count, field presence)?

- **Tool layer guard**: exact Lahiri date values (`2010-08-18`/`2027-08-18`) + exact `ayanamsha_id` string. A wrong default (e.g. accidentally `'krishnamurti'`) would return exactly 1 row but with the wrong dates — the row-count-only check passes, the date assertion fails. Correctly detects the defect class. ✓
- **Sub-query drift guard**: `levels_available` consistency test catches the two SQL sites drifting back out of sync in a future edit. ✓
- **Prompt layer guard**: anchored regex on the instructional sentence, not bare substring. A prompt edit that preserves the string but drops or waters down the instruction still fails the anchored check. ✓

## Q7 — Unverified assumptions / file:line accuracy

Verified every cited file:line against current source in main-ro:
- `get_dashas.ts:15–26` (header) — present and matches quoted text exactly. ✓
- `:127–138` (ayanamsha_id description) — lines 127–138 match. ✓
- `:210–213` (`if (args.ayanamsha_id)` no-default block) — confirmed, exact match. ✓
- system default-else branch at `:227–242` — confirmed at lines 227–241. ✓
- `:545–547` (levelsAvailable sub-query second ayanamsha_id check) — confirmed at lines 545–547. ✓
- `:565–573` (facets_applied, ayanamsha not echoed) — confirmed at 565–572; ayanamsha absent. ✓
- `constants.ts:2` (`DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'`) — confirmed exactly. ✓
- `get_chart_snapshot.ts:35,152`, `get_strength.ts:27,121`, `get_positions.ts:38,150` (sibling DEFAULT_AYANAMSHA usage) — all confirmed via grep. ✓
- `prashna_ask_synthesis.ts:88–105` (NO_LIVE_TOOLS_OVERRIDE) — confirmed at lines 88–105, zero "ayanamsha" occurrences. ✓
- `:237–282` (formatEvidenceBlock) — confirmed, serializes `e.bundle.results` verbatim. ✓
- `compiled_floor_adapter.ts:374–390` (ensureDashaContextFloor) — confirmed at exactly those lines; gated to `predictive`/`holistic` at line 376; omits `ayanamsha_id` at line 381. ✓
- Integration test file exists, REGRESSION test at lines 53–75 — confirmed exactly. ✓
- prashna_ask_synthesis.test.ts exists, assertion pattern at lines 93–95 — confirmed. ✓

No unverified assumption found. All cited file:line references are accurate.

**writer_asset / data_delta / RS-A:** Not applicable — this is a pure serving-layer TypeScript + prompt change. No writer, no DB write, no migration. Consistent with SPEC's explicit "No change to chart_dashas, any migration" statement.

## Verdict: COMPLETE

The spec is mechanistically sound, all DIAGNOSIS sub-claims are covered, every file:line citation verifies against current source, exit tests would genuinely fail on today's code with the right failure modes, recurrence guards detect the actual defect class (not proxies), and all sibling sites are addressed or excluded with stated reasons. No deficiencies found. Lane may proceed to Stage B.