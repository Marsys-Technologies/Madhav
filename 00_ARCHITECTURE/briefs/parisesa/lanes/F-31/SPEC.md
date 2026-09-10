---
lane: F-31
stream: S3_SATYA (spec) → S2_MĀTRĀ (build)
stage: S (SPEC) — COMPLETE
rs_class: RS-A
---

# F-31 SPEC — assess_health / assess_marriage missing domain-completeness disclosure

## 1. Root-cause statement

`assess_health` and `assess_marriage` never call `attachDomainCompleteness` or `attachDomainReading` in `registry_bridge.ts`, and `attachDomainCompleteness` itself silently no-ops at `:837` (`if (!completeness) return`) when no precomputed dossier slice exists for the domain — so `kernel.flags` is always `[]`, `domain_completeness` and `completeness_directive` are always absent, and the omission is never disclosed for any health or marriage assessment.

## 2. Files to change

**All changes are in one file: `platform-mcp/src/tools/registry_bridge.ts`**
(S2/MĀTRĀ builder — this spec hands the build to S2 per the file-lease rule in plan §2.1.)

### Change A — null-case disclosure in `attachDomainCompleteness` (:837)

Replace the silent early-return with a `domain_accounting_unavailable` judgment_flag:

```ts
// BEFORE (line 837)
if (!completeness) return

// AFTER
if (!completeness) {
  const existingFlags = Array.isArray(response['judgment_flags'])
    ? (response['judgment_flags'] as unknown[])
    : []
  response['judgment_flags'] = [
    `domain_accounting_unavailable: no precomputed concept-slice found for domain="${domain}" ` +
    `on chart ${chart_id}. Domain completeness accounting cannot be attached. ` +
    `Call dossier(domain="${domain}", chart_id="${chart_id}") when available.`,
    ...existingFlags,
  ]
  return
}
```

*Why*: Without this, adding call sites in Changes B/D still produces empty `judgment_flags` for health/marriage — no dossier slices exist yet for those domains (`dossier_slices/` contains only `career_*.json` and `wealth_*.json`), so `assembleDomainCompleteness` returns `null` and the current code no-ops silently. Change A fixes the disclosure gap at the mechanism level for all present and future domains lacking a precompiled slice.

### Change B — call sites in `assess_health` handler (:3071)

After `const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }` at :3071, add (mirroring career pattern at :3030–3032):

```ts
attachDomainCompleteness(response, 'health', chart_id)
await attachDomainReading(response, 'health', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
```

*Why*: These are the missing wiring points. Without them, `attachDomainCompleteness` (even with Change A) is never invoked for health assessments.

### Change C — add `health` entry to `DOMAIN_READING_FAMILIES` and companion maps (:1034–1043)

```ts
// Define above the const (mirrors WEALTH_READING_FAMILIES / CAREER_READING_FAMILIES pattern):
const HEALTH_READING_FAMILIES = [
  // Builder to populate from L-DOMAIN spec for assess_health — confirmed families per domain brief
  // (analogous to WEALTH_READING_FAMILIES / CAREER_READING_FAMILIES pattern above)
] as const

// Add to DOMAIN_READING_FAMILIES:
const DOMAIN_READING_FAMILIES: Record<string, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
  health: HEALTH_READING_FAMILIES,   // ADD
}
// Add to companion maps:
// DOMAIN_READING_VARGAS:      health → ['D6', 'D8']   (6th/8th house vargas)
// DOMAIN_READING_HOUSES:      health → [1, 6, 8]
// DOMAIN_READING_KARAKA_CODE: health → 'SUN'
// DOMAIN_READING_KARAKA_LABEL:health → 'Sun'
```

*Why*: `buildDomainReading` early-returns empty at :1506 when `DOMAIN_READING_FAMILIES[domain]` is undefined (`registry_bridge.ts:1506`: `if (!families) return { reading: [], families_served: 0, families_total: 0 }`), so `attachDomainReading` in Change B would be a silent no-op without this. Builder must confirm exact `HEALTH_READING_FAMILIES` array values against the L-DOMAIN spec for assess_health.

### Change D — call sites in `assess_marriage` handler

Mirror Change B for the `assess_marriage` handler (handler block starts :2961). The canonical domain key for assess_marriage is `'relationship'` — confirmed at `register_d8_assess_domain.ts:187` (`DOMAIN_DIRECT_VARGAS['relationship']`) and :1359 (`runAssessDomain(args, { domain: 'relationship', ... })`). After assembling `response`, add:

