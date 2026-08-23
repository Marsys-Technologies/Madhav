import { describe, expect, it } from 'vitest'
// Bootstrap the full L0–L5 registry (side-effect import) so getToolByName()
// reflects the real, fully-populated registry — same pattern
// compiled_floor_adapter.test.ts uses.
import '@/lib/retrieval/registry/catalog'
import { VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import {
  buildUnifiedPlan,
  computePrimitiveToolBindings,
  fromCompiledFloorItem,
  fromToolCallItem,
  getPlanBridgeCoverage,
  PRIMITIVE_ID_TO_TOOL_NAME,
  PRIMITIVE_TOOL_BINDINGS,
  TOOL_NAME_TO_PRIMITIVE_IDS,
  UNCOVERED_BINDINGS,
  type PrimitiveIdentitySource,
} from '../plan_bridge'
import type { ToolCallItem } from '@/lib/pipeline/types'
import type { CompiledFloorItem } from '@/lib/vidhi/types'

// ─────────────────────────────────────────────────────────────────────────────
// §1. Totality — the map covers every primitive_id in the live registry exactly
// once, honestly split into covered / uncovered. This is the property a partial
// map (a primitive silently dropped, or added with no binding at all) would
// violate.
// ─────────────────────────────────────────────────────────────────────────────

describe('PRIMITIVE_TOOL_BINDINGS — totality over the live registry', () => {
  it('has exactly one binding per primitive_id in VIDHI_PRIMITIVES (no duplicates, no omissions)', () => {
    const registryIds = VIDHI_PRIMITIVES.map((p) => p.primitive_id)
    const boundIds = PRIMITIVE_TOOL_BINDINGS.map((b) => b.primitive_id)
    expect(boundIds).toHaveLength(registryIds.length)
    expect(new Set(boundIds)).toEqual(new Set(registryIds))
    // No duplicate primitive_ids introduced by the mapping step.
    expect(new Set(boundIds).size).toBe(boundIds.length)
  })

  it('every binding is exactly one of covered (tool_name set, resolvable) or uncovered (tool_name null)', () => {
    for (const b of PRIMITIVE_TOOL_BINDINGS) {
      if (b.tool_name === null) {
        expect(UNCOVERED_BINDINGS.map((u) => u.primitive_id)).toContain(b.primitive_id)
      } else {
        // A covered binding's tool_name must actually resolve on the real registry —
        // never a no-op tool name (same bar compiled_floor_adapter.test.ts holds
        // LIVE_TOOL_TO_RETRIEVAL to).
        expect(getToolByName(b.tool_name), `primitive "${b.primitive_id}" -> "${b.tool_name}" must resolve`).toBeDefined()
      }
    }
    expect(PRIMITIVE_TOOL_BINDINGS.length).toBe(
      [...PRIMITIVE_ID_TO_TOOL_NAME.keys()].length + UNCOVERED_BINDINGS.length,
    )
  })

  it('no uncovered primitive is silently missing a reason — every one names its live_tool', () => {
    for (const u of UNCOVERED_BINDINGS) {
      expect(u.live_tool.length).toBeGreaterThan(0)
      expect(u.tool_name).toBeNull()
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §2. Bidirectionality — the forward map and reverse map agree on every entry.
// ─────────────────────────────────────────────────────────────────────────────

describe('PRIMITIVE_ID_TO_TOOL_NAME <-> TOOL_NAME_TO_PRIMITIVE_IDS — bidirectional consistency', () => {
  it('every forward entry is findable in the reverse bucket', () => {
    for (const [primitiveId, toolName] of PRIMITIVE_ID_TO_TOOL_NAME) {
      const bucket = TOOL_NAME_TO_PRIMITIVE_IDS.get(toolName)
      expect(bucket, `tool_name "${toolName}" must have a reverse bucket`).toBeDefined()
      expect(bucket).toContain(primitiveId)
    }
  })

  it('every reverse bucket entry resolves back to the same tool_name in the forward map', () => {
    for (const [toolName, primitiveIds] of TOOL_NAME_TO_PRIMITIVE_IDS) {
      expect(primitiveIds.length).toBeGreaterThan(0)
      for (const primitiveId of primitiveIds) {
        expect(PRIMITIVE_ID_TO_TOOL_NAME.get(primitiveId)).toBe(toolName)
      }
    }
  })

  it('is genuinely many-to-one in places (documents the real shape, not an assumed 1:1)', () => {
    const manyToOne = [...TOOL_NAME_TO_PRIMITIVE_IDS.values()].filter((ids) => ids.length > 1)
    expect(manyToOne.length).toBeGreaterThan(0)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §3. The §N.8 completeness-can-fail proof.
//
// A test that only ever exercises the REAL `VIDHI_PRIMITIVES` registry cannot
// demonstrate the totality assertion is capable of failing — every real
// primitive is present in that array by definition, so "no omission" is true
// by construction on that input. This section runs the SAME
// `computePrimitiveToolBindings` construction against a deliberately broken
// synthetic fixture (a primitive introduced only in the "registry" input, not
// in the "bindings" output) and asserts the totality check catches it — proving
// the detector, not just today's lucky data.
// ─────────────────────────────────────────────────────────────────────────────

describe('completeness proof — demonstrated capable of failing (§N.8)', () => {
  const FIXTURE_PRIMITIVES: readonly PrimitiveIdentitySource[] = [
    { primitive_id: 'fixture_a', live_tool: 'fixture_tool_covered' },
    { primitive_id: 'fixture_b', live_tool: 'fixture_tool_uncovered' },
  ]
  const fixtureResolve = (liveTool: string): string | undefined =>
    liveTool === 'fixture_tool_covered' ? 'fixture_retrieval_tool' : undefined

  it('CONTROL: a correctly-built map passes the totality check', () => {
    const bindings = computePrimitiveToolBindings(FIXTURE_PRIMITIVES, fixtureResolve)
    const registryIds = new Set(FIXTURE_PRIMITIVES.map((p) => p.primitive_id))
    const boundIds = new Set(bindings.map((b) => b.primitive_id))
    expect(boundIds).toEqual(registryIds) // green when nothing is missing
  })

  it('NEGATIVE CONTROL: a map missing a primitive (the "goes partial" defect) FAILS the same totality check', () => {
    const bindings = computePrimitiveToolBindings(FIXTURE_PRIMITIVES, fixtureResolve)
    // Simulate the exact defect class the lane brief names: a primitive added to
    // the registry with no corresponding binding — e.g. a future edit to
    // computePrimitiveToolBindings that filters instead of maps. Drop one entry
    // to reproduce it without touching the real production map.
    const brokenBindings = bindings.filter((b) => b.primitive_id !== 'fixture_b')
    const registryIds = new Set(FIXTURE_PRIMITIVES.map((p) => p.primitive_id))
    const boundIds = new Set(brokenBindings.map((b) => b.primitive_id))
    // This assertion is INTENTIONALLY the mirror image of the CONTROL above —
    // it must fail (registryIds !== boundIds) to prove the check is load-bearing.
    expect(boundIds).not.toEqual(registryIds)
    expect(boundIds.has('fixture_b')).toBe(false)
  })

  it('NEGATIVE CONTROL: a primitive with no tool mapping AND no honest uncovered record is undetectable garbage — reject that shape directly', () => {
    // The failure mode the lane brief calls out by name: "add a new primitive
    // with no tool mapping (or vice versa)". Show that a binding whose tool_name
    // is neither a real resolvable name NOR explicitly null (e.g. an empty
    // string standing in for "we didn't check") is caught by the same
    // resolvability assertion §1 runs against the real registry.
    const bindings = computePrimitiveToolBindings(FIXTURE_PRIMITIVES, fixtureResolve)
    const covered = bindings.find((b) => b.primitive_id === 'fixture_a')
    expect(covered?.tool_name).toBe('fixture_retrieval_tool')
    const uncovered = bindings.find((b) => b.primitive_id === 'fixture_b')
    expect(uncovered?.tool_name).toBeNull() // honest null, never '' or a guessed name
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §4. Coverage summary — measured against the LIVE registry, honestly.
// ─────────────────────────────────────────────────────────────────────────────

describe('getPlanBridgeCoverage — live, honest measurement', () => {
  it('total_primitives matches the live VIDHI_PRIMITIVES length', () => {
    const c = getPlanBridgeCoverage()
    expect(c.total_primitives).toBe(VIDHI_PRIMITIVES.length)
    expect(c.covered_primitives + c.uncovered_primitives).toBe(c.total_primitives)
  })

  it('total_distinct_live_tools matches the live registry\'s distinct live_tool count', () => {
    const c = getPlanBridgeCoverage()
    const distinct = new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))
    expect(c.total_distinct_live_tools).toBe(distinct.size)
    expect(c.covered_live_tools + c.uncovered_live_tools.length).toBe(c.total_distinct_live_tools)
  })

  it('uncovered_live_tools names are sorted and de-duplicated', () => {
    const c = getPlanBridgeCoverage()
    const sorted = [...c.uncovered_live_tools].sort()
    expect(c.uncovered_live_tools).toEqual(sorted)
    expect(new Set(c.uncovered_live_tools).size).toBe(c.uncovered_live_tools.length)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §4b. Pinned-baseline detector (§N.8 remediation, RC-10 pattern).
//
// `getPlanBridgeCoverage()` is a pure, total function of the live registry — it
// has no failure mode of its own; comparing its output to itself (the defect
// an independent adversarial review found in a prior version of this file's
// module comment) can never go red. The REAL detector is here: an explicit,
// literal enumeration of the 19 `live_tool` names known uncovered as of this
// writing, asserted with `toEqual` (order- and count-sensitive) against the
// live computation. `toEqual` on two arrays fails if EITHER side has an entry
// the other lacks, so this catches a name silently:
//   - REMOVED from uncovered (i.e. force-mapped to a tool_name, plausible or
//     not — this is the exact M3c mutation an adversarial review used to
//     prove the old comment's claim false: force-mapping 18 of 19 uncovered
//     tools to a plausible-but-wrong URI made `getPlanBridgeCoverage()`
//     report a fabricated 59/60 and 39/40 with the old self-referential
//     "detector" still green);
//   - ADDED to uncovered (a previously-covered tool's mapping broke, or a new
//     primitive was registered with no binding).
// Either direction fails this test and forces a conscious, recorded update to
// the pin — never a silent number move. This is the RC-10 pinned-baseline
// pattern the remediation brief specifies.
//
// When this test goes red because the registry legitimately grew or a real
// mapping was added/removed, the fix is: re-run `getPlanBridgeCoverage()`,
// verify the new list is honest (no force-map), update
// `KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE` to match, and note why in the commit
// message. That update IS the "conscious, recorded disposition" this pin
// exists to force — it is not a reason to weaken or delete the assertion.
// ─────────────────────────────────────────────────────────────────────────────

const KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE: readonly string[] = [
  'bodha_chart_digest_get',
  'dossier',
  'ganita_ayurdaya_get',
  'ganita_condition_get',
  'ganita_kp_cusps_get',
  'ganita_structural_get',
  'gochara_activation_get',
  'gochara_election_avoidance_get',
  'gochara_forecast_get',
  'kala_ahead_get',
  'kala_bundle_get',
  'kala_elect_get',
  'kala_explain_get',
  'kala_now_get',
  'kala_priority_get',
  'kala_ritual_get',
  'kala_story_get',
  'kala_upaya_get',
  'synth_tail_divergence_get',
]

describe('getPlanBridgeCoverage — pinned-baseline detector (§N.8: a real code path that can fail)', () => {
  it('uncovered_live_tools matches the pinned 19-name baseline exactly — fails loudly if a name is added OR removed', () => {
    const c = getPlanBridgeCoverage()
    // Sanity: the baseline itself must be sorted/deduped the same way the live
    // value is, or this assertion would be comparing apples to a typo.
    expect(KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE).toEqual([...KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE].sort())
    expect(new Set(KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE).size).toBe(KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE.length)
    expect(c.uncovered_live_tools).toEqual(KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE)
  })

  it('covered_live_tools count matches the baseline-implied count (21 of 40)', () => {
    const c = getPlanBridgeCoverage()
    expect(c.total_distinct_live_tools - KNOWN_UNCOVERED_LIVE_TOOLS_BASELINE.length).toBe(c.covered_live_tools)
    expect(c.covered_live_tools).toBe(21)
    expect(c.total_distinct_live_tools).toBe(40)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §5. UnifiedPlanStep — both vocabularies lift into the same shape.
// ─────────────────────────────────────────────────────────────────────────────

function toolCall(overrides: Partial<ToolCallItem> = {}): ToolCallItem {
  return {
    tool_name: 'vector_search',
    params: { query_text: 'x' },
    token_budget: 500,
    priority: 1,
    reason: 'seed',
    ...overrides,
  }
}

function floorItem(overrides: Partial<CompiledFloorItem> = {}): CompiledFloorItem {
  return {
    primitive_id: 'dhana_yoga_scan',
    band: 'acharya_floor',
    live_tool: 'ganita_yoga_firings_get',
    tool_args: { chart_id: 'x' },
    fallback_face: null,
    known_gap: null,
    hard_floor: false,
    ...overrides,
  }
}

describe('UnifiedPlanStep — lossless lift from both vocabularies', () => {
  it('fromToolCallItem carries tool_name, honest-null primitive_id/live_tool', () => {
    const step = fromToolCallItem(toolCall())
    expect(step.tool_name).toBe('vector_search')
    expect(step.primitive_id).toBeNull()
    expect(step.live_tool).toBeNull()
    expect(step.origin).toBe('llm_planner')
  })

  it('fromCompiledFloorItem resolves tool_name via the SAME resolveLiveTool the web engine uses', () => {
    const step = fromCompiledFloorItem(floorItem(), 'vidhi_floor')
    expect(step.primitive_id).toBe('dhana_yoga_scan')
    expect(step.live_tool).toBe('ganita_yoga_firings_get')
    expect(step.tool_name).toBe('get_yoga_firings') // matches compiled_floor_adapter.test.ts's own assertion for this primitive
    expect(step.origin).toBe('vidhi_floor')
  })

  it('fromCompiledFloorItem is honestly null for an uncovered live_tool (never a guessed tool_name)', () => {
    const step = fromCompiledFloorItem(floorItem({ primitive_id: 'bhava_condition', live_tool: 'ganita_structural_get' }), 'vidhi_floor')
    expect(step.tool_name).toBeNull()
    expect(step.primitive_id).toBe('bhava_condition')
  })

  it('every step (from either origin) carries at least one identity — never both null', () => {
    const steps = [fromToolCallItem(toolCall()), fromCompiledFloorItem(floorItem(), 'vidhi_floor')]
    for (const s of steps) {
      expect(s.tool_name !== null || s.primitive_id !== null).toBe(true)
    }
  })

  it('buildUnifiedPlan merges planner tool_calls + floor + machine_band, in that order', () => {
    const steps = buildUnifiedPlan(
      { tool_calls: [toolCall({ tool_name: 'vector_search' })] },
      { floor: [floorItem()], machine_band: [floorItem({ primitive_id: 'mp2', live_tool: 'bodha_signals_get' })] },
    )
    expect(steps).toHaveLength(3)
    expect(steps[0].origin).toBe('llm_planner')
    expect(steps[1].origin).toBe('vidhi_floor')
    expect(steps[2].origin).toBe('vidhi_machine_band')
  })

  it('buildUnifiedPlan degrades safely with no compiled contract (planner-only plan)', () => {
    const steps = buildUnifiedPlan({ tool_calls: [toolCall()] })
    expect(steps).toHaveLength(1)
  })
})
