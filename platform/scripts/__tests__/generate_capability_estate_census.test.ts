import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import {
  buildCapabilityEstateCensus,
  canonicalJson,
  censusContentSha256,
  renderCapabilityEstateCensus,
} from '../generate_capability_estate_census'

describe('capability estate census', () => {
  it('keeps runtime, public-route, producer, and reviewed-output denominators distinct', async () => {
    const census = await buildCapabilityEstateCensus()

    expect(census.denominators.runtime_descriptors).toMatchObject({
      // K7-1a adds seven stored-stage readers and seven public compatibility
      // descriptors. Neither implies a producer or reviewed output contract.
      total: 199,
      tools: 194,
      resources: 4,
      prompts: 1,
    })
    expect(census.denominators.planner_addressable_descriptors).toMatchObject({
      total: 196,
      excluded: 3,
    })
    expect(census.denominators.public_registrar_resolution).toMatchObject({
      verified: 78,
      resolved_including_ambiguous: 78,
      unresolved: 0,
      not_exposed: 121,
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
      // Pravāha A2.5 (PR #2799): ka_gochara_v4_41_candidate ships in the seed
      // is_active: false — inert to all planners — so it counts as retired
      // (inactive), never active, until the steward dispatch's transient flip.
      // Pravāha A5.3 (steward ruling M20261001T014547-357e, pins 1-2):
      // ka_gochara_v5 ships in the seed is_active: false — inert to all
      // planners — so it counts as retired (inactive), never active. Its
      // writer digest IS admitted to src/generated/nirmana-writer-digests.json
      // (regenerated at the geometry_store step, 2026-10-01), so the census
      // counts it as a WRITER identity; the analysis-layer pins admission is
      // a separate governed step and does not change this count.
      // Migration 1333 (ga_fact_identity): the Fact Identity Index becomes a registered writer. Its writer digest is admitted to
      // nirmana-writer-digests.json (writer identities 125 -> 126), it gains a seed row (the writer/seed three-way guard requires one),
      // and a reviewed output-digest spec is inserted by the migration (reviewed spec rows 119 -> 120).
      total: 132,
      active: 129,
      retired: 3,
      writer_identities: 126,
      non_writer_identities: 6,
    })
    expect(
      census.denominators.producer_assets.active + census.denominators.producer_assets.retired,
    ).toBe(census.denominators.producer_assets.total)
    expect(census.denominators.producer_assets.by_layer).toEqual({
      bodha: 23, brahmagyan: 40, ganita: 20, kala: 22, mimamsa: 15, phala: 9,
    })
    expect(census.denominators.producer_assets.by_scope).toEqual({ global: 45, per_chart: 84 })
    expect(census.denominators.producer_assets.by_storage_type).toEqual({
      pgvector: 4, postgres_table: 116, postgres_view: 1, service: 8,
    })
    expect(census.denominators.producer_assets.by_catalog_status).toEqual({
      CURRENT: 70, DRAFT: 29, undeclared: 30,
    })
    for (const subtotal of [
      census.denominators.producer_assets.by_layer,
      census.denominators.producer_assets.by_scope,
      census.denominators.producer_assets.by_storage_type,
      census.denominators.producer_assets.by_catalog_status,
    ]) expect(Object.values(subtotal).reduce((sum, value) => sum + value, 0)).toBe(129)
    expect(census.denominators.reviewed_output_digest_coverage).toMatchObject({
      assets_with_any_reviewed_spec: 121,
      // main's 9 + the inactive A2.5 candidate and A5.3 writer (no output-digest spec by
      // design — candidate-only, steward-dispatched); crucially it does NOT
      // enter active_assets_without_any_reviewed_spec below.
      // main's 9 + the inactive A5.3 skeleton (no output-digest spec by
      // design — inert, geometry pending steward pins 3-7); crucially it does
      // NOT enter active_assets_without_any_reviewed_spec below.
      assets_without_any_reviewed_spec: 11,
      active_assets_without_any_reviewed_spec: 8,
      current_source_intended_spec_rows: 120,
      current_source_intended_active_spec_rows: 120,
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
        'ka_gochara_v3_century_materialize',
        'ka_graha_sancara',
        'ka_tulana',
        'lel_events',
        'mi_abhilekha',
        'mi_seva',
      ])

    // "retired" is the census's inactive bucket (generator: !asset.is_active,
    // line ~617); the A2.5 candidate and the A5.3 writer ship inactive (planner-inert), so they
    // list here until the steward dispatch's transient flip / a steward-governed activation.
    expect(census.details.producer_assets.retired_asset_ids)
      .toEqual(['ka_gochara_sweep', 'ka_gochara_v4_41_candidate', 'ka_gochara_v5'])
    expect(census.details.reviewed_output_digest_coverage.active_assets_without_any_reviewed_spec)
      .not.toContain('ka_gochara_sweep')
    expect(census.details.reviewed_output_digest_coverage.assets_without_any_reviewed_spec)
      .toContain('ka_gochara_sweep')

    const producerContracts = census.details.producer_output_contracts
    expect(producerContracts).toHaveLength(129)
    expect(new Set(producerContracts.map((contract) => contract.asset_id)).size).toBe(129)
    expect(census.denominators.producer_output_contracts).toEqual({
      denominator: 129,
      by_disposition: {
        excluded_nondeterministic: 1,
        relational_contract_blocked: 1,
        relational_digest_current_source_intent: 118,
        service_effect_contract: 2,
        service_probe: 6,
        user_authored_source_contract: 1,
      },
      unexplained: 0,
    })
    expect(producerContracts.find((contract) => contract.asset_id === 'ph_nimitta')?.disposition)
      .toBe('excluded_nondeterministic')
    // N-143 option B: the digest specs 976 / 1009 are hash-bound and unchanged; the changed MEANING of
    // constituent_ga_vichara_ids_array (serials -> deterministic tokens) is carried in the asset's known_gaps instead.
    for (const assetId of ['bo_karanajala', 'bo_yantra_mechanism']) {
      const contract = producerContracts.find((candidate) => candidate.asset_id === assetId)
      expect(contract?.disposition).toBe('relational_digest_current_source_intent')
      const notes = (contract?.known_gaps ?? []).filter((gap) => gap.startsWith('column_meaning_changed_spec_unchanged:'))
      expect(notes).toHaveLength(1)
      expect(notes[0]).toContain('constituent_ga_vichara_ids_array')
      expect(notes[0]).toContain('vichara_token_expression.sql')
    }
    for (const assetId of ['ka_gochara_v3_century_materialize']) {
      const blocked = producerContracts.find((contract) => contract.asset_id === assetId)
      expect(blocked?.disposition).toBe('relational_contract_blocked')
      expect(blocked?.known_gaps.join(' ')).not.toHaveLength(0)
    }

    expect(census.details.descriptor_route_contracts).toHaveLength(199)
    expect(census.denominators.descriptor_route_contracts).toMatchObject({
      denominator: 199,
      non_exhaustible_paginated: 107,
      exhaustible_paginated: 5,
      descriptor_content_untyped: 194,
      full_profile_allowlist_enforced: true,
    })
    expect(Object.values(census.denominators.descriptor_route_contracts.by_public_route_disposition)
      .reduce((sum, value) => sum + value, 0)).toBe(199)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.internal_route_evidence.length > 0)).toBe(true)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.full_profile_enforcement === 'enforced')).toBe(true)
    expect(census.details.descriptor_route_contracts.every((contract) => contract.public_route_evidence.length > 0)).toBe(true)
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'get_yoga_firings'))
      .toMatchObject({
        public_route_disposition: 'reviewed_exposed',
        public_tool_names: ['ganita_yoga_firings_get'],
      })
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'get_dashas')?.pagination)
      .toMatchObject({ disposition: 'exhaustible_reviewed', declared: 'cursor' })
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'query_classical_texts')?.pagination)
      .toMatchObject({ disposition: 'exhaustible_reviewed', declared: 'cursor' })
    expect(census.details.descriptor_route_contracts.find((contract) => contract.descriptor_name === 'list_entities')?.public_routes)
      .toEqual(expect.arrayContaining([
        { tool_name: 'list_entities', route_kind: 'parallel_same_name' },
        { tool_name: 'ref_entities_list', route_kind: 'exact_uri_binding' },
      ]))
    expect(census.details.descriptor_route_contracts.filter((contract) => contract.public_route_disposition === 'reviewed_not_exposed'))
      .toHaveLength(121)
  })

  it('is deterministic and its printed SHA-256 binds canonical content and source hashes', async () => {
    const first = await buildCapabilityEstateCensus()
    const second = await buildCapabilityEstateCensus()
    expect(second).toEqual(first)

    const expectedHash = createHash('sha256').update(canonicalJson(first)).digest('hex')
    expect(censusContentSha256(first)).toBe(expectedHash)
    expect(censusContentSha256(first)).toMatch(/^[a-f0-9]{64}$/)
    expect(first.provenance.sources.length).toBeGreaterThanOrEqual(6)
    for (const source of first.provenance.sources) {
      expect(source.sha256).toMatch(/^[a-f0-9]{64}$/)
    }
    expect(renderCapabilityEstateCensus(first)).toBe(renderCapabilityEstateCensus(second))
    expect(renderCapabilityEstateCensus(first)).toMatch(/\n$/)
  }, 15_000)

  // DECISION (N-301, supersedes E6.1 follow-up item 5): the artifact stores NO generation timestamp, NO source revision and NO whole-file hash. A hand refresh used to rewrite
  // those three lines, so any two PRs that both refreshed the census collided on them even when the rest merged cleanly. Freshness is still proven: `:check` re-renders the whole
  // artifact and compares it byte for byte, and `provenance.sources[].sha256` names which source each part was built from. The hash is printed (censusContentSha256), never stored.
  it('stores no timestamp, source revision or whole-file hash, in the build output or in the committed artifact', async () => {
    const census = await buildCapabilityEstateCensus()
    const keys = Object.keys(census)
    for (const retired of ['generated_at', 'source_revision', 'content_sha256']) {
      expect(keys).not.toContain(retired)
    }
    const committed = JSON.parse(readFileSync(join(__dirname, '..', '..', 'src', 'generated', 'capability_estate_census.json'), 'utf8')) as Record<string, unknown>
    for (const retired of ['generated_at', 'source_revision', 'content_sha256']) {
      expect(Object.keys(committed)).not.toContain(retired)
    }
    // the committed artifact is exactly what the generator renders now: a stale or hand-edited file cannot pass
    expect(readFileSync(join(__dirname, '..', '..', 'src', 'generated', 'capability_estate_census.json'), 'utf8')).toBe(renderCapabilityEstateCensus(census))
  }, 30_000)

  it('refuses the retired provenance flags and never asks git', () => {
    const source = readFileSync(join(__dirname, '..', 'generate_capability_estate_census.ts'), 'utf8')
    expect(source).toMatch(/--generated-at and --source-revision were retired/)
    // refused in the '=' form AND the space form (`--generated-at 2026-...`), for both flags
    expect(source).toMatch(/arg === '--generated-at' \|\| arg\.startsWith\('--generated-at='\)/)
    expect(source).toMatch(/arg === '--source-revision' \|\| arg\.startsWith\('--source-revision='\)/)
    expect(source).not.toMatch(/child_process|execSync|spawnSync|execFileSync|rev-parse|git\s+(?:log|show|rev)/)
  })

  it('changes the rendered artifact when any hashed source differs (the gate is not a constant)', async () => {
    const census = await buildCapabilityEstateCensus()
    const tampered = structuredClone(census)
    tampered.provenance.sources[0].sha256 = tampered.provenance.sources[0].sha256.replace(/^./, (c) => (c === '0' ? '1' : '0'))
    expect(renderCapabilityEstateCensus(tampered)).not.toBe(renderCapabilityEstateCensus(census))
    expect(censusContentSha256(tampered)).not.toBe(censusContentSha256(census))
  })
})
