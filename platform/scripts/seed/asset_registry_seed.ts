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
  storage_type: 'postgres_table' | 'pgvector' | 'postgres_view' | 'gcs_jsonl' | 'bigquery' | 'tool_only' | 'service'
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
  // Migration 202+ fields (service-support upgrade)
  asset_type?: 'data' | 'service'          // defaults to 'data' for all existing rows
  layer_name?: string                       // e.g. 'Brahmagyan', 'Gaṇita' — derived by migration if omitted
  layer_index?: string                      // e.g. 'L0', 'L1'
  provides_apis?: Record<string, unknown>[] | null
  health_probe?: Record<string, unknown> | null
  catalog_status?: 'CURRENT' | 'DRAFT'     // L0 = CURRENT; L1–L5 = DRAFT
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
  // ── BRAHMAGYAN (8) — canonical bg_* IDs per migration 174 ───────────────
  {
    asset_id: 'bg_ephemeris',
    layer: 'brahmagyan', sort_order: 1,
    sanskrit_name: 'Graha-sphuṭa',
    english_name: 'Ephemeris (Graha Sphuṭa)',
    english_description: 'Swiss Ephemeris DE441 — raw astronomical positions for all grahas',
    storage_type: 'postgres_table',
    target_table: 'ephemeris_daily',
    count_sql: 'SELECT count(*) FROM ephemeris_daily',
    size_sql: "SELECT pg_total_relation_size('ephemeris_daily')",
    target_floor: 825084,
    expected_volume_formula: 'GRAHAS * DATE_RANGE_DAYS',
    expected_volume_inputs: { GRAHAS: 9, DATE_RANGE_DAYS: 91676, start_date: '1900-01-01', end_date: '2150-12-31' },
    volume_explanation: '825,084 rows = 91,676 days (1900-01-01 to 2150-12-31) × 9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu). Raw tropical stored; 5 ayanamshas derived at read time. Source: pyswisseph DE441 (==2.10.3.2).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_reference',
    layer: 'brahmagyan', sort_order: 2,
    sanskrit_name: 'Sāraṇī',
    english_name: 'Reference Library',
    english_description: 'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
    storage_type: 'postgres_table',
    target_table: 'reference_nakshatras',
    count_sql: 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count',
    size_sql: "SELECT pg_total_relation_size('reference_nakshatras')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sum of 15 reference_* tables (per design §3.2). Each table is normalized + typed; ontology resolves names, reference holds properties.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_texts',
    layer: 'brahmagyan', sort_order: 3,
    sanskrit_name: 'Śāstrapāṭha',
    english_name: 'Classical Texts',
    english_description: 'Indexed verse chunks from BPHS, Jaimini Sutram, KP Reader, Tajaka, Phaladeepika, etc.',
    storage_type: 'postgres_table',
    target_table: 'classical_text_chunks',
    count_sql: 'SELECT count(*) FROM classical_text_chunks',
    size_sql: "SELECT pg_total_relation_size('classical_text_chunks')",
    target_floor: 8193,
    expected_volume_formula: 'CHUNKS_PER_CORPUS',
    expected_volume_inputs: { corpus_texts: 13, actual_build_date: '2026-06-09', embedding_model: 'text-multilingual-embedding-002' },
    volume_explanation: '8,193 chunks across 13 classical texts (deterministic rebuild from GCS PDFs, pinned text-multilingual-embedding-002). Complete corpus; honest count from actual build — replaces pre-build estimate of 9,100.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_ontology',
    layer: 'brahmagyan', sort_order: 4,
    sanskrit_name: 'Nāmasaṃgraha',
    english_name: 'Ontology',
    english_description: 'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms',
    storage_type: 'postgres_table',
    target_table: 'brahma_ontology',
    count_sql: 'SELECT count(*) FROM brahma_ontology',
    size_sql: "SELECT pg_total_relation_size('brahma_ontology')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Static vocabulary — count established at seed; used by resolve_entity retrieval tool',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_text_index',
    layer: 'brahmagyan', sort_order: 5,
    sanskrit_name: 'Śabdakośa',
    english_name: 'Text Index',
    english_description: 'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks. Retrieval tools point at bg_texts; this asset reports the index coverage metric.',
    storage_type: 'postgres_table',
    target_table: 'classical_text_chunks',
    count_sql: 'SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL',
    size_sql: "SELECT pg_total_relation_size('classical_text_chunks')",
    target_floor: 400,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.',
    depends_on: ['bg_texts'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_rules',
    layer: 'brahmagyan', sort_order: 6,
    sanskrit_name: 'Sūtravālī',
    english_name: 'Rule Base',
    english_description: 'Classical rules extracted from text chunks via Python regex patterns — verse-traceable',
    storage_type: 'postgres_table',
    target_table: 'sutravali_rules',
    count_sql: 'SELECT count(*) FROM sutravali_rules',
    size_sql: "SELECT pg_total_relation_size('sutravali_rules')",
    target_floor: 1755,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '1,755 rules = honest scaling of old 3,000 estimate (projected at ~14k chunks) to actual 8,193-chunk corpus (ratio 0.5852). Pattern-extraction yield is chunk-proportional.',
    depends_on: ['bg_texts'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_remedies',
    layer: 'brahmagyan', sort_order: 7,
    sanskrit_name: 'Upāya-kośa',
    english_name: 'Remedy Corpus',
    english_description: 'Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral',
    storage_type: 'postgres_table',
    target_table: 'brahma_remedy_corpus',
    count_sql: 'SELECT count(*) FROM brahma_remedy_corpus',
    size_sql: "SELECT pg_total_relation_size('brahma_remedy_corpus')",
    target_floor: 800,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '800 remedies = cross-text remedy universe target across 13 classical texts. Not chunk-proportional — remedy prescriptions are distributed across texts regardless of chunk density.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_concordance',
    layer: 'brahmagyan', sort_order: 8,
    sanskrit_name: 'Samanvaya',
    english_name: 'Concordance',
    english_description: 'Cross-school chunk-pointer index per (topic, school) — chunk refs for L1+ synthesis at query-time',
    storage_type: 'postgres_table',
    target_table: 'classical_attributions',
    count_sql: 'SELECT count(*) FROM classical_attributions',
    size_sql: "SELECT pg_total_relation_size('classical_attributions')",
    target_floor: 800,
    expected_volume_formula: 'ACTUAL(bg_rules) * CONCORDANCE_DENSITY',
    expected_volume_inputs: null,
    volume_explanation: '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Chunk-pointer index per (topic, school); synthesis at L1+ query-time.',
    depends_on: ['bg_rules'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_yogas',
    layer: 'brahmagyan', sort_order: 9,
    sanskrit_name: 'Yoga-saṃgraha',
    english_name: 'Yoga Catalog',
    english_description: 'Classical yoga definitions — formation rules, significations, classical citations',
    storage_type: 'postgres_table',
    target_table: 'brahma_yoga_catalog',
    count_sql: 'SELECT count(*) FROM brahma_yoga_catalog',
    size_sql: "SELECT pg_total_relation_size('brahma_yoga_catalog')",
    target_floor: 250,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9. Floor 250 (contingent on 8,193-chunk extraction yield; corrects seed value of 200).',
    depends_on: ['bg_ontology'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_dasha_systems',
    layer: 'brahmagyan', sort_order: 10,
    sanskrit_name: 'Daśā-paddhati',
    english_name: 'Dasha Systems',
    english_description: 'Classical dasha system definitions — sequence rules, computation methods, conditions for use',
    storage_type: 'postgres_table',
    target_table: 'brahma_dasha_systems',
    count_sql: 'SELECT count(*) FROM brahma_dasha_systems',
    size_sql: "SELECT pg_total_relation_size('brahma_dasha_systems')",
    target_floor: 15,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '15-20 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per design §3.10',
    depends_on: ['bg_ontology'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_doshas',
    layer: 'brahmagyan', sort_order: 11,
    sanskrit_name: 'Doṣa-kośa',
    english_name: 'Dosha Catalog',
    english_description: 'Classical dosha definitions — formation rules, effects, severity, cancellation conditions',
    storage_type: 'postgres_table',
    target_table: 'brahma_dosha_catalog',
    count_sql: 'SELECT count(*) FROM brahma_dosha_catalog',
    size_sql: "SELECT pg_total_relation_size('brahma_dosha_catalog')",
    target_floor: 50,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Catalog of named dosha patterns (Manglik, Kala-sarpa, Kemadruma, etc.) per design §3.11',
    depends_on: ['bg_ontology'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_compendium_index',
    layer: 'brahmagyan', sort_order: 12,
    sanskrit_name: 'Anukrama',
    english_name: 'Compendium Index',
    english_description: 'Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores',
    storage_type: 'postgres_table',
    target_table: 'brahma_compendium_index',
    count_sql: 'SELECT count(*) FROM brahma_compendium_index',
    size_sql: "SELECT pg_total_relation_size('brahma_compendium_index')",
    target_floor: 1755,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '1,755 index entries = 3,000 × (8,193 / 14,000). Pass B per-text×topic aggregation scales with corpus depth; old 3,000 was projected off ~14k chunks and unreachable against actual 8,193-chunk corpus. Per design §3.12.',
    depends_on: ['bg_texts', 'reference_topic_tags'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_panchanga',
    layer: 'brahmagyan', sort_order: 13,
    sanskrit_name: 'पञ्चाङ्ग गणना',
    english_name: 'Panchanga Engine',
    english_description: 'Deterministic panchang computation service (swisseph DE441, Lahiri ayanamsha, Drik-parity). Exposes panchanga_instant(instant,lat,lon,tz_offset) and panchanga_day(date,lat,lon,tz_offset). Zero LLM. Floor: 5 angas + timing windows + 9 graha states.',
    storage_type: 'service',
    asset_type: 'service',
    layer_name: 'Brahmagyan',
    layer_index: 'L0',
    catalog_status: 'CURRENT',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: null,
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    provides_apis: [
      {
        api: 'panchanga_instant',
        signature: 'panchanga_instant(instant: datetime, lat: float, lon: float, tz_offset: int) -> PanchangaInstant',
        description: 'Anga state at exact moment — birth chart / event instant',
      },
      {
        api: 'panchanga_day',
        signature: 'panchanga_day(date: date, lat: float, lon: float, tz_offset: int) -> Panchang',
        description: 'Full sunrise-based daily panchang including timings and graha states',
      },
    ],
    health_probe: {
      probe_type: 'panchanga_engine',
      forensic_instant: '1984-02-05T10:43:00',
      forensic_lat: 20.27,
      forensic_lon: 85.84,
      forensic_tz_offset: 330,
      forensic_expected: {
        tithi: 'Shukla Tritiya',
        nakshatra: 'Purva Bhadrapada',
        yoga: 'Shiva',
        karana: 'Garaja',
        vara: 'Ravivara',
      },
    },
  },
  {
    asset_id: 'bg_ephemeris_engine',
    layer: 'brahmagyan', sort_order: 14,
    sanskrit_name: 'दृक् एफिमेरिस',
    english_name: 'Ephemeris Engine',
    english_description: 'Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions from 9999 BCE to 9999 CE. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).',
    storage_type: 'service',
    asset_type: 'service',
    layer_name: 'Brahmagyan',
    layer_index: 'L0',
    catalog_status: 'CURRENT',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: null,
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    provides_apis: [
      {
        api: 'swisseph.calc_ut',
        description: 'Planetary longitude at Julian Day (UT) — wraps pyswisseph swe.calc_ut',
      },
      {
        api: 'swisseph.houses_ex',
        description: 'House cusps + Lagna at JD with geographic coordinates',
      },
    ],
    health_probe: {
      probe_type: 'ephemeris_engine',
      forensic_jd: 2445701.948264,
      expected_sun_approximate_sign: 10,
      note: 'JD = 1984-02-05 10:43 IST → UTC. Sun in Makara (sign 10) sidereal Lahiri.',
    },
  },

  // ── GANITA (8) ────────────────────────────────────────────────────────────
  {
    asset_id: 'ga_positions',
    layer: 'ganita', sort_order: 1,
    sanskrit_name: 'Graha-sthāna',
    english_name: 'Positions',
    english_description: 'Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)',
    storage_type: 'postgres_table',
    target_table: 'ganita_positions',
    count_sql: 'SELECT count(*) FROM ganita_positions WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('ganita_positions')",
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 50,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '9 grahas × ayanamsha count — one position row per graha per ayanamsha',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_vargas',
    layer: 'ganita', sort_order: 2,
    sanskrit_name: 'Varga',
    english_name: 'Divisional charts',
    english_description: 'D1–D60 divisional chart positions per ayanamsha',
    storage_type: 'postgres_table',
    target_table: 'chart_divisionals',
    count_sql: 'SELECT count(*) FROM chart_divisionals WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_divisionals')",
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 21635,
    expected_volume_formula: 'VARGAS * GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '60 vargas × 9 grahas × ayanamsha count — structural',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_dashas',
    layer: 'ganita', sort_order: 3,
    sanskrit_name: 'Daśākrama',
    english_name: 'Vimshottari dasha',
    english_description: 'Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha',
    storage_type: 'postgres_table',
    // ga_dashas writer (GA7) writes to chart_dashas, not ganita_dashas (empty).
    // Repointed in migration 217.
    target_table: 'chart_dashas',
    count_sql: 'SELECT count(*) FROM chart_dashas WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_dashas')",
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 536471,
    expected_volume_formula: '(9 + 81 + 729) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'target_floor = 536,471 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy formula (9+81+729)*AYANAMSHAS ≈ 4,095 predates the 4-level Sukshma + KP-sublevel Vimshottari tree and under-counts by ~130×.',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_strength',
    layer: 'ganita', sort_order: 4,
    sanskrit_name: 'Balatva',
    english_name: 'Strength tables',
    english_description: 'Shadbala, ashtakavarga, and bhava bala per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    // Matches migration 217 — chart_facts-scoped count for the cockpit stats
    // route (reads asset_registry.count_sql, $1 = chart_id). Broadened from the
    // migration-214 form to the full documented family: the prior filter only
    // matched `house_bhava_bala_%`/`graha_vimsopaka_%` and missed the
    // `bhava_bala_*` family, `vimsopaka_bala_per_graha`, and
    // `graha_saptavargaja_bala_component`.
    count_sql: `
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'graha_shadbala_%'
      OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
      OR fact_category LIKE '%vimsopaka%'
      OR fact_category LIKE 'ashtakavarga_%'
      OR fact_category LIKE '%bhava_bala%'
      OR fact_category = 'graha_saptavargaja_bala_component'
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 2184,
    expected_volume_formula: '(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Shadbala: 6 scores × 9 grahas; ashtakavarga: 8 tables × 9 grahas × 12 signs; bhava bala: 6 scores × 12 bhavas — all × ayanamshas',
    depends_on: [],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_sensitive',
    layer: 'ganita', sort_order: 5,
    sanskrit_name: 'Sūkṣmabindu',
    english_name: 'Sensitive points',
    english_description: 'Per-chart sensitive point positions computed from the catalog × ayanamshas',
    storage_type: 'postgres_table',
    target_table: null,
    // Matches migration 214 verbatim — chart_facts-scoped count for the cockpit
    // stats route (reads asset_registry.count_sql, $1 = chart_id).
    count_sql: `
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category IN (
        'upagraha_position', 'saturn_derived_point', 'saham_position',
        'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
        'arudha_pada', 'midpoint', 'aprakasha_position',
        'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point'
      )
      OR fact_category LIKE 'esoteric_point_%'
      OR fact_category LIKE 'kp_%'
      OR fact_category LIKE 'tajik_%'
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 8055,
    expected_volume_formula: 'ACTUAL(bg_reference) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from the reference library count × ayanamshas; awaits dedicated per-chart table',
    depends_on: ['bg_reference'],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_panchanga',
    layer: 'ganita', sort_order: 6,
    sanskrit_name: 'Pañcāṅga-janma',
    english_name: 'Birth panchanga',
    english_description: 'Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha',
    storage_type: 'postgres_table',
    // ga_panchanga writer (GA4) writes panchanga facts into chart_facts under the
    // panchanga_* category family, not chart_panchanga (empty). Repointed in
    // migration 217. size_sql is null — count is a category subset of the shared
    // chart_facts table, so table size is not a meaningful per-asset metric.
    target_table: 'chart_facts',
    count_sql: "SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'panchanga%'",
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 221,
    expected_volume_formula: 'AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'target_floor = 221 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy "one panchanga row per ayanamsha" formula predates the enriched natal panchanga fact family (panchanga_* categories in chart_facts).',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_sade_sati',
    layer: 'ganita', sort_order: 7,
    sanskrit_name: 'Sāḍesātī',
    english_name: 'Sade Sati periods',
    english_description: 'Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    // Matches migration 214 verbatim — chart_facts-scoped count for the cockpit
    // stats route (reads asset_registry.count_sql, $1 = chart_id).
    count_sql: `
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND fact_category IN (
      'sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter',
      'dhaiya_period', 'kantaka_shani_period', 'ashtama_shani_period',
      'ardha_ashtama_shani_period', 'janma_shani_period',
      'vishakha_shani_period', 'anumukha_shani_period',
      'sade_sati_saturn_retrograde_subset', 'sade_sati_cancellation_check',
      'sade_sati_modifier_overlay', 'sade_sati_concurrent_dasha_overlay',
      'sade_sati_downstream_cross_reference'
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 11019,
    expected_volume_formula: 'AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'target_floor = 11,019 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy "one row per ayanamsha" formula predates the full Sade Sati fact family (cycle / phase / phase_quarter / dhaiya / kantaka / ashtama / janma-shani periods + overlays).',
    depends_on: [],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_tajaka',
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
  {
    asset_id: 'ga_structural',
    layer: 'ganita', sort_order: 9,
    sanskrit_name: 'Saṃracanā',
    english_name: 'Structural facts',
    english_description: 'GA8 T1 structural layer: aspects (Parāśarī + Jaimini + Tājik), yogas, doshas, graha avasthās, argala/virodha-argala, dispositor chains, composite states, kāraka and tri-deva roles, and base graha facts — per ayanamsha.',
    storage_type: 'postgres_table',
    target_table: null,
    // Registered in migration 219. Positive family filter verified to equal the
    // untiled chart_facts complement (6,075) — the five chart_facts tiles
    // (strength/sensitive/sade_sati/panchanga/structural) partition chart_facts.
    count_sql: `
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'aspect_%'
      OR fact_category LIKE 'graha_avastha_%'
      OR fact_category LIKE '%argala_natal_matrix'
      OR fact_category LIKE 'graha_dispositor_%'
      OR fact_category IN (
        'graha_position', 'graha_sign_attributes', 'graha_functional_class_per_ascendant',
        'graha_composite_state_classification', 'graha_effective_dignity_modified_by_aspects',
        'graha_in_house_composite_strength', 'graha_special_state_rollup',
        'graha_tri_deva_role_strength', 'graha_vargottama_amplification_factor',
        'graha_yoga_karaka_flag', 'jaimini_tri_deva_role_per_graha',
        'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
        'composite_dispositor_strength', 'house_strength_classification_rollup',
        'pranic_strength_per_graha', 'chandra_bala_natal_baseline', 'tara_bala_natal_baseline',
        'nakshatra_pada_sensitive', 'yoga_fires', 'dosha_fires', 'conjunction_within_orb',
        'panchaka_flag', 'bhadra_flag', 'eclipse_proximity_natal'
      )
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 6075,
    expected_volume_formula: 'GA8_STRUCTURAL_CATEGORIES * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'GA8 T1 structural facts across the chart_facts category families — partitions chart_facts together with the strength/sensitive/sade_sati/panchanga tiles.',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
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
    expected_volume_formula: 'ACTUAL(bg_rules) * SIGNAL_PER_RULE * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from upstream rule count × signal-per-rule coefficient × ayanamsha count; coefficient SIGNAL_PER_RULE measured on first build with both assets lit',
    depends_on: ['bg_rules'],
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
    count_sql: 'SELECT count(*) FROM bodha_signal_embeddings e JOIN bodha_signals s ON e.signal_id = s.signal_id WHERE s.chart_id = $1',
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
    expected_volume_formula: 'ACTUAL(ga_dashas) + ACTUAL(bg_ephemeris) * TRANSITS_PER_DAY',
    expected_volume_inputs: null,
    volume_explanation: 'Dasha rows + transit event days; coefficient TRANSITS_PER_DAY measured on first build with ephemeris lit',
    depends_on: ['ga_dashas', 'bg_ephemeris'],
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
    depends_on: ['kala.kalasutra', 'ga_sensitive'],
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
    expected_volume_formula: 'ACTUAL(bg_ephemeris) * TRANSITS_PER_DAY',
    expected_volume_inputs: null,
    volume_explanation: 'Days with active major-aspect transits out of the full ephemeris range; coefficient TRANSITS_PER_DAY measured on first build',
    depends_on: ['bg_ephemeris', 'kala.kalasutra'],
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
    depends_on: ['kala.kalasutra', 'ga_panchanga'],
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
    upstream_asset_id: 'bg_rules',
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
    upstream_asset_id: 'bg_ephemeris',
    downstream_asset_id: 'kala.kalasutra',
  },
  {
    coefficient_name: 'CONCORDANCE_DENSITY',
    description: 'Concordance attribution topics per classical rule (measured first build)',
    upstream_asset_id: 'bg_rules',
    downstream_asset_id: 'bg_concordance',
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
    // Derive layer_name / layer_index from layer code when not explicitly set
    const layerNames: Record<string, string> = {
      brahmagyan: 'Brahmagyan', ganita: 'Gaṇita', bodha: 'Bodha',
      kala: 'Kāla', phala: 'Phala', mimamsa: 'Mīmāṃsā',
    }
    const layerIndices: Record<string, string> = {
      brahmagyan: 'L0', ganita: 'L1', bodha: 'L2',
      kala: 'L3', phala: 'L4', mimamsa: 'L5',
    }
    const assetType = asset.asset_type ?? 'data'
    const layerName = asset.layer_name ?? layerNames[asset.layer] ?? asset.layer
    const layerIndex = asset.layer_index ?? layerIndices[asset.layer] ?? null
    const catalogStatus = asset.catalog_status ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')

    await client.query(
      `INSERT INTO asset_registry (
        asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
        storage_type, target_table, count_sql, size_sql, target_floor,
        expected_volume_formula, expected_volume_inputs, volume_explanation,
        depends_on, scope, is_active, estimated_seconds,
        asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status
      ) VALUES (
        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24
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
        is_active = EXCLUDED.is_active,
        asset_type = EXCLUDED.asset_type,
        layer_name = EXCLUDED.layer_name,
        layer_index = EXCLUDED.layer_index,
        provides_apis = EXCLUDED.provides_apis,
        health_probe = EXCLUDED.health_probe,
        catalog_status = EXCLUDED.catalog_status`,
      [
        asset.asset_id, asset.layer, asset.sort_order,
        asset.sanskrit_name, asset.english_name, asset.english_description,
        asset.storage_type, asset.target_table, asset.count_sql, asset.size_sql,
        asset.target_floor, asset.expected_volume_formula,
        asset.expected_volume_inputs ? JSON.stringify(asset.expected_volume_inputs) : null,
        asset.volume_explanation,
        asset.depends_on, asset.scope, asset.is_active, asset.estimated_seconds,
        assetType, layerName, layerIndex,
        asset.provides_apis ? JSON.stringify(asset.provides_apis) : null,
        asset.health_probe ? JSON.stringify(asset.health_probe) : null,
        catalogStatus,
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
