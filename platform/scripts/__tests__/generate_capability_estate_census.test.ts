import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'

import {
  buildCapabilityEstateCensus,
  canonicalJson,
  renderCapabilityEstateCensus,
} from '../generate_capability_estate_census'

describe('capability estate census', () => {
  it('keeps runtime, public-route, producer, and reviewed-output denominators distinct', async () => {
    const census = await buildCapabilityEstateCensus({
      generatedAt: '2026-09-13T00:00:00.000Z',
    })

    expect(census.denominators.runtime_descriptors).toMatchObject({
      total: 186,
      tools: 180,
      resources: 5,
      prompts: 1,
    })
    expect(census.denominators.planner_addressable_descriptors).toMatchObject({
      total: 183,
      excluded: 3,
    })
    expect(census.denominators.public_registrar_resolution).toMatchObject({
      verified: 71,
      resolved_including_ambiguous: 71,
      unresolved: 0,
      not_exposed: 115,
      ambiguous: 0,
      name_only_unverified: 0,
    })
    expect(
      census.denominators.public_registrar_resolution.verified
      + census.denominators.public_registrar_resolution.unresolved
      + census.denominators.public_registrar_resolution.not_exposed
      + census.denominators.public_registrar_resolution.ambiguous
      + census.denominators.public_registrar_resolution.name_only_unverified,
    ).toBe(census.denominators.public_registrar_resolution.descriptor_denominator)
    expect(census.denominators.producer_assets).toMatchObject({
      total: 129,
      active: 128,
      retired: 1,
      writer_identities: 123,
      non_writer_identities: 6,
    })
    expect(
      census.denominators.producer_assets.active + census.denominators.producer_assets.retired,
    ).toBe(census.denominators.producer_assets.total)
    expect(census.denominators.producer_assets.by_layer).toEqual({
      bodha: 23, brahmagyan: 40, ganita: 19, kala: 22, mimamsa: 15, phala: 9,
    })
    expect(census.denominators.producer_assets.by_scope).toEqual({ global: 45, per_chart: 83 })
    expect(census.denominators.producer_assets.by_storage_type).toEqual({
      pgvector: 4, postgres_table: 115, postgres_view: 1, service: 8,
    })
    expect(census.denominators.producer_assets.by_catalog_status).toEqual({
      CURRENT: 69, DRAFT: 29, undeclared: 30,
    })
    for (const subtotal of [
      census.denominators.producer_assets.by_layer,
      census.denominators.producer_assets.by_scope,
      census.denominators.producer_assets.by_storage_type,
      census.denominators.producer_assets.by_catalog_status,
    ]) expect(Object.values(subtotal).reduce((sum, value) => sum + value, 0)).toBe(128)
    expect(census.denominators.reviewed_output_digest_coverage).toMatchObject({
      assets_with_any_reviewed_spec: 117,
      assets_without_any_reviewed_spec: 12,
      active_assets_without_any_reviewed_spec: 11,
      current_source_intended_spec_rows: 116,
      current_source_intended_active_spec_rows: 116,
    })

    expect(census.details.reviewed_output_digest_coverage.migration_files_scanned)
      .toEqual(expect.arrayContaining([
        'platform/migrations/946_nirmana_l2_bo_grounding_output_digest_spec.sql',
        'platform/supabase/migrations/598_nirmana_output_digest_specs.sql',
      ]))
    expect(census.details.reviewed_output_digest_coverage.active_assets_without_any_reviewed_spec)
      .toEqual([
        'bg_ephemeris_engine',
        'bg_panchanga',
        'ka_dasha_kala',
        'ka_gochara_v3_century_materialize',
        'ka_graha_sancara',
        'ka_muhurta_seva',
        'ka_tulana',
        'ka_vighnakara',
        'lel_events',
        'mi_abhilekha',
        'mi_seva',
      ])

    expect(census.details.producer_assets.retired_asset_ids).toEqual(['ka_gochara_sweep'])
    expect(census.details.reviewed_output_digest_coverage.active_assets_without_any_reviewed_spec)
      .not.toContain('ka_gochara_sweep')
    expect(census.details.reviewed_output_digest_coverage.assets_without_any_reviewed_spec)
      .toContain('ka_gochara_sweep')

    const producerContracts = census.details.producer_output_contracts
    expect(producerContracts).toHaveLength(128)
    expect(new Set(producerContracts.map((contract) => contract.asset_id)).size).toBe(128)
    expect(census.denominators.producer_output_contracts).toEqual({
      denominator: 128,
      by_disposition: {
        excluded_nondeterministic: 1,
        relational_contract_blocked: 2,
        relational_digest_current_source_intent: 116,
        service_effect_contract: 2,
        service_probe: 6,
        user_authored_source_contract: 1,
      },
      unexplained: 0,
    })
    expect(producerContracts.find((contract) => contract.asset_id === 'ph_nimitta')?.disposition)
      .toBe('excluded_nondeterministic')
    for (const assetId of ['ka_vighnakara', 'ka_gochara_v3_century_materialize']) {
      const blocked = producerContracts.find((contract) => contract.asset_id === assetId)
      expect(blocked?.disposition).toBe('relational_contract_blocked')
      expect(blocked?.known_gaps.join(' ')).not.toHaveLength(0)
    }

    expect(census.details.descriptor_route_contracts).toHaveLength(186)
    expect(census.denominators.descriptor_route_contracts).toMatchObject({
      denominator: 186,
      non_exhaustible_paginated: 95,
      exhaustible_paginated: 1,
      descriptor_content_untyped: 181,
      full_profile_allowlist_enforced: true,
    })
    expect(Object.values(census.denominators.descriptor_route_contracts.by_public_route_disposition)
      .reduce((sum, value) => sum + value, 0)).toBe(186)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.internal_route_evidence.length > 0)).toBe(true)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.full_profile_enforcement === 'enforced')).toBe(true)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.public_route_evidence.length > 0)).toBe(true)
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'get_yoga_firings'))
      .toMatchObject({
        public_route_disposition: 'reviewed_exposed',
        public_tool_names: ['ganita_yoga_firings_get'],
      })
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'list_entities')?.public_routes)
      .toEqual(expect.arrayContaining([
        { tool_name: 'list_entities', route_kind: 'parallel_same_name' },
        { tool_name: 'ref_entities_list', route_kind: 'exact_uri_binding' },
      ]))
    expect(census.details.descriptor_route_contracts.filter((contract) => contract.public_route_disposition === 'reviewed_not_exposed'))
      .toHaveLength(115)
  })

  it('is deterministic and binds its SHA-256 to canonical content and source hashes', async () => {
    const options = { generatedAt: '2026-09-13T00:00:00.000Z' }
    const first = await buildCapabilityEstateCensus(options)
    const second = await buildCapabilityEstateCensus(options)
    expect(second).toEqual(first)

    const { content_sha256, ...hashMaterial } = first
    const expectedHash = createHash('sha256').update(canonicalJson(hashMaterial)).digest('hex')
    expect(content_sha256).toBe(expectedHash)
    expect(content_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(first.provenance.sources.length).toBeGreaterThanOrEqual(6)
    for (const source of first.provenance.sources) {
      expect(source.sha256).toMatch(/^[a-f0-9]{64}$/)
    }
    expect(renderCapabilityEstateCensus(first)).toBe(renderCapabilityEstateCensus(second))
    expect(renderCapabilityEstateCensus(first)).toMatch(/\n$/)
  })
})
