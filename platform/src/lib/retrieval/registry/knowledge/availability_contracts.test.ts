import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from './compiler'
import type { CapabilityKnowledgeSnapshot } from './types'

const catalog = getCatalog()
const snapshot = compileCapabilityKnowledge(catalog, '2026-09-17T00:00:00.000Z')
const source = snapshot.scus.find((scu) => (scu.producer_output_claims?.length ?? 0) > 0)!
const reviewedClaim = source.producer_output_claims!.find((claim) => claim.disposition === 'reviewed_output')!
const knownBindingId = source.bindings.find((binding) => binding.executable)!.binding_id

function withContracts(availability_contracts: unknown): CapabilityKnowledgeSnapshot {
  return {
    ...snapshot,
    scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id
      ? { ...scu, availability_contracts }
      : scu),
  } as CapabilityKnowledgeSnapshot
}

describe('binding availability contracts', () => {
  it('reports a non-array availability contract without throwing', () => {
    const inspect = () => inspectCapabilityKnowledge(catalog, withContracts({ binding_id: knownBindingId }))

    expect(inspect).not.toThrow()
    expect(inspect().findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'error',
      subject: source.scu_id,
    }))
  })

  it('rejects malformed producer requirements and contracts for unknown bindings', () => {
    const report = inspectCapabilityKnowledge(catalog, withContracts([
      {
        binding_id: knownBindingId,
        requirements: [{ kind: 'producer_output', asset_id: reviewedClaim.asset_id, spec_sha256: 'b'.repeat(64), scope: 'chart_build', source_ref: '' }],
      },
      {
        binding_id: 'registry:marsys://tool/L1/missing',
        requirements: [{ kind: 'producer_output', asset_id: '', spec_sha256: '', scope: 'wrong', source_ref: 'fixture' }],
      },
    ]))

    expect(report.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'error',
    }))
  })

  it('rejects duplicate contracts for the same binding', () => {
    const requirement = {
      kind: 'producer_output' as const,
      asset_id: reviewedClaim.asset_id,
      spec_sha256: reviewedClaim.output_digest_spec_sha256!,
      scope: 'chart_build' as const,
      source_ref: 'fixture',
    }
    const report = inspectCapabilityKnowledge(catalog, withContracts([
      { binding_id: knownBindingId, requirements: [requirement] },
      { binding_id: knownBindingId, requirements: [requirement] },
    ]))

    expect(report.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'error',
      subject: `${source.scu_id}:${knownBindingId}`,
      detail: expect.stringContaining('duplicate'),
    }))
  })

  it('validates service-probe readiness requirements instead of treating them as unsupported', () => {
    const valid = {
      kind: 'service_probe' as const,
      asset_id: 'bg_ephemeris_engine',
      probe_id: 'ephemeris_engine',
      endpoint_identity: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
      probe_contract_sha256: 'a'.repeat(64),
      max_age_seconds: 900,
      source_ref: 'fixture:authenticated-probe',
    }
    const validReport = inspectCapabilityKnowledge(catalog, withContracts([{ binding_id: knownBindingId, requirements: [valid] }]))
    expect(validReport.findings).not.toContainEqual(expect.objectContaining({
      code: 'UNSUPPORTED_BINDING_AVAILABILITY_REQUIREMENT',
      subject: `${source.scu_id}:${knownBindingId}`,
    }))
    expect(validReport.findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
    }))

    const invalidReport = inspectCapabilityKnowledge(catalog, withContracts([{
      binding_id: knownBindingId,
      requirements: [{ ...valid, endpoint_identity: 'https://untrusted.example/probe', probe_contract_sha256: 'bad', max_age_seconds: 0 }],
    }]))
    expect(invalidReport.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'error',
      subject: `${source.scu_id}:${knownBindingId}`,
    }))
  })
})
