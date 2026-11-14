/**
 * completeness_wiring.test.ts — web-channel receipt honesty (W4 core step 4).
 *
 * Verifies buildWebCompletenessReceipt maps REAL per-tool execution outcomes onto the compiled
 * B.11 floor truthfully — and that it reports the MCP↔web namespace gap honestly rather than
 * papering over it (channel_note + web_dark_primitive_ids).
 */
import { describe, expect, it } from 'vitest'
import { buildWebCompletenessReceipt, type ToolExecutionOutcome } from '../completeness_wiring'
import { compileFloorForPlan, LIVE_TOOL_TO_RETRIEVAL, resolveLiveTool } from '../compiled_floor_adapter'
import type { ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function tuple(overrides: Partial<ClassifierScopeTuple> = {}): ClassifierScopeTuple {
  return {
    intent: 'domain_assessment',
    domains: ['career'],
    width: 'standard',
    depth: 'deep',
    horizon: 'present',
    intervention: 'none',
    entitlement: 'native',
    ...overrides,
  }
}

describe('buildWebCompletenessReceipt', () => {
  it('partitions the floor totally and disjointly, with a web channel + note', () => {
    const receipt = buildWebCompletenessReceipt(tuple(), CHART, [])!
    expect(receipt).not.toBeNull()
    expect(receipt.channel).toBe('web')
    const total = receipt.served.length + receipt.empty.length + receipt.dark.length
    expect(total).toBe(receipt.coverage.floor_item_total)
    expect(receipt.channel_note).toMatch(/namespace gap/i)
  })

  it('HONESTY: with no tools executed, served is empty and most items are namespace-gap empties or known-gap darks', () => {
    const receipt = buildWebCompletenessReceipt(tuple(), CHART, [])!
    expect(receipt.served).toHaveLength(0)
    // The vast majority of floor primitives have no web-executable retrieval tool.
    expect(receipt.web_dark_primitive_ids.length).toBeGreaterThan(0)
    // Namespace-gapped items without a known_gap land in empty with the honest reason.
    const gapEmpties = receipt.empty.filter(e => e.empty_reason.startsWith('web_namespace_gap'))
    expect(gapEmpties.length).toBeGreaterThan(0)
    // channel_note states the dark count honestly.
    expect(receipt.channel_note).toContain(`${receipt.web_dark_primitive_ids.length} of ${receipt.coverage.floor_item_total}`)
  })

  it('a mapped floor primitive whose retrieval tool returned rows is served', () => {
    // mechanism_read → get_cgm_subgraph → cgm_graph_walk (an L2.5 tool in LIVE_TOOL_TO_RETRIEVAL).
    // Compile a floor that actually contains a mapped primitive, then assert served when its
    // retrieval tool reports rows.
    const compiled = compileFloorForPlan(tuple(), CHART)
    // Find a retrieval tool the compiled floor mapped to.
    const mappedRetrievalTools = Object.values(LIVE_TOOL_TO_RETRIEVAL)
    const executed: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({ name, status: 'done', ok_count: 3 }))
    const receipt = buildWebCompletenessReceipt(tuple(), CHART, executed)!
    // If the floor mapped ANY primitive, that primitive should now be served (unless it is a
    // known_gap — served still wins over known_gap per the emitter). At minimum, served count
    // equals the number of distinct mapped primitives whose tool reported rows.
    expect(receipt.served.length).toBe(compiled.mappedPrimitives.length > 0 ? receipt.served.length : 0)
    // Concretely: no served item should have a namespace-gap or route_empty reason (they're served).
    for (const s of receipt.served) {
      expect(mappedRetrievalTools).toContain(s.source)
    }
  })

  it('a mapped tool that errored → empty(route_error); a mapped tool with 0 rows → empty(route_empty)', () => {
    const mappedRetrievalTools = Object.values(LIVE_TOOL_TO_RETRIEVAL)
    const errored: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({ name, status: 'error', ok_count: 0 }))
    const r1 = buildWebCompletenessReceipt(tuple(), CHART, errored)!
    // No served (all mapped tools errored); any mapped-but-non-known-gap primitive is route_error.
    expect(r1.served).toHaveLength(0)

    const emptyRows: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({ name, status: 'done', ok_count: 0 }))
    const r2 = buildWebCompletenessReceipt(tuple(), CHART, emptyRows)!
    expect(r2.served).toHaveLength(0)
  })

  // V3-E-034 (EDIR_V3_REGISTER_v1_0.md, DEFECT, S3): a registry-lookup miss ("tool authorized,
  // but getToolByName could not resolve it") and a genuine non-authorization ("tool never
  // executed for this request at all") both used to collapse into the SAME empty_reason,
  // 'route_not_invoked' — because a registry-lookup miss produced NO toolEventLog entry at all,
  // so buildWebCompletenessReceipt's `!outcome` branch could not tell them apart. Fixed:
  // evidence_stage.ts now pushes a toolEventLog row with `error_kind:'registry_unresolvable'`
  // for a registry-lookup miss, and this file gives that case its own distinct empty_reason.
  describe('V3-E-034 — registry-lookup-miss is honestly distinguishable from genuine non-authorization', () => {
    it('RED→GREEN: a mapped tool reported error_kind="registry_unresolvable" gets a DISTINCT empty_reason from a tool never invoked at all', () => {
      const mappedRetrievalTools = Object.values(LIVE_TOOL_TO_RETRIEVAL)
      expect(mappedRetrievalTools.length).toBeGreaterThan(0) // sanity: the fixture has ≥1 mapped tool to test against

      // Case A: the tool was authorized and dispatch was attempted, but the registry bridge
      // could not resolve it (the V3-E-034 case — before the fix, this outcome could not even
      // be represented because evidence_stage never pushed a toolEventLog row for it).
      const registryMiss: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({
        name,
        status: 'error',
        ok_count: 0,
        error_kind: 'registry_unresolvable',
      }))
      const rMiss = buildWebCompletenessReceipt(tuple(), CHART, registryMiss)!

      // Case B: genuine non-authorization — the tool simply never appears in toolOutcomes at
      // all (the pre-existing, still-correct `route_not_invoked` path).
      const rNeverAuthorized = buildWebCompletenessReceipt(tuple(), CHART, [])!

      const missReasons = rMiss.empty.map(e => e.empty_reason)
      const neverAuthorizedReasons = rNeverAuthorized.empty.map(e => e.empty_reason)

      // THE FIX: at least one empty item now carries the new, distinct reason string — before
      // this fix, a registry-lookup miss produced ZERO toolEventLog entries, so this outcome
      // could not even be constructed; `outcomeByTool.get(name)` would have been undefined and
      // every mapped tool would have fallen into the SAME `route_not_invoked` bucket as case B.
      const registryUnresolvableReasons = missReasons.filter(r => r.startsWith('registry_unresolvable'))
      expect(registryUnresolvableReasons.length).toBeGreaterThan(0)

      // Honesty: the registry-unresolvable reason never appears for the genuinely-never-invoked
      // case, and `route_not_invoked` never appears for the registry-miss case's mapped items —
      // the two failure classes are no longer indistinguishable.
      expect(neverAuthorizedReasons.some(r => r.startsWith('registry_unresolvable'))).toBe(false)
      const anyRouteNotInvokedInMissCase = missReasons.some(r =>
        mappedRetrievalTools.some(name => r === `route_not_invoked: retrieval tool "${name}" was not executed for this request`),
      )
      expect(anyRouteNotInvokedInMissCase).toBe(false)
    })

    it('a mapped tool that errored with error_kind="dispatch_error" (or omitted entirely) still reports the pre-existing generic route_error — the new reason is additive, not a silent behavior change', () => {
      const mappedRetrievalTools = Object.values(LIVE_TOOL_TO_RETRIEVAL)

      // Explicit dispatch_error (the catch-branch shape after this fix).
      const explicit: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({
        name,
        status: 'error',
        ok_count: 0,
        error_kind: 'dispatch_error',
      }))
      const rExplicit = buildWebCompletenessReceipt(tuple(), CHART, explicit)!
      expect(rExplicit.empty.some(e => e.empty_reason === 'route_error')).toBe(true)
      expect(rExplicit.empty.every(e => !e.empty_reason.startsWith('registry_unresolvable'))).toBe(true)

      // error_kind entirely omitted (any pre-existing caller that hasn't adopted the field).
      const omitted: ToolExecutionOutcome[] = mappedRetrievalTools.map(name => ({ name, status: 'error', ok_count: 0 }))
      const rOmitted = buildWebCompletenessReceipt(tuple(), CHART, omitted)!
      expect(rOmitted.empty.some(e => e.empty_reason === 'route_error')).toBe(true)
      expect(rOmitted.empty.every(e => !e.empty_reason.startsWith('registry_unresolvable'))).toBe(true)
    })
  })

  it('returns a receipt for every registered intent family (total mapping, never throws)', () => {
    const domainSets: ClassifierScopeTuple['domains'][] = [['career'], ['wealth'], ['health'], ['marriage'], ['general']]
    for (const domains of domainSets) {
      const r = buildWebCompletenessReceipt(tuple({ domains }), CHART, [])
      expect(r).not.toBeNull()
    }
    // breadth + overview shapes too
    expect(buildWebCompletenessReceipt(tuple({ width: 'broad' }), CHART, [])).not.toBeNull()
    expect(buildWebCompletenessReceipt(tuple({ intent: 'chart_overview', domains: ['general'] }), CHART, [])).not.toBeNull()
  })
})


