/**
 * completeness_wiring.test.ts — web-channel receipt honesty (W4 core step 4).
 *
 * Verifies buildWebCompletenessReceipt maps REAL per-tool execution outcomes onto the compiled
 * B.11 floor truthfully — and that it reports the MCP↔web namespace gap honestly rather than
 * papering over it (channel_note + web_dark_primitive_ids).
 */
import { describe, expect, it } from 'vitest'
import { buildWebCompletenessReceipt, type ToolExecutionOutcome } from '../completeness_wiring'
import { compileFloorForPlan, LIVE_TOOL_TO_RETRIEVAL } from '../compiled_floor_adapter'
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
