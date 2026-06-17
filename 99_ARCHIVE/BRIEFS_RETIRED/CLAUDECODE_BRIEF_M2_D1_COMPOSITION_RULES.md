---
brief_id: M2_D1_COMPOSITION_RULES
karn_session_name: KARN-W6-R1-COMPOSITION-RULES
wave: 6
stream: D
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 6 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (3 TypeScript composition rules + role type extension + tests)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §D1
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W5-R2-D234-BUNDLE (L3/L4/L5 tools must exist for rules to be useful)
  blocks: KARN-W7-R1-EVAL-HARNESS (composition rules surface content the eval harness scores)
parallel_stream_note: |
  Two other Wave-6 briefs run concurrently:
  - KARN-W6-R2-PER-TOOL-PLANNER (Stream D — new router/per_tool_planner.ts; does NOT touch
    composition_rules.ts, bundle/types.ts, or rule_composer.ts)
  - KARN-W6-R3-PROVENANCE-AUDIT (Stream F — read-only audit scripts; no code overlap)
  W6-R1 is the only brief that modifies composition_rules.ts and bundle/types.ts.
  No coordination needed beyond standard append-only discipline in shared files.
estimated_time: 1 day single Claude Code session

carry_forward_notes:
  - "composition_rules.ts currently has 6 rules: floor, interpretive, predictive, discovery,
     holisticRemainder, crossNativeMeta. The 3 new rules append after crossNativeMeta in the
     COMPOSITION_RULES array — do not reorder existing rules."
  - "BundleEntryRole in platform/src/lib/bundle/types.ts line 99 is:
     'floor' | 'interpretive' | 'predictive' | 'discovery' | 'holistic'
     It does NOT yet include 'remedial', 'domain_report', or 'temporal_engine'.
     W6-R1 extends this union. The CompositionRule interface already uses
     BundleEntryRole | 'cross_native_meta' — only the type union needs updating."
  - "CAPABILITY_MANIFEST has these REPORT_* v1_1 entries (current versions):
       REPORT_CAREER_DHARMA_v1_1, REPORT_CHILDREN_v1_1, REPORT_FINANCIAL_v2_1 (note v2!),
       REPORT_HEALTH_LONGEVITY_v1_1, REPORT_PARENTS_v1_1, REPORT_PSYCHOLOGY_MIND_v1_1,
       REPORT_RELATIONSHIPS_v1_1, REPORT_SPIRITUAL_v1_1, REPORT_TRAVEL_v1_1.
     Use the v1_1 canonical IDs (or v2_1 for financial). Do NOT add v1_0 entries."
  - "REMEDIAL_CODEX: confirm in PF.4 whether REMEDIAL_CODEX_v2_0_PART1 and
     REMEDIAL_CODEX_v2_0_PART2 are in the CAPABILITY_MANIFEST. If present — use them.
     If absent — the remedialRule adds only the rag_chunks retrieval tool (no manifest
     bundle entry to add), and the rule's purpose is to set a bundle_directive flag rather
     than a manifest asset. See §2.2 for the conditional handling."
  - "05_TEMPORAL_ENGINES entries in manifest: confirm in PF.5.
     At minimum LIFETIME_TIMELINE_v1_0 was ingested by W5-R2. If it has a manifest entry,
     the timelineRule adds it. If not, same conditional handling as REMEDIAL_CODEX above."
  - "composition_rules.test.ts already imports and tests the 6 existing rules.
     It uses makeAsset(), makePlan(), makeManifest() fixture helpers — reuse them exactly.
     The vitest baseline is ~979 passing (W4-R2 end-state); 13 pre-existing Jest failures
     are known-residuals and do not count as regressions."
  - "rule_composer.ts is MUST_NOT_TOUCH. The new rules integrate via COMPOSITION_RULES
     array export — rule_composer.ts reads that array dynamically."

