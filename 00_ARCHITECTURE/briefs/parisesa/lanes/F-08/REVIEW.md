---
lane: F-08
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-08/SPEC.md, F-08/DIAGNOSIS.md (no REVIEW_LEADS.md present). Verified against main-ro source:
- `platform-mcp/src/tools/register_p1_aliases.ts` lines 1733–1858 (phala_mitigation_get + mimamsa_calibration_get)
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` (full)
- `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` lines 330–427 (queryRemedyProgramCapability)
- `platform/migrations/brahma_phala_mitigation.sql` (phala_mitigation column list)
- `platform/migrations/349_mimamsa_gunanaka.sql` (mimamsa_multipliers domain column)
- GlobalBase definition at register_p1_aliases.ts:323–326

Exit tests traced line-by-line against current source.

## Q1 — Mechanism vs. symptom

SPEC addresses mechanism. It identifies the cross-file contract mismatch: the MCP alias (`register_p1_aliases.ts`) advertises a `domain` parameter that the inner primitive never agreed to accept, and the underlying table has no domain column making the filter structurally impossible. The SPEC correctly overrides the DIAGNOSIS fix-point (which said to add domain to the primitive) with evidence from the schema migration. This is mechanistic, not symptomatic.

## Q2 — DIAGNOSIS sub-claims vs. SPEC elements

| DIAGNOSIS claim | SPEC element |
|---|---|
| (a) domain in alias schema at :1741 | Change A1: remove from alias |
| (b) never read at primitive boundary | §1 confirms primitive input_schema omits domain; handler never reads it |
| (c) byte-identical results confirmed live | Resolved by alias removal |
| (d) no disclosure in filters echo | Resolved by alias removal; no echo needed |
| §3 fix-point: query_phala_calibration.ts | §1 CORRECTS to alias-side; schema migration confirms phala_mitigation has no domain column |
| §4 sibling mimamsa_calibration_get domain/limit/offset no-op | Changes A2 + B1-B4 |
| §4 L4_phala internal check zero matches | §4 excluded (clean) |
| §4 ~46 callRegistryCap false positives | §4 excluded (false positives) |
| §5 PAR-F-08-NEEDS-LEASE query_phala_calibration.ts | §7 SUPERSEDED: alias-side fix |
| §5 PAR-F-08-SIBLING-NEEDS-LEASE query_calibration.ts | §7 COVERED: Change B1-B4 |

All DIAGNOSIS claims map to SPEC elements. The fix-point correction is the most important — it's well-argued and schema-verified.

## Q3 — Exit tests: genuinely RED on main-ro?

**Test 1** (`f08_phala_mitigation_alias.test.ts`): Finds 'phala_mitigation_get' in register_p1_aliases.ts (found at line 1733), takes a 500-char slice, asserts the block does NOT match `/domain\s*:\s*z\.string/`. Current code at line 1736 shows `domain: z.string().optional()` — match IS present. **Test FAILS on current code.** ✓

**Test 2** (`f08_calibration_domain.test.ts`): Imports `queryCalibrationCapability` and asserts `'domain' in queryCalibrationCapability.input_schema` is true. Current `input_schema` has only `chart_id`, `include_held_out`, `promoted_only` — no `domain`. **Test FAILS on current code.** ✓

Both tests would PASS after Changes A1 and B1 respectively.

## Q4 — Sibling sites

| Site | Status | Coverage |
|---|---|---|
| phala_mitigation_get (primary) | Confirmed live (identical hashes) | Change A1 |
| mimamsa_calibration_get (confirmed sibling) | Confirmed defect (domain/limit/offset forwarded to primitive that ignores all three) | Changes A2 + B1-B4 |
| L4_phala internal 5-file check | Excluded: diagnosis confirmed zero within-file declared-but-unread fields | Stated |
| ~46 callRegistryCap/callSidecarPath sites | Excluded: spot-check confirmed false positives from regex artefact | Stated |

All sibling sites from DIAGNOSIS are addressed or excluded with reasons. ✓

## Q5 — Recurrence guard

Spec proposes `alias_primitive_contract.test.ts`: statically parses all `callPlatformPrim(...)` call sites in register_p1_aliases.ts, loads each target primitive's input_schema, asserts every forwarded param key is declared. This directly detects the defect class (alias-to-primitive schema contract mismatch), not a proxy. Strong guard.

Note: SPEC designates this as a 'SEPARATE deliverable' that 'may be written after primary fixes land'. This is acceptable sequencing disclosure, not a deficiency — the guard exists and is well-specified. Builder is notified.

## Q7 — Unverified assumptions / file:line accuracy

**phala_mitigation_get line numbers:** SPEC says '~lines 1738–1753', DIAGNOSIS says '1738–1749'. Actual: `server.tool('phala_mitigation_get', ...)` opens at line 1733, closes at 1744. The inner handler body (where the DIAGNOSIS focused) begins at 1737. The ~5-line offset is minor; SPEC correctly uses '~'. The domain field IS at line 1736 — the fix target is correct.

**mimamsa_calibration_get lines 1844–1858:** Confirmed accurate — tool opens at 1844, GlobalBase spread at 1850, handler at 1852, call at 1854.

**query_calibration.ts input_schema ~line 43:** Confirmed — input_schema closes at line 43 after promoted_only (lines 39-41). Change B1 insertion point is correct.

**query_calibration.ts ~line 67 (Change B2):** Confirmed — line 67 is `const promoted_only = Boolean(args.promoted_only ?? false)`. Domain read insertion after this line is correct.

**query_calibration.ts ~lines 94-101 multiplierSql (Change B3):** Confirmed — multiplierSql construction at lines 94-101, WHERE clause at line 99 with `${multFilter}` string interpolation. Change B3 replaces this with parameterized array. The substitution `query(multiplierSql, [chart_id])` → `query(multiplierSql, multParams)` targets line 114 correctly.

**query_calibration.ts ~line 129 filters (Change B4):** Confirmed — `filters: { include_heldout, promoted_only }` at line 129.

**brahma_phala_mitigation.sql:** Confirmed NO `domain` column in phala_mitigation table. SPEC's fix-point correction is schema-verified. ✓

**349_mimamsa_gunanaka.sql line 12:** Confirmed `domain text` in mimamsa_multipliers. SPEC's claim that domain filtering is implementable at the primitive is schema-verified. ✓

No unverified assumptions found. All material file:line citations verified against main-ro source.

## Verdict: COMPLETE

The spec correctly identifies the mechanism (cross-file alias-to-primitive schema contract mismatch), corrects the DIAGNOSIS fix-point error with schema evidence, covers all DIAGNOSIS sibling sites, provides exit tests that are genuinely RED on current code, and specifies a strong structural recurrence guard. All material citations verified. Minor line-number approximation (~5 lines for phala_mitigation_get block) is within the spec's stated '~' tolerance.
