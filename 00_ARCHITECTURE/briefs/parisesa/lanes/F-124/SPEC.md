---
lane: F-124
stream: S2 (MĀTRĀ)
stage: S — SPEC
status: READY-FOR-BUILDER
authored: 2026-08-17
revision: 2
companion_lanes: F-14, F-15
closing_lanes_reading_claims: F-14-C1, F-15-C1, F-124-C1 through C4/C7/NEW
files_changed: [platform-mcp/src/tools/registry_bridge.ts]
migration: false
rs_class: RS-A
writer_asset: null
data_delta: narrow
---

# F-124 SPEC — assess_career vs. assess_marriage/assess_health depth asymmetry

## 1. Root cause (one sentence, mechanism-level)

`assess_marriage` and `assess_health` never call `attachDomainCompleteness`/`attachDomainReading` in their handlers (call sites simply absent at `registry_bridge.ts:2989` and `3071`), AND five domain-keyed maps (`DOMAIN_READING_FAMILIES` and four companion maps, `:1034–1043`) carry only `wealth`/`career` keys so `buildDomainReading` early-returns with `families_total=0` even if the call sites existed; a third, independent gate — `buildAssessResponse:2925` checks `response['completeness']` while `attachDomainCompleteness` writes `response['domain_completeness']` — additionally suppresses `domain_completeness` and `completeness_directive` for all four assess_* tools including the ostensibly-working career/wealth pair.

## 2. Files to change

Single file: `platform-mcp/src/tools/registry_bridge.ts`

### Change A — Five domain maps (lines 1034–1043): add `health` and `relationship` keys

**A1. `DOMAIN_READING_FAMILIES` (`:1034`)** — Define `AssessedDomain` union first; declare the map directly as `Record<AssessedDomain, readonly string[]>` (no cast) so tsc enforces key exhaustiveness structurally:

```ts
const RELATIONSHIP_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D9', 'argala_house_7',
  'full_dispositor_closure', 'all_chart_mechanisms_and_chains', 'special_lagnas',
  'cross_ayanamsha_agreement', 'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const
const HEALTH_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D6', 'argala_house_1', 'argala_house_6', 'argala_house_8',
  'full_dispositor_closure', 'all_chart_mechanisms_and_chains', 'special_lagnas',
  'cross_ayanamsha_agreement', 'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const

// Compile-time exhaustiveness guard: adding a new key to AssessedDomain without adding
// the corresponding entry to DOMAIN_READING_FAMILIES will cause tsc --noEmit to error.
// Update both in lockstep when a new assess_* domain is introduced.
type AssessedDomain = 'wealth' | 'career' | 'health' | 'relationship'
const DOMAIN_READING_FAMILIES: Record<AssessedDomain, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
  relationship: RELATIONSHIP_READING_FAMILIES,
  health: HEALTH_READING_FAMILIES,
}
```

Note: no `as` cast, no separate `_allDomainsWired` variable. The direct `Record<AssessedDomain, ...>` annotation is the guard — TypeScript checks object literal completeness against the mapped type structurally. A future `assess_longevity` that adds `'longevity'` to `AssessedDomain` but omits it from the map will fail `tsc --noEmit` immediately.

Family rationale — families follow the same logic as WEALTH/CAREER but scoped to each domain's primary varga and houses (per `register_d8_assess_domain.ts:184–188`):
- relationship: D9, house 7, karaka Venus — 10 families
- health: D6, houses 1/6/8, karaka Sun — 12 families (no secondary varga, three argala houses)

**A2. `DOMAIN_READING_VARGAS` (`:1040`)** — Widen type from `Record<string, [string, string]>` to `Record<string, readonly string[]>` (health and relationship have one primary varga each; the strict 2-tuple type would require `vargas[1]` to always exist, which Change B must guard against):

```ts
const DOMAIN_READING_VARGAS: Record<string, readonly string[]> = {
  wealth: ['D2', 'D11'], career: ['D10', 'D9'],
  relationship: ['D9'], health: ['D6'],
}
```

**A3. `DOMAIN_READING_HOUSES` (`:1041`)**:

```ts
const DOMAIN_READING_HOUSES: Record<string, number[]> = {
  wealth: [2, 11], career: [10],
  relationship: [7], health: [1, 6, 8],
}
```