scope_summary: |
  Add three deterministic composition rules to composition_rules.ts. Extend BundleEntryRole
  in bundle/types.ts to accommodate the new role tags. Each rule has its own test block in
  the existing composition_rules.test.ts. No LLM calls. No pipeline changes. No DB changes.

  The three rules:
  1. remedialRule     — fires on query_class='remedial'; adds REMEDIAL_CODEX manifest entries
                        to the bundle (or sets a bundle_directive flag if entries absent from manifest)
  2. domainReportRule — fires when plan.domains.length > 0; adds the matching REPORT_* canonical
                        entries for each recognized domain
  3. timelineRule     — fires when plan.forward_looking === true AND plan.time_window is set;
                        adds 05_TEMPORAL_ENGINES manifest entries (LIFETIME_TIMELINE_v1_0 etc.)

may_touch:
  - platform/src/lib/bundle/composition_rules.ts         # MODIFY — append 3 rules + exports
  - platform/src/lib/bundle/types.ts                     # MODIFY — extend BundleEntryRole union
  - platform/src/lib/bundle/__tests__/composition_rules.test.ts  # MODIFY — append 3 test blocks
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D1_COMPOSITION_RULES.md  # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_D1_VERIFICATION_<DATE>.txt  # CREATE

must_not_touch:
  - platform/src/lib/bundle/rule_composer.ts             # orchestration — W6-R1 does not modify
  - platform/src/lib/bundle/manifest_reader.ts
  - platform/src/lib/bundle/degradation.ts
  - platform/src/lib/bundle/__tests__/rule_composer.test.ts
  - platform/src/lib/bundle/__tests__/manifest_reader.test.ts
  - platform/src/lib/bundle/__tests__/degradation.test.ts
  - platform/src/lib/router/**
  - platform/src/lib/retrieve/**
  - platform/src/app/**
  - platform/src/components/**
  - platform/migrations/**
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json             # read-only for this brief
---

# KARN-W6-R1-COMPOSITION-RULES — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before touching anything. Halt immediately on any pre-flight failure.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §D1`.

You are adding three deterministic composition rules to the bundle composition layer.
These rules determine which manifest entries get included in the retrieval bundle
when the query classifier produces certain query shapes. This is pure TypeScript,
no LLM calls, no DB mutations, no pipeline changes.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list.

# PF.3 — Count current COMPOSITION_RULES array entries
grep -c "Rule," platform/src/lib/bundle/composition_rules.ts 2>/dev/null || \
  grep "COMPOSITION_RULES" platform/src/lib/bundle/composition_rules.ts | tail -1
# Expected: 6 rules (floor, interpretive, predictive, discovery, holisticRemainder, crossNativeMeta).
# If fewer → a prior run partially modified the file. Inspect and reconcile.

# PF.4 — Check REMEDIAL_CODEX manifest presence
python3 -c "
import json
with open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json') as f:
    m = json.load(f)
entries = [e for e in m.get('entries',[]) if 'REMEDIAL_CODEX' in e.get('canonical_id','')]
print('REMEDIAL_CODEX entries:', [e['canonical_id'] for e in entries])
"
# If list is empty → remedialRule uses bundle_directive approach (see §2.2 path B).
# If entries found → remedialRule uses manifest asset approach (see §2.2 path A).
# Record result. Do NOT halt either way.

# PF.5 — Check 05_TEMPORAL_ENGINES manifest presence
python3 -c "
import json
with open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json') as f:
    m = json.load(f)
entries = [e for e in m.get('entries',[]) if '05_TEMPORAL' in e.get('path','') or 'TIMELINE' in e.get('canonical_id','')]
print('Temporal entries:', [e['canonical_id'] for e in entries])
"
# Record result. Same conditional handling as PF.4. Do NOT halt.

# PF.6 — Confirm REPORT_* v1_1 entries in manifest
python3 -c "
import json
with open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json') as f:
    m = json.load(f)
reports = sorted([e['canonical_id'] for e in m.get('entries',[]) if e.get('canonical_id','').startswith('REPORT_') and '_v1_1' in e.get('canonical_id','') or '_v2_1' in e.get('canonical_id','')])
print('REPORT entries:', reports)
"
# Expected: 9 entries (one per domain, v1_1 or v2_1 for financial).
# If fewer → domainReportRule must handle missing entries gracefully (collectEntries already silently skips).

# PF.7 — Vitest baseline
cd platform && npx vitest run src/lib/bundle/__tests__/composition_rules.test.ts \
  --reporter=verbose 2>&1 | tail -15
# Record pass/fail counts. All 6 rule test suites should pass.

# PF.8 — Current BundleEntryRole union
grep "BundleEntryRole" platform/src/lib/bundle/types.ts
# Expected: 'floor' | 'interpretive' | 'predictive' | 'discovery' | 'holistic'
# Confirms the union needs extending.
```

---

## §2 — Implementation

### §2.1 — Extend BundleEntryRole in bundle/types.ts

Find the `BundleEntryRole` type definition (currently line ~99) and extend the union:

```typescript
// BEFORE:
export type BundleEntryRole = 'floor' | 'interpretive' | 'predictive' | 'discovery' | 'holistic'

// AFTER:
export type BundleEntryRole =
  | 'floor'
  | 'interpretive'
  | 'predictive'
  | 'discovery'
  | 'holistic'
  | 'remedial'
  | 'domain_report'
  | 'temporal_engine'
```

This is the only change to bundle/types.ts. No other types change.

---

### §2.2 — remedialRule

**Add after crossNativeMetaRule in `platform/src/lib/bundle/composition_rules.ts`:**

```typescript
// ── Rule 7: remedial ──────────────────────────────────────────────────────────

/**
 * For remedial queries: add REMEDIAL_CODEX source entries (L4) so the
 * synthesizer has the full codex in context alongside the retrieval tool results.
 *
 * PATH A: REMEDIAL_CODEX_v2_0_PART1 + PART2 are in the manifest — add them directly.
 * PATH B: Not in manifest — rule fires but adds no assets (the remedial_codex_query
 *         retrieval tool already surfaces the content via rag_chunks; this rule is a
 *         no-op bundle-layer gate that logs a missing-entry advisory).
 */
