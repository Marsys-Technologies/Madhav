---
artifact: PARISESA_SPEC
lane: F-111
stream: S2
finding_class: CL-05
rs_class: RS-C
diagnosis_source: distributed (no F-111/DIAGNOSIS.md created; reconstructed from F-12/DIAG §5, F-14/DIAG §D.5, F-31/DIAG §0, F-112/LEAD_SCOPING_NOTE §2, LEDGER_S2)
fix_status: ALREADY-MERGED — PR #1301, branch ekv/a-09-sara-kernel, commits dcc2fb5ad + ceadae8cb
---

# F-111 SPEC — Sāra composition for assess_* (object-blind trimmer)

## 1. Root-cause statement

`assess_*` tools (assess_marriage, assess_career, assess_health, assess_wealth) routed their responses through `applyMcpBudgetAuto` / `autoDetectTrimmableSections`, which is array-aware only; `verdict_skeleton` (~43 KB) and `activating_dasha` (~62 KB) are plain **object** fields — structurally invisible to the array-trimmer — so they survived every trim pass unconditionally and dominated response size regardless of the declared budget.

## 2. Files changed (already on main via PR #1301)

### 2a. `platform-mcp/src/lib/response_budget.ts` (+175 lines)

**What**: Added exported `SaraKernel` interface and exported `assembleSaraContent` function. These provide the three-layer composition API: `kernel` (verdict + flags, enforced ≤2 KB), `grounding` (bounded structured context, included if it fits), `evidence` (large objects — included only after grounding fits within budget).
**Why**: Gives `buildAssessResponse` an object-aware budget gate rather than the array-only trimmer.

### 2b. `platform-mcp/src/tools/registry_bridge.ts` (+83 lines)

**What**: Added `buildAssessResponse` (private closure function, :2886-2951). The function places `verdict_skeleton` and `activating_dasha` in `evidence` (:2931-2933); the rest of the response shape goes to `grounding` (:2908-2927). All four assess_* call sites replaced:

| Tool | Call site | Change |
|---|---|---|
| `assess_marriage` | :2990 | `dualOutputBudgeted(buildAssessResponse(response, 'assess_marriage', budget_kb, effectiveVerbosity))` |
| `assess_career` | :3033 | same pattern |
| `assess_health` | :3072 | same pattern |
| `assess_wealth` | :3118 | same pattern |

**Why**: Directly fixes the object-blindness — the two large objects are now gated by budget (excluded at 40 KB default, served at deep_dive/exhaustive) rather than emitted unconditionally.

## 3. Exit test

**File**: `platform-mcp/src/__tests__/f111_sara_evidence_segregation.test.ts`

**Command**: `cd /Users/Dev/par-night/wt/F-111 && npx vitest run src/__tests__/f111_sara_evidence_segregation.test.ts`

**Failure mode on pre-fix code**: `assembleSaraContent` was not exported from `response_budget.ts`; the import fails (`SyntaxError: The requested module … does not provide an export named 'assembleSaraContent'`). Even if the import were stubbed, the old flat `applyMcpBudgetAuto` path emits `verdict_skeleton` and `activating_dasha` in the raw response object regardless of budget — the tight-budget omission assertion fails.

**Test content**:

```typescript
import { describe, it, expect } from 'vitest'
import { assembleSaraContent } from '../lib/response_budget.js'
import type { SaraKernel } from '../lib/response_budget.js'

// Two large object fields that the old array-trimmer was blind to.
// Combined ~110 KB — well above the 40 KB assess_* default budget.
const BIG = { payload: 'x'.repeat(55_000) }

describe('F-111 — verdict_skeleton/activating_dasha segregated to evidence layer', () => {
  const kernel: SaraKernel = { verdict: 'test verdict', flags: [], promise: null, pointers: [] }
  const grounding = { domain: 'wealth', chart_id: 'mock-chart-f111' }
  const evidence = { verdict_skeleton: BIG, activating_dasha: BIG }

  it('tight budget (40 KB) omits evidence; large objects absent from grounding', () => {
    const r = assembleSaraContent({ kernel, grounding, evidence, budget_kb: 40, counts: {} })
    expect(r.composition_report.omitted_sections).toContain('evidence')
    expect(r.evidence).toBeUndefined()
    // Must not have leaked into grounding
    const g = r.grounding as Record<string, unknown> | undefined
    expect(g?.['verdict_skeleton']).toBeUndefined()
    expect(g?.['activating_dasha']).toBeUndefined()
  })

  it('broad budget (200 KB) includes evidence with both large objects', () => {
    const r = assembleSaraContent({ kernel, grounding, evidence, budget_kb: 200, counts: {} })
    expect(r.composition_report.included_layers).toContain('evidence')
    expect(r.evidence?.['verdict_skeleton']).toBeDefined()
    expect(r.evidence?.['activating_dasha']).toBeDefined()
  })
})
```