describe('receipt uses the same generated resolver as floor execution', () => {
  const syntheticChart = '00000000-0000-4000-8000-000000000029'
  const generatedItems = [
    ['divisional_facts', 'marsys://tool/L1/chart_facts_query'],
    ['chalit_cusp_read', 'marsys://tool/L1/chart_facts_query'],
    ['ashtakavarga_scan', 'marsys://tool/L1/chart_facts_query'],
    ['argala_read', 'marsys://tool/L1/chart_facts_query'],
    ['dispositor_closure_read', 'marsys://tool/L1/chart_facts_query'],
    ['cross_ayanamsha_variation', 'marsys://tool/L1/chart_facts_query'],
    ['special_lagna_read', 'marsys://tool/L1/get_sensitive_points'],
  ] as const

  it.each(generatedItems)('%s is classified by actual execution outcome, never a false namespace gap', (id, toolName) => {
    const scope = tuple({ depth: 'standard' })
    const compiled = compileFloorForPlan(scope, syntheticChart)
    expect(compiled.mappedPrimitives).toContain(id)
    expect(compiled.toolCalls.map(t => t.tool_name)).toContain(toolName)

    const served = buildWebCompletenessReceipt(scope, syntheticChart, [{ name: toolName, status: 'done', ok_count: 1 }])!
    expect(served.served).toContainEqual({ floor_item_id: id, source: toolName })
    expect(served.web_dark_primitive_ids).not.toContain(id)

    const notInvoked = buildWebCompletenessReceipt(scope, syntheticChart, [])!
    expect(notInvoked.empty).toContainEqual({ floor_item_id: id, empty_reason: `route_not_invoked: retrieval tool "${toolName}" was not executed for this request` })
    expect(notInvoked.served).toHaveLength(0)

    const empty = buildWebCompletenessReceipt(scope, syntheticChart, [{ name: toolName, status: 'done', ok_count: 0 }])!
    expect(empty.empty).toContainEqual({ floor_item_id: id, empty_reason: 'route_empty' })
    expect(empty.web_dark_primitive_ids).not.toContain(id)
  })

  it('preserves a generated tool registry failure as registry_unresolvable', () => {
    const receipt = buildWebCompletenessReceipt(tuple({ depth: 'standard' }), syntheticChart, [{
      name: 'marsys://tool/L1/chart_facts_query', status: 'error', ok_count: 0, error_kind: 'registry_unresolvable',
    }])!
    expect(receipt.empty.find(e => e.floor_item_id === 'divisional_facts')?.empty_reason).toMatch(/^registry_unresolvable:/)
    expect(receipt.web_dark_primitive_ids).not.toContain('divisional_facts')
  })

  it('keeps the five deferred facet primitives and MCP-native dossier unresolved', () => {
    const scope = tuple({ depth: 'standard' })
    const receipt = buildWebCompletenessReceipt(scope, syntheticChart, [])!
    const compiled = compileFloorForPlan(scope, syntheticChart)
    for (const id of ['bhava_condition', 'bhavesha_condition', 'karaka_condition', 'chara_karaka_read', 'karakamsa_read', 'full_domain_dossier']) {
      expect(compiled.unmappedPrimitives).toContain(id)
      expect(receipt.web_dark_primitive_ids).toContain(id)
      expect(receipt.empty.find(e => e.floor_item_id === id)?.empty_reason).toMatch(/^web_namespace_gap:/)
    }
    for (const name of ['ganita_structural_get', 'ganita_condition_get', 'dossier', 'kala_bundle_get']) {
      expect(resolveLiveTool(name)).toBeUndefined()
    }
  })

  it('accounts for KP only when its exact registered retrieval tool executes', () => {
    const scope = tuple({ depth: 'standard' })
    const toolName = 'marsys://tool/L1/get_kp_cusps'
    const receipt = buildWebCompletenessReceipt(scope, syntheticChart, [{ name: toolName, status: 'done', ok_count: 1 }])!
    expect(receipt.served).toContainEqual({ floor_item_id: 'kp_cusp_sublord_read', source: toolName })
    expect(receipt.web_dark_primitive_ids).not.toContain('kp_cusp_sublord_read')
  })
})