const remedialRule: CompositionRule = {
  name: 'remedial',
  role: 'remedial',

  applies(plan: QueryPlan): boolean {
    return plan.query_class === 'remedial'
  },

  assets_to_add(_plan: QueryPlan, manifest: ManifestData): AssetEntry[] {
    return collectEntries(manifest, [
      { canonicalId: 'REMEDIAL_CODEX_v2_0_PART1', pathSubstring: 'REMEDIAL_CODEX_v2_0_PART1' },
      { canonicalId: 'REMEDIAL_CODEX_v2_0_PART2', pathSubstring: 'REMEDIAL_CODEX_v2_0_PART2' },
    ])
    // collectEntries silently skips missing entries — path B is naturally handled.
  },
}
```

**Note:** If PF.4 found REMEDIAL_CODEX entries with different canonical_id strings (e.g. no version suffix, or different version), use those exact IDs instead of the strings above.

---

### §2.3 — domainReportRule

```typescript
// ── Rule 8: domain_report ─────────────────────────────────────────────────────

/**
 * When a query references specific domains, add the matching REPORT_* manifest
 * entries so the synthesizer has the full L3 domain synthesis in context.
 *
 * Domain → canonical_id mapping uses v1_1 (or v2_1 for financial) per current manifest.
 * collectEntries silently skips any missing entry.
 */

