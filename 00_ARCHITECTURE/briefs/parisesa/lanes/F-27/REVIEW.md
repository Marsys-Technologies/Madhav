---
lane: F-27
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, F-27/SPEC.md (revised), F-27/DIAGNOSIS.md, F-27/REVIEW.md (prior pool-1 draft, ratified to INCOMPLETE-RETURN).
Source read: `query_calibration.ts` (full, 141 lines) — confirmed defect live in current source.
Citation spot-checks: `register_p1_aliases.ts` lines 1844–1858 (alias block); `query_predictions.ts` lines 75–89 (sibling p++ pattern).
Context: post-revision re-review. Prior pool-1 REVIEW said COMPLETE; ratifier downgraded to INCOMPLETE-RETURN. SPEC was revised in response (key change: parameterization fix from off-by-one `$${vParams.length + 1}` to `const vDomainIdx = vParams.push(domain)`, and limit/offset explicitly excluded with negative-assertion guards).

## Q1 — Mechanism vs symptom

Fully mechanism-level. The spec identifies the three-layer failure: (1) `input_schema` (lines 27–43) omits `domain`; (2) handler (lines 64–67) never reads `args.domain`; (3) `verdictSql` carries no domain predicate AND the deeper structural cause — `mimamsa_calibration` has no `domain` column, requiring a JOIN to `mimamsa_predictions` on `prediction_id`. Each layer has a corresponding §2 fix element. Symptom (identical `result_hash`) is cited in §7 as evidence only. PASS.

## Q2 — Diagnosis sub-claims vs spec elements

All DIAGNOSIS sub-claims mapped:
- (a) alias declares/forwards domain (line 1849, 1854) → §2 rationale, §7 entry (no alias change, forwarding already present) ✓
- (b) result_hash identical → exit tests 2–3 (domain wired changes params) ✓
- (c) 57-row data → §7 entry; mock used, noted ✓
- input_schema omits domain (lines 27–43) → §2 change #1 ✓
- handler never reads args.domain (lines 64–67) → §2 change #2 ✓
- verdictSql has no domain predicate → §2 change #3 (JOIN + filter) ✓
- mimamsa_calibration has no domain column → §2 change #3 (JOIN approach) ✓
- Bonus limit/offset no-ops → explicitly excluded from primitive per F-08 Change A2; negative-assertion guards in exit test 1 ✓
- Sibling census (7 correct, 1 defect) → §4 ✓
- Adjacent lead phala_mitigation_get → F-08 Change A1, out of scope with stated reason ✓
- Blast radius vs F-10 → §6 ✓
- CL-03 harness → §5 scoped to schema-guard, explicitly acknowledged ✓

No unmapped diagnosis claims. PASS.

## Q3 — Exit test fails on today's code

Traced all 4 tests against current `query_calibration.ts` source (141 lines, mocked DB):

- **Test 1** (`input_schema declares domain; NOT limit/offset`): input_schema (lines 27–43) contains only `chart_id`, `include_held_out`, `promoted_only`. `toHaveProperty('domain')` → **FAIL** ✓. The two `not.toHaveProperty` assertions (limit, offset) PASS today (correct — these are regression guards against future mis-addition). Test as a whole FAILS.
- **Test 2** (`no domain: verdictSql param array length 1`): current code calls `query(verdictSql, [chart_id])` — params length = 1. `toHaveLength(1)` → **PASS**. This is a post-fix baseline guard; expected to pass today. OK.
- **Test 3** (`domain wired: verdictSql JOINs mimamsa_predictions and carries domain param`): handler ignores `args.domain`; verdictSql calls `query(verdictSql, [chart_id])`. SQL is `FROM mimamsa_calibration WHERE chart_id = $1`. `toContain('mimamsa_predictions')` → **FAIL** ✓. `toContain('career')` → **FAIL** ✓.
- **Test 4** (`domain wired: multiplierSql also carries domain param`): calls `query(multiplierSql, [chart_id])`; params do not contain 'career'. → **FAIL** ✓.

