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
    ['scu.catalog.resolve_entity', 'source-query:resolve-entity:v1', 'platform/migrations/ws2_l0_ontology.sql:15-37'],
    ['scu.catalog.read_chapter', 'source-query:read-chapter:v1', 'platform/migrations/ws2_l0_texts.sql:42-65'],
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

  it.each([
    ['source-query:resolve-entity:v1', 'FROM brahma_ontology', "ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id"],
    ['source-query:read-chapter:v1', 'FROM classical_text_chunks', 'ORDER BY verse_start, chunk_id'],
  ])('keeps %s as an exact, zero-row-safe handler source probe', (contractId, relationMarker, orderMarker) => {
    const contract = getSourceQueryAvailabilityContract(contractId)!

    expect(contract.parameter_binding).toBe('global')
    expect(contract.empty_semantics).toBe('query_success_is_available')
    expect(contract.sql).toContain(relationMarker)
    expect(contract.sql).toContain(orderMarker)
    expect(contract.sql).toContain('LIMIT 0')
  })

  it.each([
    ['scu.catalog.query_avastha_schemes', 'source-query:query-avastha-schemes:v1', 'platform/migrations/250_bg_dignity_reference.sql:239-256'],
    ['scu.catalog.query_combustion_orbs', 'source-query:query-combustion-orbs:v1', 'platform/migrations/250_bg_dignity_reference.sql:484-497'],
  ])('binds %s to its exact global source-query contract without a producer-output claim', (scuId, contractId, schemaRef) => {
    const scu = snapshot.scus.find((candidate) => candidate.scu_id === scuId)!
    const requirement = scu.availability_contracts![0]!.requirements[0]!

    expect(requirement).toMatchObject({
      kind: 'source_query',
      contract_id: contractId,
      scope: 'global',
      contract_sha256: expect.stringMatching(/^sha256:[a-f0-9]{64}$/),
      source_ref: expect.stringContaining(schemaRef),
    })
    expect(scu.producer_output_claims ?? []).toEqual([])
    expect(scu.availability_dispositions ?? []).toEqual([])
    expect(inspectCapabilityKnowledge(catalog, snapshot).findings).not.toContainEqual(expect.objectContaining({
      code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
      subject: `${scu.scu_id}:${scu.availability_contracts![0]!.binding_id}`,
    }))
  })

  it.each([
    {
      contractId: 'source-query:query-avastha-schemes:v1',
      markers: [
        'SELECT scheme_name, state_name, state_order, determination_rule',
        'classical_citation, notes',
        'FROM bg_avastha_schemes',
        'LOWER(scheme_name) = LOWER(NULL::text)',
        'LOWER(state_name) = LOWER(NULL::text)',
        'ORDER BY scheme_name, state_order',
      ],
    },
    {
      contractId: 'source-query:query-combustion-orbs:v1',
      markers: [
        'SELECT graha, orb_degrees, deep_orb_degrees, retrograde_note',
        'classical_citation',
        'FROM bg_combustion_orbs',
        'LOWER(graha) = LOWER(NULL::text)',
        'ORDER BY graha',
      ],
    },
  ])('keeps $contractId as an exact, zero-row-safe handler source probe', ({ contractId, markers }) => {
    const contract = getSourceQueryAvailabilityContract(contractId)!

    expect(contract.parameter_binding).toBe('global')
    expect(contract.empty_semantics).toBe('query_success_is_available')
    for (const marker of markers) expect(contract.sql).toContain(marker)
    expect(contract.sql).toContain('LIMIT 0')
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
    ['scu.catalog.list_entities', 'source-query:list-entities:v1', 'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:17'],
    ['scu.catalog.list_classical_texts', 'source-query:list-classical-texts:v1', 'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:16'],
    ['scu.catalog.query_graha_naisargika_friendship', 'source-query:query-graha-naisargika-friendship:v1', 'platform/migrations/250_bg_dignity_reference.sql:128-140'],
    ['scu.catalog.query_motion_state_thresholds', 'source-query:query-motion-state-thresholds:v1', 'platform/migrations/250_bg_dignity_reference.sql:406-423'],
    ['scu.catalog.query_vastu_directions', 'source-query:query-vastu-directions:v1', 'platform/migrations/284_bg_vastu_directions.sql:10-33'],
    ['scu.catalog.query_vastu_direction_remedials', 'source-query:query-vastu-direction-remedials:v1', 'platform/migrations/284_bg_vastu_directions.sql:37-89'],
    ['scu.catalog.query_graha_dik', 'source-query:query-graha-dik:v1', 'platform/migrations/304_bg_graha_dik.sql:22-32'],
    ['scu.catalog.query_shashtiamsha_deities', 'source-query:query-shashtiamsha-deities:v1', 'platform/supabase/migrations/430_bg_shashtiamsha_deities.sql:34-42'],
    ['scu.catalog.query_prashna_lagna_methods', 'source-query:query-prashna-lagna-methods:v1', 'platform/migrations/261_bg_prashna_rules_schema.sql:6-16'],
    ['scu.catalog.query_prashna_tajik_yogas', 'source-query:query-prashna-tajik-yogas:v1', 'platform/migrations/261_bg_prashna_rules_schema.sql:19-29'],
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

  it('preserves directed natural-friendship pairs and the exact case-sensitive relation predicate', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-graha-naisargika-friendship:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT graha, other_graha, relation, classical_citation')
    expect(contract.sql).toContain('LOWER(graha) = LOWER(NULL::text)')
    expect(contract.sql).toContain('LOWER(other_graha) = LOWER(NULL::text)')
    expect(contract.sql).toContain('relation = NULL::text')
    expect(contract.sql).not.toContain('LOWER(relation)')
    expect(contract.sql).toContain('ORDER BY graha, other_graha')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
  })

  it('preserves nullable, nonuniform global motion thresholds without chart or count inference', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-motion-state-thresholds:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT graha, motion_state, speed_threshold_low, speed_threshold_high, threshold_type,')
    expect(contract.sql).toContain('typical_speed_dps, classical_citation, notes')
    expect(contract.sql).toContain('LOWER(graha) = LOWER(NULL::text)')
    expect(contract.sql).toContain('LOWER(motion_state) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY graha, motion_state')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toContain('COALESCE(speed_threshold_')
    expect(contract.sql).not.toMatch(/\bmotion_state\s+IN\s*\(/i)
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves the exact Vastu direction projection, nullable fields, predicates, and degree ordering', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-vastu-directions:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT direction, direction_deg, ruling_graha, secondary_graha, favorable_color, element,')
    expect(contract.sql).toContain('classical_citation')
    expect(contract.sql).toContain('LOWER(direction) = LOWER(NULL::text)')
    expect(contract.sql).toContain('LOWER(ruling_graha) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY direction_deg')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toContain('COALESCE(secondary_graha')
    expect(contract.sql).not.toContain('COALESCE(favorable_color')
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves open Vastu remedy types and the exact direction/remedy ordering', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-vastu-direction-remedials:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT direction, remedy_type, remedy_description, classical_citation')
    expect(contract.sql).toContain('LOWER(direction) = LOWER(NULL::text)')
    expect(contract.sql).toContain('LOWER(remedy_type) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY direction, remedy_type')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toMatch(/\bremedy_type\s+IN\s*\(/i)
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves the exact Dig Bala projection and nullable paired graha without chart or producer inference', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-graha-dik:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT graha, peak_house, peak_direction, debility_house, paired_graha, school_note,')
    expect(contract.sql).toContain('classical_citation')
    expect(contract.sql).toContain('LOWER(graha) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY graha')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toContain('COALESCE(paired_graha')
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves the exact Shashtiamsha projection, nullable deity name, and optional typed predicates', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-shashtiamsha-deities:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT amsa_number, quality, deity_name, classical_citation, rule_notes')
    expect(contract.sql).toContain('NULL::integer IS NULL OR amsa_number = NULL::integer')
    expect(contract.sql).toContain('LOWER(quality) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY amsa_number')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toContain('COALESCE(deity_name')
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves the complete Prashna-lagna method projection and open tradition filter', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-prashna-lagna-methods:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT method_id, method_name, method_name_sa, derivation_rule, derivation_rule_jsonb,')
    expect(contract.sql).toContain('classical_citation, is_primary, tradition')
    expect(contract.sql).toContain('method_id = NULL::text')
    expect(contract.sql).toContain('LOWER(tradition) = LOWER(NULL::text)')
    expect(contract.sql).toContain('ORDER BY method_id')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toMatch(/\btradition\s+IN\s*\(/i)
    expect(contract.sql).not.toContain('chart_id')
  })

  it('preserves the complete Tajik-yoga projection and typed false-capable indicator filter', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-prashna-tajik-yogas:v1')!

    expect(contract).toMatchObject({
      scope: 'global',
      parameter_binding: 'global',
      empty_semantics: 'query_success_is_available',
    })
    expect(contract.sql).toContain('SELECT yoga_id, yoga_name, yoga_name_sa, judgment_meaning, formation_rule,')
    expect(contract.sql).toContain('formation_rule_jsonb, classical_citation, is_fructification_indicator')
    expect(contract.sql).toContain('yoga_id = NULL::text')
    expect(contract.sql).toContain('NULL::boolean IS NULL OR is_fructification_indicator = NULL::boolean')
    expect(contract.sql).toContain('ORDER BY yoga_id')
    expect(contract.sql).toContain('LIMIT 0')
    expect(contract.sql).not.toMatch(/\bCOUNT\s*\(/i)
    expect(contract.sql).not.toMatch(/\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b/i)
    expect(contract.sql).not.toContain('COALESCE(is_fructification_indicator')
    expect(contract.sql).not.toContain('chart_id')
  })

  it.each([
    'scu.catalog.query_graha_naisargika_friendship',
    'scu.catalog.query_motion_state_thresholds',
    'scu.catalog.query_vastu_directions',
    'scu.catalog.query_vastu_direction_remedials',
    'scu.catalog.query_graha_dik',
    'scu.catalog.query_shashtiamsha_deities',
    'scu.catalog.query_prashna_lagna_methods',
    'scu.catalog.query_prashna_tajik_yogas',
  ])('does not infer a producer-output claim for %s from its shared source writer', (scuId) => {
    const scu = snapshot.scus.find((candidate) => candidate.scu_id === scuId)!
    expect(scu.producer_output_claims ?? []).toEqual([])
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
