/**
 * asset_registry_seed.ts — Seed asset_registry, asset_coefficients for Cockpit v2.
 *
 * Rules enforced (brief §5 author rules):
 *   1. No hardcoded empirical output numbers (e.g. 569, 4589, 57).
 *   2. No empirical defaults for coefficients — all start NULL.
 *   3. No estimated_seconds defaults — all start NULL.
 *   4. Catalog-driven formulas use ACTUAL().
 *   5. Source-of-truth files use FILE_COUNT().
 *
 * Pre-flight: for each row, SELECT to_regclass(target_table) in prod.
 *   Returns NULL → mark is_active=false; continue.
 * More than 5 absent target_tables → hard stop before any INSERT.
 *
 * Usage: DATABASE_URL=<url> npx tsx scripts/seed/asset_registry_seed.ts
 */

import { Client } from 'pg'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// ── Types ─────────────────────────────────────────────────────────────────────

interface AssetDef {
  asset_id: string
  layer: 'brahmagyan' | 'ganita' | 'bodha' | 'kala' | 'phala' | 'mimamsa'
  sort_order: number
  sanskrit_name: string
  english_name: string
  english_description: string
  storage_type: 'postgres_table' | 'pgvector' | 'postgres_view' | 'gcs_jsonl' | 'bigquery' | 'tool_only'
  target_table: string | null
  count_sql: string | null
  size_sql: string | null
  target_floor: number | null
  expected_volume_formula: string | null
  expected_volume_inputs: Record<string, unknown> | null
  volume_explanation: string | null
  depends_on: string[]
  scope: 'global' | 'per_chart'
  is_active: boolean  // overridden to false if target_table absent in prod
  estimated_seconds: null  // always null — measured on first build
}

interface CoefficientDef {
  coefficient_name: string
  description: string
  upstream_asset_id: string
  downstream_asset_id: string
}

// ── Formula validator ─────────────────────────────────────────────────────────
// Accepts: arithmetic (+ - * / parentheses), named constants, ACTUAL(asset_id), FILE_COUNT(path, marker)
// Rejects: anything else (no eval/exec)

const ALLOWED_VARS = new Set([
  'AYANAMSHAS', 'GRAHAS', 'SIGNS', 'HOUSES', 'NAKSHATRAS',
  'VARGAS', 'BHAVAS', 'LIFE_SPAN_YEARS', 'DATE_RANGE_DAYS',
])
const DEFAULTS: Record<string, number> = {
  AYANAMSHAS: 5, GRAHAS: 9, SIGNS: 12, HOUSES: 12,
  NAKSHATRAS: 27, VARGAS: 60, BHAVAS: 12,
  LIFE_SPAN_YEARS: 90, DATE_RANGE_DAYS: 44000,
}

function parseFormula(
  formula: string,
  knownCoefficients: Set<string> = new Set(),
): {
  hasActual: boolean
  hasFileCount: boolean
  referencedAssets: string[]
  canEval: boolean
  evalResult?: number
} {
  const actualMatches = [...formula.matchAll(/ACTUAL\(([^)]+)\)/g)]
  const fileCountMatches = [...formula.matchAll(/FILE_COUNT\([^)]+\)/g)]
  const referencedAssets = actualMatches.map(m => m[1].trim())

  const hasActual = actualMatches.length > 0
  const hasFileCount = fileCountMatches.length > 0

  // Strip ACTUAL() and FILE_COUNT() calls for pure arithmetic check
  let stripped = formula
    .replace(/ACTUAL\([^)]+\)/g, '1')
    .replace(/FILE_COUNT\([^)]+\)/g, '1')

  // Validate only allowed chars remain: digits, operators, parens, spaces, variable names
  const noVars = stripped.replace(/[A-Z_]+/g, '0')
  if (!/^[\d\s\+\-\*\/\(\)\.]+$/.test(noVars)) {
    throw new Error(`Formula contains disallowed characters after stripping: "${formula}" → "${noVars}"`)
  }

  // Replace known constants with defaults, then substitute coefficient names with 1
  let evalStr = stripped
  for (const [varName, val] of Object.entries(DEFAULTS)) {
    evalStr = evalStr.replace(new RegExp(`\\b${varName}\\b`, 'g'), String(val))
  }
  for (const coeff of knownCoefficients) {
    evalStr = evalStr.replace(new RegExp(`\\b${coeff}\\b`, 'g'), '1')
  }

  // Verify no unknown identifiers remain
  if (/[A-Z_]/.test(evalStr)) {
    const unknowns = evalStr.match(/[A-Z][A-Z_]*/g) ?? []
    throw new Error(`Unknown variables in formula "${formula}": ${unknowns.join(', ')}`)
  }

  let evalResult: number | undefined
  try {
    // Safe arithmetic eval: only digits, operators, parens
    if (!/^[\d\s\+\-\*\/\(\)\.]+$/.test(evalStr)) {
      throw new Error('Unsafe eval string')
    }
    // eslint-disable-next-line no-new-func
    evalResult = Function(`"use strict"; return (${evalStr})`)() as number
  } catch {
    throw new Error(`Formula eval failed: "${formula}" → "${evalStr}"`)
  }

  return { hasActual, hasFileCount, referencedAssets, canEval: !hasActual && !hasFileCount, evalResult }
}