Suite fails 3/4 today (tests 1, 3, 4). Exit test is genuine. PASS.

## Q4 — Sibling sites

All 7 sites from DIAGNOSIS §4 covered in SPEC §4. Spot-checked:
- `query_predictions.ts:82` — `if (domain) { conds.push(\`domain = $${p++}\`); params.push(domain) }` ✓ (read in source, confirms p++ pattern referenced in §2 note)
- `lel_intake_checklist.ts` — in-memory filter, consistent with file purpose (noted as not exhaustively grepped; acceptable for campaign scope).

`phala_mitigation_get` excluded with stated reason (L4 Phala, handled by F-08 Change A1). No additional sibling sites uncovered. PASS.

## Q5 — Recurrence guard

Two-tier guard:
1. **Schema presence**: exit test 1 `toHaveProperty('domain')` — future removal fails this test.
2. **Negative guard**: exit test 1 `not.toHaveProperty('limit'/'offset')` — future re-addition of semantically undefined pagination fails these assertions.
3. **Behavior wiring**: exit tests 3–4 assert domain param appears in both verdictSql and multiplierSql call params — any future reversal of handler wiring fails these.

Guards directly detect the defect class (unwired optional filter param). Not a weak proxy. PASS.

## Q7 — Unverified assumptions / citations

All citations verified against current source:
- `query_calibration.ts` lines 27–43: input_schema confirmed — no domain/limit/offset. ✓
- `query_calibration.ts` lines 64–67: handler reads only chart_id, include_held_out, promoted_only. ✓
- `query_calibration.ts` lines 72–84 (verdictSql), 86–92 (reliabilitySql), 94–101 (multiplierSql), 103–108 (qaSql): all confirmed at exact lines in 141-line file. ✓
- `multiplierSql` at line 95 selects `domain` — confirms mimamsa_multipliers carries a domain column; §2 change #4 (WHERE domain = $n directly) is correct. ✓
- `reliabilitySql` / `qaSql` exclusion: SELECT columns confirmed have no domain column. ✓
- `register_p1_aliases.ts:1852–1854`: confirmed — line 1852 is the async handler `async ({ chart_id, domain, limit, offset }) =>`, line 1854 is `callPlatformPrim('query_calibration', { chart_id, domain, limit, offset }, principal)`. Minor note: SPEC says this "already forwards { chart_id, domain }" but currently it still forwards limit/offset too (pre-F-08). The parenthetical "(after F-08 Change A2 removes the limit/offset spread)" makes this explicit — not a blocking deficiency, just a future-state description.
- `query_predictions.ts:82` sibling pattern (p++ evaluate-before-increment): confirmed. ✓
- §2 change #3 parameterization: `const vDomainIdx = vParams.push(domain)` — `Array.push()` returns new length; for vParams=[chart_id] (length 1), push returns 2, so `$${vDomainIdx}` = `$2`. Correct for PostgreSQL 1-indexed params. Off-by-one concern from prior review (old `$${vParams.length + 1}` wording) is resolved in the revised spec. ✓
- `writer_asset: null`, `data_delta: narrow` (SPEC frontmatter rs_class: RS-A): read-path change only; no writer-layer modification; no asset rebuild triggered. ✓

## Verdict: COMPLETE

The revised SPEC correctly addresses the defect mechanism at all three layers (schema, handler, SQL), prescribes the JOIN approach required by the missing domain column, covers all 7 diagnosed sibling sites with reasons, explicitly resolves the limit/offset no-op via F-08 alignment rather than silent wiring, and provides an exit test that genuinely fails on today's source (3/4 tests fail). The parameterization fix (using push return value for index) resolves the off-by-one concern from the prior review. All `file:line` citations are accurate. `writer_asset: null`, `data_delta: narrow` confirmed correct.