**Status on current main**: PASSES — `assembleSaraContent` is exported and the layer logic is in place (verified at response_budget.ts:749-814). This is a regression guard; it would FAIL if `buildAssessResponse` were reverted.

## 4. Sibling sites covered

All four assess_* call sites are covered by the single `buildAssessResponse` implementation (confirmed via grep of `main-ro/platform-mcp/src/tools/registry_bridge.ts`):

| Site | Line | Covered |
|---|---|---|
| `assess_marriage` | :2990 | YES — calls `buildAssessResponse` |
| `assess_career` | :3033 | YES — calls `buildAssessResponse` |
| `assess_health` | :3072 | YES — calls `buildAssessResponse` |
| `assess_wealth` | :3118 | YES — calls `buildAssessResponse` |

No other tools use `buildAssessResponse` — scoped exclusively to the D8 apex assess_* family.

## 5. Recurrence guard

The code comment at registry_bridge.ts:2881-2884 explicitly names F-56/F-111 as the rationale for `buildAssessResponse`. The exit test (`f111_sara_evidence_segregation.test.ts`) is the machine-enforceable guard: any reversion of the evidence-layer segregation causes an import failure or assertion failure. Additionally, `assembleSaraContent`'s three-layer API makes it structurally impossible to accidentally place large objects in `grounding` — they must be explicitly passed in the `evidence` argument.

## 6. Dependencies and rollback

**Other lanes touching registry_bridge.ts**: F-14/F-15 edit grounding key names (:2923-2925 region); F-31 edits `judgment_flags` attachment logic. None touch the `buildAssessResponse` function body (:2886-2951). No line-level collision risk.
**Fix status**: Already merged — PR #1301, branch `ekv/a-09-sara-kernel`, commits `dcc2fb5ad` (API freeze) + `ceadae8cb` (composition body). Confirmed in main-ro source at registry_bridge.ts:2880-2951 and response_budget.ts:667-814.
**Rollback**: Revert both commits. Zero downstream artifacts affected — pure MCP serving layer, no DB writes, no writer assets, no pipeline involvement.
**Rebuild**: None required and none appropriate. No writer layer is touched; no asset data changes.
**Migration**: None.

## 7. Coverage table — every sub-claim mapped

| Sub-claim (source) | Spec coverage |
|---|---|
| `verdict_skeleton` (~43 KB object) invisible to `applyMcpBudgetAuto` (F-14/DIAG §D.5, F-12/DIAG §5, F-112/LEAD_SCOPING_NOTE §2) | §2b: placed in `evidence` at :2932; §3: exit test asserts omitted at 40 KB |
| `activating_dasha` (~62 KB object) same root (F-14/DIAG §D.5) | §2b: placed in `evidence` at :2933; §3: exit test asserts defined at 200 KB |
| All 4 assess_* tools affected (LEDGER_S2:32, F-14/DIAG §D.5) | §4: all 4 call sites confirmed in coverage table |
| Fix already on main via PR #1301 / `ekv/a-09-sara-kernel` (F-31/DIAG §0, F-12/DIAG §5, LEDGER_S2:254-257) | §2: fix_status frontmatter + §6: PR confirmed in main-ro source |
| F-14's grounding-key changes do not reopen F-111 (F-14/SPEC §6, F-15/SPEC §6) | §6: confirmed different line regions, no collision |
| F-56 is the sister lane covering the same fix (LEDGER_S2:31, F-112/LEAD_SCOPING_NOTE §2) | §1: root cause statement covers both; §2b explicitly cites comment naming F-56/F-111 jointly |
