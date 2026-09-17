import { describe, expect, it } from 'vitest'
import snapshotJson from '../../../src/generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../../src/lib/retrieval/registry/knowledge/types'
import { buildCapabilityCoverage } from '../capability_coverage'

const snapshot = snapshotJson as CapabilityKnowledgeSnapshot

describe('Purna capability coverage projection', () => {
  it('preserves the complete generated denominator and exposes the contract deficit', () => {
    const rows = buildCapabilityCoverage(snapshot)
    expect(rows).toHaveLength(182)
    expect(new Set(rows.map((row) => row.scu_id)).size).toBe(182)
    expect(rows.filter((row) => row.blocker === 'availability_contract_missing')).toHaveLength(157)
  })

  it('keeps semantic outputs, bindings, and exact evidence dependencies together', () => {
    const mechanism = buildCapabilityCoverage(snapshot).find((row) => row.scu_id === 'scu.bodha.mechanism.network')
    expect(mechanism).toMatchObject({
      outputs: expect.arrayContaining(['mechanisms']),
      availability_contract_binding_ids: ['registry:marsys://tool/L2/query_mechanisms'],
      source_dependencies: expect.arrayContaining(['producer:bo_yantra_mechanism']),
      blocker: 'overlay_not_measured',
    })
  })
})
