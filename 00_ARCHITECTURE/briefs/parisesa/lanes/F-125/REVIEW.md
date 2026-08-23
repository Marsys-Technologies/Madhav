---
lane: F-125
stream: S2 MĀTRĀ
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-125/DIAGNOSIS.md, F-125/SPEC.md, F-125/NEEDS_LEASE.md.

Source verified at `/Users/Dev/par-night/main-ro` (origin/main read-only mirror):
- `registry_bridge.ts:2061` — `fetchOrientationContext` export status
- `kala_views/upaya.ts:494-528` — `registerKalaUpayaGet` handler body
- `register_p1_aliases.ts:351-384` — `regAlias` function body (no orientation fetch)
- `register_p1_aliases.ts:1015-1025` — `bodha_remedies_get` registration
- `register_p1_aliases.ts:503` — `bodha_domain_reading_get` registration
- `register_p1_aliases.ts:1028` — `bodha_remedies_search` registration
- `register_p1_aliases.ts:1042` — `bodha_quality_get` registration
- Test harness patterns in `registry_bridge_r5w3_judgment_and_portrait.test.ts` (stubFetch/makeCapturingServer)
- `CLAUDE.md` root — B.11 section existence at line 224

Exit test traced line-by-line against current source (no CI run — main-ro is read-only, no jest available in mirror). Failure path reasoned from source.

## Q1 — Mechanism vs symptom

PASS. The spec identifies the structural root cause: `fetchOrientationContext` is module-private (no `export` keyword, confirmed at line 2061), making it structurally unreachable from `upaya.ts` and `register_p1_aliases.ts` regardless of developer intent. The §2a fix (add `export`) directly addresses the structural barrier, not just the downstream effect. The sequencing model (§2a → §2b + §2c) is mechanistically coherent.

## Q2 — Diagnosis sub-claims → spec elements

PASS. All sub-claims fully mapped:

| Diagnosis sub-claim | Spec coverage |
|---|---|
| A1: assess_* carry orientation_ok | No-change acknowledged; exit test contrast validates |
| A2: kala_upaya_get missing orientation | §2b fix + exit test §3 test 1 |
| A3: bodha_remedies_get missing orientation | §2c fix + exit test §3 test 2 |
| A4: interpretive class, not RS-4-exempt | Accepted; §2c flag design excludes RS-4 aliases |
| A5: structural gap — unexported private function | §2a export is the exact structural remedy |
| §3b: bodha_remedies_get shares URI with get_remedies but drops orientation | §2c closes parity gap; noted in §7 |
| §4 census: bodha_domain_reading_get, bodha_remedies_search, bodha_quality_get same class | §2c covers all three via requiresOrientation flag |
| §4 census: 12 RS-4-exempt regAlias tools | §4 table explicit exclusion with rationale |
| §4 census: kala_views/*, phala/*, mechanism_retrodiction | §4 table with follow-on exclusion per site + stream |
| §5 LEASE VERDICT split S2/S4/S5 | §2a/§2b/§2c builder assignments + §6 sequencing |

No unmapped diagnosis claim found.

## Q3 — Exit test would fail on current code

PASS (traced, not run).

**Test 1 (`kala_upaya_get`):** Handler at `upaya.ts:494-528` calls `buildKalaUpayaResult()` and returns `JSON.stringify(response, null, 2)` directly. The `buildKalaUpayaResult` function (confirmed by grep in DIAGNOSIS §3b: `grep -c "orientation" upaya.ts = 0`) never touches orientation. `expect(parsed).toHaveProperty('orientation_ok')` → FAILS on current code. ✓

**Test 2 (`bodha_remedies_get`):** Handler at `register_p1_aliases.ts:351-384` (`regAlias`) calls `callRegistryCap(uri, ..., principal)` then returns `dualOutput(data, name)`. No orientation fetch anywhere in the helper. `expect(inner).toHaveProperty('orientation_ok')` → FAILS on current code. ✓

**Minor note on test harness:** The exit test snippet references `callTool('kala_upaya_get', ...)` without defining the helper or its imports. The comment "Uses the same UCD mock fixture as assess_career's existing tests" is imprecise — the assess_career tests (`elev_alpha_assess_completeness.test.ts`) test pure functions without HTTP-level UCD mocking; the actual relevant pattern is `registry_bridge_r5w3_judgment_and_portrait.test.ts`'s `makeCapturingServer` + `stubFetch` harness (which defaults `marsys://tool/L2/query_ucd` to an empty digest). The builder must implement this harness pattern for both `registerKalaUpayaGet` (from `kala_views/upaya.ts`) and `registerP1Aliases` (from `register_p1_aliases.ts`) — the spec omits this setup. This is a builder-implementation detail, not a spec correctness defect, since the failure assertions are correct and the harness pattern is documented in the codebase. Not elevated to INCOMPLETE-RETURN.

## Q4 — Sibling site coverage

PASS. All 18+ sites from DIAGNOSIS §4 census are accounted for in SPEC §4:

- 4 `regAlias` tools explicitly covered with `requiresOrientation: true` (bodha_domain_reading_get, bodha_remedies_get, bodha_remedies_search, bodha_quality_get)
- 12 `regAlias` tools excluded as RS-4-exempt factual lookups (ganita_*, kala_priority_ranking_get, standing_predictions_read, etc.) — rationale stated
- 8 kala_views/* tools excluded as follow-on with stream/lease indicated
- 3+ phala/* tools excluded as follow-on
- mechanism_retrodiction_get excluded as follow-on

All exclusions carry stated reasons. No site from the diagnosis census is silently dropped.

## Q5 — Recurrence guard

PASS. Two-layer guard:
1. CI exit test (`b11_gate_f125.test.ts`) directly checks `orientation_ok` and `orientation_context` on the two primary tools — tests for the defect class itself, not a proxy.
2. CLAUDE.md §I B.11 doc-block amendment requiring new interpretive tools to either call `fetchOrientationContext` or carry a `// B.11-EXEMPT: RS-4 retrieval — <reason>` comment at registration site.

The `export` + required import chain provides structural enforcement: any caller that imports `fetchOrientationContext` makes the architectural intent explicit at compile time.

## Q7 — Citation verification

PASS. All cited file:line references verified against current source:

| Citation | Claimed | Actual | Match |
|---|---|---|---|
| `fetchOrientationContext` in registry_bridge.ts | line 2061, not exported | line 2061, `async function` (no export) | ✓ |
| `registerKalaUpayaGet` in upaya.ts | lines 494-528 | lines 494-528 | ✓ |
| `bodha_remedies_get` regAlias in register_p1_aliases.ts | line 1015 | line 1015 | ✓ |
| `bodha_domain_reading_get` regAlias | line 503 | line 503 | ✓ |
| `bodha_remedies_search` regAlias | line 1028 | line 1028 | ✓ |
| `regAlias` function definition | lines 351-384 | lines 351-384 | ✓ |
| `bodha_quality_get` | no line cited | actual line 1042 | Minor omission (no line given, not wrong) |
| CLAUDE.md §I B.11 | stated to exist | confirmed at line 224 | ✓ |

No incorrect citations. `bodha_quality_get` has no line number in §2c but this is an omission, not an error.

`writer_asset: null` and `data_delta: narrow` are accurate — this is a TypeScript platform-mcp change with no DB writes, adding a live pre-fetch path.

## Named deficiencies

None. Exit test harness underspecification (Q3 note) is implementation-level and does not prevent the builder from producing a correct test.

## Verdict: COMPLETE