**A4. `DOMAIN_READING_KARAKA_CODE` (`:1042`)**:

```ts
const DOMAIN_READING_KARAKA_CODE: Record<string, string> = {
  wealth: 'JUP', career: 'SAT',
  relationship: 'VEN', health: 'SUN',
}
```

**A5. `DOMAIN_READING_KARAKA_LABEL` (`:1043`)**:

```ts
const DOMAIN_READING_KARAKA_LABEL: Record<string, string> = {
  wealth: 'Jupiter', career: 'Saturn',
  relationship: 'Venus', health: 'Sun',
}
```

### Change B — `buildDomainReading` varga-label/index guard (lines 1531–1532)

Current code accesses `vargas[0]` and `vargas[1]` with a `wealth`/non-wealth ternary label. After type-widening in A2, `vargas[1]` is `string | undefined` for single-varga domains. Replace lines 1531–1532 with:

```ts
add(readVargaFamily(vargaAnalysis, vargas[0],
  domain === 'wealth'       ? 'Horā — liquid wealth'
  : domain === 'health'     ? 'Ṣaṣṭhāṃśa — health/vitality'
  : domain === 'relationship' ? 'Navāṃśa — relationship/dharma'
  : 'Daśāṃśa — career/status'))
if (vargas[1] != null) add(readVargaFamily(vargaAnalysis, vargas[1],
  domain === 'wealth' ? 'Rudrāṃśa — gains/income' : 'Navāṃśa — dharma/marriage cross-check'))
```