const DOMAIN_TO_CANONICAL: Record<string, { canonicalId: string; pathSubstring: string }> = {
  career:        { canonicalId: 'REPORT_CAREER_DHARMA_v1_1',     pathSubstring: 'REPORT_CAREER_DHARMA' },
  dharma:        { canonicalId: 'REPORT_CAREER_DHARMA_v1_1',     pathSubstring: 'REPORT_CAREER_DHARMA' },
  children:      { canonicalId: 'REPORT_CHILDREN_v1_1',          pathSubstring: 'REPORT_CHILDREN' },
  financial:     { canonicalId: 'REPORT_FINANCIAL_v2_1',         pathSubstring: 'REPORT_FINANCIAL' },
  finance:       { canonicalId: 'REPORT_FINANCIAL_v2_1',         pathSubstring: 'REPORT_FINANCIAL' },
  wealth:        { canonicalId: 'REPORT_FINANCIAL_v2_1',         pathSubstring: 'REPORT_FINANCIAL' },
  health:        { canonicalId: 'REPORT_HEALTH_LONGEVITY_v1_1',  pathSubstring: 'REPORT_HEALTH_LONGEVITY' },
  longevity:     { canonicalId: 'REPORT_HEALTH_LONGEVITY_v1_1',  pathSubstring: 'REPORT_HEALTH_LONGEVITY' },
  parents:       { canonicalId: 'REPORT_PARENTS_v1_1',           pathSubstring: 'REPORT_PARENTS' },
  psychology:    { canonicalId: 'REPORT_PSYCHOLOGY_MIND_v1_1',   pathSubstring: 'REPORT_PSYCHOLOGY_MIND' },
  mind:          { canonicalId: 'REPORT_PSYCHOLOGY_MIND_v1_1',   pathSubstring: 'REPORT_PSYCHOLOGY_MIND' },
  relationships: { canonicalId: 'REPORT_RELATIONSHIPS_v1_1',     pathSubstring: 'REPORT_RELATIONSHIPS' },
  marriage:      { canonicalId: 'REPORT_RELATIONSHIPS_v1_1',     pathSubstring: 'REPORT_RELATIONSHIPS' },
  spiritual:     { canonicalId: 'REPORT_SPIRITUAL_v1_1',         pathSubstring: 'REPORT_SPIRITUAL' },
  travel:        { canonicalId: 'REPORT_TRAVEL_v1_1',            pathSubstring: 'REPORT_TRAVEL' },
}

const domainReportRule: CompositionRule = {
  name: 'domain_report',
  role: 'domain_report',

  applies(plan: QueryPlan): boolean {
    return plan.domains.length > 0
  },

  assets_to_add(plan: QueryPlan, manifest: ManifestData): AssetEntry[] {
    const targets: Array<{ canonicalId: string; pathSubstring: string }> = []
    const seen = new Set<string>()
    for (const domain of plan.domains) {
      const mapping = DOMAIN_TO_CANONICAL[domain.toLowerCase()]
      if (mapping && !seen.has(mapping.canonicalId)) {
        targets.push(mapping)
        seen.add(mapping.canonicalId)
      }
    }
    return collectEntries(manifest, targets)
  },
}
```

---

### §2.4 — timelineRule

```typescript
// ── Rule 9: temporal_engine ───────────────────────────────────────────────────

/**
 * For forward-looking queries with a time_window: add 05_TEMPORAL_ENGINES
 * manifest entries (lifetime timeline, sade sati cycles) so the synthesizer
 * has the temporal arc documents in context.
 *
 * Gate: both forward_looking AND time_window must be set. Forward-looking alone
 * (no explicit window) does not fire this rule — the predictiveRule already
 * adds LEL and SADE_SATI_CYCLES_ALL for that case.
 */
const timelineRule: CompositionRule = {
  name: 'temporal_engine',
  role: 'temporal_engine',

  applies(plan: QueryPlan): boolean {
    return plan.forward_looking === true && plan.time_window != null
  },

  assets_to_add(_plan: QueryPlan, manifest: ManifestData): AssetEntry[] {
    return collectEntries(manifest, [
      { canonicalId: 'LIFETIME_TIMELINE_v1_0',   pathSubstring: 'LIFETIME_TIMELINE_v1_0' },
      { canonicalId: 'SADE_SATI_CYCLES_ALL',      pathSubstring: 'SADE_SATI_CYCLES_ALL' },
    ])
    // collectEntries silently skips entries absent from manifest.
  },
}
```

**Note on naming:** The rule is named `temporal_engine` (not `timeline`) to avoid collision
with the `timeline_query` retrieval tool name. The `name` field in CompositionRule is used
for logging/trace only.

---

### §2.5 — Update COMPOSITION_RULES export

Append the three new rules to the end of the `COMPOSITION_RULES` array and add them to the
named exports:

```typescript
// In COMPOSITION_RULES array (replace the existing export):
export const COMPOSITION_RULES: CompositionRule[] = [
  floorRule,
  interpretiveRule,
  predictiveRule,
  discoveryRule,
  holisticRemainderRule,
  crossNativeMetaRule,
  remedialRule,       // W6-R1
  domainReportRule,   // W6-R1
  timelineRule,       // W6-R1
]

