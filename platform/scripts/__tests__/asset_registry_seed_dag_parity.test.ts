import { readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import {
  assetRegistryWriterGovernance,
  ASSET_REGISTRY_UPSERT_SQL,
  ASSETS,
} from '../seed/asset_registry_seed'

// Production at migration 615 plus the deterministic dependency rewrites in
// migrations 619, 626, and 1030, plus the direct read edges declared by
// migration 1210 (Suvarna Track I; each is appended after the pre-existing
// edges and marked below). These are the 28 rows whose dependency sets
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
    'ga_yoga', // migration 1253 (ga_yoga_firings read, bo_laksana.py)
  ],
  bo_bimba: [
    'bo_laksana', 'bo_sudarshana', 'bo_nakshatra_semantic',
    'bo_arudha', 'bo_special_lagna', 'bo_vargottama_dhana',
  ],
  bo_karanajala: [
    'bo_laksana', 'bo_bimba', 'ga_positions', 'bo_sudarshana',
    'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
    'bo_vargottama_dhana',
    'ga_vichara', // migration 1210 (chart_vichara read, bo_karanajala.py)
  ],
  bo_pratijna: [
    'bo_laksana', 'bo_sangati',
    'ga_vargas', // migration 1210 (chart_divisionals read, chart_reader_v4.py)
    'ga_fact_identity', // migration 1333 (chart_fact_identity read, chart_reader_v4.py)
  ],
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
    'bo_bimba', 'ga_vichara', // migration 1210 (cgm_nodes + chart_vichara reads, bo_laksana.py rerank writer)
  ],
  ka_kalasutra: [
    'ka_yojaka', 'ka_sangam', 'bo_laksana',
    'ga_dashas', // migration 1210 (chart_dashas read via ka_temporal date_resolver)
  ],
  ka_sangam: [
    'ka_yojaka', 'ka_dasha_kala', 'ka_gochara', 'ka_muhurta_seva',
    'bo_laksana', 'ga_dashas', 'ga_strength', 'ga_positions',
    'ga_tajaka', 'bg_transit_rules',
  ],
  ka_vighnakara: [
    'ka_sangam', 'ka_gochara', 'ka_muhurta_seva', 'ga_positions',
    'ga_dashas', // migration 1210 (chart_dashas read via ka_temporal date_resolver)
  ],
  ka_jivana_parva: [
    'ka_kala_darshana', 'ka_dasha_kala', 'ka_sangam', 'ka_yojaka',
    'ga_dashas',
  ],
  ka_bhavishya_lekha: [
    'ka_kala_darshana', 'ka_vighnakara', 'ka_sangam', 'bo_laksana',
  ],
  // Migration 1360 (SS N-430) RETIRES bg_sarvatobhadra_grid in the live registry and removes it from ka_vedha_gochara.depends_on. The seed row
  // is deliberately NOT edited (hashed census source): the seed upsert never rewrites depends_on of an existing row and keeps a RETIRED row
  // RETIRED / inactive, so the seed literal below is the pre-1360 set and the live registry is this set minus bg_sarvatobhadra_grid.
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
// Pravāha A2.5 (steward-directed, PR #2799): ka_gochara_v4_41_candidate is a
// candidate-only writer, is_active: false in the seed (inert to all planners
// — runPreparation.ts:183 / recalibrationEnqueue.ts:141 never select it) and
// NOT an elevation-denominator identity; it ships so the steward dispatch can
// stage its one governed run.
// Pravāha A5.3 (steward ruling M20261001T014547-357e, pins 1-2):
// ka_gochara_v5 is a registered INERT writer skeleton, is_active: false in
// the seed (inert to all planners — runPreparation.ts:183 /
// recalibrationEnqueue.ts:141 never select it) and NOT an
// elevation-denominator identity; it ships so registration conformance can be
// proven while the geometry/solver stays blocked pending steward pins 3-7.
const SUPPORTING_WRITER_IDS = ['bo_grounding', 'ka_gochara_v4_41_candidate', 'ka_gochara_v5'] as const

const SHARED_MSR_DAG_MIGRATION = readFileSync(
  new URL('../../migrations/1030_nirmana_l2_shared_msr_consumer_dependencies.sql', import.meta.url),
  'utf8',
)

