---
lane: F-73
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, DIAGNOSIS.md, SPEC.md (revision 1 / R2 — explain.ts sibling coverage added). No REVIEW_LEADS.md present (previous REVIEW.md present from pool-1 with INCOMPLETE-RETURN; this is a fresh assessment of R2). Source read from `/Users/Dev/par-night/main-ro` (read-only).

Files read / searched:
- `platform-mcp/src/tools/kala_views/now.ts` (lines 1350–1430) — all cited lines confirmed
- `platform-mcp/src/tools/kala_views/explain.ts` (lines 450–484) — sibling site at 456, 475–476 confirmed
- `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` (lines 1595–1700) — `computeGocharaForecast` export and `windows` return key confirmed
- Grep: `marsys://tool/L4/gochara_forecast_get` across `platform-mcp/src/**` — 4 hits: 2 production call sites (now.ts:1373, explain.ts:476) + 2 test mock handlers (kala_now_get_c4_narrative.test.ts:159, kala_explain_get_c4_a5.test.ts:139)

## Q1 — Mechanism vs. symptom

SPEC addresses mechanism. §0/§1 correctly identifies the root cause as a phantom registry URI (`marsys://tool/L4/gochara_forecast_get`) never backed by any registered capability, causing every call to 404 silently and force `insufficient_data`. §0 also corrects DIAGNOSIS.md's originally-wrong fix location ("add registration to layers/L4_phala/index.ts") to the mechanically correct one ("replace HTTP round-trip with direct in-process call to the already-exported `computeGocharaForecast`"). Both affected files identified. ✓

## Q2 — Sub-claim coverage

All four DIAGNOSIS.md §2 sub-claims covered:
1. "field_gochara_alignment is 'insufficient_data' unconditionally" → SPEC §1/§2 (replaces always-404ing call in now.ts AND explain.ts)
2. "root cause is phantom URI with no registration" → SPEC §0/§1 (corrected: URI was never meant to exist)
3. "underlying substrate is healthy" → SPEC §2 (fix reuses that healthy substrate directly)
4. "different root cause from F-53" → implicitly resolved by mechanism identification (domain naming trap structurally inapplicable)

SPEC §7 table maps sub-claims 1–3 explicitly; sub-claim 4 is a negative differentiation requiring no spec element. ✓

## Q3 — Exit test genuinely fails today

YES — traced against current source:

**kala_now_get**: `now.ts:1372–1380` calls `callRegistryCapability('marsys://tool/L4/gochara_forecast_get', ...)`. Grep on `platform/src/lib/retrieval/registry/layers/*/index.ts` for 'gochara' → zero matches (confirmed). `now.ts:1381`: `if (!resp.ok || !resp.content) return []` — 404 silently returns empty. `now.ts:1427`: `if (!moonTransitAvailable || activeWindows.length === 0) { fieldGocharaAlignment = 'insufficient_data' }` fires unconditionally. Exit test failure is structurally guaranteed. ✓

**kala_explain_get**: `explain.ts:475–476` calls `callKalaRegistryCap('marsys://tool/L4/gochara_forecast_get', ...)` — same phantom URI, same 404 path, `unwrapKalaPayload` returns `{}`, `windows` defaults to `[]`, `buildA5GocharaAgreement` returns `insufficient_data`. Exit test failure guaranteed. ✓

## Q4 — Sibling sites covered

R2 addresses the prior INCOMPLETE-RETURN deficiency in full. SPEC §4 now:
- Explicitly confirms `explain.ts:456–483` / line 475 as the sibling call site (lines 456, 475–476 match current source exactly — verified this pass)
- Adds explain.ts to §2 "Files to change" with a complete code prescription
- Adds `kala_explain_get` exit test to §3
- States "no further sibling sites remain" with supporting grep

Minor inaccuracy: spec claims "exactly these two occurrences" but grep surfaces 4 total — the additional 2 are test mock handlers that intercept the phantom URI via `fetch` mock. These are not production call sites; no additional bugs. Builder note (not a spec deficiency): after the fix bypasses `fetch` entirely, these test mocks will silently stop injecting gochara-window data, potentially causing CI failures. Builder must update test mocks to stub `computeGocharaForecast` directly (module mock) rather than via HTTP interception. The spec is silent on this — acceptable (test updates are Stage B work). ✓

## Q5 — Recurrence guard

SPEC §5 recommends a registry-catalog lint flagging any `marsys://tool/...` URI string literal in `platform-mcp/src/**` with no matching registry-layer entry. Guard correctly targets the defect class (phantom URI references). Correctly marked as a governance addition, not required for COMPLETE. ✓

## Q7 — Unverified assumptions / bad citations

All cited file:line values verified against current source:
- `now.ts:1359` → ✓ `fetchGocharaForecastWindows` function definition
- `now.ts:1373` → ✓ phantom URI literal
- `now.ts:1423` → ✓ call site in `buildGocharaNarrativeBlock`
- `register_gochara_windows.ts:1605` → ✓ `export async function computeGocharaForecast`
- `register_gochara_windows.ts:1634` → ✓ `windows: []` key confirmed in return shape
- `explain.ts:456–483` → ✓ `fetchA5GocharaWindows` function body
- `explain.ts:475` → ✓ `callKalaRegistryCap` call; line 476 is the URI string (spec §4 labels it "confirmed line 476" — correct)
- Import path `'../retrieval/register_gochara_windows.js'` → ✓ correct relative path (kala_views/ → retrieval/)

No unverified assumptions on critical claims. The `computeGocharaForecast` signature matches exactly what the spec prescribes: `(chartId, dateRange, eventClass, valence, limit, principal, domain?, resolution?)`. The spec's `result['windows']` extraction is confirmed by the function's return shape. ✓

## Named deficiencies

None blocking COMPLETE.

Builder note (not counted as a spec deficiency):
- `kala_now_get_c4_narrative.test.ts:159` and `kala_explain_get_c4_a5.test.ts:139` currently mock the phantom URI via `fetch` interception. After the fix, these mocks will not be reached (code calls `computeGocharaForecast` directly). Builder must update these test files to use module-level mocking of `computeGocharaForecast` instead of HTTP interception, or tests that previously passed with injected gochara windows will regress.

## Verdict: COMPLETE