// Add to named exports:
export {
  floorRule,
  interpretiveRule,
  predictiveRule,
  discoveryRule,
  holisticRemainderRule,
  crossNativeMetaRule,
  CROSS_NATIVE_PLACEHOLDER,
  remedialRule,       // W6-R1
  domainReportRule,   // W6-R1
  timelineRule,       // W6-R1
  DOMAIN_TO_CANONICAL, // W6-R1 — exported for test use
}
```

---

## §3 — Tests

**Append three new describe blocks to `composition_rules.test.ts`.**
Add these fixtures at the top alongside existing ones:

```typescript
// W6-R1 fixtures
const REMEDIAL_P1 = makeAsset('REMEDIAL_CODEX_v2_0_PART1', '04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md')
const REMEDIAL_P2 = makeAsset('REMEDIAL_CODEX_v2_0_PART2', '04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md')
const REPORT_CAREER = makeAsset('REPORT_CAREER_DHARMA_v1_1', '03_DOMAIN_REPORTS/REPORT_CAREER_DHARMA_v1_1.md')
const REPORT_RELATIONSHIPS = makeAsset('REPORT_RELATIONSHIPS_v1_1', '03_DOMAIN_REPORTS/REPORT_RELATIONSHIPS_v1_1.md')
const REPORT_FINANCIAL = makeAsset('REPORT_FINANCIAL_v2_1', '03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_1.md')
const TIMELINE = makeAsset('LIFETIME_TIMELINE_v1_0', '05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md')

const W6_MANIFEST = makeManifest([
  FORENSIC, CGM, UCN, CDLM, RM, LEL, SADE, PATTERN, CONTRADICTION, CLUSTER, RESONANCE,
  REMEDIAL_P1, REMEDIAL_P2, REPORT_CAREER, REPORT_RELATIONSHIPS, REPORT_FINANCIAL, TIMELINE,
])
```

Also add a `makePlanWith()` helper for plans with extra fields:
```typescript
function makePlanWith(
  query_class: QueryPlan['query_class'],
  overrides: Partial<QueryPlan> = {},
): QueryPlan {
  return { ...makePlan(query_class), ...overrides }
}
```

### Test block: remedialRule

```typescript
import { remedialRule, domainReportRule, timelineRule, DOMAIN_TO_CANONICAL } from '../composition_rules'

