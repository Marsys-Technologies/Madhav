import { describe, expect, it } from 'vitest'
import snapshotJson from '../../../src/generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../../src/lib/retrieval/registry/knowledge/types'
import { buildCapabilityCoverage } from '../capability_coverage'
import { getCatalog } from '../../../src/lib/retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../../src/lib/retrieval/registry/knowledge/compiler'
import { loadChartCapabilityOverlay } from '../../../src/lib/retrieval/registry/knowledge/overlay_loader'

const snapshot = snapshotJson as CapabilityKnowledgeSnapshot

describe('Purna capability coverage projection', () => {
  it('preserves the complete generated denominator and exposes the contract deficit', () => {
    const rows = buildCapabilityCoverage(snapshot)
    expect(rows).toHaveLength(186)
    expect(new Set(rows.map((row) => row.coverage_id)).size).toBe(186)
    expect(new Set(rows.map((row) => row.scu_id)).size).toBe(182)
    // R3 boundary regen: RC-7 proof typing (7 plan/resource/discovery bindings) and the
    // assess_* derived contracts moved 14 bindings off "missing"; channel_chat_dispatch moved
    // from missing to deliberately_dark (RC-9 legacy-route disposition). Remaining missing: the
    // seven required-product proof-typing bindings still open (strength group, sidecar probes,
    // direct-DB composites) plus classical_attribution_lookup (fails closed by design, RC-9),
    // query_muhurat and query_sutravali_rules_for_planet (both explicitly out of scope, review
    // §4 / R0 salvage matrix).
    expect(rows.filter((row) => row.blocker === 'availability_contract_missing')).toHaveLength(10)
    expect(rows.filter((row) => row.availability_contract === 'authored')).toHaveLength(173)
    expect(rows.filter((row) => row.availability_contract === 'deliberately_dark')).toHaveLength(3)
  })

  it('keeps semantic outputs, bindings, and exact evidence dependencies together', () => {
    const mechanism = buildCapabilityCoverage(snapshot).find((row) => row.scu_id === 'scu.bodha.mechanism.network')
    expect(mechanism).toMatchObject({
      outputs: expect.arrayContaining(['mechanisms']),
      binding_id: 'registry:marsys://tool/L2/query_mechanisms',
      availability_contract: 'authored',
      source_dependencies: expect.arrayContaining(['producer:bo_yantra_mechanism']),
      blocker: 'overlay_not_measured',
    })
  })

  it('keeps every executable binding occurrence when one SCU exposes multiple routes', () => {
    const rows = buildCapabilityCoverage(snapshot)
    expect(rows.filter((row) => row.scu_id === 'scu.catalog.get_divisionals')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.catalog.query_planet_transit')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.finance.prosperity_assessment')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.yoga.firing_and_cancellation')).toHaveLength(2)

    const sharedBindingId = rows.filter((row) =>
      row.binding_id === 'registry:marsys://tool/L0/query_current_transit_snapshot')
    expect(sharedBindingId).toHaveLength(2)
    expect(new Set(sharedBindingId.map((row) => row.scu_id))).toEqual(new Set([
      'scu.catalog.query_current_transit_snapshot',
      'scu.catalog.query_planet_transit',
    ]))
  })

  it('reports plan/resource/discovery capabilities as resource_ok, never as dark answer routes (RC-7)', async () => {
    const compiled = compileCapabilityKnowledge(getCatalog(), '2026-09-27T00:00:00.000Z') as CapabilityKnowledgeSnapshot
    const overlay = await loadChartCapabilityOverlay(compiled, '482012f1-710e-4a25-994a-93821f5871aa', async () => ({ rows: [] }))
    const rows = buildCapabilityCoverage(compiled, overlay)
    const resources = rows.filter((row) => row.proof_kind !== 'answer')
    expect(resources.map((row) => row.scu_id).sort()).toEqual([
      'scu.catalog.channel_mcp_wiring', 'scu.catalog.intent_classify', 'scu.catalog.maro_mcp_surface',
      'scu.catalog.maro_orchestrate', 'scu.catalog.maro_profiles', 'scu.catalog.route', 'scu.catalog.tool_search',
    ])
    for (const row of resources) {
      expect(row).toMatchObject({ readiness: 'resource_ok', blocker: 'resource_not_answer', availability_contract: 'authored' })
      expect(row.source_dependencies[0]).toMatch(/^snapshot:/)
    }
  })
})
