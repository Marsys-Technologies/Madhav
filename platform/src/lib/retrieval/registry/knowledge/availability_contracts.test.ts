import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from './compiler'
import { getSourceQueryAvailabilityContract } from './source_query_availability'
import type { CapabilityKnowledgeSnapshot } from './types'

const catalog = getCatalog()
const snapshot = compileCapabilityKnowledge(catalog, '2026-09-17T00:00:00.000Z')
const source = snapshot.scus.find((scu) => (scu.producer_output_claims?.length ?? 0) > 0)!
const reviewedClaim = source.producer_output_claims!.find((claim) => claim.disposition === 'reviewed_output')!
const knownBindingId = source.bindings.find((binding) => binding.executable)!.binding_id
const derivedLeg = snapshot.scus.find((scu) => scu.scu_id !== source.scu_id
  && scu.scope === source.scope
  && (scu.availability_contracts?.length ?? 0) > 0
  && scu.bindings.some((binding) => binding.executable))!
const derivedLegBindingId = derivedLeg.bindings.find((binding) => binding.executable)!.binding_id

function withContracts(availability_contracts: unknown): CapabilityKnowledgeSnapshot {
  return {
    ...snapshot,
    scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id
      ? { ...scu, availability_contracts }
      : scu),
  } as CapabilityKnowledgeSnapshot
}

function withBindings(bindings: unknown): CapabilityKnowledgeSnapshot {
  return {
    ...snapshot,
    scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id
      ? { ...scu, bindings }
      : scu),
  } as CapabilityKnowledgeSnapshot
}