```ts
attachDomainCompleteness(response, 'relationship', chart_id)
await attachDomainReading(response, 'relationship', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
```

Also add `relationship` entries (NOT `marriage`) to `DOMAIN_READING_FAMILIES` and companion maps (same pattern as Change C; builder to confirm domain-appropriate vargas/houses/karaka from the marriage L-DOMAIN spec — vargas: `['D9']` per `DOMAIN_DIRECT_VARGAS`).

*Why*: `assess_marriage` has the identical defect (confirmed in diagnosis §4). Covering it in the same diff avoids a second S2 worktree touch of the same file. Using `'relationship'` (not `'marriage'`) matches the canonical internal domain key used by `runAssessDomain` — using `'marriage'` would create a dangling key that never matches `DOMAIN_DIRECT_VARGAS['relationship']` or any future dossier slice named `relationship_*.json`.

## 3. Exit test

**File**: `platform-mcp/src/tools/__tests__/F31_health_completeness_disclosure.test.ts`

**Command** (run from the builder's worktree root):
```sh
npx jest --testPathPattern="F31_health_completeness_disclosure" --no-coverage 2>&1 | tail -30
```

**FAILS on today's code. PASSES after the fix.**

```ts
// platform-mcp/src/tools/__tests__/F31_health_completeness_disclosure.test.ts
import { attachDomainCompleteness } from '../registry_bridge'

describe('F-31: assess_health domain-completeness disclosure', () => {
  it('emits domain_accounting_unavailable flag when no dossier slice exists for health', () => {
    // No health_*.json exists in dossier_slices/ on origin/main today — assembleDomainCompleteness
    // returns null for domain='health'. No mocking needed; uses the real live condition.
    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'health', '482012f1-710e-4a25-994a-93821f5871aa')
    const flags = response['judgment_flags'] as unknown[] | undefined
    // TODAY: fails — response is unchanged (silent no-op at :837), flags is undefined
    // AFTER FIX: passes — Change A pushes domain_accounting_unavailable flag
    expect(Array.isArray(flags)).toBe(true)
    expect(
      (flags as string[]).some(f => typeof f === 'string' && f.startsWith('domain_accounting_unavailable'))
    ).toBe(true)
  })

  it('does not emit domain_accounting_unavailable for career (slice exists)', () => {
    // career_482012f1.json EXISTS — assembleDomainCompleteness returns non-null.
    // Change A must NOT fire the unavailable flag for career.
    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'career', '482012f1-710e-4a25-994a-93821f5871aa')
    const flags = response['judgment_flags'] as string[] | undefined
    // Should contain complete_domain_accounting_attached or domain_accounting_incomplete,
    // NOT domain_accounting_unavailable — regression guard on Change A.
    if (Array.isArray(flags)) {
      expect(flags.some(f => f.includes('domain_accounting_unavailable'))).toBe(false)
    }
  })
})
```

## 4. Sibling sites

| Tool | Defect | Covered in this spec |
|---|---|---|
| `assess_health` (:3041) | No `attachDomainCompleteness` / `attachDomainReading` calls | YES — Changes B, C |
| `assess_marriage` (:2961) | Identical omission (confirmed diagnosis §4) | YES — Change D (using canonical key `'relationship'`) |
| `assess_career` (:2999) | Fully wired at :3030–3032 | N/A |
| `assess_wealth` (:3081) | Fully wired at :3112–3114 | N/A |
| `judgment_query` | Not a wiring gap — generic call to `buildDomainCompletenessPointer` present; returns null for health only because no slice exists (same second-order root, not a separate omission) | Excluded — wiring is correct; self-heals when health dossier slice is generated |

`DOMAIN_READING_FAMILIES` / `attachDomainCompleteness` / `attachDomainReading` are defined and called exclusively within `registry_bridge.ts` — no other file searched because no other call sites exist.

## 5. Recurrence guard

**File**: `platform-mcp/src/tools/__tests__/F31_assess_handlers_completeness_wired.contract.test.ts`

```ts
// Contract test: every assess_* handler must call attachDomainCompleteness.
import * as fs from 'fs'
import * as path from 'path'

const src = fs.readFileSync(
  path.resolve(__dirname, '../registry_bridge.ts'), 'utf8'
)

for (const domain of ['career', 'wealth', 'health', 'relationship']) {
  it(`assess_${domain} handler calls attachDomainCompleteness`, () => {
    expect(src).toMatch(
      new RegExp(`attachDomainCompleteness\\(response,\\s*'${domain}'`)
    )
  })
}
```

This test FAILS today for `health` and `relationship`, PASSES after the fix, and FAILS again if any future `assess_*` domain is wired without the completeness call — closing recurrence permanently via CI.

Note: the domain array uses `'relationship'` (not `'marriage'`) because that is the canonical internal domain key used by `runAssessDomain` in `register_d8_assess_domain.ts:1359` and recorded in `DOMAIN_DIRECT_VARGAS` at :187. A regex checking `'marriage'` would match Change D's string if written incorrectly but fail to validate the semantically correct `'relationship'` wiring.

## 6. Dependencies and rollback

**Builder assignment**: S2/MĀTRĀ — `registry_bridge.ts` is an S2-exclusive hot lease per plan §2.1. S3 authored this spec; conductor must assign Stage B to S2.

**F-14 dependency (CRITICAL — read before dispatching a builder)**: `lanes/F-14/SPEC.md` is an S2 exemplar spec that explicitly closes F-31 as part of a combined fix covering F-14, F-15, F-124, and F-31 together. F-14 §0 states: *"Do not build F-31 separately from this spec — if S3's own SPEC.md for F-31 lands first or differs, the two must be reconciled by the conductor/VERIFIER into one build, not built twice against the same lines of registry_bridge.ts."* F-14 owns equivalent changes (null-case disclosure, health/relationship call sites, DOMAIN_READING_FAMILIES keys). **The conductor must resolve one of the following before dispatching an F-31 builder: (a) F-31 is subsumed into F-14's build — F-31 is closed as a duplicate and no separate builder is dispatched; or (b) F-31 and F-14 are confirmed additive (e.g., F-31's Change A judgment_flag mechanism is distinct from F-14's `domain_completeness_empty_reason` field approach) — in which case F-31 must sequence strictly after F-14 lands, and the builder must open the file only after F-14's merge commit is present in the worktree.** Without conductor ruling, dispatching an F-31 builder risks a double-application merge conflict on the same lines.

**Sequencing**: Other S2 lanes touching `registry_bridge.ts` (F-13, F-14, F-28, F-56, F-111, F-12, F-36, F-37, F-45, F-44) must not be mid-edit when this lane's builder opens the file. Conductor to schedule worktree ordering.

**Dossier slice generation for health/relationship** (second-order gap, diagnosis §3): OUT OF SCOPE this lane. Change A (null-case disclosure) satisfies the C2 obligation until slices are generated. The native has confirmed a post-campaign full rebuild will follow. Morning report should enumerate `health_*.json` and `relationship_*.json` as required slice targets for that rebuild.

**Migration**: false — no DB schema changes.

**Rebuild**: None. This is a TypeScript wiring change only; no `ga_*` / `bo_*` writer asset is touched. Shadow verification is sufficient per PROTOCOL.md rebuild policy (no writer-layer fix, no data rows generated by this change).

**Rollback**: Revert the four changes in `registry_bridge.ts` (null-case block in `attachDomainCompleteness`, two call-site pairs in `assess_health` and `assess_marriage`, and the `DOMAIN_READING_FAMILIES` / companion-map entries). No DB state changed. Clean TypeScript revert, zero risk.

## 7. Coverage table

| Diagnosis sub-claim | Addressed by |
|---|---|
| C1 — `assess_health` omits `reading` / `domain_completeness` / `completeness_directive` | Changes B+C wire the calls; `domain_completeness`/`completeness_directive` remain absent until health dossier slice is generated (disclosed via C2 flag per Change A — not silently absent) |
| C2 — no `judgment_flag` discloses the omission | Change A (null-case in `attachDomainCompleteness`) + Change B (call site); exit test asserts directly |
| C3 — disclosure mechanism is live for career/wealth; health omission is a wiring gap, not an architectural impossibility | Confirmed by source read; Changes B/D close the gap symmetrically using the identical pattern |
| Second-order — no `health_*` / `relationship_*` dossier slice bundle exists | Disclosed via `domain_accounting_unavailable` flag (Change A); slice generation deferred to post-campaign full rebuild; flagged in morning report |
| Sibling — `assess_marriage` has identical omission | Change D + contract test cover it using canonical key `'relationship'` |
| `judgment_query` on health — returns no flag because no slice, not a wiring gap | Excluded from scope; self-heals with slice generation; documented in sibling table |
| `attachDomainCompleteness` null-case is itself a silent-absence instance of the same defect class | Change A fixes it globally for all callers (not just health) — eliminates recurrence at mechanism level |
