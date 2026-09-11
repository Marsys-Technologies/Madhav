import { readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import {
  assetRegistryWriterGovernance,
  ASSET_REGISTRY_UPSERT_SQL,
  ASSETS,
} from '../seed/asset_registry_seed'

// Production at migration 615 plus the deterministic dependency rewrites in
// migrations 619, 626, and 1030. These are the 28 rows whose dependency sets
// are pinned here (migration 1030 supersedes bo_sangati's earlier two-edge
// entry without changing this denominator).
const MIGRATION_GOVERNED_DEPENDENCIES: Record<string, string[]> = {
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
  bo_bimba: [
    'bo_laksana', 'bo_sudarshana', 'bo_nakshatra_semantic',
    'bo_arudha', 'bo_special_lagna', 'bo_vargottama_dhana',
  ],
  bo_karanajala: [
    'bo_laksana', 'bo_bimba', 'ga_positions', 'bo_sudarshana',
    'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
    'bo_vargottama_dhana',
  ],
  bo_pratijna: ['bo_laksana', 'bo_sangati'],
  bo_samskara: [
    'bo_arudha', 'bo_laksana', 'bo_nakshatra_semantic',
    'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana',
  ],
  bo_sangati: [
    'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
    'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
    'bo_vargottama_dhana', 'bo_laksana_rerank',
  ],
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
  bo_grounding: [
    'ga_yoga', 'bo_laksana', 'bo_sudarshana',
    'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
    'bo_vargottama_dhana',
  ],
  bo_laksana_rerank: [
    'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
    'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
    'bo_vargottama_dhana',
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
}

// D-NATIVE-11 (#2258, native-ruled 2026-09-07): supporting infrastructure
// writers register in the DAG (so they need a seed/registry row) but are NOT
// elevation-denominator assets — the 128-identity below deliberately excludes
// them and stays exactly 128. Adding a name here requires its own native
// ruling; adding a seed row without listing it here still fails the identity.
const SUPPORTING_WRITER_IDS = ['bo_grounding'] as const

const SHARED_MSR_DAG_MIGRATION = readFileSync(
  new URL('../../migrations/1030_nirmana_l2_shared_msr_consumer_dependencies.sql', import.meta.url),
  'utf8',
)

describe('asset_registry_seed — migration-governed DAG parity', () => {
  const assetsById = new Map(ASSETS.map((asset) => [asset.asset_id, asset]))

  it('has the complete 128-identity post-626 registry seed (+ ruled supporting writers)', () => {
    const denominatorAssets = ASSETS.filter(
      (asset) => !SUPPORTING_WRITER_IDS.includes(asset.asset_id as (typeof SUPPORTING_WRITER_IDS)[number]),
    )
    expect(denominatorAssets).toHaveLength(128)
    expect(assetsById.size).toBe(128 + SUPPORTING_WRITER_IDS.length)
    for (const supportingId of SUPPORTING_WRITER_IDS) {
      expect(assetsById.has(supportingId), `${supportingId} must have a seed row (it registers in the DAG)`).toBe(true)
    }
  })

  it('pins all 28 substantive migration-governed dependency arrays', () => {
    expect(Object.keys(MIGRATION_GOVERNED_DEPENDENCIES)).toHaveLength(28)

    for (const [assetId, dependencies] of Object.entries(MIGRATION_GOVERNED_DEPENDENCIES)) {
      expect(assetsById.get(assetId)?.depends_on, assetId).toEqual(dependencies)
    }
  })

  it('pins the canonical order for the set-equal ga_structural dependencies', () => {
    expect(assetsById.get('ga_structural')?.depends_on).toEqual([
      'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions',
      'ga_sensitive', 'ga_strength', 'ga_vargas',
    ])
  })

  it('preserves the migration-governed collision-free Bodha order', () => {
    expect(assetsById.get('bo_cgm_motifs')?.sort_order).toBe(4)
    expect(assetsById.get('bo_cgm_paths')?.sort_order).toBe(5)
    expect(assetsById.get('bo_chart_gestalt')?.sort_order).toBe(11)
    expect(assetsById.get('bo_yantra_mechanism')?.sort_order).toBe(15)
    expect(assetsById.get('bo_pratijna')?.sort_order).toBe(18)
    expect(assetsById.get('bo_nakshatra_semantic')?.sort_order).toBe(20)

    const seen = new Map<number, string>()
    for (const asset of ASSETS.filter((candidate) => candidate.layer === 'bodha')) {
      const previous = seen.get(asset.sort_order)
      expect(previous, `sort_order ${asset.sort_order}: ${previous} / ${asset.asset_id}`).toBeUndefined()
      seen.set(asset.sort_order, asset.asset_id)
    }
  })

  it('runs every shared-MSR consumer after the complete producer set', () => {
    const sangati = assetsById.get('bo_sangati')
    const insertProducers = [
      'bo_laksana', 'bo_sudarshana', 'bo_nakshatra_semantic',
      'bo_arudha', 'bo_special_lagna', 'bo_vargottama_dhana',
    ]
    const karanajala = assetsById.get('bo_karanajala')
    const bimba = assetsById.get('bo_bimba')
    const samskara = assetsById.get('bo_samskara')
    const grounding = assetsById.get('bo_grounding')
    const rerank = assetsById.get('bo_laksana_rerank')

    expect(bimba?.depends_on).toEqual(insertProducers)
    expect(samskara?.depends_on).toEqual([
      'bo_arudha', 'bo_laksana', 'bo_nakshatra_semantic',
      'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana',
    ])
    expect(grounding?.depends_on).toEqual([
      'ga_yoga', ...insertProducers,
    ])
    expect(karanajala?.depends_on).toEqual([
      'bo_laksana', 'bo_bimba', 'ga_positions', 'bo_sudarshana',
      'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
      'bo_vargottama_dhana',
    ])
    expect(rerank?.depends_on).toEqual([
      'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
      'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
      'bo_vargottama_dhana',
    ])
    expect(sangati?.depends_on).toEqual([
      'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
      'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
      'bo_vargottama_dhana', 'bo_laksana_rerank',
    ])
    expect(bimba?.sort_order).toBe(24)
    expect(grounding?.sort_order).toBe(25)
    expect(samskara?.sort_order).toBe(26)
    expect(karanajala?.sort_order).toBe(27)
    expect(rerank?.sort_order).toBe(28)
    expect(sangati?.sort_order).toBe(29)

    for (const assetId of insertProducers) {
      const upstream = assetsById.get(assetId)
      expect(upstream?.target_table, assetId).toBe('bodha_msr_signals')
      expect(upstream?.sort_order, assetId).toBeLessThan(bimba!.sort_order)
    }
    expect(bimba?.sort_order).toBeLessThan(karanajala!.sort_order)
    expect(samskara?.sort_order).toBeLessThan(karanajala!.sort_order)
    expect(karanajala?.sort_order).toBeLessThan(rerank!.sort_order)
    expect(rerank?.sort_order).toBeLessThan(sangati!.sort_order)

    const correctedOrders = new Set([
      bimba?.sort_order, grounding?.sort_order, samskara?.sort_order,
      karanajala?.sort_order, rerank?.sort_order, sangati?.sort_order,
    ])
    const collidingBodhaAssets = ASSETS.filter(
      (asset) => asset.layer === 'bodha'
        && ![
          'bo_bimba', 'bo_grounding', 'bo_samskara', 'bo_karanajala',
          'bo_laksana_rerank', 'bo_sangati',
        ].includes(asset.asset_id)
        && correctedOrders.has(asset.sort_order),
    )
    expect(collidingBodhaAssets.map((asset) => asset.asset_id)).toEqual([])
  })

  it('keeps the bo_laksana_rerank to bo_sangati upstream closure acyclic', () => {
    const visited = new Set<string>()
    const active = new Set<string>()

    const visit = (assetId: string): void => {
      if (active.has(assetId)) throw new Error(`dependency cycle at ${assetId}`)
      if (visited.has(assetId)) return
      active.add(assetId)
      for (const dependency of assetsById.get(assetId)?.depends_on ?? []) visit(dependency)
      active.delete(assetId)
      visited.add(assetId)
    }

    expect(() => visit('bo_sangati')).not.toThrow()
    expect(visited.has('bo_laksana_rerank')).toBe(true)
  })

  it('migrates the live registry to the same shared-MSR dependency order', () => {
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_bimba'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_samskara'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_karanajala'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_laksana_rerank'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_sangati'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain("WHERE asset_id = 'bo_grounding'")
    expect(SHARED_MSR_DAG_MIGRATION).toContain('sort_order = 24')
    expect(SHARED_MSR_DAG_MIGRATION).toContain('sort_order = 29')
    expect(SHARED_MSR_DAG_MIGRATION).not.toMatch(/\b(?:INSERT\s+INTO|DELETE\s+FROM)\s+asset_registry\b/i)
  })

  it('pins the three L0 upstream contracts required by downstream assets', () => {
    expect(Object.keys(L0_CONTRACT_DEPENDENCIES)).toHaveLength(3)

    for (const [assetId, dependencies] of Object.entries(L0_CONTRACT_DEPENDENCIES)) {
      expect(assetsById.get(assetId)?.depends_on, assetId).toEqual(dependencies)
    }
  })

  it('keeps ga_vastu dependent only on the condition data it reads', () => {
    expect(assetsById.get('ga_vastu')).toMatchObject({
      target_table: 'ga_vastu_planet_direction_map',
      depends_on: ['ga_condition'],
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
