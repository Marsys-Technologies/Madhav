---
finding: F-125
spec_by: SPEC_WRITER (PARIŚEṢA-RĀTRI)
stage: S DRAFT
rs_class: RS-A
writer_asset: null
data_delta: narrow
---

# SPEC — F-125: B.11 Orientation Gate Missing on kala_upaya_get + bodha_* regAlias Family

## 1. Root-cause statement

`fetchOrientationContext` is declared without `export` in `registry_bridge.ts:2061` and is called only at 15 hard-coded sites inside that one file, so tools registered in external modules — `kala_upaya_get` (in `kala_views/upaya.ts`) and every tool built through the `regAlias` helper in `register_p1_aliases.ts` — cannot call it; the B.11 orientation gate is structurally unreachable from outside `registry_bridge.ts`, not merely forgotten.

## 2. Files to change

### 2a. `platform-mcp/src/tools/registry_bridge.ts` — builder: S2 MĀTRĀ (owns file)
**Change:** Add `export` keyword to `fetchOrientationContext` at line 2061.
```diff
-async function fetchOrientationContext(
+export async function fetchOrientationContext(
```
**Why:** Sole prerequisite for every other stream's wiring. No behavioral change in this file; the 15 existing call sites are unaffected. Also export the `OrientationEnvelope` type for compile-time safety:
```ts
export type OrientationEnvelope = { orientation_context: unknown; orientation_ok: boolean }
```

### 2b. `platform-mcp/src/tools/kala_views/upaya.ts` — builder: S4 VĀCA (owns file per plan §2.1 kala_views split)
**Change:** Import `fetchOrientationContext` from `../registry_bridge.js` and call it inside `registerKalaUpayaGet`'s handler, merging `orientation_context`/`orientation_ok` into the returned response JSON. `ayanamsha_id` is not in `KalaUpayaInputShape`; pass `undefined`.
```ts
// Add to imports:
import { fetchOrientationContext } from '../registry_bridge.js'

// Inside handler, after buildKalaUpayaResult returns, before return:
const { orientation_context, orientation_ok } = await fetchOrientationContext(
  chart_id, undefined, principal
)
return {
  content: [{ type: 'text' as const,
    text: JSON.stringify({ ...response, orientation_context, orientation_ok }, null, 2) }],
}
```
**Why:** Closes A2 (named finding). `kala_upaya_get` issues PACT-chain verdict/prescription — definitionally interpretive synthesis per A4, not RS-4-exempt.

### 2c. `platform-mcp/src/tools/register_p1_aliases.ts` — builder: S5 MŪLA (owns file; land AFTER S1 CL-11 sweep)
**Change:** (1) Add `fetchOrientationContext` to the existing `registry_bridge.js` import. (2) Add `requiresOrientation?: boolean` to `regAlias`'s `opts` parameter. (3) Inside the `regAlias` handler, when `opts.requiresOrientation` is true, call `fetchOrientationContext` and merge the result into the `dualOutput` payload. (4) Set `requiresOrientation: true` on exactly four registrations: `bodha_domain_reading_get` (line 503), `bodha_remedies_get` (line 1015), `bodha_remedies_search` (line 1028), and `bodha_quality_get`.
**Why:** Closes A3 (named finding) and the same-mechanism siblings identified in diagnosis §4. The remaining 12 `regAlias` registrations (ganita_*, standing_predictions_read, etc.) are RS-4-exempt factual lookups (diagnosis §4 explicit); they keep the flag false/absent.

## 3. Exit test

**File:** `platform-mcp/src/__tests__/b11_gate_f125.test.ts`
**Command:** `cd platform-mcp && npx jest --testPathPattern=b11_gate_f125 --no-coverage`

FAILS on current code (orientation keys absent), PASSES after fix:
```ts
describe('F-125 B.11 orientation gate', () => {
  const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

  it('kala_upaya_get response carries orientation_ok and orientation_context', async () => {
    const result = await callTool('kala_upaya_get', { chart_id: CHART, domain: 'career' })
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed).toHaveProperty('orientation_ok')      // FAILS today
    expect(parsed).toHaveProperty('orientation_context') // FAILS today
  })

  it('bodha_remedies_get response carries orientation_ok and orientation_context', async () => {
    const result = await callTool('bodha_remedies_get', { chart_id: CHART })
    // dualOutput nests under content — drill one level
    const envelope = JSON.parse(result.content[0].text)
    const inner = (envelope.content ?? envelope) as Record<string, unknown>
    expect(inner).toHaveProperty('orientation_ok')      // FAILS today
    expect(inner).toHaveProperty('orientation_context') // FAILS today
  })
})
// Uses the same UCD mock fixture as assess_career's existing tests.
```

## 4. Sibling sites covered

All 18 tools from diagnosis §4 census enumerated; covered or explicitly excluded:

| Tool(s) | File | Covered? | Reason |
|---|---|---|---|
| `kala_upaya_get` | `kala_views/upaya.ts` | YES — §2b | Primary named finding A2 |
| `bodha_remedies_get` | `register_p1_aliases.ts` | YES — §2c | Primary named finding A3 |
| `bodha_domain_reading_get` | `register_p1_aliases.ts` | YES — §2c | Same regAlias mechanism; diagnosis §4 confirms same interpretive class |
| `bodha_remedies_search` | `register_p1_aliases.ts` | YES — §2c | Same regAlias mechanism; same class as bodha_remedies_get |
| `bodha_quality_get` | `register_p1_aliases.ts` | YES — §2c | Same regAlias mechanism; diagnosis §4 confirms interpretive class |
| `ganita_medical_get`, `ganita_vastu_get`, `ganita_ayurdaya_get`, `ganita_sensitive_degrees_get`, `ganita_vichara_get`, `ganita_yoga_firings_get`, `ganita_av_transit_gating_get`, `kala_priority_ranking_get`, `ganita_dashas_get`, `standing_predictions_read`, `ganita_dasha_periods_get`, `query_dasha_periods` | `register_p1_aliases.ts` | EXCLUDED | Diagnosis §4 explicit: "L0/L1 factual reference lookups plausibly RS-4-exempt"; regAlias flag defaults false |
| `kala_ahead_get` | `kala_views/ahead.ts` | EXCLUDED — follow-on | S4 VĀCA lease; §2a export is the prerequisite; conductor to issue follow-on for S4 wiring |
| `kala_dasha_sandhi_get` | `kala_views/dasha_sandhi.ts` | EXCLUDED — follow-on | Lease unconfirmed (not in plan §2.1 split table); follow-on after conductor assigns |
| `kala_elect_get` | `kala_views/elect.ts` | EXCLUDED — follow-on | S2 MĀTRĀ lease but outside F-125 builder scope; S2 self-assigns follow-on after F-125 lands |
| `kala_explain_get` | `kala_views/explain.ts` | EXCLUDED — follow-on | S4 VĀCA lease; follow-on |
| `kala_now_get` | `kala_views/now.ts` | EXCLUDED — follow-on | S4 VĀCA lease; follow-on |
| `kala_priority_get` | `kala_views/priority.ts` | EXCLUDED — follow-on | S2 MĀTRĀ lease; follow-on |
| `kala_ritual_get` | `kala_views/ritual.ts` | EXCLUDED — follow-on | S2 MĀTRĀ lease; follow-on |
| `kala_story_get` | `kala_views/story.ts` | EXCLUDED — follow-on | S2 MĀTRĀ lease; the 1 orientation hit is a drill_pointers pointer string (line 748), never a fetch — fails identically; follow-on |
| `phala_mitigation_get` | `phala_mitigation_map.ts` | EXCLUDED — follow-on | Lease unconfirmed; follow-on |
| `phala_outlook_get` | `phala_outlook.ts` | EXCLUDED — follow-on | Lease unconfirmed; follow-on |
| `phala_anchors_get`, `phala_predictive_anchors_get` | `phala_event_anchors.ts` | EXCLUDED — follow-on | Lease unconfirmed; follow-on |
| `mechanism_retrodiction_get` | `mechanism_retrodiction.ts` | EXCLUDED — follow-on | Lease unconfirmed; follow-on |

## 5. Recurrence guard

The exit test file `b11_gate_f125.test.ts` runs on every CI pass and fails closed if orientation keys are dropped from either named tool.

Additionally, add to `registry_bridge.ts`'s doc block and CLAUDE.md §I B.11 section:
> Any new interpretive MCP tool registered outside `registerRegistryBridgeTools` MUST either (a) import and call `fetchOrientationContext`, or (b) carry a `// B.11-EXEMPT: RS-4 retrieval — <reason>` comment at its registration site. The exit test for F-125 checks the two primary tools; new interpretive tools must be added to that test or a sibling.

## 6. Dependencies, rollback

**Sequencing:**
1. §2a (S2, `registry_bridge.ts` export) — must land first; unblocks §2b and §2c.
2. §2b (S4, `upaya.ts`) — depends on §2a.
3. §2c (S5, `register_p1_aliases.ts`) — depends on §2a; must land AFTER S1's CL-11 `dualOutput` sweep on the same file (plan §2.1 row 4).

**No DB migration.** This is a platform-mcp TypeScript read-path change. It adds a live `marsys://tool/L2/query_ucd` pre-fetch to the affected tools — same pre-fetch already made by `assess_*` family; no stored data changes.

**Shadow run (Level 0, mandatory):** Mount `kala_upaya_get` and `bodha_remedies_get` against mock registry with UCD fixture (reuse `assess_career` harness); assert `orientation_ok` present in response; `conn.rollback()` in finally. Log to `results/F-125.shadow.log`.

**Rollback:** Revert `export` on `fetchOrientationContext` in `registry_bridge.ts` — this produces an immediate TypeScript compile error in `upaya.ts` and `register_p1_aliases.ts`, making the rollback self-auditing. Revert the import+call hunk in `upaya.ts`. Revert `requiresOrientation` additions in `regAlias`.

## 7. Coverage table

| Sub-claim (DIAGNOSIS) | Spec section |
|---|---|
| A1: assess_* carry orientation_ok (confirmed present) | No change needed; exit test's contrast validates it remains |
| A2: kala_upaya_get carries no orientation | §2b fix + exit test §3 test 1 |
| A3: bodha_remedies_get carries no orientation | §2c fix + exit test §3 test 2 |
| A4: interpretive class confirmed, not RS-4-exempt | Accepted; §2c flag design explicitly leaves RS-4-exempt aliases at flag=false |
| A5: mechanism is the unexported private function — structural gap | §2a (export) is the exact structural remedy; its prerequisite role for §2b/§2c confirms the diagnosis |
| §3b bodha_remedies_get identical URI to get_remedies but without orientation | §2c closes the parity gap |
| §4 census: bodha_domain_reading_get, bodha_remedies_search, bodha_quality_get same class | §2c covers all three via requiresOrientation flag |
| §4 census: kala_views/* siblings, phala/* siblings, mechanism_retrodiction | §4 table with explicit follow-on exclusion reason per site |
| §5 LEASE VERDICT split (S2/S4/S5) | §2a/§2b/§2c builder assignments + §6 sequencing |