Why: health and relationship are single-primary-varga domains; `vargas[1]` is `undefined` for them. Without the guard, `readVargaFamily(vargaAnalysis, undefined, ...)` would produce a bogus `divisional_undefined` family entry that would be filtered by `byFamily.get(f)` at line 1552 (it won't appear in HEALTH/RELATIONSHIP_READING_FAMILIES) but wastes a call and potentially causes type-unsafe behaviour. The guard is the clean fix. Lines 1533–1534 (wealth/career domain-specific add calls) require no change — health/relationship have no equivalent singleton family; their structural richness comes from multiple argala houses already enumerated in the FAMILIES arrays.

### Change C — `buildAssessResponse` key-mismatch fix (line 2925)

Replace:
```ts
if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']
```
with:
```ts
if (response['domain_completeness'] !== undefined) grounding['domain_completeness'] = response['domain_completeness']
if (response['completeness_directive'] !== undefined) grounding['completeness_directive'] = response['completeness_directive']
```

Why: `attachDomainCompleteness` (`:835`) mutates `response['domain_completeness']` and `response['completeness_directive']`. The old allow-list checked `response['completeness']` — a key no function ever sets — so both fields were silently dropped in the Sāra envelope for ALL four assess_* tools. This is a key-name mismatch introduced when `buildAssessResponse` (A-09/Sāra-kernel merge) was written without cross-referencing `attachDomainCompleteness`'s actual output keys. Change C fixes this for all four tools simultaneously.

### Change D — Missing call sites in assess_marriage and assess_health handlers

**D1. `assess_marriage` handler**, after `registry_bridge.ts:2989` (`const response = { orientation_context, orientation_ok, ...data ... }`):

```ts
// SATYA-ŚEṢA W7 + Elevation α: domain reading parity with assess_career/assess_wealth (F-14/F-15/F-124)
attachDomainCompleteness(response, 'relationship', chart_id)
await attachDomainReading(response, 'relationship', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
```

Domain key is `'relationship'` (not `'marriage'`) — matching `DOMAIN_READING_FAMILIES`, `DOMAIN_DIRECT_VARGAS`, and `assembleDomainCompleteness`'s domain routing. The L-DOMAIN capability URI (`marsys://tool/L-DOMAIN/assess_marriage`) is unchanged.

**D2. `assess_health` handler**, after `registry_bridge.ts:3071` (`const response = { orientation_context, orientation_ok, ...data ... }`):

```ts
// SATYA-ŚEṢA W7 + Elevation α: domain reading parity with assess_career/assess_wealth (F-14/F-15/F-124)
attachDomainCompleteness(response, 'health', chart_id)
await attachDomainReading(response, 'health', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
```

## 3. Exit test

**Test file**: `platform-mcp/src/tools/__tests__/F124_domain_reading_wiring.test.ts`

**Command** (FAILS on current code, PASSES after Changes A–D):
```
cd /Users/Dev/par-night/wt/F-124/platform-mcp && npx vitest run src/tools/__tests__/F124_domain_reading_wiring.test.ts
```

Builder must confirm test runner (`vitest` vs `jest`) by inspecting `platform-mcp/package.json` and mirror the import pattern from existing test files in `platform-mcp/src/tools/__tests__/`.

Test assertions (all must be checked):

1. **[FAILS TODAY — A1 gate]** Import or expose `DOMAIN_READING_FAMILIES`; assert `DOMAIN_READING_FAMILIES['health']` is a non-empty array. Today: key absent, `buildDomainReading` early-returns `families_total=0`.

2. **[FAILS TODAY — A1 gate]** Assert `DOMAIN_READING_FAMILIES['relationship']` is a non-empty array. Same reason.

3. **[FAILS TODAY — A2 gate]** Assert `DOMAIN_READING_VARGAS['health']` equals `['D6']` and `DOMAIN_READING_VARGAS['relationship']` equals `['D9']`. Today: both `undefined`.

4. **[FAILS TODAY — C gate]** Invoke `buildAssessResponse` (export it, or test via a spy) with a mock `response` containing `{ domain_completeness: { test: true }, completeness_directive: 'TEST' }`. Assert the returned content's parsed `grounding` object has `domain_completeness` defined. Today: the check is on `response['completeness']` (never set), so `grounding.domain_completeness` is absent.

5. **[FAILS TODAY — D gate]** Assert that after calling `attachDomainCompleteness(response, 'health', chartId)` + `await attachDomainReading(response, 'health', chartId, ayanamshaId, principal)` on a response object, `response['reading']` is defined and `response['domain_completeness']` is defined. Today: without the family-map entries (gate 1) and without the call sites (gate 2), neither key is set.

All five assertions PASS after the fix.

## 4. Sibling sites covered

From F-14 §4 (F-124 §4 defers entirely to F-14 §4; verified identical on live source today):

| Site | File:line | This spec |
|---|---|---|
| `DOMAIN_READING_FAMILIES` | `registry_bridge.ts:1034` | COVERED — Change A1 |
| `DOMAIN_READING_VARGAS` | `registry_bridge.ts:1040` | COVERED — Change A2 (+ type widened) |
| `DOMAIN_READING_HOUSES` | `registry_bridge.ts:1041` | COVERED — Change A3 |
| `DOMAIN_READING_KARAKA_CODE` | `registry_bridge.ts:1042` | COVERED — Change A4 |
| `DOMAIN_READING_KARAKA_LABEL` | `registry_bridge.ts:1043` | COVERED — Change A5 |
| `assess_marriage` call site absent | `registry_bridge.ts:2989` | COVERED — Change D1 |
| `assess_health` call site absent | `registry_bridge.ts:3071` | COVERED — Change D2 |
| `buildAssessResponse:2925` key-mismatch | `registry_bridge.ts:2925` | COVERED — Change C (F-124-unique) |
| `buildDomainReading` vargas index | `registry_bridge.ts:1531–1532` | COVERED — Change B |
| `assess_career` handler | `registry_bridge.ts:3030,3032` | NO CHANGE — already wired |
| `assess_wealth` handler | `registry_bridge.ts:3112,3114` | NO CHANGE — already wired |

No sites excluded.

## 5. Recurrence guard

The compile-time guard in Change A1 is the `AssessedDomain` type union applied directly to the map declaration:

```ts
type AssessedDomain = 'wealth' | 'career' | 'health' | 'relationship'
const DOMAIN_READING_FAMILIES: Record<AssessedDomain, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
  relationship: RELATIONSHIP_READING_FAMILIES,
  health: HEALTH_READING_FAMILIES,
}
```

Because `DOMAIN_READING_FAMILIES` is typed directly as `Record<AssessedDomain, readonly string[]>` (not `Record<string, ...>`), TypeScript checks the object literal against the mapped type structurally — every key in `AssessedDomain` must appear in the literal. If a developer adds `'longevity'` to `AssessedDomain` without adding the corresponding entry to the map, `tsc --noEmit` will error: `Property 'longevity' is missing in type '...' but required in type 'Record<AssessedDomain, readonly string[]>'`. No `as` cast is used — casts from `Record<string, T>` to `Record<K, T>` always succeed regardless of missing keys and must not be used as guards.

Note: the Change B guard (vargas[1] null check enforced by tsc after type-widening DOMAIN_READING_VARGAS from `[string, string]` to `readonly string[]`) is also legitimately enforced — removing the `!= null` guard reintroduces `string | undefined` passed to `readVargaFamily`, which tsc catches once A2's widening is in place.

**Lint command that must pass (add to CI merge gate for S2 stream)**:
```
cd platform-mcp && npx tsc --noEmit
```

## 6. Dependencies, rollback, integration note

**Upstream dependencies**: None blocking. The L-DOMAIN health and relationship capabilities already compute real domain data — confirmed by `register_d8_assess_domain.ts:184–188`'s `DOMAIN_DIRECT_VARGAS` having all four keys (F-14 §4 cross-file check, verified on live source at `/Users/Dev/par-night/main-ro/`). This is a pure presentation-layer wiring change. No DB migration.

**HOT-lease conflict**: F-14, F-15, and F-124 all declare `files_owned_this_lane: platform-mcp/src/tools/registry_bridge.ts (S2 HOT lease)`. This spec is the canonical and most complete spec for all changes in that file for this fix cluster. The integrator must designate ONE builder worktree for this file or explicitly sequence F-124's builder last (rebase order: F-14 → F-15 → F-124, with F-124 absorbing any conflicts). F-14/F-15's `reading` sub-claims are fully closed by Changes A–D of this spec; their builders need not independently touch these sites if the integrator sequences F-124 as the canonical.

**Rollback**: Revert `platform-mcp/src/tools/registry_bridge.ts`. No migration to undo, no persisted data to restore. All four assess_* tools revert to their current shapes.

**Out of scope (flagged for conductor per F-14 §5 NEW item)**: `assembleSaraContent`'s all-or-nothing layer-omission at `reading_depth:'deep_dive'` drops the entire `grounding` layer for all four assess_* tools when orientation payload pushes `kernel+grounding` past 40KB. This is a distinct, separately scoped defect — the literal reproduce_cmd in F-14/F-15 uses `reading_depth:'deep_dive'`, so post-fix callers using that setting may still see no `reading`. This spec does not claim F-14/F-15 fully closed at `deep_dive` depth; a new lane is recommended.

## 7. Coverage table — sub-claims from F-124 diagnosis

| F-124 Claim | Text | Covered? |
|---|---|---|
| C1 | `assess_career` returns `reading` (12 families) | Verified true today; unchanged by this spec; preserved |
| C2 | `assess_career` returns `completeness_directive` | FIXED — Change C corrects `buildAssessResponse:2925` key-mismatch |
| C3 | `assess_career` returns structured `domain_completeness` | FIXED — same Change C |
| C4 | `assess_marriage`/`assess_health` return NO `reading`, `completeness_directive`, `domain_completeness` | FIXED — Changes A1–A5 + B + D1/D2 add maps and call sites |
| C5 | `assess_career` returns 2 confirmed domain-bearing yoga firings marriage/health don't | NOT COVERED — flagged `unverified` in diagnosis (B.10 discipline); yoga firings live in `evidence` layer, separate from reading-digest; out of scope for this spec; new lane if confirmed gap |
| C6 | Depth asymmetry invisible in envelope (`orientation_ok:true`, `reading_checklist`) | PARTIALLY COVERED — `orientation_ok:true` preserved; `reading_checklist` noted as potentially condition-gated (diagnosis §C6); this spec does not alter `reading_checklist` population logic; builder should note whether `reading_checklist` appears in responses post-fix and flag for follow-up if still absent |
| C7 | Suspected mechanism confirmed: Omega5 reading layer wired to career only | FULLY COVERED — Changes A–D expand wiring to all four domains |
| NEW §3.4 | `buildAssessResponse:2925` key-mismatch drops `domain_completeness`/`completeness_directive` for ALL four tools | FULLY COVERED — Change C |