describe('binding availability contracts', () => {
  it('accepts the exact registry-owned source-query contract and rejects a fingerprint change', () => {
    const yoga = snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.query_yoga_catalog')!
    const requirement = yoga.availability_contracts![0]!.requirements[0]!
    expect(requirement).toMatchObject({
      kind: 'source_query',
      contract_id: 'source-query:query-yoga-catalog:v1',
      scope: 'global',
    })
    expect(inspectCapabilityKnowledge(catalog, snapshot).findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${yoga.scu_id}:${yoga.availability_contracts![0]!.binding_id}`,
    }))

    const tampered = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === yoga.scu_id ? {
        ...scu,
        availability_contracts: [{
          ...yoga.availability_contracts![0]!,
          requirements: [{ ...requirement, contract_sha256: `sha256:${'0'.repeat(64)}` }],
        }],
      } : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, tampered).findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${yoga.scu_id}:${yoga.availability_contracts![0]!.binding_id}`,
      detail: expect.stringContaining('source-query'),
    }))
  })

  it.each([
    ['scu.catalog.get_ayurdaya', 'source-query:get-ayurdaya:v1'],
    ['scu.catalog.get_sensitive_degrees', 'source-query:get-sensitive-degrees:v1'],
  ])('binds %s to its exact chart-and-active-build source-query contract', (scuId, contractId) => {
    const scu = snapshot.scus.find((candidate) => candidate.scu_id === scuId)!
    const requirement = scu.availability_contracts![0]!.requirements[0]!

    expect(requirement).toMatchObject({
      kind: 'source_query',
      contract_id: contractId,
      scope: 'chart',
      contract_sha256: expect.stringMatching(/^sha256:[a-f0-9]{64}$/),
      source_ref: expect.stringContaining('platform/supabase/migrations/204_chart_facts.sql:10-29'),
    })
    expect(scu.availability_dispositions ?? []).toEqual([])
    expect(inspectCapabilityKnowledge(catalog, snapshot).findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${scu.scu_id}:${scu.availability_contracts![0]!.binding_id}`,
    }))
  })

  it.each([
    ['source-query:get-ayurdaya:v1', "fact_category = 'ayurdaya'"],
    ['source-query:get-sensitive-degrees:v1', "fact_category = ANY(ARRAY['sensitive_degree_check', 'sensitive_point_yogi']::text[])"],
  ])('keeps %s as a non-reducing query-success probe across the handler category set', (contractId, categoryPredicate) => {
    const contract = getSourceQueryAvailabilityContract(contractId)!

    expect(contract.empty_semantics).toBe('query_success_is_available')
    expect(contract.sql).toContain(categoryPredicate)
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).toContain('SELECT COUNT(*)::text AS total')
    expect(contract.sql).not.toMatch(/\b(?:WHERE|AND)\s+fact_key\s*(?:=|IN|LIKE)\b/i)
  })

  it.each([
    ['scu.catalog.query_dosha_catalog', 'source-query:query-dosha-catalog:v1', 'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:52-71'],
    ['scu.catalog.query_compendium_index', 'source-query:query-compendium-index:v1', 'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:74-93'],
  ])('binds %s to its exact global source-query contract', (scuId, contractId, schemaRef) => {
    const scu = snapshot.scus.find((candidate) => candidate.scu_id === scuId)!
    const requirement = scu.availability_contracts![0]!.requirements[0]!

    expect(requirement).toMatchObject({
      kind: 'source_query',
      contract_id: contractId,
      scope: 'global',
      contract_sha256: expect.stringMatching(/^sha256:[a-f0-9]{64}$/),
      source_ref: expect.stringContaining(schemaRef),
    })
    expect(scu.availability_dispositions ?? []).toEqual([])
    expect(inspectCapabilityKnowledge(catalog, snapshot).findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${scu.scu_id}:${scu.availability_contracts![0]!.binding_id}`,
    }))
  })

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

  it('rejects duplicate executable binding IDs rather than selecting one arbitrarily', () => {
    const bindings = source.bindings.map((binding) => ({ ...binding }))
    bindings.push({ ...bindings[0]! })

    const report = inspectCapabilityKnowledge(catalog, withBindings(bindings))
    expect(report.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'error',
      subject: knownBindingId,
      detail: expect.stringContaining('duplicated'),
    }))
  })

  it('reports executable binding IDs duplicated across SCUs', () => {
    const duplicateScu = {
      ...source,
      scu_id: `${source.scu_id}.duplicate`,
      bindings: source.bindings.map((binding) => ({ ...binding })),
    }
    const crossScuSnapshot = { ...snapshot, scus: [...snapshot.scus, duplicateScu] } as CapabilityKnowledgeSnapshot

    const report = inspectCapabilityKnowledge(catalog, crossScuSnapshot)
    expect(report.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      severity: 'warning',
      subject: knownBindingId,
      detail: expect.stringContaining('across SCUs'),
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

  it('accepts a derived composite only when every mandatory leg has an explicit scope-compatible contract', () => {
    const derived = {
      kind: 'derived' as const,
      scope: 'chart' as const,
      required_binding_ids: [derivedLegBindingId],
      source_ref: 'fixture:composite-handler-leg',
    }
    const validReport = inspectCapabilityKnowledge(catalog, withContracts([{ binding_id: knownBindingId, requirements: [derived] }]))
    expect(validReport.findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
    }))

    const missingLegReport = inspectCapabilityKnowledge(catalog, withContracts([{
      binding_id: knownBindingId,
      requirements: [{ ...derived, required_binding_ids: ['registry:marsys://tool/L2/query_domain_reading'] }],
    }]))
    expect(missingLegReport.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
      detail: expect.stringContaining('existing exact availability contract'),
    }))

    const incompatibleScopeReport = inspectCapabilityKnowledge(catalog, withContracts([{
      binding_id: knownBindingId,
      requirements: [{ ...derived, scope: 'global' as const }],
    }]))
    expect(incompatibleScopeReport.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
      detail: expect.stringContaining('same global scope'),
    }))
  })

  it('rejects duplicate or malformed derived legs without throwing during cycle inspection', () => {
    const derived = {
      kind: 'derived' as const,
      scope: 'chart' as const,
      required_binding_ids: [derivedLegBindingId, derivedLegBindingId],
      source_ref: 'fixture:duplicate-derived-leg',
    }
    const duplicateReport = inspectCapabilityKnowledge(catalog, withContracts([{ binding_id: knownBindingId, requirements: [derived] }]))
    expect(duplicateReport.findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
      detail: expect.stringContaining('unique set'),
    }))

    const malformedSnapshot = withContracts([{ binding_id: knownBindingId, requirements: [null] }])
    expect(() => inspectCapabilityKnowledge(catalog, malformedSnapshot)).not.toThrow()
    expect(inspectCapabilityKnowledge(catalog, malformedSnapshot).findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${source.scu_id}:${knownBindingId}`,
    }))

    const mixedContractSnapshot = withContracts([null, {
      binding_id: knownBindingId,
      requirements: [{
        kind: 'derived',
        scope: 'chart',
        required_binding_ids: [derivedLegBindingId],
        source_ref: 'fixture:mixed-null-contract-derived-leg',
      }],
    }])
    expect(() => inspectCapabilityKnowledge(catalog, mixedContractSnapshot)).not.toThrow()
    expect(inspectCapabilityKnowledge(catalog, mixedContractSnapshot).findings).toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: source.scu_id,
    }))
  })
})
