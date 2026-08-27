import { describe, expect, it } from 'vitest'

import {
  assetRegistryWriterGovernance,
  ASSET_REGISTRY_UPSERT_SQL,
  ASSETS,
} from '../seed/asset_registry_seed'

// Production at migration 615 plus the deterministic dependency rewrites in
// migrations 619 and 626. These are the 24 rows whose dependency *sets* had
// diverged from the seed (58 canonical edges missing; one stale edge present).
const POST_626_DEPENDENCIES: Record<string, string[]> = {
  ga_strength: ['ga_positions', 'ga_vargas'],
  ga_sade_sati: [
    'ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas',
    'ga_dashas', 'ga_structural', 'ga_nakshatra',
  ],
  ga_tajaka: ['ga_positions', 'ga_dashas', 'ga_sensitive'],
  bo_laksana: [
    'bg_rules', 'ga_positions', 'ga_strength', 'ga_sensitive',
    'ga_panchanga', 'ga_sade_sati', 'ga_structural', 'ga_nakshatra',
    'ga_condition', 'ga_vargas', 'ga_vichara',
  ],
  bo_karanajala: ['bo_laksana', 'bo_bimba', 'ga_positions'],
  bo_pratijna: ['bo_laksana', 'bo_sangati'],
  bo_sangati: ['bo_laksana', 'bo_karanajala'],
  bo_samvada: [
    'bo_laksana', 'bo_karanajala', 'bo_upaya', 'bo_sangati',
    'bo_pramana_mapa',
  ],
  bo_pramana_mapa: [
    'bo_upaya', 'bo_drishti', 'bo_anveshana', 'bo_laksana',
    'bo_sangati', 'bo_bimba', 'bo_karanajala', 'bo_samskara',
  ],
  bo_anveshana: [
    'bo_sangati', 'bo_karanajala', 'bo_samskara', 'bo_drishti',
    'bo_bimba', 'bo_laksana',
  ],
  ka_kalasutra: ['ka_yojaka', 'ka_sangam', 'bo_laksana'],
  ka_sangam: [
    'ka_yojaka', 'ka_dasha_kala', 'ka_gochara', 'ka_muhurta_seva',
    'bo_laksana', 'ga_dashas', 'ga_strength', 'ga_positions',
    'ga_tajaka', 'bg_transit_rules',
  ],
  ka_vighnakara: ['ka_sangam', 'ka_gochara', 'ka_muhurta_seva', 'ga_positions'],
  ka_jivana_parva: [
    'ka_kala_darshana', 'ka_dasha_kala', 'ka_sangam', 'ka_yojaka',
    'ga_dashas',
  ],
  ka_bhavishya_lekha: [
    'ka_kala_darshana', 'ka_vighnakara', 'ka_sangam', 'bo_laksana',
  ],
  ka_vedha_gochara: [
    'ga_positions', 'bg_ephemeris', 'bg_transit_rules',
    'bg_sarvatobhadra_grid', 'bg_vedha_malefic_scale',
    'bg_phaladeepika_latta',
  ],
  ph_nimitta: [
    'ka_sangam', 'ka_bhavishya_lekha', 'bo_bimba', 'bo_samskara',
    'bo_karanajala', 'bo_sangati', 'bo_anveshana', 'bo_cgm_paths',
    'bo_laksana',
  ],
  ph_muhurta: [
    'ph_nimitta', 'ka_kalasutra', 'ga_panchanga', 'ka_vighnakara',
    'ga_condition', 'ka_gochara', 'ga_positions', 'ka_sangam',
  ],
  ph_pratikara: ['ph_nimitta', 'bo_upaya', 'ka_vighnakara', 'ka_sangam'],
  ph_suddha_sodhana: ['ph_sodhana', 'ph_nimitta'],
  ph_phaladesa: [
    'ph_nimitta', 'ph_muhurta', 'ph_pratikara', 'ph_suddha_sodhana',
    'ph_sankrama', 'ph_pramana', 'bo_laksana',
  ],
  mi_bhavisya: [
    'ph_pramana', 'ph_nimitta', 'ph_phaladesa', 'mi_kula',
    'mi_jivanaghatana', 'bo_laksana',
  ],
  mi_adhilepa: [
    'mi_gunanaka', 'bo_laksana', 'ka_sangam', 'ph_nimitta',
    'ga_positions',
  ],
  mi_sambandha: ['mi_pramana', 'mi_pariksha', 'mi_bhavisya'],
}

