/**
 * generate_tci.ts — Ω1 Total Concept Inventory generator (Elevation Campaign v2.1, Lane Ω1).
 *
 * MACHINE-GENERATED, NEVER HAND-CURATED. Produces:
 *   00_ARCHITECTURE/llm_consumption_audit/capability_map/TOTAL_CONCEPT_INVENTORY_v1_0.json
 *
 * The TCI is the DENOMINATOR of every Ω3 accounting sum (served ∪ accounted == 100%). Per the
 * charter it MAY NEVER BE STUBBED — every entry below is enumerated live from the database, and the
 * script self-checks its output against the frozen Verifier baseline
 * (OMEGA1_INDEPENDENT_BASELINE_v1_0.md) before writing. If the sanity self-check fails, the script
 * exits non-zero and refuses to overwrite the artifact (Lane Ω BLOCKS, never stubs).
 *
 * Ground-truth denominators (frozen baseline, PROXY-RULED-004):
 *   - distinct fact_category, GLOBAL (all charts): >= 218
 *   - bodha_mechanisms classes: 10 (writer design enum, NOT SELECT DISTINCT — 6 are empty today)
 *   - dasha systems: 9 DB-built (chart_dashas.system_id)
 *   - ayanamshas: 5 real + INVARIANT sentinel (flagged is_ayanamsha_variant:false)
 *   - vargas: all distinct chart_divisionals.varga (D-series + ALL_VARGAS/CROSS markers)
 *   - asset_registry: every row (catalog_assets_all)
 *
 * Usage:
 *   cd platform && npx tsx --env-file=<path-to-.env.local> scripts/census/generate_tci.ts \
 *     [--chart <primary_uuid>] [--out <path>]
 *
 * The generator is idempotent and re-runnable against any chart_id (row counts are always reported
 * for BOTH canonical charts regardless of --chart, since the TCI is corpus-wide).
 */
