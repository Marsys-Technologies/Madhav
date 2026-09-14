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
      total: 185,
      tools: 179,
      resources: 5,
      prompts: 1,
    })
    expect(census.denominators.planner_addressable_descriptors).toMatchObject({
      total: 182,
      excluded: 3,
    })
    expect(census.denominators.public_registrar_resolution).toMatchObject({
      verified: 59,
      resolved_including_ambiguous: 62,
      unresolved: 123,
      ambiguous: 3,
    })
    expect(
      census.denominators.public_registrar_resolution.verified
      + census.denominators.public_registrar_resolution.unresolved
      + census.denominators.public_registrar_resolution.ambiguous,
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
    expect(census.denominators.reviewed_output_digest_coverage).toMatchObject({
      assets_with_any_reviewed_spec: 111,
      assets_without_any_reviewed_spec: 18,
      active_assets_without_any_reviewed_spec: 17,
      current_spec_rows: 'not_mechanically_resolved',
    })

    expect(census.details.reviewed_output_digest_coverage.migration_files_scanned)
      .toEqual(expect.arrayContaining([
        'platform/migrations/946_nirmana_l2_bo_grounding_output_digest_spec.sql',
        'platform/supabase/migrations/598_nirmana_output_digest_specs.sql',
      ]))
    expect(census.details.reviewed_output_digest_coverage.active_assets_without_any_reviewed_spec)
      .toEqual([
        'bg_ephemeris_engine',
        'bg_gochara_citation_resolution',
        'bg_nakshatra_medical',
        'bg_panchanga',
        'bg_sign_medical',
        'bg_transit_engine',
        'ka_avadhi',
        'ka_dasha_kala',
        'ka_gochara_v3_century_materialize',
        'ka_graha_sancara',
        'ka_kalasutra',
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
