import { describe, expect, it } from 'vitest'
import snapshotJson from '../../../src/generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../../src/lib/retrieval/registry/knowledge/types'
import { buildCapabilityCoverage } from '../capability_coverage'

const snapshot = snapshotJson as CapabilityKnowledgeSnapshot

describe('Purna capability coverage projection', () => {
  it('preserves the complete generated denominator and exposes the contract deficit', () => {
    const rows = buildCapabilityCoverage(snapshot)
    expect(rows).toHaveLength(186)
    expect(new Set(rows.map((row) => row.coverage_id)).size).toBe(186)
    expect(new Set(rows.map((row) => row.scu_id)).size).toBe(182)
    expect(rows.filter((row) => row.blocker === 'availability_contract_missing')).toHaveLength(46)
    expect(rows.filter((row) => row.availability_contract === 'authored')).toHaveLength(132)
    expect(rows.filter((row) => row.availability_contract === 'deliberately_dark')).toHaveLength(8)
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
})