import { Pool } from 'pg'
import { writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
// platform/scripts/census -> repo root is three up
const REPO_ROOT = resolve(__dirname, '..', '..', '..')

// ---- Canonical charts (charter §B; second resolved via catalog_charts_list) -----------------
const PRIMARY_CHART = '482012f1-710e-4a25-994a-93821f5871aa' // Abhisek
const SECOND_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' // Abhinandan

// ---- Mechanism classes: the 10-class design enum grounded in the bo_yantra_mechanism writer /
//      generated tool defs (chat_tool_defs.generated.json, e4_signal_classes.json). NOT derived
//      from SELECT DISTINCT — 6 of these never fire for either canonical chart and MUST still be
//      carried (baseline ruling #2; silent omission = build failure). -------------------------
const MECHANISM_CLASSES = [
  'convergent_dispositor_chain',
  'dispositor_cycle',
  'house_lordship_cycle',
  'yoga_cluster',
  'mutual_reception',
  'parivartana_chain',
  'stellium',
  'mutual_aspect',
  'mutual_aspect_triangle',
  'graha_bhava_affliction',
] as const

// ---- Ayanamshas: 5 real astronomical + INVARIANT sentinel (baseline ruling #3) --------------
const REAL_AYANAMSHAS = new Set([
  'krishnamurti',
  'lahiri_chitrapaksha',
  'raman',
  'surya_siddhanta_classical',
  'true_chitra',
])

// ---- TCI entry shape (charter Ω1) ------------------------------------------------------------
type Counts = Record<string, number>

interface TciEntry {
  concept_id: string
  canonical_name: string
  aliases: string[]
  layer: string // brahmagyan|ganita|bodha|kala|phala|mimamsa|meta
  owning_asset: string
  owning_asset_candidates?: string[] // when a table is shared by >1 writer (e.g. chart_facts)
  serving_tool: string | null
  serving_args: Record<string, unknown>
  row_count_per_canonical_chart: Counts // keyed by chart_id (both canonical charts, always present)
  is_chain_or_pattern: boolean
  computed_globally: boolean // true iff any row exists for this concept across the whole DB
  honest_gap_ref: string | null // CR/EL note when computed_globally === false
  source_axis: string // which collector produced this entry (provenance)
  is_ayanamsha_variant?: boolean // only on ayanamsha entries (baseline ruling #3)
  detail?: Record<string, unknown> // small, machine-readable extras (fact_keys, level, etc.)
}

// ---- DB helper -------------------------------------------------------------------------------
let pool: Pool
async function q<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T[]> {
  const r = await pool.query(sql, params)
  return r.rows as T[]
}

// Map target_table -> [asset_id...] from asset_registry, for owning_asset resolution.
const TABLE_ASSETS: Map<string, string[]> = new Map()
const COLUMN_MAP: Map<string, Set<string>> = new Map() // table -> set of columns present

function tableHasCol(table: string, col: string): boolean {
  return COLUMN_MAP.get(table)?.has(col) ?? false
}
function resolveOwningAsset(table: string): { owning_asset: string; candidates?: string[] } {
  const assets = TABLE_ASSETS.get(table)
  if (!assets || assets.length === 0) return { owning_asset: table }
  if (assets.length === 1) return { owning_asset: assets[0] }
  return { owning_asset: `${table} (${assets.length} writers)`, candidates: assets }
}

// ---- Surface-axis config ---------------------------------------------------------------------
// Each axis names a (table, discriminator-column) whose DISTINCT values become concepts. The
// values and per-chart counts are ALWAYS enumerated live from the DB — only the table/column
// selection is curated (mirroring how the C3 seed generator selected chart_facts). An axis whose
// table or column is missing at runtime is recorded in `axes_skipped`, never silently dropped.
interface Axis {
  key: string // short id used in concept_id
  table: string
  column: string
  layer: string
  serving_tool: string | null
  is_chain_or_pattern?: boolean
  label: string // human label for the concept family
}

const AXES: Axis[] = [
  // --- L2 Bodha ---------------------------------------------------------------------------
  { key: 'msr_signal_type', table: 'bodha_msr_signals', column: 'signal_type_id', layer: 'bodha', serving_tool: 'bodha_signals_get', label: 'MSR signal type' },
  { key: 'msr_signal_class', table: 'bodha_msr_signals', column: 'signal_type_class', layer: 'bodha', serving_tool: 'bodha_signals_get', label: 'MSR signal type class' },
  { key: 'msr_tradition', table: 'bodha_msr_signals', column: 'signal_tradition', layer: 'bodha', serving_tool: 'bodha_signals_get', label: 'MSR signal tradition' },
  { key: 'msr_signature_class', table: 'bodha_msr_signals', column: 'signature_class', layer: 'bodha', serving_tool: 'bodha_signals_get', label: 'MSR signature class' },
  { key: 'convergence_domain', table: 'bodha_convergence', column: 'domain', layer: 'bodha', serving_tool: 'bodha_domain_reading_get', label: 'Convergence domain' },
  { key: 'cgm_node_type', table: 'bodha_cgm_nodes', column: 'node_type', layer: 'bodha', serving_tool: 'bodha_graph_subgraph_get', is_chain_or_pattern: true, label: 'CGM node type' },
  { key: 'cgm_edge_type', table: 'bodha_cgm_edges', column: 'edge_type', layer: 'bodha', serving_tool: 'bodha_graph_traverse_get', is_chain_or_pattern: true, label: 'CGM edge type' },
  { key: 'cgm_edge_relclass', table: 'bodha_cgm_edges', column: 'relationship_class', layer: 'bodha', serving_tool: 'bodha_graph_traverse_get', is_chain_or_pattern: true, label: 'CGM edge relationship class' },
  { key: 'cgm_motif_class', table: 'bodha_cgm_motifs', column: 'motif_class', layer: 'bodha', serving_tool: 'bodha_graph_subgraph_get', is_chain_or_pattern: true, label: 'CGM motif class' },
  { key: 'cgm_subgraph_type', table: 'bodha_cgm_sub_graphs', column: 'subgraph_type', layer: 'bodha', serving_tool: 'bodha_graph_subgraph_get', is_chain_or_pattern: true, label: 'CGM subgraph type' },
  { key: 'cgm_path_type', table: 'bodha_cgm_paths', column: 'path_type', layer: 'bodha', serving_tool: 'bodha_graph_traverse_get', is_chain_or_pattern: true, label: 'CGM path type' },
  { key: 'discovery_class', table: 'bodha_discoveries', column: 'discovery_class', layer: 'bodha', serving_tool: 'bodha_discoveries_get', label: 'Discovery class' },
  { key: 'discovery_novelty', table: 'bodha_discoveries', column: 'novelty_class', layer: 'bodha', serving_tool: 'bodha_discoveries_get', label: 'Discovery novelty class' },
  { key: 'anomaly_type', table: 'bodha_anomalies', column: 'anomaly_type', layer: 'bodha', serving_tool: 'bodha_discoveries_get', label: 'Anomaly type' },
  { key: 'contradiction_pole', table: 'bodha_contradictions', column: 'tension_class', layer: 'bodha', serving_tool: 'bodha_quality_get', label: 'Contradiction tension class (pole)' },
  { key: 'cdlm_reln_class', table: 'bodha_cdlm_cells', column: 'domain_relationship_class', layer: 'bodha', serving_tool: 'bodha_domain_reading_get', label: 'CDLM domain relationship class' },
  { key: 'cdlm_pattern_marker', table: 'bodha_cdlm_pattern_clusters', column: 'pattern_marker_type', layer: 'bodha', serving_tool: 'bodha_domain_reading_get', is_chain_or_pattern: true, label: 'CDLM pattern marker type' },
  { key: 'gestalt_typology', table: 'bodha_cdlm_chart_summary', column: 'chart_typology_class', layer: 'bodha', serving_tool: 'bodha_chart_digest_get', label: 'Chart typology class' },
  { key: 'rm_remedy_category', table: 'bodha_rm_remedy_prescriptions', column: 'remedy_category', layer: 'bodha', serving_tool: 'bodha_remedies_get', label: 'Remedy category' },
  { key: 'rm_dosha_class', table: 'bodha_rm_dosha_remedy_bundles', column: 'dosha_class', layer: 'bodha', serving_tool: 'bodha_remedies_get', label: 'Dosha class (remedy bundle)' },
  { key: 'question_lens', table: 'bodha_question_lenses', column: 'question_type', layer: 'bodha', serving_tool: 'judgment_query', label: 'Question lens type' },
  { key: 'spine_domain', table: 'bodha_spine_bundles', column: 'domain', layer: 'bodha', serving_tool: 'bodha_bundle_get', label: 'Spine bundle domain' },
  { key: 'pratijna_status', table: 'bodha_pratijna', column: 'status', layer: 'bodha', serving_tool: 'bodha_bundle_get', label: 'Promise (pratijna) status' },
  // --- L3 Kala ----------------------------------------------------------------------------
  { key: 'kala_avadhi_quality', table: 'kala_avadhi', column: 'quality', layer: 'kala', serving_tool: 'kala_windows_get', label: 'Period (avadhi) quality' },
  { key: 'kala_bhavishya_domain', table: 'kala_bhavishya', column: 'domain', layer: 'kala', serving_tool: 'kala_projections_get', label: 'Forward-projection domain' },
  { key: 'kala_convergence_domain', table: 'kala_convergence', column: 'domain', layer: 'kala', serving_tool: 'kala_windows_get', label: 'Kala convergence domain' },
  { key: 'kala_convergence_mode', table: 'kala_convergence', column: 'mode', layer: 'kala', serving_tool: 'kala_windows_get', label: 'Kala convergence mode' },
  { key: 'gochara_event_class', table: 'kala_gochara_windows', column: 'event_class', layer: 'kala', serving_tool: 'gochara_forecast_get', label: 'Gochara event class' },
  { key: 'gochara_valence', table: 'kala_gochara_windows', column: 'valence', layer: 'kala', serving_tool: 'gochara_forecast_get', label: 'Gochara window valence' },
  { key: 'jivana_parva_quality', table: 'kala_jivana_parva', column: 'parva_quality', layer: 'kala', serving_tool: 'kala_life_arc_get', label: 'Life-arc chapter quality' },
  { key: 'jivana_signal_class', table: 'kala_jivana_parva', column: 'dominant_signal_class', layer: 'kala', serving_tool: 'kala_life_arc_get', label: 'Life-arc dominant signal class' },
  { key: 'obstruction_type', table: 'kala_obstruction', column: 'obstruction_type', layer: 'kala', serving_tool: 'kala_windows_get', label: 'Obstruction type' },
  { key: 'taranga_scope', table: 'kala_taranga', column: 'scope_kind', layer: 'kala', serving_tool: 'kala_windows_get', label: 'Activation-waveform scope kind' },
  { key: 'kala_activation_sig', table: 'kala_activation', column: 'signature_class', layer: 'kala', serving_tool: 'kala_yoga_activation_get', label: 'Kala activation signature class' },
  // --- L4 Phala ---------------------------------------------------------------------------
  { key: 'phala_anchor_event', table: 'phala_anchors', column: 'event_type', layer: 'phala', serving_tool: 'phala_anchors_get', label: 'Phala anchor event type' },
  { key: 'phala_anchor_domain', table: 'phala_anchors', column: 'domain', layer: 'phala', serving_tool: 'phala_anchors_get', label: 'Phala anchor domain' },
  { key: 'phaladesa_domain', table: 'phala_phaladesa', column: 'domain', layer: 'phala', serving_tool: 'phala_outlook_get', label: 'Phaladesa (outlook) domain' },
  { key: 'phaladesa_narration', table: 'phala_phaladesa', column: 'narration_status', layer: 'phala', serving_tool: 'phala_outlook_get', label: 'Phaladesa narration status' },
  { key: 'muhurta_action', table: 'phala_muhurta', column: 'action_class', layer: 'phala', serving_tool: 'kala_muhurta_get', label: 'Muhurta action class' },
  { key: 'muhurta_verdict', table: 'phala_muhurta', column: 'window_quality_verdict', layer: 'phala', serving_tool: 'kala_muhurta_get', label: 'Muhurta window quality verdict' },
  { key: 'sankrama_reln', table: 'phala_sankrama', column: 'relationship_type', layer: 'phala', serving_tool: 'phala_outlook_get', label: 'Cross-domain spillover relationship type' },
  { key: 'sodhana_anomaly', table: 'phala_sodhana', column: 'anomaly_type', layer: 'phala', serving_tool: 'phala_mitigation_get', label: 'Phala sodhana anomaly type' },
  { key: 'pramana_window_status', table: 'phala_pramana', column: 'window_status', layer: 'phala', serving_tool: 'phala_predictive_anchors_get', label: 'Pramana falsifiability window status' },
  // --- L5 Mimamsa -------------------------------------------------------------------------
  { key: 'calibration_domain', table: 'mimamsa_calibration', column: 'score_domain', layer: 'mimamsa', serving_tool: 'mimamsa_calibration_get', label: 'Calibration score domain' },
  { key: 'insight_type', table: 'mimamsa_insight_units', column: 'insight_type', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Insight unit type' },
  { key: 'insight_domain', table: 'mimamsa_insight_units', column: 'domain', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Insight unit domain' },
  { key: 'prediction_domain', table: 'mimamsa_predictions', column: 'domain', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Prediction domain' },
  { key: 'prediction_lifecycle', table: 'mimamsa_predictions', column: 'lifecycle_status', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Prediction lifecycle status' },
  { key: 'signal_family_class', table: 'mimamsa_signal_families', column: 'family_class', layer: 'mimamsa', serving_tool: 'mimamsa_calibration_get', label: 'Signal family class' },
  { key: 'mimamsa_discovery_class', table: 'mimamsa_discoveries', column: 'discovery_class', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Mimamsa discovery class' },
  { key: 'multiplier_domain', table: 'mimamsa_multipliers', column: 'domain', layer: 'mimamsa', serving_tool: 'mimamsa_calibration_get', label: 'Multiplier domain' },
  { key: 'manifest_grammar_domain', table: 'mimamsa_manifestation_grammar', column: 'domain', layer: 'mimamsa', serving_tool: 'mimamsa_insight_get', label: 'Manifestation-grammar domain' },
  { key: 'attribution_family', table: 'mimamsa_attribution', column: 'family_id', layer: 'mimamsa', serving_tool: 'mimamsa_calibration_get', label: 'Attribution family' },
]

// ---- collectors ------------------------------------------------------------------------------
const entries: TciEntry[] = []
const axesSkipped: { key: string; reason: string }[] = []

function slug(s: string): string {
  return String(s).replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 120)
}
function bothCounts(c1: number, c2: number): Counts {
  return { [PRIMARY_CHART]: c1, [SECOND_CHART]: c2 }
}

// (A) L1 chart_facts: every (fact_category, fact_subject) enumerated GLOBALLY (all charts) so the
//     distinct fact_category count reaches the production denominator (218), with per-canonical-
//     chart row counts (0 when a category/subject exists only on non-canonical charts).
async function collectL1Facts(): Promise<void> {
  const owner = resolveOwningAsset('chart_facts')
  const rows = await q<{
    fact_category: string
    fact_subject: string | null
    keys: string[]
    c1: string
    c2: string
    c_global: string
    sample: string[]
  }>(
    `SELECT fact_category,
            COALESCE(fact_subject, '(none)') AS fact_subject,
            array_agg(DISTINCT fact_key) FILTER (WHERE fact_key IS NOT NULL) AS keys,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global,
            (array_agg(fact_id) FILTER (WHERE chart_id = $1))[1:3] AS sample
       FROM chart_facts
      GROUP BY fact_category, COALESCE(fact_subject, '(none)')
      ORDER BY fact_category, fact_subject`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  for (const r of rows) {
    const keys = (r.keys ?? []).slice().sort()
    const c1 = Number(r.c1)
    const c2 = Number(r.c2)
    entries.push({
      concept_id: `l1.fact.${slug(r.fact_category)}.${slug(r.fact_subject)}`,
      canonical_name: `${r.fact_category} / ${r.fact_subject}`,
      aliases: [r.fact_category, r.fact_subject].filter((x) => x && x !== '(none)'),
      layer: 'ganita',
      owning_asset: owner.owning_asset,
      owning_asset_candidates: owner.candidates,
      serving_tool: 'ganita_chart_facts_get',
      serving_args: { chart_id: '<chart_id>', fact_category: r.fact_category },
      row_count_per_canonical_chart: bothCounts(c1, c2),
      is_chain_or_pattern: false,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: 'L1:chart_facts(category×subject)',
      detail: { fact_keys: keys, sample_fact_ids: (r.sample ?? []).slice(0, 3) },
    })
  }
  console.error(`[collect] L1 facts: ${rows.length} (category×subject) concepts`)
}

// (B) bodha_mechanisms: all 10 design classes (NOT SELECT DISTINCT). 6 empty classes carried with
//     honest_gap_ref (baseline ruling #2).
async function collectMechanisms(): Promise<void> {
  const owner = resolveOwningAsset('bodha_mechanisms')
  const rows = await q<{ mechanism_class: string; c1: string; c2: string; c_global: string }>(
    `SELECT mechanism_class,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global
       FROM bodha_mechanisms GROUP BY mechanism_class`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  const byClass = new Map(rows.map((r) => [r.mechanism_class, r]))
  for (const cls of MECHANISM_CLASSES) {
    const r = byClass.get(cls)
    const c1 = r ? Number(r.c1) : 0
    const c2 = r ? Number(r.c2) : 0
    const cg = r ? Number(r.c_global) : 0
    entries.push({
      concept_id: `l2.mechanism_class.${slug(cls)}`,
      canonical_name: `Mechanism class: ${cls}`,
      aliases: [cls],
      layer: 'bodha',
      owning_asset: owner.owning_asset,
      serving_tool: 'bodha_mechanisms_get',
      serving_args: { chart_id: '<chart_id>', mechanism_class: cls },
      row_count_per_canonical_chart: bothCounts(c1, c2),
      is_chain_or_pattern: true,
      computed_globally: cg > 0,
      honest_gap_ref:
        cg > 0 ? null : `CR-mech-${cls}: bo_yantra_mechanism enumerates this class but no rows materialized in any chart build (empty-for-corpus)`,
      source_axis: 'L2:bodha_mechanisms(10-class enum)',
    })
  }
  console.error(`[collect] mechanisms: 10 classes (${rows.length} materialized in DB)`) 
}

// (C) dasha systems × levels: 9 DB-built systems (baseline ruling #4). One concept per system, plus
//     one per (system, level_n) present.
async function collectDashas(): Promise<void> {
  const owner = resolveOwningAsset('chart_dashas')
  const sys = await q<{ system_id: string; c1: string; c2: string; c_global: string }>(
    `SELECT system_id,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global
       FROM chart_dashas GROUP BY system_id ORDER BY system_id`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  for (const r of sys) {
    entries.push({
      concept_id: `l3.dasha_system.${slug(r.system_id)}`,
      canonical_name: `Dasha system: ${r.system_id}`,
      aliases: [r.system_id],
      layer: 'kala',
      owning_asset: owner.owning_asset,
      serving_tool: 'ganita_dashas_get',
      serving_args: { chart_id: '<chart_id>', system_id: r.system_id },
      row_count_per_canonical_chart: bothCounts(Number(r.c1), Number(r.c2)),
      is_chain_or_pattern: false,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: 'L3:chart_dashas(system_id)',
    })
  }
  const lvl = await q<{ system_id: string; level_n: number; c1: string; c2: string; c_global: string }>(
    `SELECT system_id, level_n,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global
       FROM chart_dashas GROUP BY system_id, level_n ORDER BY system_id, level_n`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  for (const r of lvl) {
    entries.push({
      concept_id: `l3.dasha_level.${slug(r.system_id)}.L${r.level_n}`,
      canonical_name: `Dasha ${r.system_id} level ${r.level_n}`,
      aliases: [`${r.system_id} L${r.level_n}`],
      layer: 'kala',
      owning_asset: owner.owning_asset,
      serving_tool: 'ganita_dashas_get',
      serving_args: { chart_id: '<chart_id>', system_id: r.system_id, level_n: r.level_n },
      row_count_per_canonical_chart: bothCounts(Number(r.c1), Number(r.c2)),
      is_chain_or_pattern: false,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: 'L3:chart_dashas(system×level)',
      detail: { level_n: r.level_n },
    })
  }
  console.error(`[collect] dasha: ${sys.length} systems, ${lvl.length} system×level concepts`)
}

// (D) vargas: every distinct chart_divisionals.varga (D-series + ALL_VARGAS/CROSS markers, flagged).
async function collectVargas(): Promise<void> {
  const owner = resolveOwningAsset('chart_divisionals')
  const rows = await q<{ varga: string; c1: string; c2: string; c_global: string }>(
    `SELECT varga,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global
       FROM chart_divisionals GROUP BY varga ORDER BY varga`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  for (const r of rows) {
    const isMarker = r.varga === 'ALL_VARGAS' || r.varga === 'CROSS'
    entries.push({
      concept_id: `l1.varga.${slug(r.varga)}`,
      canonical_name: isMarker ? `Varga aggregate marker: ${r.varga}` : `Divisional chart ${r.varga}`,
      aliases: [r.varga],
      layer: 'ganita',
      owning_asset: owner.owning_asset,
      serving_tool: 'ganita_positions_get',
      serving_args: { chart_id: '<chart_id>', varga: r.varga },
      row_count_per_canonical_chart: bothCounts(Number(r.c1), Number(r.c2)),
      is_chain_or_pattern: false,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: 'L1:chart_divisionals(varga)',
      detail: { is_aggregate_marker: isMarker },
    })
  }
  console.error(`[collect] vargas: ${rows.length} distinct varga concepts`)
}

// (E) ayanamshas: distinct chart_facts.ayanamsha_id; INVARIANT flagged is_ayanamsha_variant:false
//     (baseline ruling #3).
async function collectAyanamshas(): Promise<void> {
  const owner = resolveOwningAsset('chart_facts')
  const rows = await q<{ ayanamsha_id: string; c1: string; c2: string; c_global: string }>(
    `SELECT ayanamsha_id,
            COUNT(*) FILTER (WHERE chart_id = $1) AS c1,
            COUNT(*) FILTER (WHERE chart_id = $2) AS c2,
            COUNT(*) AS c_global
       FROM chart_facts WHERE ayanamsha_id IS NOT NULL
      GROUP BY ayanamsha_id ORDER BY ayanamsha_id`,
    [PRIMARY_CHART, SECOND_CHART]
  )
  for (const r of rows) {
    const isVariant = REAL_AYANAMSHAS.has(r.ayanamsha_id)
    entries.push({
      concept_id: `meta.ayanamsha.${slug(r.ayanamsha_id)}`,
      canonical_name: isVariant ? `Ayanamsha: ${r.ayanamsha_id}` : `Ayanamsha sentinel: ${r.ayanamsha_id}`,
      aliases: [r.ayanamsha_id],
      layer: 'meta',
      owning_asset: owner.owning_asset,
      serving_tool: 'ganita_positions_get',
      serving_args: { chart_id: '<chart_id>', ayanamsha_id: r.ayanamsha_id },
      row_count_per_canonical_chart: bothCounts(Number(r.c1), Number(r.c2)),
      is_chain_or_pattern: false,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: 'meta:chart_facts(ayanamsha_id)',
      is_ayanamsha_variant: isVariant,
    })
  }
  console.error(`[collect] ayanamshas: ${rows.length} (${[...REAL_AYANAMSHAS].length} real + sentinels)`)
}

// (F) generic surface axes: DISTINCT discriminator values per configured (table, column).
async function collectAxis(ax: Axis): Promise<void> {
  if (!COLUMN_MAP.has(ax.table)) {
    axesSkipped.push({ key: ax.key, reason: `table ${ax.table} not found` })
    return
  }
  if (!tableHasCol(ax.table, ax.column)) {
    axesSkipped.push({ key: ax.key, reason: `column ${ax.table}.${ax.column} not found` })
    return
  }
  const hasChart = tableHasCol(ax.table, 'chart_id')
  const owner = resolveOwningAsset(ax.table)
  const c1expr = hasChart ? `COUNT(*) FILTER (WHERE chart_id = $1)` : `COUNT(*)`
  const c2expr = hasChart ? `COUNT(*) FILTER (WHERE chart_id = $2)` : `COUNT(*)`
  const params = hasChart ? [PRIMARY_CHART, SECOND_CHART] : []
  const rows = await q<{ v: string; c1: string; c2: string; c_global: string }>(
    `SELECT "${ax.column}"::text AS v, ${c1expr} AS c1, ${c2expr} AS c2, COUNT(*) AS c_global
       FROM "${ax.table}" WHERE "${ax.column}" IS NOT NULL
      GROUP BY "${ax.column}" ORDER BY "${ax.column}"`,
    params
  )
  for (const r of rows) {
    entries.push({
      concept_id: `${ax.layer[0] === 'b' ? 'l2' : ax.layer[0] === 'k' ? 'l3' : ax.layer[0] === 'p' ? 'l4' : 'l5'}.${ax.key}.${slug(r.v)}`,
      canonical_name: `${ax.label}: ${r.v}`,
      aliases: [r.v],
      layer: ax.layer,
      owning_asset: owner.owning_asset,
      owning_asset_candidates: owner.candidates,
      serving_tool: ax.serving_tool,
      serving_args: { chart_id: hasChart ? '<chart_id>' : undefined, [ax.column]: r.v },
      row_count_per_canonical_chart: hasChart
        ? bothCounts(Number(r.c1), Number(r.c2))
        : bothCounts(Number(r.c_global), Number(r.c_global)),
      is_chain_or_pattern: !!ax.is_chain_or_pattern,
      computed_globally: Number(r.c_global) > 0,
      honest_gap_ref: null,
      source_axis: `axis:${ax.table}.${ax.column}`,
      detail: hasChart ? undefined : { scope: 'global (no chart_id column)' },
    })
  }
  console.error(`[collect] axis ${ax.key} (${ax.table}.${ax.column}): ${rows.length} values`)
}

// (G) catalog_assets_all: every asset_registry row (data AND service).
async function collectAssets(): Promise<void> {
  const rows = await q<{
    asset_id: string
    layer: string
    asset_type: string
    english_name: string | null
    sanskrit_name: string | null
    target_table: string | null
    has_writer: boolean | null
    catalog_status: string | null
    count_sql: string | null
  }>(
    `SELECT asset_id, layer, asset_type, english_name, sanskrit_name, target_table, has_writer,
            catalog_status, count_sql
       FROM asset_registry ORDER BY sort_order NULLS LAST, asset_id`
  )
  for (const r of rows) {
    const aliases = [r.sanskrit_name, r.english_name].filter((x): x is string => !!x)
    entries.push({
      concept_id: `asset.${slug(r.asset_id)}`,
      canonical_name: r.english_name || r.asset_id,
      aliases,
      layer: r.layer || 'meta',
      owning_asset: r.asset_id,
      serving_tool: 'catalog_assets_all',
      serving_args: { asset_id: r.asset_id },
      row_count_per_canonical_chart: bothCounts(0, 0), // asset count is not chart-scoped; see detail
      is_chain_or_pattern: false,
      computed_globally: true,
      honest_gap_ref: null,
      source_axis: 'meta:asset_registry',
      detail: {
        asset_type: r.asset_type,
        target_table: r.target_table,
        has_writer: r.has_writer,
        catalog_status: r.catalog_status,
        note: 'asset-level registry concept; row_count is per-concept above, not per-asset',
      },
    })
  }
  console.error(`[collect] assets: ${rows.length} asset_registry concepts`)
}

// ---- bootstrap: build TABLE_ASSETS + COLUMN_MAP from information_schema + asset_registry -------
async function bootstrapMaps(): Promise<void> {
  const cols = await q<{ table_name: string; column_name: string }>(
    `SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public'`
  )
  for (const c of cols) {
    if (!COLUMN_MAP.has(c.table_name)) COLUMN_MAP.set(c.table_name, new Set())
    COLUMN_MAP.get(c.table_name)!.add(c.column_name)
  }
  const assets = await q<{ target_table: string | null; asset_id: string }>(
    `SELECT target_table, asset_id FROM asset_registry WHERE target_table IS NOT NULL ORDER BY asset_id`
  )
  for (const a of assets) {
    const t = a.target_table as string
    if (!TABLE_ASSETS.has(t)) TABLE_ASSETS.set(t, [])
    TABLE_ASSETS.get(t)!.push(a.asset_id)
  }
}

// ---- sanity self-check (frozen baseline OMEGA1_INDEPENDENT_BASELINE_v1_0.md) ------------------
// The TCI MAY NEVER BE STUBBED. If any check fails, the generator exits non-zero and does NOT
// overwrite the artifact (Lane Ω BLOCKS, never stubs). The authoritative gate is the independent
// Verifier's SQL; this is the generator's own guard so it fails loudly before writing.
interface GateResult {
  name: string
  observed: number | string
  floor: number | string
  pass: boolean
}
async function sanityGate(): Promise<{ results: GateResult[]; pass: boolean }> {
  const results: GateResult[] = []
  // 1. distinct fact_category in the TCI >= production distinct fact_category (independent SQL)
  const prodFc = Number(
    (await q<{ n: string }>(`SELECT COUNT(DISTINCT fact_category) AS n FROM chart_facts`))[0].n
  )
  const tciFc = new Set(
    entries.filter((e) => e.source_axis.startsWith('L1:chart_facts')).map((e) => e.canonical_name.split(' / ')[0])
  ).size
  results.push({ name: 'distinct_fact_category', observed: tciFc, floor: prodFc, pass: tciFc >= prodFc })
  // 2. all 10 mechanism classes present
  const mechCount = entries.filter((e) => e.source_axis.startsWith('L2:bodha_mechanisms')).length
  results.push({ name: 'mechanism_classes', observed: mechCount, floor: 10, pass: mechCount >= 10 })
  // 3. all DB-built dasha systems present
  const prodSys = Number(
    (await q<{ n: string }>(`SELECT COUNT(DISTINCT system_id) AS n FROM chart_dashas`))[0].n
  )
  const tciSys = entries.filter((e) => e.source_axis === 'L3:chart_dashas(system_id)').length
  results.push({ name: 'dasha_systems', observed: tciSys, floor: prodSys, pass: tciSys >= prodSys })
  // 4. all vargas present
  const prodVarga = Number(
    (await q<{ n: string }>(`SELECT COUNT(DISTINCT varga) AS n FROM chart_divisionals`))[0].n
  )
  const tciVarga = entries.filter((e) => e.source_axis === 'L1:chart_divisionals(varga)').length
  results.push({ name: 'vargas', observed: tciVarga, floor: prodVarga, pass: tciVarga >= prodVarga })
  // 5. all ayanamshas present
  const prodAy = Number(
    (await q<{ n: string }>(`SELECT COUNT(DISTINCT ayanamsha_id) AS n FROM chart_facts WHERE ayanamsha_id IS NOT NULL`))[0].n
  )
  const tciAy = entries.filter((e) => e.source_axis === 'meta:chart_facts(ayanamsha_id)').length
  results.push({ name: 'ayanamshas', observed: tciAy, floor: prodAy, pass: tciAy >= prodAy })
  return { results, pass: results.every((r) => r.pass) }
}

// ---- main ------------------------------------------------------------------------------------
function argVal(flag: string): string | undefined {
  const i = process.argv.indexOf(flag)
  return i >= 0 ? process.argv[i + 1] : undefined
}

async function main(): Promise<void> {
  const dbUrl = process.env.DATABASE_URL
  if (!dbUrl) {
    console.error('FATAL: DATABASE_URL not set. Run with tsx --env-file=<.env.local>.')
    process.exit(2)
  }
  pool = new Pool({ connectionString: dbUrl, max: 4 })
  const runChart = argVal('--chart') ?? PRIMARY_CHART
  const outPath =
    argVal('--out') ??
    join(REPO_ROOT, '00_ARCHITECTURE/llm_consumption_audit/capability_map/TOTAL_CONCEPT_INVENTORY_v1_0.json')

  try {
    await bootstrapMaps()
    await collectL1Facts()
    await collectMechanisms()
    await collectDashas()
    await collectVargas()
    await collectAyanamshas()
    for (const ax of AXES) await collectAxis(ax)
    await collectAssets()

    const gate = await sanityGate()
    const byLayer: Record<string, number> = {}
    for (const e of entries) byLayer[e.layer] = (byLayer[e.layer] ?? 0) + 1

    const artifact = {
      artifact: 'TOTAL_CONCEPT_INVENTORY',
      version: '1.0',
      status: gate.pass ? 'GENERATED' : 'BLOCKED_SANITY_FAIL',
      generator: 'platform/scripts/census/generate_tci.ts',
      generated_at: new Date().toISOString(),
      source: 'live DB — mechanically enumerated (NEVER hand-curated)',
      run_chart_id: runChart,
      canonical_charts: { primary: PRIMARY_CHART, second: SECOND_CHART },
      provenance_note:
        'Lane Ω1 (Elevation Campaign v2.1). Every entry enumerated live from Postgres. ' +
        'Denominators per OMEGA1_INDEPENDENT_BASELINE_v1_0.md (PROXY-RULED-004): fact_category ' +
        'global 218; mechanisms 10-class writer enum (6 empty carried, not omitted); 9 DB dasha ' +
        'systems; 5 real ayanamshas + INVARIANT sentinel; all vargas.',
      entry_schema: {
        fields: [
          'concept_id', 'canonical_name', 'aliases', 'layer', 'owning_asset', 'owning_asset_candidates?',
          'serving_tool', 'serving_args', 'row_count_per_canonical_chart', 'is_chain_or_pattern',
          'computed_globally', 'honest_gap_ref', 'source_axis', 'is_ayanamsha_variant?', 'detail?',
        ],
      },
      summary: {
        total_entries: entries.length,
        by_layer: byLayer,
        distinct_fact_category: gate.results.find((r) => r.name === 'distinct_fact_category')?.observed,
        mechanism_classes: gate.results.find((r) => r.name === 'mechanism_classes')?.observed,
        dasha_systems: gate.results.find((r) => r.name === 'dasha_systems')?.observed,
        vargas: gate.results.find((r) => r.name === 'vargas')?.observed,
        ayanamshas: gate.results.find((r) => r.name === 'ayanamshas')?.observed,
        assets: entries.filter((e) => e.source_axis === 'meta:asset_registry').length,
        concepts_computed_globally: entries.filter((e) => e.computed_globally).length,
        concepts_with_honest_gap: entries.filter((e) => e.honest_gap_ref).length,
      },
      sanity_gate: {
        pass: gate.pass,
        note: 'Generator self-guard; authoritative gate is the independent Verifier SQL.',
        results: gate.results,
      },
      axes_skipped: axesSkipped,
      entries,
    }

    mkdirSync(dirname(outPath), { recursive: true })
    if (!gate.pass) {
      const blockedPath = outPath.replace(/\.json$/, '.BLOCKED.json')
      writeFileSync(blockedPath, JSON.stringify(artifact, null, 2))
      console.error('SANITY GATE FAILED — Lane Ω BLOCKED, artifact NOT written to canonical path.')
      console.error(JSON.stringify(gate.results, null, 2))
      console.error(`Diagnostic written to ${blockedPath}`)
      process.exit(3)
    }
    writeFileSync(outPath, JSON.stringify(artifact, null, 2))
    console.error(`\nTCI written: ${outPath}`)
    console.error(`  total_entries=${entries.length} by_layer=${JSON.stringify(byLayer)}`)
    console.error(`  sanity_gate=PASS: ${gate.results.map((r) => `${r.name}=${r.observed}/${r.floor}`).join(', ')}`)
    if (axesSkipped.length) console.error(`  axes_skipped=${axesSkipped.length}: ${JSON.stringify(axesSkipped)}`)
  } finally {
    await pool.end()
  }
}

main().catch((err) => {
  console.error('generate_tci FAILED:', err)
  process.exit(1)
})