// ── FILE_COUNT evaluator ───────────────────────────────────────────────────────

function evalFileCount(path: string, marker: string): number {
  const repoRoot = resolve(__dirname, '../../..')
  const absPath = resolve(repoRoot, path)
  const content = readFileSync(absPath, 'utf8')
  // marker = 'EVT' → count unique tokens matching EVT.YYYY.MM.DD.NN
  const re = new RegExp(`${marker}\\.[0-9]{4}\\.[0-9X]{2}\\.[0-9X]{2}\\.[0-9]+`, 'g')
  const matches = content.match(re) ?? []
  const unique = new Set(matches)
  return unique.size
}

// ── Asset definitions ─────────────────────────────────────────────────────────

const ASSETS: AssetDef[] = [
  // ── BRAHMAGYAN (8) ────────────────────────────────────────────────────────
  {
    asset_id: 'brahmagyan.kalapancanga',
    layer: 'brahmagyan', sort_order: 1,
    sanskrit_name: 'Kālapañcāṅga',
    english_name: 'Ephemeris',
    english_description: 'Swiss Ephemeris DE441 — raw astronomical positions for all grahas',
    storage_type: 'postgres_table',
    target_table: 'ephemeris_daily',
    count_sql: 'SELECT count(*) FROM ephemeris_daily',
    size_sql: "SELECT pg_total_relation_size('ephemeris_daily')",
    target_floor: 29200,
    expected_volume_formula: 'GRAHAS * DATE_RANGE_DAYS',
    expected_volume_inputs: null,
    volume_explanation: '9 grahas × date-range days — structural, no upstream dependency',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.sarani',
    layer: 'brahmagyan', sort_order: 2,
    sanskrit_name: 'Sāraṇī',
    english_name: 'Reference library',
    english_description: 'Nakshatra attributes, sign lordships, bounds, dignity tables',
    storage_type: 'postgres_table',
    target_table: 'reference_nakshatras',
    count_sql: 'SELECT count(*) FROM reference_nakshatras',
    size_sql: "SELECT pg_total_relation_size('reference_nakshatras')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Reference library is itself a source of truth — live count is the authoritative floor once seeded',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.sutravali',
    layer: 'brahmagyan', sort_order: 3,
    sanskrit_name: 'Sūtravālī',
    english_name: 'Rules corpus',
    english_description: 'Classical rules (BPHS, Jaimini Sutram, KP Reader, Tajaka) as indexed chunks',
    storage_type: 'postgres_table',
    target_table: 'classical_text_chunks',
    count_sql: 'SELECT count(*) FROM classical_text_chunks',
    size_sql: "SELECT pg_total_relation_size('classical_text_chunks')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Empirical writer output — first ingest establishes the count; re-runs must match exactly',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.samanvaya',
    layer: 'brahmagyan', sort_order: 4,
    sanskrit_name: 'Samanvaya',
    english_name: 'Concordance',
    english_description: 'Cross-text attribution index mapping rules to classical sources',
    storage_type: 'postgres_table',
    target_table: 'classical_attributions',
    count_sql: 'SELECT count(*) FROM classical_attributions',
    size_sql: "SELECT pg_total_relation_size('classical_attributions')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(brahmagyan.sutravali) * CONCORDANCE_DENSITY',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from upstream rule count × concordance-density coefficient; coefficient CONCORDANCE_DENSITY measured on first build with both assets lit',
    depends_on: ['brahmagyan.sutravali'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.sensitive_point_catalog',
    layer: 'brahmagyan', sort_order: 5,
    sanskrit_name: 'Sphuṭa-sūcī',
    english_name: 'Sensitive point catalog',
    english_description: 'Reference catalog of upagrahas, special lagnas, sahams, arudhas',
    storage_type: 'postgres_table',
    target_table: 'reference_aspects',
    count_sql: 'SELECT count(*) FROM reference_aspects',
    size_sql: "SELECT pg_total_relation_size('reference_aspects')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Static reference catalog — count established at first load; re-runs must match',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.shastra',
    layer: 'brahmagyan', sort_order: 6,
    sanskrit_name: 'Śāstra',
    english_name: 'Classical texts',
    english_description: 'Source texts: BPHS, Jaimini Sutram, KP Reader, Tajaka Neelakanthi',
    storage_type: 'postgres_table',
    target_table: 'classical_texts',
    count_sql: 'SELECT count(*) FROM classical_texts',
    size_sql: "SELECT pg_total_relation_size('classical_texts')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Source text library — count is whatever the 4 canonical texts produce (BPHS + Jaimini + KP + Tajaka)',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.upaya_kosha',
    layer: 'brahmagyan', sort_order: 7,
    sanskrit_name: 'Upāya-kośa',
    english_name: 'Remedy corpus',
    english_description: 'Classical remedy texts: mantras, gemstones, herbs, rituals',
    storage_type: 'postgres_table',
    target_table: 'brahma_remedy_corpus',
    count_sql: 'SELECT count(*) FROM brahma_remedy_corpus',
    size_sql: "SELECT pg_total_relation_size('brahma_remedy_corpus')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Static corpus — count established at first load',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'brahmagyan.panchanga_almanac',
    layer: 'brahmagyan', sort_order: 8,
    sanskrit_name: 'Nitya-pañcāṅga',
    english_name: 'Daily almanac',
    english_description: 'Daily panchanga almanac (tithi, vara, nakshatra, yoga, karana) 1900–2100',
    storage_type: 'postgres_table',
    target_table: 'panchanga_daily',
    count_sql: 'SELECT count(*) FROM panchanga_daily',
    size_sql: "SELECT pg_total_relation_size('panchanga_daily')",
    target_floor: 73000,
    expected_volume_formula: 'DATE_RANGE_DAYS',
    expected_volume_inputs: null,
    volume_explanation: 'One row per day in the date range — structural',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },

  // ── GANITA (8) ────────────────────────────────────────────────────────────
  {
    asset_id: 'ganita.graha_sthana',
    layer: 'ganita', sort_order: 1,
    sanskrit_name: 'Graha-sthāna',
    english_name: 'Positions',
    english_description: 'Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)',
    storage_type: 'postgres_table',
    target_table: 'ganita_positions',
    count_sql: 'SELECT count(*) FROM ganita_positions WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('ganita_positions')",
    target_floor: null,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '9 grahas × ayanamsha count — one position row per graha per ayanamsha',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.varga',
    layer: 'ganita', sort_order: 2,
    sanskrit_name: 'Varga',
    english_name: 'Divisional charts',
    english_description: 'D1–D60 divisional chart positions per ayanamsha',
    storage_type: 'postgres_table',
    target_table: 'chart_divisionals',
    count_sql: 'SELECT count(*) FROM chart_divisionals WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_divisionals')",
    target_floor: null,
    expected_volume_formula: 'VARGAS * GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '60 vargas × 9 grahas × ayanamsha count — structural',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.dasakrama',
    layer: 'ganita', sort_order: 3,
    sanskrit_name: 'Daśākrama',
    english_name: 'Vimshottari dasha',
    english_description: 'Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha',
    storage_type: 'postgres_table',
    target_table: 'ganita_dashas',
    count_sql: 'SELECT count(*) FROM ganita_dashas WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('ganita_dashas')",
    target_floor: null,
    expected_volume_formula: '(9 + 81 + 729) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Vimshottari tree: 9 MD + 81 AD + 729 PD = 819 rows × ayanamsha count — structural',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.balatva',
    layer: 'ganita', sort_order: 4,
    sanskrit_name: 'Balatva',
    english_name: 'Strength tables',
    english_description: 'Shadbala, ashtakavarga, and bhava bala per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: '(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Shadbala: 6 scores × 9 grahas; ashtakavarga: 8 tables × 9 grahas × 12 signs; bhava bala: 6 scores × 12 bhavas — all × ayanamshas',
    depends_on: [],
    scope: 'per_chart', is_active: false, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.suksmabindu',
    layer: 'ganita', sort_order: 5,
    sanskrit_name: 'Sūkṣmabindu',
    english_name: 'Sensitive points',
    english_description: 'Per-chart sensitive point positions computed from the catalog × ayanamshas',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: 'ACTUAL(brahmagyan.sensitive_point_catalog) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from the sensitive-point catalog count × ayanamshas; awaits catalog lit + dedicated per-chart table',
    depends_on: ['brahmagyan.sensitive_point_catalog'],
    scope: 'per_chart', is_active: false, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.pancanga_janma',
    layer: 'ganita', sort_order: 6,
    sanskrit_name: 'Pañcāṅga-janma',
    english_name: 'Birth panchanga',
    english_description: 'Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha',
    storage_type: 'postgres_table',
    target_table: 'chart_panchanga',
    count_sql: 'SELECT count(*) FROM chart_panchanga WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_panchanga')",
    target_floor: null,
    expected_volume_formula: 'AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'One panchanga row per ayanamsha — structural',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.sade_sati',
    layer: 'ganita', sort_order: 7,
    sanskrit_name: 'Sāḍesātī',
    english_name: 'Sade Sati periods',
    english_description: 'Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: 'AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'One row per ayanamsha for the native\'s Sade Sati window; awaits dedicated table',
    depends_on: [],
    scope: 'per_chart', is_active: false, estimated_seconds: null,
  },
  {
    asset_id: 'ganita.tajaka',
    layer: 'ganita', sort_order: 8,
    sanskrit_name: 'Tājaka',
    english_name: 'Tajaka Varshaphal',
    english_description: 'Annual chart (Varshaphal) and Tajaka aspects per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Writer output — row count depends on aspect configurations found; awaits dedicated table',
    depends_on: [],
    scope: 'per_chart', is_active: false, estimated_seconds: null,
  },

  // ── BODHA (8) ─────────────────────────────────────────────────────────────
  {
    asset_id: 'bodha.laksana',
    layer: 'bodha', sort_order: 1,
    sanskrit_name: 'Lakṣaṇa',
    english_name: 'Signal store (MSR)',
    english_description: 'MARSYS Signal Register — grounded signals derived from rules × chart facts',
    storage_type: 'postgres_table',
    target_table: 'bodha_signals',
    count_sql: 'SELECT count(*) FROM bodha_signals WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_signals')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(brahmagyan.sutravali) * SIGNAL_PER_RULE * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from upstream rule count × signal-per-rule coefficient × ayanamsha count; coefficient SIGNAL_PER_RULE measured on first build with both assets lit',
    depends_on: ['brahmagyan.sutravali'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.karanajala',
    layer: 'bodha', sort_order: 2,
    sanskrit_name: 'Kāraṇajāla',
    english_name: 'Signal graph edges (CGM)',
    english_description: 'Causal Graph Model — valenced edges between signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_graph_edges',
    count_sql: 'SELECT count(*) FROM bodha_graph_edges WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_graph_edges')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(bodha.laksana) * EDGE_DENSITY',
    expected_volume_inputs: null,
    volume_explanation: 'Fraction of signal pairs forming a CGM edge; coefficient EDGE_DENSITY measured on first build with both assets lit',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.bimba',
    layer: 'bodha', sort_order: 3,
    sanskrit_name: 'Bimba',
    english_name: 'Signal graph nodes',
    english_description: 'CGM node registry — one node per signal in the graph',
    storage_type: 'postgres_table',
    target_table: 'bodha_graph',
    count_sql: 'SELECT count(*) FROM bodha_graph WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_graph')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(bodha.laksana)',
    expected_volume_inputs: null,
    volume_explanation: 'One node per signal — exact 1:1 with Lakṣaṇa count',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.samskara',
    layer: 'bodha', sort_order: 4,
    sanskrit_name: 'Saṃskāra',
    english_name: 'Signal embeddings',
    english_description: 'Vertex AI 768-dim vector embeddings — one per MSR signal',
    storage_type: 'pgvector',
    target_table: 'bodha_signal_embeddings',
    count_sql: 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_signal_embeddings')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(bodha.laksana)',
    expected_volume_inputs: null,
    volume_explanation: 'One embedding per signal — exact 1:1 with Lakṣaṇa count',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.sangati',
    layer: 'bodha', sort_order: 5,
    sanskrit_name: 'Saṅgati',
    english_name: 'Domain links (CDLM)',
    english_description: 'Cross-Domain Linkage Matrix — inter-domain causal and correlation edges',
    storage_type: 'postgres_table',
    target_table: 'bodha_domain_links',
    count_sql: 'SELECT count(*) FROM bodha_domain_links WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_domain_links')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from cross-domain signal analysis; count depends on contradiction hubs identified',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.upaya',
    layer: 'bodha', sort_order: 6,
    sanskrit_name: 'Upāya',
    english_name: 'Remediation (RM)',
    english_description: 'Remediation Map — classical remedies keyed to activated signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_remediation',
    count_sql: 'SELECT count(*) FROM bodha_remediation WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_remediation')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived once contradiction hubs are identified; count not predictable a priori',
    depends_on: ['bodha.laksana', 'bodha.sangati'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.samvada',
    layer: 'bodha', sort_order: 7,
    sanskrit_name: 'Saṃvāda',
    english_name: 'UCN resonance',
    english_description: 'Universal Chart Notation resonance map — signal-to-archetype convergence scores',
    storage_type: 'postgres_table',
    target_table: 'bodha_resonance',
    count_sql: 'SELECT count(*) FROM bodha_resonance WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_resonance')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from synthesis convergence analysis',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bodha.pramana_mapa',
    layer: 'bodha', sort_order: 8,
    sanskrit_name: 'Pramāṇa-māpā',
    english_name: 'Synthesis quality',
    english_description: 'Per-query synthesis quality scorecard (citation density, whole-chart coverage, derivation compliance)',
    storage_type: 'postgres_table',
    target_table: 'synthesis_quality_scorecard',
    count_sql: 'SELECT count(*) FROM synthesis_quality_scorecard',
    size_sql: "SELECT pg_total_relation_size('synthesis_quality_scorecard')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per synthesis query — accumulates over usage; not a per-build target',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },

  // ── KALA (4) ──────────────────────────────────────────────────────────────
  {
    asset_id: 'kala.kalasutra',
    layer: 'kala', sort_order: 1,
    sanskrit_name: 'Kālasūtra',
    english_name: 'Timeline',
    english_description: 'Integrated dasha-transit-signal timeline: one row per date for the native\'s life span',
    storage_type: 'postgres_table',
    target_table: 'kala_timeline',
    count_sql: 'SELECT count(*) FROM kala_timeline WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_timeline')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(ganita.dasakrama) + ACTUAL(brahmagyan.kalapancanga) * TRANSITS_PER_DAY',
    expected_volume_inputs: null,
    volume_explanation: 'Dasha rows + transit event days; coefficient TRANSITS_PER_DAY measured on first build with ephemeris lit',
    depends_on: ['ganita.dasakrama', 'brahmagyan.kalapancanga'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'kala.sangam',
    layer: 'kala', sort_order: 2,
    sanskrit_name: 'Saṅgam',
    english_name: 'Convergence windows',
    english_description: 'Dasha-transit convergence windows: periods of elevated multi-factor alignment',
    storage_type: 'postgres_table',
    target_table: 'kala_convergence',
    count_sql: 'SELECT count(*) FROM kala_convergence WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_convergence')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from dasha + transit cluster analysis; count depends on alignment density',
    depends_on: ['kala.kalasutra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'kala.vighnakara',
    layer: 'kala', sort_order: 3,
    sanskrit_name: 'Vighnakāra',
    english_name: 'Obstruction periods',
    english_description: 'Inauspicious and obstructed windows: Rahu/Saturn transits over sensitive points',
    storage_type: 'postgres_table',
    target_table: 'kala_obstruction',
    count_sql: 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_obstruction')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from transit analysis over sensitive points; count depends on graha configuration',
    depends_on: ['kala.kalasutra', 'ganita.suksmabindu'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'kala.transit_almanac',
    layer: 'kala', sort_order: 4,
    sanskrit_name: 'Kāla-sañcara',
    english_name: 'Transit event almanac',
    english_description: 'Timeline rows with active major-aspect transit events (non-empty transit_highlights)',
    storage_type: 'postgres_table',
    target_table: 'kala_timeline',
    count_sql: "SELECT count(*) FROM kala_timeline WHERE chart_id = $1 AND jsonb_array_length(transit_highlights) > 0",
    size_sql: "SELECT pg_total_relation_size('kala_timeline')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(brahmagyan.kalapancanga) * TRANSITS_PER_DAY',
    expected_volume_inputs: null,
    volume_explanation: 'Days with active major-aspect transits out of the full ephemeris range; coefficient TRANSITS_PER_DAY measured on first build',
    depends_on: ['brahmagyan.kalapancanga', 'kala.kalasutra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  // ── PHALA (5) ─────────────────────────────────────────────────────────────
  {
    asset_id: 'phala.nimitta',
    layer: 'phala', sort_order: 1,
    sanskrit_name: 'Nimitta',
    english_name: 'Predictive anchors',
    english_description: 'Phase-locked predictive anchors derived from convergence windows',
    storage_type: 'postgres_table',
    target_table: 'phala_anchors',
    count_sql: 'SELECT count(*) FROM phala_anchors WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_anchors')",
    target_floor: null,
    expected_volume_formula: 'ACTUAL(kala.sangam) * ANCHOR_PER_CONVERGENCE',
    expected_volume_inputs: null,
    volume_explanation: 'Anchors derived per convergence window; coefficient ANCHOR_PER_CONVERGENCE measured on first build with both assets lit',
    depends_on: ['kala.sangam'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'phala.muhurta',
    layer: 'phala', sort_order: 2,
    sanskrit_name: 'Muhūrta',
    english_name: 'Auspicious windows',
    english_description: 'Candidate muhurta windows scored by Panchanga + transit + dasha alignment',
    storage_type: 'postgres_table',
    target_table: 'phala_muhurta',
    count_sql: 'SELECT count(*) FROM phala_muhurta WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_muhurta')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from multi-factor timing analysis; count depends on query window',
    depends_on: ['kala.kalasutra', 'ganita.pancanga_janma'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'phala.sodhana',
    layer: 'phala', sort_order: 3,
    sanskrit_name: 'Śodhana',
    english_name: 'Rectification',
    english_description: 'Birth-time rectification hypotheses scored against life events',
    storage_type: 'postgres_table',
    target_table: 'phala_rectification',
    count_sql: 'SELECT count(*) FROM phala_rectification WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_rectification')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per candidate rectification hypothesis; count depends on search space',
    depends_on: ['bodha.laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'phala.pratikara',
    layer: 'phala', sort_order: 4,
    sanskrit_name: 'Pratīkāra',
    english_name: 'Mitigation',
    english_description: 'Active mitigation strategies for flagged malefic configurations',
    storage_type: 'postgres_table',
    target_table: 'phala_mitigation',
    count_sql: 'SELECT count(*) FROM phala_mitigation WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_mitigation')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from remediation + active obstruction periods',
    depends_on: ['bodha.upaya', 'kala.vighnakara'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'phala.suddha_sodhana',
    layer: 'phala', sort_order: 5,
    sanskrit_name: 'Śuddha-śodhana',
    english_name: 'Best rectification',
    english_description: 'Top-scored rectification hypothesis per search run',
    storage_type: 'postgres_table',
    target_table: 'phala_rectification_best',
    count_sql: 'SELECT count(*) FROM phala_rectification_best WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_rectification_best')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per rectification search run — accumulates across runs',
    depends_on: ['phala.sodhana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  // ── MIMAMSA (6) ───────────────────────────────────────────────────────────
  {
    asset_id: 'mimamsa.jivanaghatana',
    layer: 'mimamsa', sort_order: 1,
    sanskrit_name: 'Jīvanaghaṭanā',
    english_name: 'Life event log (held-out)',
    english_description: 'LEL — held-out event log isolated from generation; ground truth for prediction calibration',
    storage_type: 'postgres_table',
    target_table: 'life_events',
    count_sql: 'SELECT count(*) FROM life_events',
    size_sql: "SELECT pg_total_relation_size('life_events')",
    target_floor: null,
    expected_volume_formula: "FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')",
    expected_volume_inputs: null,
    volume_explanation: 'Deterministic given the source-of-truth file. Re-runs MUST match the file count exactly; divergence is a bug.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mimamsa.bhavisya',
    layer: 'mimamsa', sort_order: 2,
    sanskrit_name: 'Bhaviṣya',
    english_name: 'Predictions',
    english_description: 'Time-indexed prospective predictions with confidence + falsifiers',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_predictions',
    count_sql: 'SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_predictions')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates as predictions are logged — not a deterministic target',
    depends_on: ['bodha.laksana', 'kala.kalasutra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mimamsa.pramana',
    layer: 'mimamsa', sort_order: 3,
    sanskrit_name: 'Pramāṇa',
    english_name: 'Calibration',
    english_description: 'Prediction outcome calibration records — confidence score vs outcome mapping',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_calibration',
    count_sql: 'SELECT count(*) FROM mimamsa_calibration',
    size_sql: "SELECT pg_total_relation_size('mimamsa_calibration')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates as prediction outcomes are recorded — not a deterministic target',
    depends_on: ['mimamsa.bhavisya'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mimamsa.gunanaka',
    layer: 'mimamsa', sort_order: 4,
    sanskrit_name: 'Guṇānaka',
    english_name: 'Multipliers',
    english_description: 'Empirical multiplier weights learned from calibration outcomes',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_multipliers',
    count_sql: 'SELECT count(*) FROM mimamsa_multipliers',
    size_sql: "SELECT pg_total_relation_size('mimamsa_multipliers')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per multiplier type — small, stable catalog; grows only when new signal categories are added',
    depends_on: ['mimamsa.pramana'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mimamsa.pariksha',
    layer: 'mimamsa', sort_order: 5,
    sanskrit_name: 'Parīkṣā',
    english_name: 'QA evaluation',
    english_description: 'Answer quality evaluation runs — automated + human QA over synthesis outputs',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_qa_eval',
    count_sql: 'SELECT count(*) FROM mimamsa_qa_eval',
    size_sql: "SELECT pg_total_relation_size('mimamsa_qa_eval')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates as eval runs are executed — not a deterministic target',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mimamsa.vistara',
    layer: 'mimamsa', sort_order: 6,
    sanskrit_name: 'Vistāra',
    english_name: 'Export log',
    english_description: 'Audit log of all synthesis export events (PDF, JSON, MCP bundles)',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_export_log',
    count_sql: 'SELECT count(*) FROM mimamsa_export_log',
    size_sql: "SELECT pg_total_relation_size('mimamsa_export_log')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates with each export event — operational audit log',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
]

// ── Coefficient definitions ───────────────────────────────────────────────────

const COEFFICIENTS: CoefficientDef[] = [
  {
    coefficient_name: 'SIGNAL_PER_RULE',
    description: 'Signals produced per classical rule per ayanamsha set (measured first build)',
    upstream_asset_id: 'brahmagyan.sutravali',
    downstream_asset_id: 'bodha.laksana',
  },
  {
    coefficient_name: 'EDGE_DENSITY',
    description: 'Fraction of signal pairs forming a CGM edge (measured first build)',
    upstream_asset_id: 'bodha.laksana',
    downstream_asset_id: 'bodha.karanajala',
  },
  {
    coefficient_name: 'ANCHOR_PER_CONVERGENCE',
    description: 'Predictive anchors derived per convergence window (measured first build)',
    upstream_asset_id: 'kala.sangam',
    downstream_asset_id: 'phala.nimitta',
  },
  {
    coefficient_name: 'TRANSITS_PER_DAY',
    description: 'Major-aspect transit events per calendar day across the ephemeris range (measured first build)',
    upstream_asset_id: 'brahmagyan.kalapancanga',
    downstream_asset_id: 'kala.kalasutra',
  },
  {
    coefficient_name: 'CONCORDANCE_DENSITY',
    description: 'Concordance attribution topics per classical rule (measured first build)',
    upstream_asset_id: 'brahmagyan.sutravali',
    downstream_asset_id: 'brahmagyan.samanvaya',
  },
]

// ── Formula validation ────────────────────────────────────────────────────────

function validateFormulas(assets: AssetDef[], coefficients: CoefficientDef[]): void {
  const assetIds = new Set(assets.map(a => a.asset_id))
  const coeffNames = new Set(coefficients.map(c => c.coefficient_name))

  console.log('Validating formulas...')
  for (const asset of assets) {
    if (!asset.expected_volume_formula) continue
    const formula = asset.expected_volume_formula
    try {
      const parsed = parseFormula(formula, coeffNames)

      // Rule 3.1a-2: referenced assets must exist
      for (const refId of parsed.referencedAssets) {
        if (!assetIds.has(refId)) {
          throw new Error(`ACTUAL(${refId}) references unknown asset_id`)
        }
      }

      // Every coefficient referenced in formula must exist in COEFFICIENTS
      const coeffRe = /\b([A-Z_]+)\b/g
      const formulaTokens = [...formula.matchAll(coeffRe)].map(m => m[1])
      for (const token of formulaTokens) {
        if (ALLOWED_VARS.has(token)) continue
        if (token.startsWith('ACTUAL') || token.startsWith('FILE_COUNT')) continue
        // It's a coefficient name
        if (!coeffNames.has(token)) {
          throw new Error(`Formula for ${asset.asset_id} references undeclared coefficient ${token}`)
        }
      }

      if (parsed.canEval && parsed.evalResult !== undefined) {
        if (parsed.evalResult <= 0 || !Number.isFinite(parsed.evalResult)) {
          throw new Error(`Formula evaluates to non-positive: ${parsed.evalResult}`)
        }
        console.log(`  ✓ ${asset.asset_id}: formula="${formula}" → ${parsed.evalResult.toLocaleString()} @ defaults`)
      } else {
        console.log(`  ✓ ${asset.asset_id}: formula="${formula}" (ACTUAL/FILE_COUNT — not evaluated at seed time)`)
      }
    } catch (err) {
      throw new Error(`Formula validation failed for ${asset.asset_id}: ${(err as Error).message}`)
    }
  }
  console.log('Formula validation passed.\n')
}

// ── Dependency cycle check ────────────────────────────────────────────────────

function checkNoCycles(assets: AssetDef[]): void {
  const assetMap = new Map(assets.map(a => [a.asset_id, a]))
  const visited = new Set<string>()
  const stack = new Set<string>()

  function dfs(id: string): void {
    if (stack.has(id)) throw new Error(`Cycle detected at: ${id}`)
    if (visited.has(id)) return
    stack.add(id)
    const asset = assetMap.get(id)
    if (asset) {
      for (const dep of asset.depends_on) {
        dfs(dep)
      }
      // Also check ACTUAL() references in formula
      if (asset.expected_volume_formula) {
        const refs = [...asset.expected_volume_formula.matchAll(/ACTUAL\(([^)]+)\)/g)].map(m => m[1].trim())
        for (const ref of refs) {
          dfs(ref)
        }
      }
    }
    stack.delete(id)
    visited.add(id)
  }

  for (const asset of assets) {
    dfs(asset.asset_id)
  }
  console.log('Dependency cycle check passed.\n')
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const dbUrl = process.env.DATABASE_URL
  if (!dbUrl) throw new Error('DATABASE_URL env var required')

  // Pre-validate formulas before touching the DB
  validateFormulas(ASSETS, COEFFICIENTS)
  checkNoCycles(ASSETS)

  // Evaluate FILE_COUNT for LEL to populate expected_volume_inputs (audit trail).
  // The formula string FILE_COUNT('...', 'EVT') is preserved in expected_volume_formula — never replaced with the literal count.
  const lelCount = evalFileCount('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')
  const lelAsset = ASSETS.find(a => a.asset_id === 'mimamsa.jivanaghatana')!
  // Do NOT overwrite expected_volume_formula — it must stay as the FILE_COUNT expression.
  lelAsset.expected_volume_inputs = { file_count: lelCount, source_file: '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md' }
  console.log(`FILE_COUNT(LEL, EVT) = ${lelCount}\n`)

  const client = new Client({ connectionString: dbUrl })
  await client.connect()

  // Pre-flight: verify target tables exist
  console.log('Pre-flight: verifying target tables...')
  const absentAssets: string[] = []

  for (const asset of ASSETS) {
    if (!asset.target_table) {
      console.log(`  ⚠ ${asset.asset_id}: no target_table — marking is_active=false`)
      asset.is_active = false
      absentAssets.push(`${asset.asset_id} (no target_table declared)`)
      continue
    }
    const { rows } = await client.query<{ to_regclass: string | null }>(
      'SELECT to_regclass($1) AS to_regclass',
      [asset.target_table],
    )
    if (!rows[0]?.to_regclass) {
      console.log(`  ✗ ${asset.asset_id}: target_table '${asset.target_table}' absent in prod — marking is_active=false`)
      asset.is_active = false
      absentAssets.push(`${asset.asset_id} (target_table '${asset.target_table}' not found)`)
    } else {
      console.log(`  ✓ ${asset.asset_id}: ${asset.target_table}`)
    }
  }

  console.log()

  if (absentAssets.length > 5) {
    await client.end()
    throw new Error(
      `HARD STOP: ${absentAssets.length} assets have absent target_tables (limit: 5).\n` +
      `Absent:\n${absentAssets.map(a => `  - ${a}`).join('\n')}\n` +
      'Report to Cowork before proceeding.',
    )
  }

  if (absentAssets.length > 0) {
    console.log(`Inactive assets (${absentAssets.length}/5 limit):`)
    absentAssets.forEach(a => console.log(`  - ${a}`))
    console.log()
  }

  // Insert asset_registry rows
  console.log('Seeding asset_registry...')
  for (const asset of ASSETS) {
    await client.query(
      `INSERT INTO asset_registry (
        asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
        storage_type, target_table, count_sql, size_sql, target_floor,
        expected_volume_formula, expected_volume_inputs, volume_explanation,
        depends_on, scope, is_active, estimated_seconds
      ) VALUES (
        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18
      ) ON CONFLICT (asset_id) DO UPDATE SET
        layer = EXCLUDED.layer,
        sort_order = EXCLUDED.sort_order,
        sanskrit_name = EXCLUDED.sanskrit_name,
        english_name = EXCLUDED.english_name,
        english_description = EXCLUDED.english_description,
        storage_type = EXCLUDED.storage_type,
        target_table = EXCLUDED.target_table,
        count_sql = EXCLUDED.count_sql,
        size_sql = EXCLUDED.size_sql,
        target_floor = EXCLUDED.target_floor,
        expected_volume_formula = EXCLUDED.expected_volume_formula,
        expected_volume_inputs = EXCLUDED.expected_volume_inputs,
        volume_explanation = EXCLUDED.volume_explanation,
        depends_on = EXCLUDED.depends_on,
        scope = EXCLUDED.scope,
        is_active = EXCLUDED.is_active`,
      [
        asset.asset_id, asset.layer, asset.sort_order,
        asset.sanskrit_name, asset.english_name, asset.english_description,
        asset.storage_type, asset.target_table, asset.count_sql, asset.size_sql,
        asset.target_floor, asset.expected_volume_formula,
        asset.expected_volume_inputs ? JSON.stringify(asset.expected_volume_inputs) : null,
        asset.volume_explanation,
        asset.depends_on, asset.scope, asset.is_active, asset.estimated_seconds,
      ],
    )
    console.log(`  ${asset.is_active ? '✓' : '⚠'} ${asset.asset_id}`)
  }

  // Insert coefficient definitions (current_value = NULL, measurement_count = 0)
  console.log('\nSeeding asset_coefficients...')
  for (const coeff of COEFFICIENTS) {
    await client.query(
      `INSERT INTO asset_coefficients (coefficient_name, description, upstream_asset_id, downstream_asset_id)
       VALUES ($1,$2,$3,$4)
       ON CONFLICT (coefficient_name) DO UPDATE SET
         description = EXCLUDED.description,
         upstream_asset_id = EXCLUDED.upstream_asset_id,
         downstream_asset_id = EXCLUDED.downstream_asset_id`,
      [coeff.coefficient_name, coeff.description, coeff.upstream_asset_id, coeff.downstream_asset_id],
    )
    console.log(`  ✓ ${coeff.coefficient_name} (${coeff.upstream_asset_id} → ${coeff.downstream_asset_id})`)
  }

  await client.end()

  // Verification summary
  const active = ASSETS.filter(a => a.is_active)
  const inactive = ASSETS.filter(a => !a.is_active)
  console.log('\n── Seed complete ────────────────────────────────────────────────')
  console.log(`Total:    ${ASSETS.length}`)
  console.log(`Active:   ${active.length}`)
  console.log(`Inactive: ${inactive.length}`)
  if (inactive.length > 0) {
    console.log('Inactive list (target_table missing or null):')
    inactive.forEach(a => console.log(`  - ${a.asset_id} (${a.target_table ?? 'no table declared'})`))
  }
  console.log('\nCoefficients seeded (all current_value = NULL — measured on first build):')
  COEFFICIENTS.forEach(c => console.log(`  - ${c.coefficient_name}`))
  console.log()
}

main().catch(err => {
  console.error('\nSeed failed:', err.message)
  process.exit(1)
})