describe('remedialRule', () => {
  it('applies only to remedial query class', () => {
    expect(remedialRule.applies(makePlan('remedial'))).toBe(true)
    for (const c of ['factual', 'interpretive', 'predictive', 'cross_domain',
                     'discovery', 'holistic', 'cross_native'] as const) {
      expect(remedialRule.applies(makePlan(c))).toBe(false)
    }
  })

  it('adds REMEDIAL_CODEX PART1 and PART2 when present in manifest', () => {
    const assets = remedialRule.assets_to_add(makePlan('remedial'), W6_MANIFEST)
    const ids = assets.map(a => a.canonical_id)
    expect(ids).toContain('REMEDIAL_CODEX_v2_0_PART1')
    expect(ids).toContain('REMEDIAL_CODEX_v2_0_PART2')
  })

  it('returns empty array (no error) when REMEDIAL_CODEX absent from manifest', () => {
    const emptyManifest = makeManifest([FORENSIC, CGM])
    const assets = remedialRule.assets_to_add(makePlan('remedial'), emptyManifest)
    expect(assets).toEqual([])
  })

  it('role is remedial', () => {
    expect(remedialRule.role).toBe('remedial')
  })
})
```

### Test block: domainReportRule

```typescript
describe('domainReportRule', () => {
  it('applies when plan.domains is non-empty', () => {
    expect(domainReportRule.applies(makePlanWith('interpretive', { domains: ['career'] }))).toBe(true)
    expect(domainReportRule.applies(makePlanWith('factual', { domains: ['health', 'mind'] }))).toBe(true)
  })

  it('does not apply when domains is empty', () => {
    expect(domainReportRule.applies(makePlan('interpretive'))).toBe(false)
    expect(domainReportRule.applies(makePlan('holistic'))).toBe(false)
  })

  it('adds the matched REPORT_* entry for career domain', () => {
    const plan = makePlanWith('interpretive', { domains: ['career'] })
    const assets = domainReportRule.assets_to_add(plan, W6_MANIFEST)
    expect(assets.map(a => a.canonical_id)).toContain('REPORT_CAREER_DHARMA_v1_1')
  })

  it('deduplicates when career and dharma both appear (same report)', () => {
    const plan = makePlanWith('interpretive', { domains: ['career', 'dharma'] })
    const assets = domainReportRule.assets_to_add(plan, W6_MANIFEST)
    const careerEntries = assets.filter(a => a.canonical_id === 'REPORT_CAREER_DHARMA_v1_1')
    expect(careerEntries).toHaveLength(1)
  })

  it('returns empty for unrecognized domain without error', () => {
    const plan = makePlanWith('factual', { domains: ['alchemy'] })
    const assets = domainReportRule.assets_to_add(plan, W6_MANIFEST)
    expect(assets).toEqual([])
  })

  it('role is domain_report', () => {
    expect(domainReportRule.role).toBe('domain_report')
  })
})
```

### Test block: timelineRule

```typescript
describe('timelineRule', () => {
  it('applies when forward_looking=true AND time_window is set', () => {
    const plan = makePlanWith('predictive', {
      forward_looking: true,
      time_window: { start: '2026-01-01', end: '2029-12-31' },
    })
    expect(timelineRule.applies(plan)).toBe(true)
  })

  it('does not apply when forward_looking=true but time_window absent', () => {
    const plan = makePlanWith('predictive', { forward_looking: true })
    expect(timelineRule.applies(plan)).toBe(false)
  })

  it('does not apply when time_window set but forward_looking=false', () => {
    const plan = makePlanWith('factual', {
      forward_looking: false,
      time_window: { start: '2026-01-01', end: '2029-12-31' },
    })
    expect(timelineRule.applies(plan)).toBe(false)
  })

  it('adds LIFETIME_TIMELINE_v1_0 when in manifest', () => {
    const plan = makePlanWith('predictive', {
      forward_looking: true,
      time_window: { start: '2026-01-01', end: '2029-12-31' },
    })
    const assets = timelineRule.assets_to_add(plan, W6_MANIFEST)
    expect(assets.map(a => a.canonical_id)).toContain('LIFETIME_TIMELINE_v1_0')
  })

  it('returns empty array without error when temporal entries absent from manifest', () => {
    const emptyManifest = makeManifest([FORENSIC, CGM])
    const plan = makePlanWith('predictive', {
      forward_looking: true,
      time_window: { start: '2027-01-01', end: '2028-12-31' },
    })
    const assets = timelineRule.assets_to_add(plan, emptyManifest)
    expect(assets).toEqual([])
  })

  it('role is temporal_engine', () => {
    expect(timelineRule.role).toBe('temporal_engine')
  })
})
```

---

## §4 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — COMPOSITION_RULES array has 9 entries
```bash
node -e "
const { COMPOSITION_RULES } = require('./platform/src/lib/bundle/composition_rules')
console.log('rules:', COMPOSITION_RULES.map(r => r.name))
" 2>/dev/null || \
grep -c "Rule," platform/src/lib/bundle/composition_rules.ts
```
Array has 9 entries. (If the grep approach is used: count increased from 6 to 9.)

### AC.2b — Named rules present
```bash
grep -E "^  remedialRule,|^  domainReportRule,|^  timelineRule," \
  platform/src/lib/bundle/composition_rules.ts
```
All three lines present.

### AC.3 — BundleEntryRole extended
```bash
grep "BundleEntryRole" platform/src/lib/bundle/types.ts
```
Output contains `'remedial'`, `'domain_report'`, and `'temporal_engine'`.

### AC.4 — TypeScript compiles clean
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v node_modules | grep "error TS" | head -10
```
No new errors (composition_rules.ts and types.ts changes typecheck clean).