// L0 dependency-contract corrections. These edges ensure a downstream writer
// cannot be planned before the L0 asset that supplies its source contract.
const L0_CONTRACT_DEPENDENCIES: Record<string, string[]> = {
  ga_panchanga: ['ga_positions', 'bg_panchanga'],
  bg_class_lifetime_counts: ['bg_ghatana'],
  ga_prashna: ['ga_positions', 'bg_prashna_rules'],
  ga_vastu: ['ga_condition', 'bg_vastu_directions'],
}

describe('asset_registry_seed — post-626 DAG parity', () => {
  const assetsById = new Map(ASSETS.map((asset) => [asset.asset_id, asset]))

  it('has the complete 128-identity post-626 registry seed', () => {
    expect(ASSETS).toHaveLength(128)
    expect(assetsById.size).toBe(128)
  })

  it('pins all 24 substantive migration-governed dependency arrays', () => {
    expect(Object.keys(POST_626_DEPENDENCIES)).toHaveLength(24)

    for (const [assetId, dependencies] of Object.entries(POST_626_DEPENDENCIES)) {
      expect(assetsById.get(assetId)?.depends_on, assetId).toEqual(dependencies)
    }
  })

  it('pins the canonical order for the set-equal ga_structural dependencies', () => {
    expect(assetsById.get('ga_structural')?.depends_on).toEqual([
      'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions',
      'ga_sensitive', 'ga_strength', 'ga_vargas',
    ])
  })

  it('pins the four L0 upstream contracts required by downstream assets', () => {
    expect(Object.keys(L0_CONTRACT_DEPENDENCIES)).toHaveLength(4)

    for (const [assetId, dependencies] of Object.entries(L0_CONTRACT_DEPENDENCIES)) {
      expect(assetsById.get(assetId)?.depends_on, assetId).toEqual(dependencies)
    }
  })

  it('uses the ga_vastu registry asset id for the Vastu map table contract', () => {
    expect(assetsById.get('ga_vastu')).toMatchObject({
      target_table: 'ga_vastu_planet_direction_map',
      depends_on: ['ga_condition', 'bg_vastu_directions'],
    })
    expect(assetsById.has('ga_vastu_planet_direction_map')).toBe(false)
  })

  it('includes the migration-owned static citation-resolution asset', () => {
    expect(assetsById.get('bg_gochara_citation_resolution')).toMatchObject({
      layer: 'brahmagyan',
      sort_order: 80,
      storage_type: 'postgres_table',
      target_table: 'bg_gochara_citation_resolution',
      target_floor: 14,
      scope: 'global',
      is_active: true,
      catalog_status: 'CURRENT',
      asset_kind: 'data',
      depends_on: ['bg_texts'],
      has_writer: false,
      has_substeps: false,
      writer_timeout_seconds: 60,
    })

    expect(assetRegistryWriterGovernance(
      assetsById.get('bg_gochara_citation_resolution')!,
    )).toEqual([false, false, 60])
  })

  it('never overwrites migration-governed dependencies during a conflict update', () => {
    expect(ASSET_REGISTRY_UPSERT_SQL).toContain(
      'depends_on = asset_registry.depends_on',
    )
    expect(ASSET_REGISTRY_UPSERT_SQL).not.toContain(
      'depends_on = EXCLUDED.depends_on',
    )
  })

  it('preserves migration-governed writer metadata during a conflict update', () => {
    expect(ASSET_REGISTRY_UPSERT_SQL).toContain(
      'has_writer = asset_registry.has_writer',
    )
    expect(ASSET_REGISTRY_UPSERT_SQL).toContain(
      'has_substeps = asset_registry.has_substeps',
    )
    expect(ASSET_REGISTRY_UPSERT_SQL).toContain(
      'writer_timeout_seconds = asset_registry.writer_timeout_seconds',
    )
    expect(ASSET_REGISTRY_UPSERT_SQL).not.toMatch(
      /(?:has_writer|has_substeps|writer_timeout_seconds) = EXCLUDED/,
    )
  })
})