describe('asset_registry_seed — migration-governed DAG parity', () => {
  const assetsById = new Map(ASSETS.map((asset) => [asset.asset_id, asset]))

  it('has the complete 129-identity registry seed: the 128 of migration 626 plus ga_fact_identity (migration 1333) (+ ruled supporting writers)', () => {
    const denominatorAssets = ASSETS.filter(
      (asset) => !SUPPORTING_WRITER_IDS.includes(asset.asset_id as (typeof SUPPORTING_WRITER_IDS)[number]),
    )
    // Migration 1333: ga_fact_identity is an ordinary build asset (a registered writer that bo_pratijna depends on), NOT a supporting writer: a
    // supporting writer cannot be a dependency of a denominator asset (the elevation manifest requires every dependency to be in it).
    // This pin moved 128 -> 129 on purpose; it is the denominator change SS must rule on (successor elevation definition).
    expect(denominatorAssets).toHaveLength(129)
    expect(assetsById.size).toBe(129 + SUPPORTING_WRITER_IDS.length)
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

  it('carries the four pre-S-L1 L1 edges of migration 1226 (ordered as the migration appends them)', () => {
    expect(assetsById.get('ga_dashas')?.depends_on).toEqual([
      'ga_positions',
      'ga_sensitive', 'ga_vargas', // migration 1226 (karaka assignments; chart_divisionals)
    ])
    expect(assetsById.get('ga_yoga')?.depends_on).toEqual([
      'ga_structural', 'ga_dashas',
      'ga_vargas', // migration 1226 (D9 via ga_structural_writer._load_varga_positions)
    ])
    expect(assetsById.get('ga_vargas')?.depends_on).toEqual([
      'ga_positions',
      'ga_sensitive', // migration 1226 (kn_rao_rahu_included karaka assignments; N-69, S-L1)
    ])
    // The two L2 edges (bo_laksana += ga_yoga, bo_upaya += bo_bimba) are migration 1253's, not this migration's.
    expect(assetsById.get('ga_sensitive')?.depends_on).toEqual(['ga_positions', 'bg_reference'])
  })

  it('pins the canonical order for the set-equal ga_structural dependencies', () => {
    expect(assetsById.get('ga_structural')?.depends_on).toEqual([
      'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions',
      'ga_sensitive', 'ga_strength', 'ga_vargas',
    ])
  })

  it('carries the two L2 pre-S-L2 edges of migration 1253 (ordered as the migration appends them)', () => {
    expect(assetsById.get('bo_upaya')?.depends_on).toEqual([
      'bo_laksana', 'bo_sangati', 'ga_structural', 'ga_dashas', 'bo_cgm_motifs',
      'bo_bimba', // migration 1253 (bodha_cgm_nodes join, bo_upaya.py)
    ])
    // bo_laksana += ga_yoga is pinned in MIGRATION_GOVERNED_DEPENDENCIES above. The four L1 edges are migration
    // 1226's (a separate PR); this PR's seed must not carry them.
    expect(assetsById.get('ga_yoga')?.depends_on).not.toContain('bo_laksana')
    expect(assetsById.get('bo_bimba')?.depends_on).not.toContain('bo_upaya')
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
      'ga_vichara', // migration 1210
    ])
    expect(rerank?.depends_on).toEqual([
      'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
      'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
      'bo_vargottama_dhana',
      'bo_bimba', 'ga_vichara', // migration 1210
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

  it('includes the dispatchable static citation-resolution asset', () => {
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
      has_writer: true,
      has_substeps: false,
      writer_timeout_seconds: 60,
    })

    expect(assetRegistryWriterGovernance(
      assetsById.get('bg_gochara_citation_resolution')!,
    )).toEqual([true, false, 60])
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
  it('keeps migration 1360 (retire bg_sarvatobhadra_grid) durable across a routine re-seed', () => {
    // The seed row of bg_sarvatobhadra_grid stays (hashed census source), so a re-seed MUST NOT resurrect the retired row or restore the edge:
    // depends_on is never rewritten (asserted above), a RETIRED catalog_status is preserved, and is_active follows a RETIRED row.
    expect(ASSET_REGISTRY_UPSERT_SQL).toMatch(/is_active = CASE WHEN asset_registry\.catalog_status = 'RETIRED'\s+THEN asset_registry\.is_active/)
    expect(ASSET_REGISTRY_UPSERT_SQL).toMatch(/WHEN asset_registry\.catalog_status = 'RETIRED'\s+THEN asset_registry\.catalog_status/)
    expect(ASSET_REGISTRY_UPSERT_SQL).not.toMatch(/data_disposition|superseded_by/)    // the seed never writes the lifecycle columns 1360 sets
    const migration = readFileSync(new URL('../../migrations/1360_retire_bg_sarvatobhadra_grid.sql', import.meta.url), 'utf8')
    expect(migration).toContain("catalog_status = 'RETIRED'")
    expect(migration).toContain('array_remove(depends_on, c_grid)')
    // the seed literal is the pre-1360 set; only ka_vedha_gochara names the grid as a dependency
    const dependents = ASSETS.filter((asset) => asset.depends_on.includes('bg_sarvatobhadra_grid')).map((asset) => asset.asset_id)
    expect(dependents).toEqual(['ka_vedha_gochara'])
  })
})