### AC.5 — All new tests pass
```bash
cd platform && npx vitest run src/lib/bundle/__tests__/composition_rules.test.ts \
  --reporter=verbose 2>&1 | tail -20
```
≥ 17 tests pass (6 existing rule suites + ~17 new tests across 3 new suites).
Zero failures.

### AC.6 — Full vitest suite: no new failures
```bash
cd platform && npx vitest run 2>&1 | tail -5
```
Pass count ≥ pre-flight baseline. 13 pre-existing Jest failures are expected residuals.

### AC.7 — Existing rules unmodified (structural check)
```bash
grep -n "floorRule\|interpretiveRule\|predictiveRule\|discoveryRule\|holisticRemainderRule\|crossNativeMetaRule" \
  platform/src/lib/bundle/composition_rules.ts | head -20
```
All 6 existing rule names still present and in original position.

### AC.8 — rule_composer.ts untouched
```bash
git diff platform/src/lib/bundle/rule_composer.ts
```
Empty diff (no changes).

---

## §5 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **TypeScript compile errors after extension of BundleEntryRole:** If extending the union
   causes downstream type errors in rule_composer.ts or other consumers, investigate. The
   fix is likely to add the new role values to a type guard or switch statement there — but
   rule_composer.ts is must_not_touch. HALT and report the exact error lines.
3. **Vitest regression: > 3 new failures** vs pre-flight baseline in the full suite.
4. **PF.3 finds COMPOSITION_RULES already has 9 entries:** A prior attempt ran. Inspect each
   rule carefully — if the 3 new rules are already present and correct, run AC tests and
   close if all pass. If partially added or wrong, reconcile and continue.

Non-halting: REMEDIAL_CODEX absent from manifest (path B handling per §2.2 — log and continue);
temporal entries absent from manifest (same silent-skip via collectEntries).

---

## §6 — Closing summary template

```
SESSION CLOSE — M2_D1_COMPOSITION_RULES — <ISO timestamp>

Pre-flight findings:
  REMEDIAL_CODEX in manifest: <YES canonical_ids | NO — path B applied>
  Temporal entries in manifest: <YES canonical_ids | NO — collectEntries skip>
  REPORT_* v1_1 entries found: <count>
  Vitest baseline: <X passing / Y failing>

ACs result:
  AC.1: <PASS|FAIL> — branch redesign/r0-foundation
  AC.2: <PASS|FAIL> — COMPOSITION_RULES array has 9 entries
  AC.2b: <PASS|FAIL> — 3 named rules present in exports
  AC.3: <PASS|FAIL> — BundleEntryRole extended (remedial | domain_report | temporal_engine)
  AC.4: <PASS|FAIL> — TypeScript compiles clean
  AC.5: <PASS|FAIL> — all new tests pass (≥17 total in suite)
  AC.6: <PASS|FAIL> — no new vitest failures
  AC.7: <PASS|FAIL> — 6 existing rules unmodified
  AC.8: <PASS|FAIL> — rule_composer.ts untouched

Files modified:
  platform/src/lib/bundle/composition_rules.ts  (MODIFY — 3 rules added + exports)
  platform/src/lib/bundle/types.ts              (MODIFY — BundleEntryRole extended)
  platform/src/lib/bundle/__tests__/composition_rules.test.ts  (MODIFY — 3 test blocks)

DB changes: none
Cloud Run: none (no deploy — composition layer is stateless TS; ships with next full deploy)

Tests:
  Before: <X passed / Y failed>
  After:  <X' passed / Y' failed>
  Delta:  <new failures count>

Halt-and-report cases: <none | description>
Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: KARN-W6-R2-PER-TOOL-PLANNER (parallel) / KARN-W7-R1-EVAL-HARNESS (sequential)
```

After emitting closing summary, append session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1,
and flip `status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_D1_COMPOSITION_RULES v1.0 (authored 2026-04-30 — Wave 6 open).*
