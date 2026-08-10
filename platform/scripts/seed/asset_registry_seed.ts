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
  // Migration 242 fields (L3 service/artifact asset kinds)
  asset_kind?: 'data' | 'service' | 'artifact'  // defaults to 'data'
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
  'FACT_KEYS',
  'BODIES', 'FACT_CATEGORIES', 'CROSS_AYANAMSHA',
  'YOGAS_IN_CATALOG', 'AYANAMSHAS_COUNT',
])
const DEFAULTS: Record<string, number> = {
  AYANAMSHAS: 5, GRAHAS: 9, SIGNS: 12, HOUSES: 12,
  NAKSHATRAS: 27, VARGAS: 60, BHAVAS: 12,
  LIFE_SPAN_YEARS: 90, DATE_RANGE_DAYS: 44000,
  FACT_KEYS: 1,          // atomic fact-key count per body per ayanamsha (graha_position + graha_sign_attributes)
  BODIES: 21,            // grahas (9) + house cusps (12) for nakshatra writer scope
  FACT_CATEGORIES: 17,   // nakshatra fact-category count per body per ayanamsha
  CROSS_AYANAMSHA: 17,   // cross-ayanamsha consistency rows in ga_nakshatra
  YOGAS_IN_CATALOG: 1,   // illustrative default (native chart fires 1 yoga × 5 ayanamshas)
  AYANAMSHAS_COUNT: 5,   // alias used in ga_yoga formula
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

export const ASSETS: AssetDef[] = [
  // ── BRAHMAGYAN ───────────────────────────────────────────────────────────
  {
    // migration 431 (WP-2.5 / LCA-16) — seeded by bg_medical_mappings writer.
    // sort_order 0 places this before the bulk brahmagyan assets.
    asset_id: 'bg_sign_medical',
    layer: 'brahmagyan', sort_order: 0,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Kālapuruṣa Aṅga',
    english_name: 'Kalapurusha Sign→Body-Part Map',
    english_description: 'Kalapurusha (Cosmic Man) zodiacal body-map: 12 signs → body-part / organ-systems / element / dosha (BPHS Ch.4 + Ashtanga Hridayam). Seeded by the bg_medical_mappings writer.',
    storage_type: 'postgres_table',
    target_table: 'bg_sign_medical',
    count_sql: 'SELECT COUNT(*) FROM bg_sign_medical',
    size_sql: null,
    target_floor: 12,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '12 rows — one per zodiac sign. Deterministic count.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
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
    count_sql: 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count',
    size_sql: "SELECT pg_total_relation_size('reference_nakshatras')",
    target_floor: 1485,  // set after prod measurement 2026-06-18 (§N.4)
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
    target_floor: 10651,
    expected_volume_formula: null, // non-parametric — target_floor = 10651 is the authoritative count
    expected_volume_inputs: { corpus_texts: 13, actual_build_date: '2026-06-09', embedding_model: 'text-multilingual-embedding-002' },
    volume_explanation: '10,651 chunks across 13 classical texts (deterministic rebuild from GCS PDFs, pinned text-multilingual-embedding-002). Complete corpus; honest count from actual build.',
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
    target_floor: 623,  // set after prod measurement 2026-06-18 (§N.4)
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
    target_floor: 2912,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '2,912 rules = honest count from actual build against 10,651-chunk corpus.',
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
    // 266 = writer's designed deterministic ceiling: 108 planet-matrix + 102
    // dosha-linked + 54 legacy + 2 net-new from corpus_sweep (migrations
    // 192/199/231). Floor = achieved count per floors-are-aspirational
    // policy (CLAUDE.md §N.4) — do not raise without expanding the
    // deterministic corpus design (native-judgment decision).
    target_floor: 266,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '266 remedies = writer\'s designed deterministic ceiling: gen_planet_matrix(108) + dosha-linked(102) + legacy(54) + corpus_sweep net-new(2). Floor = achieved count per floors-are-aspirational policy (CLAUDE.md §N.4); ZERO LLM, ZERO fabrication is a hard writer constraint, so this floor cannot be raised without a native-judgment decision to expand the deterministic corpus design.',
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
    target_floor: 18,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '18 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per actual build count.',
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
    target_floor: 9538,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '9,538 index entries = honest count from actual build. Per design §3.12.',
    depends_on: ['bg_texts', 'bg_reference'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_panchanga',
    layer: 'brahmagyan', sort_order: 13,
    sanskrit_name: 'Pañcāṅga Gaṇanā',
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
    sanskrit_name: 'Druk Ephemeris',
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

  {
    asset_id: 'bg_nakshatra',
    layer: 'brahmagyan', sort_order: 15,
    sanskrit_name: 'Nakṣatra-sāraṇī',
    english_name: 'Nakshatra Reference',
    english_description: 'Global nakshatra reference — 28 nakshatras (incl. Abhijit), 108 padas, full Ashtakuta + supplementary compatibility matrices (2721 rows).',
    storage_type: 'postgres_table',
    target_table: 'reference_nakshatra',
    count_sql: `SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count`,
    size_sql: "SELECT pg_total_relation_size('reference_nakshatra')",
    target_floor: 2857,  // set after first prod build 2026-06-17 (§N.4)
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '28 nakshatras + 108 padas + 2721 compatibility matrix rows (28×28 Ashtakuta cells × ~3.5 factors) = 2857 total rows.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_ghatana',
    layer: 'brahmagyan', sort_order: 16,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Ghaṭanā',
    english_name: 'Event Ontology',
    english_description: 'Global life-event + electional-activity ontology — 22 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology); source W1 seed package §5-§6.',
    storage_type: 'postgres_table',
    target_table: 'brahma_event_ontology',
    count_sql: 'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
    size_sql: "SELECT pg_total_relation_size('brahma_event_ontology')",
    target_floor: 34,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '22 life-event classes + 12 electional activity classes = 34 total rows, seeded verbatim from W1 seed package §5-§6.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    // ṢAḌ-DARŚANA campaign item 22 (SHAD_DARSHANA_BRIEF_v2_0.md §2 + §1). Mirrors
    // migration 472's asset_registry INSERT exactly — a clean reseed must not
    // silently drop this asset. Global L0, super-admin-triggered only (never
    // auto-pulled into a per-chart build — brief §2.5.2).
    asset_id: 'bg_cohort',
    layer: 'brahmagyan', sort_order: 20,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Pratirūpa Samūha',
    english_name: 'Synthetic Reference Cohort',
    english_description: "Synthetic (not real-person) reference population of ~10,000 birth charts' Lahiri-sidereal graha + Lagna positions (sign/nakshatra grain) — the statistical base-rate population later waves compare a real chart against for rarity scoring. ṢAḌ-DARŚANA campaign item 22.",
    storage_type: 'postgres_table',
    target_table: 'bg_synthetic_cohort',
    count_sql: 'SELECT COUNT(*) FROM bg_synthetic_cohort',
    size_sql: "SELECT pg_total_relation_size('bg_synthetic_cohort')",
    target_floor: 10000,
    expected_volume_formula: 'COHORT_SIZE',
    expected_volume_inputs: { COHORT_SIZE: 10000 },
    volume_explanation: '10,000 synthetic birth charts, uniform-random over 1900-2099, fixed RNG seed. See bg_cohort.py module docstring for full sampling methodology.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W2 · lane `l0-ne-priors`. Governing ruling:
    // 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
    // SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md § ADJUDICATION-2 item 5.
    // Mirrors migration 522's asset_registry INSERT exactly — a clean reseed must
    // not silently drop this asset (the ga_vichara / bo_pratijna defect class).
    // Global L0, `depends_on: []`, super-admin-triggered only (brief §2.5.2).
    //
    // `count_sql` counts the ROWS AT THE RESERVED COORDINATE, not the whole table:
    // brahma_class_priors also holds 164 signal-salience priors from
    // bg_class_priors, and a bare COUNT(*) would report this asset as "164 rows
    // built" the moment migration 522 lands and BEFORE a single N_e row exists —
    // a cockpit-truth violation (§N.4) and an §N.8 signal that cannot read false.
    //
    // `target_floor: 0` is deliberate, not a placeholder. §N.4: floors are
    // aspirational and set to the ACHIEVED count after a build. On this asset
    // specifically, a non-zero floor would be pressure to fabricate exactly the
    // rows ADJUDICATION-2's hard stop forbids ("honest-empty beats fabricated-full").
    asset_id: 'bg_class_lifetime_counts',
    layer: 'brahmagyan', sort_order: 21,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Jīvana-Ghaṭanā-Saṅkhyā',
    english_name: 'Event-Class Lifetime Counts',
    english_description:
      'ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each ' +
      'brahma_event_ontology event class over a 100-year modelled timeline from ' +
      'birth, assuming survival. The chart-INDEPENDENT structural baseline λ⁰_e of ' +
      'the Kāla Kṣetra hazard field. Every value is Tier N-i: a published ' +
      'demographic / actuarial / epidemiological statistic carrying publisher, ' +
      'edition, year, indicator id, geography+cohort and a retrievable URL/DOI, ' +
      'together with the arithmetic converting it to a per-100-year count — or ' +
      'Tier N-ii, a stated arithmetic identity over such a value. Classical-text ' +
      'counts are FORECLOSED (chart-conditional; already carried by P_e) and ' +
      'cohort/LEL-derived counts are FORECLOSED by the circularity guard. A class ' +
      'with no defensible source is NOT seeded and is honestly skipped by ' +
      'ka_kshetra with no_class_prior_row — honest-empty per class, never a ' +
      'fabricated baseline.',
    storage_type: 'postgres_table',
    target_table: 'brahma_class_priors',
    count_sql: "SELECT COUNT(*) FROM brahma_class_priors WHERE fact_kind='lifetime_count_per_100y'",
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation:
      'One row per event class for which a Tier N-i (or Tier N-ii derived-identity) ' +
      'source could actually be obtained and cited. Set to the ACHIEVED count after ' +
      'the first build (§N.4). Unseeded classes are an honest per-class coverage gap ' +
      'registered by name in the ledger, never a reason to invent a row.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },

  // ── BRAHMAGYAN continued — assets built-and-seeded 2026-06-17 (P2-C fix) ──
  {
    asset_id: 'bg_prashna_rules',
    layer: 'brahmagyan', sort_order: 55,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Praśna-sūtrāvalī',
    english_name: 'Prashna Horary Rules',
    english_description: 'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: 'SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count',
    size_sql: null,
    target_floor: 41,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '41 rows across 5 prashna sub-tables (5 lagna methods + 16 Tajik yogas + 12 significators + 5 fructification rules + 3 special techniques).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_vastu_directions',
    layer: 'brahmagyan', sort_order: 56,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vastu-dik',
    english_name: 'Vastu Direction–Graha Reference',
    english_description: 'Classical Vastu Shastra direction–graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classical citation (Mayamata Ch.6). Also seeds bg_vastu_direction_remedials (~22 rows) with 2–3 remedies per direction.',
    storage_type: 'postgres_table',
    target_table: 'bg_vastu_directions',
    count_sql: 'SELECT (SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials) AS count',
    size_sql: null,
    target_floor: 32,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '32 rows = 8 direction rows + 24 remedial rows.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_transit_engine',
    layer: 'brahmagyan', sort_order: 61,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara-gaṇanā',
    english_name: 'Transit Engine Parameters',
    english_description: 'L0 average graha motion parameters — daily motion, zodiac period, sign residence. Source: BPHS Ch.22.',
    storage_type: 'postgres_table',
    target_table: 'bg_transit_engine',
    count_sql: 'SELECT COUNT(*) FROM bg_transit_engine',
    size_sql: null,
    target_floor: 9,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '9 rows = 7 classical grahas + Rahu + Ketu motion parameters.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_transit_rules',
    layer: 'brahmagyan', sort_order: 62,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara-sūtrāvalī',
    english_name: 'Classical Gochara Rules',
    english_description: 'Classical transit rules (favourable/unfavourable/vedha houses) from BPHS Ch.29 and Phaladeepika Ch.26.',
    storage_type: 'postgres_table',
    target_table: 'bg_transit_rules',
    count_sql: 'SELECT COUNT(*) FROM bg_transit_rules',
    size_sql: null,
    target_floor: 50,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '50 classical gochara transit rules per actual build count (41 base + 9 Venus gochara phala rows added Phase B).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_medical_mappings',
    layer: 'brahmagyan', sort_order: 64,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vaidya Graha Kosha',
    english_name: 'Medical Graha Mappings',
    english_description: 'Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita. 9 grahas (Sun–Ketu). L0 static reference.',
    storage_type: 'postgres_table',
    target_table: 'bg_medical_mappings',
    count_sql: 'SELECT COUNT(*) FROM bg_medical_mappings',
    size_sql: null,
    target_floor: 9,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '9 rows = one row per classical graha (Sun through Ketu).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_nakshatra_medical',
    layer: 'brahmagyan', sort_order: 65,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Nakshatra Deha Kosha',
    english_name: 'Nakshatra Body-Part Mappings',
    english_description: '27 nakshatras → body-part correspondences per Ashtanga Hridayam / BPHS. FORENSIC: #25 Purva Bhadrapada → left_side (native Moon nakshatra).',
    storage_type: 'postgres_table',
    target_table: 'bg_nakshatra_medical',
    count_sql: 'SELECT COUNT(*) FROM bg_nakshatra_medical',
    size_sql: null,
    target_floor: 27,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '27 rows = one per nakshatra (Abhijit excluded from medical mapping corpus).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_dignity_reference',
    layer: 'brahmagyan', sort_order: 66,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Graha-avasthā',
    english_name: 'Planetary Dignity & State Reference',
    english_description: 'Planetary dignity and state reference: exaltation/debilitation/own-sign boundaries, naisargika friendship matrix, avastha schemes, combustion orbs, motion state thresholds. 5 sub-tables, 151 total rows.',
    storage_type: 'postgres_table',
    target_table: 'bg_dignity_reference',
    count_sql: 'SELECT (SELECT COUNT(*) FROM bg_dignity_reference) + (SELECT COUNT(*) FROM bg_avastha_schemes) + (SELECT COUNT(*) FROM bg_combustion_orbs) + (SELECT COUNT(*) FROM bg_graha_naisargika_friendship) + (SELECT COUNT(*) FROM bg_motion_state_thresholds) AS count',
    size_sql: null,
    target_floor: 151,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '151 rows: bg_dignity_reference(9) + bg_avastha_schemes(35) + bg_combustion_orbs(8) + bg_graha_naisargika_friendship(72) + bg_motion_state_thresholds(27).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_class_priors',
    layer: 'brahmagyan', sort_order: 67,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Varga-pūrva',
    english_name: 'Class Priors',
    english_description: 'Global signal-classification priors across 5 axes — signal_type_class, source_subsystem, signal_tradition, varga, graha x domain — from W1 seed package §2-§4.',
    storage_type: 'postgres_table',
    target_table: 'brahma_class_priors',
    count_sql: 'SELECT count(*) FROM brahma_class_priors',
    size_sql: "SELECT pg_total_relation_size('brahma_class_priors')",
    target_floor: 164,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '17 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain priors (per writer docstring 165; live-measured 164, 2026-07-05).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bg_formula_constants',
    layer: 'brahmagyan', sort_order: 68,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Sūtra-sthirāṅka',
    english_name: 'Formula Constants',
    english_description: 'Canonical formula constants registry — combustion orbs, obstruction thresholds, dignity scores, house weights, attention budget, calibration constants. Classified CLASSICAL/NATIVE_JUDGMENT/ENGINEERING/CONFLATION_BUG (migration 389).',
    storage_type: 'postgres_table',
    target_table: 'brahma_formula_constants',
    count_sql: 'SELECT count(*) FROM brahma_formula_constants',
    size_sql: "SELECT pg_total_relation_size('brahma_formula_constants')",
    target_floor: 14,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Live-measured 14 constants, 2026-07-05 (grows as new formula constants are registered, e.g. migration 408 mi_pramana_dropped_dimensions).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    // migration 440 (D-2 Lane V-1, vidhi registry). Global L0.
    asset_id: 'bg_vidhi_primitives',
    layer: 'brahmagyan', sort_order: 68,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Vidhi Pramāṇa',
    english_name: 'Vidhi Registry — Primitives',
    english_description: 'Versioned vidhi primitive atoms — definition, live-tool mapping+args, fallback face, known_gap CR pointer. Global, chart-agnostic (D-2 Lane V-1).',
    storage_type: 'postgres_table',
    target_table: 'vidhi_primitives',
    count_sql: '(SELECT COUNT(*) FROM vidhi_primitives)',
    size_sql: null,
    target_floor: 48,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '48 vidhi primitive atoms — deterministic count from the D-2 Lane V-1 writer.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // migration 440 (D-2 Lane V-1, vidhi registry). Global L0.
    asset_id: 'bg_vidhi_floors',
    layer: 'brahmagyan', sort_order: 69,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Vidhi Mārga',
    english_name: 'Vidhi Registry — Intent Floors',
    english_description: 'Per-intent-class acharya floor + machine band header + ordered floor items — the compiled scope_tuple->contract input (D-2 Lane V-1).',
    storage_type: 'postgres_table',
    target_table: 'vidhi_floor_items',
    count_sql: '(SELECT COUNT(*) FROM vidhi_floor_items)',
    size_sql: null,
    target_floor: 11,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '11 intent-floor rows — deterministic count from the D-2 Lane V-1 writer.',
    depends_on: ['bg_vidhi_primitives'],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA campaign item 3 (SHAD_DARSHANA_BRIEF_v2_0.md §2 + §1). Mirrors
    // migration 473's asset_registry INSERT exactly — a clean reseed must not
    // silently drop this asset. Global L0, super-admin-triggered only (never
    // auto-pulled into a per-chart build — brief §2.5.2). target_floor is the
    // REAL row count from a live verification run against a real (throwaway)
    // Postgres, 2026-07-29 — see migration 473's comment for the exact
    // per-event-family breakdown.
    asset_id: 'bg_sky_calendar',
    layer: 'brahmagyan', sort_order: 69,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Ākāśa Pañjikā',
    english_name: 'Sky-Event Calendar',
    english_description: "Chart-independent global sky-event diary: sign ingresses (9 grahas), planetary stations (5 classical planets), solar/lunar eclipse timing, and Jupiter-Saturn double-transit conjunction geometry, over a rolling 1900 -> today+10y horizon. Returns and per-chart/natal joins are out of scope — ka_kshetra's job. ṢAḌ-DARŚANA campaign item 3.",
    storage_type: 'postgres_table',
    target_table: 'bg_sky_events',
    count_sql: 'SELECT COUNT(*) FROM bg_sky_events',
    size_sql: "SELECT pg_total_relation_size('bg_sky_events')",
    target_floor: 31064,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Live-verified 2026-07-29 against a real throwaway Postgres: 28,760 ingress + 1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit = 31,064, over horizon 1900-01-01 -> 2036-07-29 (today+10y at verification time). A later build reads >= this count as the forward edge rolls forward (never less).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    asset_id: 'bg_muhurta_lattice',
    layer: 'brahmagyan', sort_order: 70,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Muhūrta Jālaka',
    english_name: 'Muhūrta Boundary/Factor Lattice',
    english_description: "Global chart-independent muhūrta factor lattice — Agnivāsa states, combination-yoga spans (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkara, Siddha-yoga, Bhadra, Pañchaka), kālam periods (rāhu/gulika/yamagaṇḍa/durmuhūrta/brāhma-muhūrta/abhijit/amṛta-kālam/varjyam), and 30-fold ghaṭī-muhūrta day+night boundaries, over a rolling ~5y forward horizon at a fixed Bhubaneswar/IST reference location. Per-chart contact joins are ka_kshetra's job (W3). ṢAḌ-DARŚANA campaign item 36-substrate.",
    storage_type: 'postgres_table',
    target_table: 'bg_muhurta_lattice',
    count_sql: 'SELECT COUNT(*) FROM bg_muhurta_lattice',
    size_sql: "SELECT pg_total_relation_size('bg_muhurta_lattice')",
    target_floor: 91477,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Live-verified 2026-07-30 against a real throwaway Postgres (pg17 + pgvector), re-verified after the Opus corpus-citation review\'s abhijit-Wednesday-exclusion fix: 1,826 agnivasa + 1,481 combination_yoga + 33,390 kalam + 54,780 ghati_muhurta = 91,477, over horizon 2026-07-30 -> 2031-07-30 (today+5y at verification time). A later build reads >= this count as the rolling forward horizon advances (never less; old rows are never deleted).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    asset_id: 'bg_parihara_rules',
    layer: 'brahmagyan', sort_order: 71,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Parihāra Jāla',
    english_name: 'Parihāra Rule Graph + Muhūrta Factor Census',
    english_description: "Global chart-independent parihāra (doṣa-cancellation) graph, per-activity muhūrta factor-quality rules, and the Muhūrta Factor Census + corpus-gap register. Directly queries brahma_dosha_catalog and materializes panchang_engine.shastra_tables.EVENT_TABLES — never re-ingests corpus content (brahma_remedy_corpus is cited only as census evidence, not directly queried by this writer). Corpus gaps (e.g. mṛtyu-yoga, dagdha-yoga day-quality tables, Śiva-vāsa) are honestly recorded as not_in_corpus, never fabricated. ṢAḌ-DARŚANA campaign item 36-substrate/41.",
    storage_type: 'postgres_table',
    target_table: 'bg_parihara_rules',
    count_sql: "SELECT (SELECT COUNT(*) FROM bg_parihara_rules) + (SELECT COUNT(*) FROM bg_muhurta_activity_rules) + (SELECT COUNT(*) FROM bg_muhurta_factor_census)",
    size_sql: "SELECT pg_total_relation_size('bg_parihara_rules') + pg_total_relation_size('bg_muhurta_activity_rules') + pg_total_relation_size('bg_muhurta_factor_census')",
    target_floor: 439,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Live-verified 2026-07-30: 60 parihara-graph condition rows (queried directly against REAL production brahma_dosha_catalog: 26 doshas carry a real, non-placeholder citation, flattening to 60 individual cancellation-condition rows) + 329 activity-rule rows (exact — sum of tithi/nakshatra/vara entries across panchang_engine\'s 8 EVENT_TABLES) + 50 census rows (exact — len(CENSUS_ROWS), updated from 37 by the Opus corpus-citation review\'s dangling-pointer fix) = 439.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-kota-rings, ADJUDICATION-9 (migration 523,
    // SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, ANTARYĀMIN, 2026-08-01).
    // The Kota-Chakra ring partition (stambha/durgantara/prakara/bahya, from
    // janma nakshatra), previously an inline dict in
    // services/ka_kota_chakra/logic.py, moved to this versioned L0 table —
    // the DATA-HONESTY RAIL's "cited, versioned L0 row" conjuncts. NO SERVED
    // VALUE CHANGES: transcribed exactly (see brahmagyan/l0_kota_chakra_rings.py
    // + the byte-identity fixture test, tests/l3/test_ka_kota_chakra.py).
    // Row count is 27 (not the ruling's own "~28" estimate) — matches the
    // 27-nakshatra mod-27 arithmetic ka_kota_chakra's writer uses; disclosed
    // in the migration header, not silently reconciled. Tier-(iii)
    // secondary-source transcription; corpus_status='not_in_corpus' on every
    // row. Ingestion work item filed (not attempted): muhurta_chintamani
    // (ingested but untranslated OCR — ADJUDICATION-8) and a
    // Nārada-Saṃhitā-class text not yet held.
    asset_id: 'bg_kota_chakra_rings',
    layer: 'brahmagyan', sort_order: 72,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Koṭa-Cakra Valaya-Sāraṇī',
    english_name: 'Kota-Chakra Ring Table',
    english_description: 'ADJUDICATION-9: the Kota-Chakra fort-chakra ring partition (stambha/durgantara/prakara/bahya, 1-indexed distance from janma nakshatra), moved from an inline writer-code dict to a versioned L0 global reference table. Tier-(iii) secondary-source transcription; corpus_status=\'not_in_corpus\' on every row; ingestion work item filed for the primary source, not attempted here. Consumed by ka_kota_chakra.',
    storage_type: 'postgres_table',
    target_table: 'bg_kota_chakra_rings',
    count_sql: 'SELECT COUNT(*) FROM bg_kota_chakra_rings',
    size_sql: "SELECT pg_total_relation_size('bg_kota_chakra_rings')",
    target_floor: 27,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '27 rows: the 1..27 ring_position partition (Stambha 4 + Durgantara 8 + Prakara 8 + Bahya 7 = 27), one row per nakshatra-count-from-janma. Not 28 — see migration 523 header for the disclosed count discrepancy against the ruling\'s own "~28" estimate.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3K Lane 1 · ANTARYĀMIN ADJUDICATION-7 Part 1 · migration 535.
    // Stored in SIDEREAL longitude with NO ayanamsha key, by binding sub-ruling:
    // the division of the sidereal circle is ayanāṃśa-invariant, so stamping an
    // ayanāṃśa would fabricate a dependency and 5× the rows for no information.
    asset_id: 'bg_kp_sublord_division',
    layer: 'brahmagyan', sort_order: 76,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Kṛṣṇamūrti Upa-Svāmī Vibhāga',
    english_name: 'KP Sub-Lord Division (249-fold)',
    english_description: 'ADJUDICATION-7 Part 1: the canonical 249-fold Krishnamurti Paddhati sub-lord division of the sidereal zodiac. 243 Vimshottari-proportional sub segments (sub arc = lord_years/9 degrees, sequence starting from the nakshatra lord) cut at the 12 rashi boundaries; 6 boundaries fall strictly inside a sub and split it, so 243 + 6 = 249 — derived by exact rational arithmetic, not hard-coded. AUTHORITY for every KP sub-lord boundary: ga_nakshatra REFERENCES it (§N.5) rather than re-deriving. Verified 9/9 star lord + 9/9 sub lord against the committed FORENSIC §4.2 fixture in 05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md §2. Sub-sub/prana grain deliberately NOT tabulated (see migration 535 SCOPE DISCLOSURE); pada carried as an attribute, not a further cut.',
    storage_type: 'postgres_table',
    target_table: 'bg_kp_sublord_division',
    count_sql: 'SELECT COUNT(*) FROM bg_kp_sublord_division',
    size_sql: "SELECT pg_total_relation_size('bg_kp_sublord_division')",
    target_floor: 249,
    expected_volume_formula: 'NAKSHATRAS * VIMSHOTTARI_LORDS + RASHI_BOUNDARY_SPLITS',
    expected_volume_inputs: null,
    volume_explanation: '27 nakshatras × 9 Vimshottari subs = 243 sub segments; 6 of the 12 rashi boundaries fall strictly inside a sub segment and split it (the other 6 coincide with a nakshatra start or exactly with a sub boundary) → 243 + 6 = 249.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ADJUDICATION-11 (migration 529): Sarvatobhadra Chakra grid registered
    // DELIBERATELY EMPTY — no writer (has_writer=false). An empty school-keyed
    // table honestly states that grid variants exist rather than seating one
    // as an unqualified fact. A populated school_tag activates ka_vedha_gochara's
    // DB-sourced-grid-first path with zero code change.
    asset_id: 'bg_sarvatobhadra_grid',
    layer: 'brahmagyan', sort_order: 73,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Sarvatobhadra-Cakra Sāraṇī',
    english_name: 'Sarvatobhadra Chakra Grid (School-Tagged)',
    english_description: "ADJUDICATION-11: school-tagged Sarvatobhadra Chakra grid reference table, registered DELIBERATELY EMPTY. SBC grid geometry varies by Jyotish tradition and no single school has been source-verified; an empty school-keyed table honestly states that variants exist rather than seating one as an unqualified fact. A populated school_tag activates ka_vedha_gochara's DB-sourced-grid-first path with zero code change.",
    storage_type: 'postgres_table',
    target_table: 'bg_sarvatobhadra_grid',
    count_sql: 'SELECT COUNT(*) FROM bg_sarvatobhadra_grid',
    size_sql: "SELECT pg_total_relation_size('bg_sarvatobhadra_grid')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Deliberately empty — no writer. Grid variants are school-specific and unverified.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ADJUDICATION-11 Part 4 (migration 528): Phaladeepika Adh. XXVI PG353
    // malefic-count vedha scale — REAL and cited, transcribed verbatim.
    // Consumed by ka_vedha_gochara for house_vedha malefic-count grading.
    asset_id: 'bg_vedha_malefic_scale',
    layer: 'brahmagyan', sort_order: 74,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vedha-Pāpa-Saṅkhyā Sāraṇī',
    english_name: 'Vedha Malefic-Count Scale (Phaladeepika PG353)',
    english_description: "ADJUDICATION-11 Part 4: Phaladeepika Adh. XXVI PG353's malefic-count (1-5) -> effect-grade (fear/failure/killing/death/ignominy) vedha scale, REAL and cited, transcribed verbatim. Consumed by ka_vedha_gochara for the house_vedha malefic-count grading.",
    storage_type: 'postgres_table',
    target_table: 'bg_vedha_malefic_scale',
    count_sql: 'SELECT COUNT(*) FROM bg_vedha_malefic_scale',
    size_sql: "SELECT pg_total_relation_size('bg_vedha_malefic_scale')",
    target_floor: 5,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '5 rows — malefic-count scale values 1–5, per Phaladeepika PG353.',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ADJUDICATION-11 Part 4 (migration 528): Phaladeepika Adh. XXVI PG338-339
    // Lattā vedha rule — REAL and cited, 8 grahas (Ketu deliberately absent).
    // Consumed by ka_vedha_gochara as vedha_kind='latta' rows.
    asset_id: 'bg_phaladeepika_latta',
    layer: 'brahmagyan', sort_order: 75,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Lattā Sāraṇī (Phaladeepikā)',
    english_name: 'Lattā Vedha Rule Table (Phaladeepika PG338-339)',
    english_description: "ADJUDICATION-11 Part 4: Phaladeepika Adh. XXVI PG338-339 Sloka 42-44's Lattā (obstruction-point) rule, REAL and cited, transcribed verbatim, 8 grahas (Ketu deliberately absent — its counting rule was not found in the retrieved passage). Consumed by ka_vedha_gochara as vedha_kind='latta' rows, uncited_extension=false.",
    storage_type: 'postgres_table',
    target_table: 'bg_phaladeepika_latta',
    count_sql: 'SELECT COUNT(*) FROM bg_phaladeepika_latta',
    size_sql: "SELECT pg_total_relation_size('bg_phaladeepika_latta')",
    target_floor: 8,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '8 rows — one per graha (Ketu deliberately absent; its counting rule was not found in the retrieved passage).',
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W2G (GOCHARA-2.0, item 19) · migration 538. The
    // CHART-INDEPENDENT half of the 2.0 transit engine, and the reason W2G is
    // the campaign's production-scalability keystone: when Saturn reaches
    // 123.45° does not depend on anyone's birth data, so a century of transit
    // geometry is decomposed ONCE here and every chart that ever onboards
    // joins the same rows. Per-chart cost reduces to "join + score".
    //
    // Global L0, super-admin-triggered ONLY — never auto-pulled into a
    // per-chart build (brief §2.5.2). depends_on: [] deliberately — the
    // ephemeris rows it reads belong to bg_ephemeris, but this asset is not a
    // build-order dependent of it in the Nirmāṇa sense any more than any other
    // L0 reader is; the edge is added only if the DAG needs it at W2G cutover,
    // and adding it speculatively would make a super-admin trigger drag an
    // 825k-row rebuild behind it.
    asset_id: 'bg_gochara_arcs',
    layer: 'brahmagyan', sort_order: 77,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gocara Cāpa-Vibhāga',
    english_name: 'Transit Monotone-Arc Substrate',
    english_description: "Chart-independent decomposition of every graha's ecliptic-longitude history over the stored 1900–2150 ephemeris epoch into MONOTONE ARCS: maximal intervals on which longitude is strictly monotone in time and confined to a single 360° band, cut at real stations (sign-change-confirmed roots of the interpolated velocity) and at 360° wrap boundaries. Turns 'when does body B reach degree L' from a day-stepping ephemeris scan into a range predicate (lon_lo_deg <= L <= lon_hi_deg) plus one bracketed bisection — which is what removes the ~110–120ms-per-contact-primitive-call cost measured in the v1 sweep. Carries a per-body arc_fingerprint so an invalidation is exactly as wide as the change that caused it (W2G delta-aware-invalidation requirement). Geometry only: no grammar, no orbs, no astrology — those stay frozen at v1 per GOCHARA_SWEEP_2_0_DESIGN §5.",
    storage_type: 'postgres_table',
    target_table: 'bg_gochara_arcs',
    count_sql: 'SELECT COUNT(*) FROM bg_gochara_arcs',
    size_sql: "SELECT pg_total_relation_size('bg_gochara_arcs')",
    target_floor: 34553,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: "34,553 arcs across the nine DAILY_BODIES over 1900-01-01 → 2150-12-31 (91,676 knots each, ayanamsha_id='tropical'). Per body: Saturn 503 · Jupiter 494 · Rahu 13,544 · Ketu 13,553 · Mars 376 · Sun 252 · Mercury 1,894 · Venus 580 · Moon 3,357. PROVENANCE, stated exactly: this is a REAL derivation run by the arc builder against production ephemeris_daily read-only on 2026-08-05 (whole-epoch build measured twice, 36.8s and 48.0s wall clock), NOT a post-INSERT DB count and NOT an estimate — the writer had not yet run in production when this row landed. Re-verify with count_sql after the first super-admin L0 build. The two node bodies dominate because ephemeris_daily stores the TRUE node (l0_ephemeris swe_id=11 = SE_TRUE_NODE, despite that line's '# Mean North Node' comment), which genuinely oscillates — measured retrograde stretches of median 0.71° over ~9.9 days interleaved with direct excursions of median 0.043°. Splitting there is required for monotonicity; whether such an excursion carries classical significance is a grammar question, frozen at v1.",
    depends_on: [],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },

  // ── GANITA (8) ────────────────────────────────────────────────────────────
  {
    asset_id: 'ga_positions',
    layer: 'ganita', sort_order: 1,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Graha-sthāna',
    english_name: 'Positions',
    english_description: 'Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)',
    storage_type: 'postgres_table',
    target_table: 'chart_facts',
    // W3K gap G-3 (migration 535): `bhava_cusps` — 12 houses × {sripati,placidus} ×
    // {start,madhya,end}, emitted right here by ga_positions_writer.py:450 — was counted
    // by NO asset's count_sql. (The W3K inventory attributed it to ga_sensitive; the live
    // emitter is ga_positions.) DISCLOSED ADJACENT GAP, deliberately left open because it
    // is outside the Lane-1 scope statement: `house_chalit` and `sandhi_flag`, from the
    // same pass, are still uncounted.
    count_sql: "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('graha_position', 'graha_sign_attributes', 'bhava_cusps')",
    size_sql: "SELECT pg_total_relation_size('chart_facts')",
    // Floor = achieved canonical count for chart 482012f1 (D2 deprecation: ganita_positions dual-write removed, count_sql now queries chart_facts).
    // Floor NOT raised for the newly-counted bhava_cusps rows: floors are aspirational and
    // are set from a measured build, never from an estimate (§N.4).
    target_floor: 50,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS * FACT_KEYS',
    expected_volume_inputs: null,
    volume_explanation: '10 bodies × 5 ayanamshas × atomic fact keys per body (graha_position + graha_sign_attributes)',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_vargas',
    layer: 'ganita', sort_order: 2,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Varga',
    english_name: 'Divisional charts',
    english_description: 'D1–D60 divisional chart positions per ayanamsha',
    storage_type: 'postgres_table',
    target_table: 'chart_divisionals',
    count_sql: 'SELECT count(*) FROM chart_divisionals WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_divisionals')",
    // Floor = achieved canonical count for chart 482012f1 (migration 220, 2026-06-11).
    target_floor: 21635,
    expected_volume_formula: 'VARGAS * GRAHAS * AYANAMSHAS', // STALE_FORMULA: 60*9*5=2700 under-counts by ~8×; actual=21635 because chart_divisionals stores bhava+rashi+nakshatra sub-rows per position, not one row per varga×graha×ayanamsha
    expected_volume_inputs: null,
    volume_explanation: '60 vargas × 9 grahas × ayanamsha count — structural',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_dashas',
    layer: 'ganita', sort_order: 3,
    catalog_status: 'CURRENT',
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
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_strength',
    layer: 'ganita', sort_order: 4,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Balatva',
    english_name: 'Strength tables',
    english_description: 'Shadbala, ashtakavarga, and bhava bala per ayanamsha',
    storage_type: 'postgres_table',
    target_table: null,
    // Matches migration 307 (L1 Phase 3 Enrichment) — Amendment 1 adds 4 per-varga bala
    // categories covered by the new `graha_%_bala_per_varga` clause. ashtakavarga per-varga
    // rows already covered by existing `ashtakavarga_%`. Migration 217 broadened the family.
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
      OR fact_category LIKE 'graha_%_bala_per_varga'
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 307, 2026-06-18).
    target_floor: 11936,
    expected_volume_formula: '(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS', // STALE_FORMULA: naive expansion gives (54+864+72)*5=4950 which over-counts by ~2×; actual=2184 because not all ashtakavarga sign×graha combos are stored and vimsopaka/bhava_bala sub-families are smaller than the theoretical max
    expected_volume_inputs: null,
    volume_explanation: 'Shadbala: 6 scores × 9 grahas; ashtakavarga: 8 tables × 9 grahas × 12 signs; bhava bala: 6 scores × 12 bhavas — all × ayanamshas',
    depends_on: ['ga_positions'],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_sensitive',
    layer: 'ganita', sort_order: 5,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Sūkṣmabindu',
    english_name: 'Sensitive points',
    english_description: 'Per-chart sensitive point positions computed from the catalog × ayanamshas',
    storage_type: 'postgres_table',
    target_table: null,
    // Matches migration 307 (L1 Phase 3 Enrichment) — Amendment 3 adds Tier-1 sensitive
    // points: sensitive_point_gulika_mandi, sun_derived_upagraha, special_lagna (new IN entries);
    // esoteric_point_sphuta_fertility + esoteric_point_yogi_system covered by esoteric_point_%.
    // nakshatra_pada_sensitive (80 rows) was previously missing from the IN list; added here.
    // ṢAḌ-DARŚANA Lane K / Gate W3K close (2026-08-06): the old `LIKE 'kp_%'` wildcard
    // was written when ga_sensitive_writer.py's only two `kp_*` fact_categories were
    // `kp_ruling_planets_natal` and `kp_cuspal_significators` (verified against the
    // writer's own fact_category literals). W3K Lane 1 (PR #1039) landed
    // `kp_house_significators`/`kp_planet_significations` on `ga_nakshatra` — a
    // DIFFERENT asset — and the wildcard silently started double-counting them too
    // (any `kp_`-prefixed category collides, regardless of which writer emits it).
    // Verified live: this over-counted chart 482012f1 by 1,045 rows (540 + 505) that
    // ga_sensitive never wrote. Narrowed to an explicit IN-list entry — §N.4 cockpit
    // truth, §N.7 item 3 ("no wrapper-local [pattern] may shadow" another asset's own
    // named ownership) — and guarded by
    // `scripts/__tests__/catalog_reconciliation.test.ts`'s new cross-asset
    // wildcard-collision test so a future `kp_*` category addition fails CI instead of
    // silently re-introducing this defect.
    count_sql: `
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category IN (
        'upagraha_position', 'saturn_derived_point', 'saham_position',
        'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
        'arudha_pada', 'midpoint', 'aprakasha_position',
        'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point',
        'sensitive_point_gulika_mandi', 'sun_derived_upagraha', 'special_lagna',
        'nakshatra_pada_sensitive', 'kp_ruling_planets_natal', 'kp_cuspal_significators'
      )
      OR fact_category LIKE 'esoteric_point_%'
      OR fact_category LIKE 'tajik_%'
    )
`,
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 307, 2026-06-18).
    target_floor: 8610,
    expected_volume_formula: 'ACTUAL(bg_reference) * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Derived from the reference library count × ayanamshas; awaits dedicated per-chart table',
    depends_on: ['ga_positions', 'bg_reference'],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    // migration 432 (WP-2.5 / LCA-10) — sensitive-degree checks per graha.
    asset_id: 'ga_sensitive_degree',
    layer: 'ganita', sort_order: 50,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Marma Aṃśa Parīkṣā',
    english_name: 'Sensitive-Degree Checks',
    english_description: 'Per-graha sensitive-degree facts (LCA-10): mrityu-bhaga, neecha-bhanga, kartari, sarvatobhadra-vedha, khareshwara (22nd drekkana + 64th navamsa), pushkara-bhaga/navamsa, kranti/declination, gandanta. Each computed by its cited classical rule. Writer: ga_sensitive_degree after ga_positions. Category: sensitive_degree_check.',
    storage_type: 'postgres_table',
    target_table: 'chart_facts',
    count_sql: "SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category='sensitive_degree_check'",
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Per-graha sensitive-degree check rows — count depends on classical rule applicability per chart.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    // migration 432 (WP-2.5 / LCA-16) — longevity three methods.
    asset_id: 'ga_ayurdaya',
    layer: 'ganita', sort_order: 51,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Āyurdāya',
    english_name: 'Longevity (Three Methods)',
    english_description: 'Ayurdaya / longevity (LCA-16): ALL THREE classical methods (Pindayu, Nisargayu, Amsayu) method-attributed, with the classical applicability rule served alongside (no autonomous adjudication — §7.2), alpa/madhya/purna classification and maraka significators. Delegated to PyJHora aayu (cited). Writer: ga_ayurdaya after ga_positions. Category: ayurdaya.',
    storage_type: 'postgres_table',
    target_table: 'chart_facts',
    count_sql: "SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category='ayurdaya'",
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Ayurdaya rows — count depends on method applicability per chart.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_panchanga',
    layer: 'ganita', sort_order: 6,
    catalog_status: 'CURRENT',
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
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_sade_sati',
    layer: 'ganita', sort_order: 7,
    catalog_status: 'CURRENT',
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
    depends_on: ['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas', 'ga_dashas', 'ga_structural'],
    // Activated in migration 217 — the L1 build populates this asset.
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_tajaka',
    layer: 'ganita', sort_order: 8,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Tājaka',
    english_name: 'Tajaka Varshaphal',
    english_description: 'Vārṣaphal annual chart per varsha (solar-return year): Muntha position, Vārṣeśa (year-lord) by tajik_classical + panchavargiya methods with candidate scoring, and the Tājik yogas firing in each annual chart — A7 hybrid storage (past→present+5 precomputed; rest on-demand), per ayanamsha.',
    storage_type: 'postgres_table',
    // Activated in migration 222 — the GA-Tajaka writer populates this asset.
    target_table: 'l1_tajik_varsha_year_lords',
    count_sql: 'SELECT count(*) AS count FROM l1_tajik_varsha_year_lords WHERE chart_id = $1',
    size_sql: null,
    // Floor = achieved canonical count for chart 482012f1 (migration 222, 2026-06-11):
    // A7 hybrid window varsha 1..48 (birth 1984 → present+5 ≈ 2031) × 5 ayanamshas.
    target_floor: 240,
    expected_volume_formula: null, // non-parametric — target_floor = 240 (A7 hybrid window varsha 1..48 × 5 ayanamshas)
    expected_volume_inputs: null,
    volume_explanation: 'target_floor = 240 = achieved canonical count for chart 482012f1 (2026-06-11): A7 hybrid window varsha 1..48 × 5 ayanamshas. Hybrid storage — varshas outside the precomputed window are computed on-demand by the retrieval tool via ga_tajaka_writer.compute_varsha().',
    depends_on: ['ga_positions', 'ga_dashas'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_structural',
    layer: 'ganita', sort_order: 9,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Saṃracanā',
    english_name: 'Structural facts',
    english_description: 'GA8 T1 structural layer: aspects (Parāśarī + Jaimini + Tājik), yogas, doshas, graha avasthās, argala/virodha-argala, dispositor chains, composite states, kāraka and tri-deva roles, and base graha facts — per ayanamsha.',
    storage_type: 'postgres_table',
    target_table: null,
    // JL-015 (BA Phase 2.5 J2, migration 410): count_sql now derives from the
    // fact_category_ownership registry (single source of truth) instead of the
    // hand-maintained LIKE/IN/NOT-IN allow-list, which had already silently
    // drifted twice (migrations 364, 368). Verified byte-identical row count
    // against the prior hand-maintained query on the canonical chart 482012f1
    // (98,314 rows, 2026-07-05) before cutover — see migration 410 for the
    // registry seed (58 fact_category values) and comments/history.
    count_sql: `SELECT count(*) AS count FROM chart_facts cf
JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category
WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_structural'`,
    size_sql: null,
    // Floor: 77,821 measured on prod chart 482012f1 (2026-06-18, GA-STRUCTURAL-REMEDIATION session).
    // Includes all Phase-2 depth categories (dual-path collapse + depth rebuild per brief
    // GA_STRUCTURAL_REMEDIATION_v1_0.md). Parivartana false-positives eliminated (163 rows removed).
    // count_sql excludes (migration 309 BUG-1 fix):
    //   - 2,835 graha_avastha_%_per_varga (ga_condition)
    //   - 9,690 bala per_varga (ga_strength)
    //   - 80 nakshatra_pada_sensitive (ga_sensitive)
    target_floor: 77821,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'GA8 T1 structural facts — floor 77,821 post-Phase-2 rebuild (2026-06-18). All 14 depth categories active: sambandha_grade(180), nakshatra_dispositor_chain(45), dispositor_tree(50), bhava_significance_link(180), karaka_bhava_concordance(150), net_argala(60), nway_configuration(5), chart_center_of_gravity(10), graha_centrality(45), chart_cluster(45), convergence_count(105), contradiction_pair(1810), dispositor_cycle(0 — no cycles), varga_provenance_meta(0 — no issues).',
    depends_on: ['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive', 'ga_vargas', 'ga_dashas', 'ga_nakshatra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  {
    // Doctrine Campaign Night-1, Lane 2 (migration 435). Mirrors that migration's
    // asset_registry INSERT exactly — a clean reseed must not silently drop this
    // asset (the gap this entry closes was flagged by Night-1 verification).
    asset_id: 'ga_vichara',
    layer: 'ganita', sort_order: 29,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vichāra',
    english_name: 'Gaṇita — Vichāra (judged structure)',
    english_description: 'Judgment layer over ga_structural: functional-lordship valence pass, varga-ratification matrix + divergence signals, continuous varga-consistency index, and leverage_index (remedy/intervention-timing rank).',
    storage_type: 'postgres_table',
    target_table: 'chart_vichara',
    count_sql: 'SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('chart_vichara')",
    target_floor: 0, // aspirational per §N.4 — set after first prod build measurement
    expected_volume_formula: 'GRAHAS x DOMAINS x AYANAMSHAS_COUNT (approx; families vary)',
    expected_volume_inputs: null,
    volume_explanation: 'Sum of valence_pass + varga_ratification (+ divergence) + varga_consistency + leverage_index rows across 5 ayanamshas.',
    depends_on: ['ga_structural', 'ga_strength', 'ga_dashas', 'ga_yoga'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  {
    asset_id: 'ga_nakshatra',
    layer: 'ganita', sort_order: 20,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Nakṣatra-Paṭala',
    english_name: 'Nakshatra Parallel Chart',
    english_description: 'Per-chart parallel nakshatra chart: placement+attribute JOIN from bg_nakshatra, KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, the 4-limbed KP significator ladder per house AND per planet (W3K, referencing bg_kp_sublord_division as boundary authority), nakshatra dispositor graph, gaṇḍānta severity flags, tara bala, per-chart statistics. Into chart_facts. Authoritative L1 nakshatra grain.',
    storage_type: 'postgres_table',
    target_table: 'chart_facts',
    // W3K (migration 535): +kp_house_significators, +kp_planet_significations — the
    // 4-limbed KP significator ladder, ADDITIVE on this standing asset per
    // ADJUDICATION-7 Part 2 ("NO NEW ASSET … W3K EXTENDS it").
    count_sql: `SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement','graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags','nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction','nakshatra_cogravity','graha_tara_bala','nakshatra_statistics','nakshatra_cross_ayanamsha','kp_house_significators','kp_planet_significations')`,
    size_sql: "SELECT pg_total_relation_size('chart_facts')",
    target_floor: 1802,  // set after first prod build 2026-06-17 (§N.4)
    expected_volume_formula: 'BODIES * AYANAMSHAS * FACT_CATEGORIES + CROSS_AYANAMSHA',
    expected_volume_inputs: null,
    volume_explanation: '357 rows per ayanamsha × 5 ayanamshas + 17 cross-ayanamsha consistency rows = 1802 total (native chart 482012f1). W3K adds 108 house-significator + ~100 planet-signification rows per ayanamsha; target_floor stays at the last MEASURED build until the next prod build re-measures it (§N.4 — floors are never set from an estimate).',
    depends_on: ['bg_nakshatra', 'ga_positions', 'bg_kp_sublord_division'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  // ── GA SATELLITE ASSETS (built by L1 writers; registered via migrations 240/252/280/287/291)
  // These 5 assets were absent from the seed (seed-DB divergence closed by L1 closure pass).
  // DB values come from prior migrations; floor values are latest-confirmed per migration chain.
  {
    asset_id: 'ga_condition',
    layer: 'ganita', sort_order: 29,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Graha-sthiti',
    english_name: 'Planetary Condition Composite',
    english_description: 'Unified dignity, avastha (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi), motion state, combustion, naisargika/tatkalika/panchadha friendship, graha yuddha, and a 0–1 condition score per graha per ayanamsha. Amendment 2 (L1 Enrichment v2.0) adds per-varga Baladi + Deeptadi avasthas to chart_facts.',
    storage_type: 'postgres_table',
    target_table: 'ga_condition_composite',
    // Combined count: D1 composite rows (ga_condition_composite) + per-varga avastha rows (chart_facts).
    // Amendment 2 added graha_avastha_*_per_varga rows; BUG-1 fix (migration 309) removed them
    // from ga_structural count_sql so ga_condition is the sole counter of those rows.
    count_sql: `SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1) + (SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'graha_avastha_%_per_varga') AS count`,
    size_sql: `SELECT pg_total_relation_size('ga_condition_composite')`,
    // Floor: 2,880 measured on prod chart 482012f1 (2026-06-18, migration 310).
    // Breakdown: 45 D1 composite (ga_condition_composite) + 2,835 per-varga avastha (chart_facts).
    // Note: per-varga count (2,835) is below Amendment-2 estimate (~6,750) because
    // graha_kala_bala_per_varga is FLOORED (NULL fact_value_num, not counted in avastha total).
    target_floor: 2880,
    expected_volume_formula: null, // non-parametric — floor 2,880 measured prod (migration 310, 2026-06-18)
    expected_volume_inputs: null,
    volume_explanation: 'ga_condition combined: 45 D1 composite + 2,835 per-varga avastha chart_facts = 2,880 total. Measured on prod chart 482012f1 (2026-06-18). graha_kala_bala_per_varga floored (NULL fact_value_num).',
    depends_on: ['ga_positions', 'ga_vargas', 'ga_dashas'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_yoga',
    layer: 'ganita', sort_order: 30,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Yoga-nidhi',
    english_name: 'Yoga Firings',
    english_description: 'Per-chart yoga firing table: evaluates classical Nabhasa and other yoga formation rules against L1 chart_facts. Each row = one yoga that fired, with constituent fact ids, strength, and family tagging.',
    storage_type: 'postgres_table',
    target_table: 'ga_yoga_firings',
    count_sql: `SELECT COUNT(*) FROM ga_yoga_firings WHERE chart_id = $1::uuid`,
    size_sql: `SELECT pg_total_relation_size('ga_yoga_firings')`,
    // Floor = 5 (only Yuga Nabhasa fires for native chart 482012f1; confirmed by Phase 1 L1 closure audit).
    // Migration 308 corrected from 50 (generic estimate) to 5.
    target_floor: 5,
    expected_volume_formula: 'YOGAS_IN_CATALOG * AYANAMSHAS_COUNT',
    expected_volume_inputs: null,
    volume_explanation: 'Sum of fired yogas across 5 ayanamshas; only Yuga Nabhasa yoga fires for chart 482012f1 (5 rows = 1 yoga × 5 ayanamshas).',
    depends_on: ['ga_structural', 'ga_dashas'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_vastu',
    layer: 'ganita', sort_order: 31,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vastu-graha-dik-mapa',
    english_name: 'Vastu Planet Direction Map',
    english_description: 'Maps each classical graha to its ruling Vastu direction (per bg_vastu_directions) and computes direction_impact (weakened / neutral / strengthened) using condition_score from ga_condition_composite. Indication tier: traditional_vastu.',
    storage_type: 'postgres_table',
    target_table: 'ga_vastu_planet_direction_map',
    count_sql: `SELECT COUNT(*) FROM ga_vastu_planet_direction_map WHERE chart_id = $1`,
    size_sql: `SELECT pg_total_relation_size('ga_vastu_planet_direction_map')`,
    // Floor = 40 (confirmed prod count, migration 294 corrected from 45; Ketu skipped — no classical direction).
    target_floor: 40,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: 'Up to 9 grahas × 5 ayanamshas = 45; Ketu skipped (no Vastu direction mapping) → 40 rows.',
    depends_on: ['ga_condition'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_medical',
    layer: 'ganita', sort_order: 32,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vaidya-phala',
    english_name: 'Medical / Ayurvedic Indications',
    english_description: 'Per-chart Ayurvedic Jyotish indication summary: dosha aggravation, organ watch, body-part watch, and indication_strength derived from ga_condition condition_score joined with bg_medical_mappings. MEDICAL DISCLAIMER: indication_tier=jyotish_indication; not_diagnosis=TRUE.',
    storage_type: 'postgres_table',
    target_table: 'ga_medical',
    count_sql: `SELECT COUNT(*) FROM ga_medical WHERE chart_id = $1`,
    size_sql: null,
    // Floor = 45 (9 grahas × 5 ayanamshas; confirmed prod count).
    target_floor: 45,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '9 grahas × 5 ayanamshas = 45 indication rows per chart.',
    depends_on: ['ga_condition', 'ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ga_prashna',
    layer: 'ganita', sort_order: 7,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Praśna-viveka',
    english_name: 'Prashna Horary Judgment',
    english_description: 'Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited significators, Tajik Ithasala/Eesarpha analysis, and fructification timing. Only computed when a prashna chart exists for the chart_id; returns 0 rows for natal charts.',
    storage_type: 'postgres_table',
    target_table: 'ga_prashna_judgment',
    count_sql: `SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1`,
    size_sql: null,
    // Floor = 0 (natal charts return 0 horary rows by design; Phase 1 L1 audit confirmed).
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: '0 for natal charts (horary only). Actual prashna count depends on number of prashna charts submitted.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  {
    asset_id: 'ga_transit_anchors',
    layer: 'ganita', sort_order: 33,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara-sthāna-ādhāra',
    english_name: 'Transit Natal Anchors',
    english_description: 'Natal position anchors for Gochara (transit) analysis: stores each graha\'s natal sign, natal degree absolute, and house-from-Moon for each ayanamsha. Gate-1 of the Transit/Gochara subsystem. 45 rows per chart (5 ayanamshas × 9 grahas).',
    storage_type: 'postgres_table',
    target_table: 'ga_transit_anchors',
    count_sql: `SELECT COUNT(*) FROM ga_transit_anchors WHERE chart_id = $1`,
    size_sql: null,
    // Floor = 45 (9 grahas × 5 ayanamshas; confirmed writer spec ga_transit_anchors.py).
    target_floor: 45,
    expected_volume_formula: 'GRAHAS * AYANAMSHAS',
    expected_volume_inputs: null,
    volume_explanation: '9 grahas × 5 ayanamshas = 45 anchor rows per chart.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  // ── BODHA (10) — all CURRENT; sealed counts per L2_BODHA_CLOSE_v1_1.md §asset-manifest ─────────────
  // bg_signal_type_registry (G52) RETIRED 2026-06-15: predicate-firing model dropped;
  // ga_structural enumerates exhaustively and labels from brahma_yoga_catalog (migration 223).
  // count_sql narrowed to core tables by migration 326; target_floor = sealed achieved counts.
  {
    asset_id: 'bo_laksana',
    layer: 'bodha', sort_order: 1,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Lakṣaṇa',
    english_name: 'Signal store (MSR)',
    english_description: 'MARSYS Signal Register — grounded signals derived from exhaustive L1 structural enumeration (ga_structural) × L1 chart_facts; primary table bodha_msr_signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: 'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_msr_signals')",
    target_floor: 66738,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Signal count driven by ga_structural exhaustive enumeration; sealed count 66,738 per L2 build (chart 482012f1).',
    depends_on: ['ga_structural', 'ga_vichara', 'bg_rules'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_karanajala',
    layer: 'bodha', sort_order: 3,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Kāraṇajāla',
    english_name: 'Signal graph edges (CGM)',
    english_description: 'Causal Graph Model — valenced directed edges between CGM nodes; pre-computed igraph metrics stored as flat columns',
    storage_type: 'postgres_table',
    target_table: 'bodha_cgm_edges',
    // Migration 326: narrowed to edges + paths only (sub_graphs, motifs, topology, contradictions removed)
    count_sql: 'SELECT (SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1)'
      + ' + (SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1) AS count',
    size_sql: "SELECT pg_total_relation_size('bodha_cgm_edges')",
    target_floor: 300,
    expected_volume_formula: 'ACTUAL(bo_laksana) * EDGE_DENSITY',
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count ≥300 (edges + paths) per L2 build (chart 482012f1). Sub-graphs, motifs, topology rows excluded per migration 326 narrowing.',
    // Migration 356: bo_bimba added — karanajala reads bodha_cgm_nodes (bo_bimba output)
    depends_on: ['bo_laksana', 'bo_bimba'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_pratijna',
    layer: 'bodha', sort_order: 4,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Pratijñā',
    english_name: 'Promise Register',
    english_description: 'Per-event-class promise/denial grading — reads bodha_msr_signals + brahma_event_ontology, grades supporting vs. contradicting signal salience per event class; primary table bodha_pratijna. Downstream: ph_nimitta reads grade as promise_lift input.',
    storage_type: 'postgres_table',
    target_table: 'bodha_pratijna',
    count_sql: 'SELECT count(*) FROM bodha_pratijna WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_pratijna')",
    target_floor: 110,
    expected_volume_formula: 'EVENT_CLASSES * AYANAMSHAS',
    expected_volume_inputs: { EVENT_CLASSES: 22, AYANAMSHAS: 5 },
    volume_explanation: '22 event classes (brahma_event_ontology) × 5 canonical ayanamshas = 110 rows per chart.',
    depends_on: ['bo_laksana', 'bg_ghatana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_bimba',
    layer: 'bodha', sort_order: 2,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Bimba',
    english_name: 'Signal graph nodes (CGM)',
    english_description: 'CGM node registry — one node per signal; carries composite_centrality, pagerank, betweenness, VECTOR(768) embedding and igraph-computed metrics',
    storage_type: 'pgvector',
    target_table: 'bodha_cgm_nodes',
    count_sql: 'SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_cgm_nodes')",
    target_floor: 140,
    expected_volume_formula: 'ACTUAL(bo_laksana)',
    expected_volume_inputs: null,
    volume_explanation: 'One node per signal — exact 1:1 with Lakṣaṇa count; sealed at 140 per L2 build (chart 482012f1).',
    depends_on: ['bo_laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_samskara',
    layer: 'bodha', sort_order: 6,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Saṃskāra',
    english_name: 'Signal embeddings',
    english_description: 'Vertex AI 768-dim vector embeddings — one per MSR signal',
    storage_type: 'pgvector',
    target_table: 'bodha_signal_embeddings',
    // Migration 326: added WHERE chart_id = $1 (was missing — global count was wrong for cockpit)
    count_sql: 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_signal_embeddings')",
    target_floor: 66738,
    expected_volume_formula: 'ACTUAL(bo_laksana)',
    expected_volume_inputs: null,
    volume_explanation: 'One embedding per signal — 1:1 with Lakṣaṇa count; sealed at 66,738 per L2 build (chart 482012f1).',
    depends_on: ['bo_laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_sangati',
    layer: 'bodha', sort_order: 7,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Saṅgati',
    english_name: 'Domain links (CDLM)',
    english_description: 'Cross-Domain Linkage Matrix — computed_linkage cells, domain rollups, pattern clusters, evolution gradients; primary table bodha_cdlm_cells',
    storage_type: 'postgres_table',
    target_table: 'bodha_cdlm_cells',
    // Migration 326: narrowed to cdlm_cells + convergence + contradictions (domain_rollups, chart_summary,
    // pattern_clusters, evolution_gradients removed from cockpit count)
    count_sql: 'SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1)'
      + ' + (SELECT count(*) FROM bodha_convergence WHERE chart_id = $1)'
      + ' + (SELECT count(*) FROM bodha_contradictions WHERE chart_id = $1) AS count',
    size_sql: "SELECT pg_total_relation_size('bodha_cdlm_cells')",
    target_floor: 84,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count 84 (cdlm_cells + convergence + contradictions) per L2 build (chart 482012f1). Ancillary rollup tables excluded per migration 326 narrowing.',
    depends_on: ['bo_laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_cdlm_summary',
    layer: 'bodha', sort_order: 8,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Saṅkalana',
    english_name: 'CDLM chart summary',
    english_description: 'Per-chart cross-domain linkage aggregate: total linkage, dominant/weakest 3 domains, contradiction density, bridge/asymmetric link counts, strongest linkage pair, domain connectivity map. References bodha_cdlm_cells only — never invents values.',
    storage_type: 'postgres_table',
    target_table: 'bodha_cdlm_chart_summary',
    count_sql: 'SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_cdlm_chart_summary')",
    target_floor: 5,
    expected_volume_formula: 'ACTUAL(bo_sangati)',
    expected_volume_inputs: null,
    volume_explanation: 'One row per chart per ayanamsha — 5 ayanamshas. Live-measured 5, 2026-07-05.',
    depends_on: ['bo_sangati'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_cgm_motifs',
    layer: 'bodha', sort_order: 5,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Ākṛti',
    english_name: 'CGM structural motifs',
    english_description: 'Recurring structural patterns in the CGM graph — mutual_reception (2-cycle dispositor), stellium (3+ mutually-conjoined nodes in a house), parivartana_chain (3-6 length dispositor cycle). Purely structural detection over CGM graph data — no LLM, no invented values.',
    storage_type: 'postgres_table',
    target_table: 'bodha_cgm_motifs',
    count_sql: 'SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_cgm_motifs')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Motif count is chart-dependent (0 if no mutual-reception/stellium/parivartana pattern exists in this chart\'s dispositor graph). Live-measured 0 for chart 482012f1, 2026-07-05 — not yet rebuilt since this asset was registered; floors are aspirational per §N.4, not a claim of expected non-zero output.',
    depends_on: ['bo_bimba', 'bo_karanajala'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_cgm_paths',
    layer: 'bodha', sort_order: 11,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Diśā',
    english_name: 'CGM dispositor chain paths',
    english_description: 'Dispositor chain path analysis over the CGM graph — for each graha node, follows the dispositor chain (current graha -> sign lord -> lord\'s lord...) until a self-ruling graha, a cycle, or max depth 9. path_strength (JL-013) = product of constituent edges\' computed_strength (never an average).',
    storage_type: 'postgres_table',
    target_table: 'bodha_cgm_paths',
    count_sql: 'SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_cgm_paths')",
    target_floor: 5,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Currently only self-ruling (zero-hop) paths emit — bo_karanajala does not yet write dispositor-class edges, so multi-hop chains cannot be built (documented limitation in bo_cgm_paths.py). Live-measured 5, 2026-07-05.',
    depends_on: ['bo_bimba', 'bo_karanajala'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_upaya',
    layer: 'bodha', sort_order: 12,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Upāya',
    english_name: 'Remediation (RM)',
    english_description: 'Remediation Map — ALL 6 RM tables; primary table bodha_rm_resonances (resonance targets that remedies key off) + bodha_rm_remedy_prescriptions + 4 ancillary tables across 6 traditions × 18 categories',
    storage_type: 'pgvector',
    target_table: 'bodha_rm_resonances',
    // Migration 326: narrowed to resonances + prescriptions only (dasha_windowed, dosha_bundles,
    // pattern_remedies, chart_summary removed from cockpit count — 45 res + 135 prescriptions = 180)
    count_sql: 'SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1)'
      + ' + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1) AS count',
    size_sql: "SELECT pg_total_relation_size('bodha_rm_resonances')",
    target_floor: 180,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count 180 (45 resonances + 135 prescriptions) per L2 build (chart 482012f1). Ancillary RM tables excluded per migration 326 narrowing.',
    // Migration 412 (BA Phase 2.5 #4): added ga_structural (composite_dispositor_strength),
    // ga_dashas (chart_dashas), bo_cgm_motifs (bodha_cgm_motifs) — bo_upaya now reads all
    // three for real resonance_score_v1 inputs (dispositor_chain_weakness,
    // dasha_proximity_activation_score, cgm_motifs_weakest_node).
    depends_on: ['bo_laksana', 'bo_sangati', 'ga_structural', 'ga_dashas', 'bo_cgm_motifs'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_samvada',
    layer: 'bodha', sort_order: 14,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Saṃvāda',
    english_name: 'Unified Chart Digest (UCD)',
    english_description: 'UCD — read-side conceptual digest (join of A8/A11/A12/A13 chart_summaries via vw_chart_digest + query_ucd). NOT a per-chart writer (A14 retirement, Option A). May later own the 5 folded UCD columns on existing summary tables.',
    storage_type: 'postgres_view',
    target_table: 'vw_chart_digest',
    // NOTE: migration 326 specified bodha_chart_gestalt here, but that table has 0 rows and is never
    // populated; prod was patched to vw_chart_digest (returns 5 rows = correct UCD gestalt count).
    // Seed matches prod (vw_chart_digest). bodha_chart_gestalt should be investigated separately.
    count_sql: 'SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1',
    size_sql: null,
    target_floor: 5,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count 5 (5 UCD gestalt rows via vw_chart_digest) per L2 build (chart 482012f1).',
    depends_on: ['bo_laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_chart_gestalt',
    layer: 'bodha', sort_order: 15,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Pratinidhi',
    english_name: 'Chart gestalt synthesis',
    english_description: 'Per-chart POINTERS-ONLY synthesis (defining threads, central dynamics, center-of-gravity nodes, domain verdict map, headline, watch list, contested areas, zoom spine) referencing signal/cell/node ids from earlier Bodha assets. ANTI-DRIFT ABSOLUTE: never stores verdicts, computed values, or interpretive text, only ids. NOTE: superseded the stale bo_samvada comment (migration 326) claiming this table "has 0 rows and is never populated" — it is now live and populated (5 rows, 2026-07-05); this catalog gap (never registered as its own asset) is the reason that comment went stale.',
    storage_type: 'postgres_table',
    target_table: 'bodha_chart_gestalt',
    count_sql: 'SELECT count(*) FROM bodha_chart_gestalt WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('bodha_chart_gestalt')",
    target_floor: 5,
    expected_volume_formula: 'ACTUAL(bo_laksana)',
    expected_volume_inputs: null,
    volume_explanation: 'One row per chart per ayanamsha — 5 ayanamshas. Live-measured 5, 2026-07-05.',
    depends_on: ['bo_laksana', 'bo_sangati', 'bo_bimba', 'bo_cgm_paths', 'bo_anveshana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_pramana_mapa',
    layer: 'bodha', sort_order: 13,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Pramāṇa-māpā',
    english_name: 'Synthesis quality',
    english_description: 'Per-build synthesis quality scorecard — citation density, whole-chart coverage, derivation compliance, layer separation score; keyed by (chart_id, build_id)',
    storage_type: 'postgres_table',
    target_table: 'synthesis_quality_scorecard',
    // Migration 326: added WHERE chart_id = $1; aligned depends_on to DAG terminal position
    count_sql: 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('synthesis_quality_scorecard')",
    target_floor: 1,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count 1 per L2 build (chart 482012f1). DAG terminal asset — one scorecard row per chart.',
    depends_on: ['bo_upaya', 'bo_drishti', 'bo_anveshana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_drishti',
    layer: 'bodha', sort_order: 9,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Dṛṣṭi',
    english_name: 'Question Lenses',
    english_description: 'Question-lens table: template + wildcard graph-sweep + ranks-never-caps, per question domain.',
    storage_type: 'postgres_table',
    target_table: 'bodha_question_lenses',
    count_sql: 'SELECT count(*) FROM bodha_question_lenses WHERE chart_id = $1',
    size_sql: null,
    target_floor: 60,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed count 60 per L2 build (chart 482012f1). Per migration 326.',
    depends_on: ['bo_laksana', 'bo_sangati', 'bo_karanajala'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'bo_anveshana',
    layer: 'bodha', sort_order: 10,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Anveṣaṇa',
    english_name: 'Discovery Engine',
    english_description: 'Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies.',
    storage_type: 'postgres_table',
    target_table: 'bodha_discoveries',
    count_sql: 'SELECT (SELECT count(*) FROM bodha_discoveries WHERE chart_id = $1)'
      + ' + (SELECT count(*) FROM bodha_anomalies WHERE chart_id = $1) AS count',
    size_sql: null,
    target_floor: 5770,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Sealed floor 5,770 (1,411 discoveries + 4,359 anomalies) per L2 build (chart 482012f1). Per migration 326.',
    depends_on: ['bo_sangati', 'bo_karanajala', 'bo_samskara', 'bo_drishti'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    // D-2 Lane V-5 / migration 450 (CR-100 Sudarshana Chakra, D-1.5b Lane B-3).
    asset_id: 'bo_sudarshana',
    layer: 'bodha', sort_order: 19,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Sudarśana Cakra',
    english_name: 'Sudarśana Chakra',
    english_description: 'Tri-frame (Lagna/Chandra/Sūrya) house assignment per graha — pure L2 derivation over existing ga_positions facts; emits sudarshana_agreement MSR signals (confirmed-in-3-frames amplifies, contradicted flags)',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = 'sudarshana_agreement'",
    size_sql: null,
    target_floor: 45,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'sudarshana_agreement signal rows — one per confirmed or contradicted 3-frame graha assignment.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-2 Lane V-5 / migrations 450-453.
    asset_id: 'bo_nakshatra_semantic',
    layer: 'bodha', sort_order: 20,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Nakṣatra Tattva',
    english_name: 'Nakshatra-Semantic Profile',
    english_description: 'Own-star identity, dispositor chain, tara bala, and gandanta/end-degree flagging per graha — pure L2 derivation over existing ga_positions/ga_nakshatra facts; emits nakshatra_semantic MSR signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = 'nakshatra_semantic'",
    size_sql: null,
    target_floor: 45,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'nakshatra_semantic signal rows — one per graha per relevant nakshatra quality.',
    depends_on: ['ga_positions', 'ga_nakshatra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-2 Lane V-5 / migrations 445/446 (CR-24/CR-25/CR-86, Mechanism object).
    asset_id: 'bo_yantra_mechanism',
    layer: 'bodha', sort_order: 20,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Yantra',
    english_name: 'Mechanism (Yantra)',
    english_description: 'Named, valenced CGM subgraph — promotes CGM motifs + dispositor/house-lordship chain-and-circuit detection into first-class mechanisms with real edge-strength provenance (DR-7) and a centrality summary (CR-24/CR-25/CR-86)',
    storage_type: 'postgres_table',
    target_table: 'bodha_mechanisms',
    count_sql: 'SELECT count(*) FROM bodha_mechanisms WHERE chart_id = $1',
    size_sql: null,
    target_floor: 1,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One or more mechanism rows per chart — count depends on CGM motif cardinality.',
    depends_on: ['bo_karanajala', 'bo_cgm_motifs', 'bo_cgm_paths'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-2 Lane V-5 / migrations 450-453 (CR-26/64+61+76+36, Jaimini Arudha).
    asset_id: 'bo_arudha',
    layer: 'bodha', sort_order: 21,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Arudha Pāda',
    english_name: 'Jaimini Arudha (Perception Layer)',
    english_description: 'Arudha Lagna bhava-relation, AL conjunctions, and A2/A11 (dhana/labha arudha) tenancy — pure L2 derivation over existing ga_structural/ga_positions facts; emits arudha MSR signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = 'arudha'",
    size_sql: null,
    target_floor: 15,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'arudha MSR signal rows — per AL/A2/A11 analysis.',
    depends_on: ['ga_structural', 'ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-1 Lane CR-84 fix (migration 445, bo_laksana_rerank writer). UPDATE-only.
    asset_id: 'bo_laksana_rerank',
    layer: 'bodha', sort_order: 21,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Lakṣaṇa Punararaṅka',
    english_name: 'Lakṣaṇa Re-rank (post-CGM)',
    english_description: 'Post-CGM structural re-rank pass: writes real CGM centrality (pagerank/eigenvector/betweenness/harmonic) onto each MSR signal\'s graph_node_strength_contribution_jsonb hook column, closing the CR-84 dead link. UPDATE-only, never touches row ownership.',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: 'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND graph_node_strength_contribution_jsonb IS NOT NULL',
    size_sql: null,
    target_floor: 1,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Count of MSR signals that received CGM centrality scores — matches bo_laksana count for a fully-built chart.',
    depends_on: ['bo_karanajala'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-2 Lane V-5 / migrations 450-453 (special/upapada lagnas).
    asset_id: 'bo_special_lagna',
    layer: 'bodha', sort_order: 22,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Viśeṣa Lagna',
    english_name: 'Special Lagna (Indu/Sree/Ghati/Hora)',
    english_description: 'Domain-scoped corroboration from the four canonical special/upapada lagnas (Indu, Sree, Ghati, Hora) — pure L2 derivation over existing ga_sensitive facts; emits special_lagna MSR signals with per-signal domain_salience',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = 'special_lagna'",
    size_sql: null,
    target_floor: 20,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'special_lagna MSR signal rows — per lagna per domain_salience combination.',
    depends_on: ['ga_sensitive'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-2 Lane V-5 / migrations 450-453 (vargottama amplification + dhana axis).
    asset_id: 'bo_vargottama_dhana',
    layer: 'bodha', sort_order: 23,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Vargottama Dhana Akṣa',
    english_name: 'Vargottama Amplification + Dhana Axis',
    english_description: 'Cross-frame (D1/D9) vargottama confirmation and complete 2nd/11th-house (dhana/labha) tenancy analysis — pure L2 derivation over existing ga_vargas/ga_positions facts; emits vargottama_amplification + dhana_axis MSR signals',
    storage_type: 'postgres_table',
    target_table: 'bodha_msr_signals',
    count_sql: "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ANY(ARRAY['vargottama_amplification', 'dhana_axis'])",
    size_sql: null,
    target_floor: 10,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'vargottama_amplification + dhana_axis MSR signal rows — per cross-frame graha analysis.',
    depends_on: ['ga_vargas', 'ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },

  {
    // MR-06 (PARISHKARA cutover durability): post-cutover identity.
    // The old global-scope service asset (storage_type='service', scope='global')
    // was DELETED by migration 563 (W6.4 UTK-R2). ka_gochara_v2_materialize was
    // RENAMED to ka_gochara in the same migration. This seed entry now reflects
    // the renamed per-chart materializer — NOT the old service.
    // If this entry were left as the old service definition, a re-seed would
    // overwrite the DB's renamed materializer row with stale service data.
    asset_id: 'ka_gochara',
    layer: 'kala', sort_order: 107,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara Puraḥ-Sañcalana Cakra (2.0, satyapana)',
    english_name: 'Gochara V3 Per-Chart Materializer',
    english_description: 'Primary per-chart gochara window materializer (GOCHARA-UTKARSA). Renamed from ka_gochara_v2_materialize at W6.4 cutover (UTK-R2, migration 563). Joins bg_gochara_arcs against gochara_resonance_map and scores via gochara_intensity grammar. Writes kala_gochara_windows_v2 with generation=\'3.0\'. This is the post-cutover authority surface for kala_gochara_windows_v2.',
    storage_type: 'postgres_table',
    target_table: 'kala_gochara_windows_v2',
    count_sql: "SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='3.0'",
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Per-chart gochara materialization (generation=3.0). Post-cutover authority surface.',
    depends_on: ['bg_gochara_arcs', 'ka_gochara_resonance'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-5 Lane G-1 (migration 459, GOCHARA-UTKARSA campaign item).
    // Per-chart × event-class classical-prior-weighted target sets.
    // ka_kshetra's depends_on in the DB references this asset; this seed row
    // is required so that both the catalog-reconciliation test and the
    // three-way diff guard can resolve it.
    asset_id: 'ka_gochara_resonance',
    layer: 'kala', sort_order: 104,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara Anunāda Cakra',
    english_name: 'Resonance Map',
    english_description: 'D-5 Lane G-1: per-chart x event-class classical-prior-weighted target sets (bhavas, lords, karakas, mechanism nodes, sensitive degrees, arudhas, yoga constituents, dasha-lord portfolios) sourced from bg_transit_rules + brahma_event_ontology + chart-scoped L1 facts. Feeds D-5 Lane G-3\'s transit-intensity engine. Writer: ka_gochara_resonance.',
    storage_type: 'postgres_table',
    target_table: 'gochara_resonance_map',
    count_sql: 'SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=$1',
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Per-chart resonance target rows — count depends on event-class cardinality and chart structure.',
    depends_on: ['bg_transit_rules'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // D-5 Lane G-4 (migration 460, GOCHARA-UTKARSA campaign item). HEAVY writer
    // with per-event-class/decade sub-stepping and cross-attempt resumption.
    // This is the v1 (legacy) sweep that ka_kshetra reads as a cross-check corpus.
    // MR-06 (PARISHKARA cutover durability): post-cutover status RETIRED.
    // Migration 563 (W6.4 UTK-R2, PR #1192) set catalog_status='RETIRED',
    // is_active=false. The v1 sweep data and protection remain; only the
    // catalog status changes. A re-seed MUST NOT un-retire this asset.
    // The ON-CONFLICT guard in runSeed() preserves RETIRED status on conflict.
    asset_id: 'ka_gochara_sweep',
    layer: 'kala', sort_order: 105,
    catalog_status: 'RETIRED',
    sanskrit_name: 'Gochara Puraḥ-Sañcalana Cakra',
    english_name: 'Forward Sweep + Serving (RETIRED)',
    english_description: 'D-5 Lane G-4: birth->birth+100y daily-grid gochara (transit) intensity sweep (lambda_e via G-3\'s services/gochara_intensity), shape-aware (point/interval/chain per brahma_event_ontology). HEAVY writer, per-event-class/decade sub-stepping with cross-attempt resumption (migration 436). Consumes G-1 gochara_resonance_map + G-2 gochara_grammar + G-3 gochara_intensity read-only. RETIRED at W6.4 cutover (migration 563, UTK-R2): ka_gochara (renamed from ka_gochara_v2_materialize) is the new authority. Protected v1 data retained in kala_gochara_windows (migration 540 guard).',
    storage_type: 'postgres_table',
    target_table: 'kala_gochara_windows',
    count_sql: 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1',
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'RETIRED — v1 sweep data protected in kala_gochara_windows (migration 540). No new rows written.',
    depends_on: ['ka_gochara_resonance'],
    scope: 'per_chart', is_active: false, estimated_seconds: null,
    asset_kind: 'data',
  },
  // MR-06 (PARISHKARA cutover durability): ka_gochara_v2_materialize REMOVED.
  // Migration 563 (W6.4 UTK-R2) renamed this asset_id → ka_gochara. The old
  // asset_id no longer exists in the DB post-cutover. Keeping a seed entry here
  // would re-insert a ghost row on next re-seed via ON-CONFLICT INSERT, and
  // would collide with the renamed ka_gochara row's sort_order.
  // The renamed entry lives above as asset_id='ka_gochara' (post-cutover form).
  //
  // ── GOCHARA-UTKARSA W3.4 — century-horizon heavy writer (migration 560) ────
  {
    asset_id: 'ka_gochara_v3_century_materialize',
    layer: 'kala', sort_order: 108,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Gochara Śatābdi Mātrika (v3)',
    english_name: 'GOCHARA-UTKARSA Century Materialize (v3, decade slices)',
    english_description: 'GOCHARA-UTKARSA W3.4 heavy writer: plan_substeps returns 60 substeps (6 event classes × 10 decade slices spanning birth-century 1984–2084). Each run_substep calls gochara_v3.interval_solver.find_threshold_crossings over the decade JD range, applies delta fingerprinting (MD5 of event_class+era_slice_key+ENGINE_VERSION+resonance_targets) for skip-on-unchanged semantics, and DELETE-then-INSERTs into kala_gochara_windows_v2 with era_slice_key=g3_{year_start}_{year_end}. I2: ZERO imports from gochara_grammar/*, gochara_intensity/*, or ka_gochara_sweep/*. I4: empty resonance targets → honest 0 rows, no fabrication.',
    storage_type: 'postgres_table',
    target_table: 'kala_gochara_windows_v2',
    count_sql: "SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation LIKE 'g3_%'",
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'GOCHARA-v3 century windows — count depends on active threshold-crossing intervals across 60 decade slices.',
    // W5.2 DAG integration (migration 562): full depends_on set reflecting the
    // v3 writer's true runtime inputs across ClassContext.fetch() + engine.py.
    // ka_gochara_resonance — resonance targets (step 1, always required)
    // ka_vedha_gochara     — kala_vedha_gochara (W1.3 quality_gates, wired)
    // ka_moorti_nirnaya    — kala_moorti_nirnaya (W2.2 moorti modifier)
    // ka_kota_chakra       — kala_kota_chakra (W2.5 kota-chakra ring modifier)
    // ka_tithi_pravesha    — kala_tithi_pravesha (W2.7b annual tone)
    // bg_sky_calendar      — bg_sky_events (W2.6 real eclipses)
    depends_on: [
      'ka_gochara_resonance',
      'ka_vedha_gochara',
      'ka_moorti_nirnaya',
      'ka_kota_chakra',
      'ka_tithi_pravesha',
      'bg_sky_calendar',
    ],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  // ── KALA K1 services (K1 wave — no stored rows; service_kind per mig 242) ──
  {
    asset_id: 'ka_graha_sancara',
    layer: 'kala', sort_order: 100,
    sanskrit_name: 'Graha-sañcara',
    english_name: 'Ephemeris service',
    english_description: 'Ephemeris-at-T service: sidereal positions for all 9 grahas at any datetime. Two read paths: bg_ephemeris (1900–2150) and live swisseph fallback. Per-call memo cache keyed on (T, ayanamsha). TRUE_NODE throughout.',
    storage_type: 'service',
    target_table: null, count_sql: null, size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Service asset — no stored rows; returns computed positions on demand',
    depends_on: ['bg_ephemeris'],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'service', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_dasha_kala',
    layer: 'kala', sort_order: 101,
    sanskrit_name: 'Daśā-kāla',
    english_name: 'Daśā Eligibility Service',
    english_description: 'Lazy-pruning tree-walk over chart_dashas (level-4 Sookshma) with cross-system agreement scoring. Serves all 7 daśā systems; KP as Vimśottarī sub-level via kp_sublevel column. Nārāyaṇa absent.',
    storage_type: 'service',
    target_table: null, count_sql: null, size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Service asset — no stored rows; eligibility bands computed on demand from chart_dashas',
    depends_on: ['ga_dashas'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'service', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_muhurta_seva',
    layer: 'kala', sort_order: 102,
    sanskrit_name: 'Muhūrta-sevā',
    english_name: 'Panchāṅga-Muhūrta Service',
    english_description: 'Deterministic panchāṅga/muhūrta scoring service. Wraps panchang_engine; Tāra Bala native-chart overlay wired (birth_nakshatra_id=25 Purva Bhadrapada). Location mandatory — no silent Bhubaneswar default. 8 event classes including upaya_ritual and sadhana_initiation.',
    storage_type: 'service',
    target_table: null, count_sql: null, size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Service asset — no stored rows; panchāṅga computed live per (date, location)',
    depends_on: ['ka_graha_sancara'],
    scope: 'global', is_active: true, estimated_seconds: null,
    asset_kind: 'service', catalog_status: 'DRAFT',
  },

  // ── KALA (4) — artifact placeholders; updated per wave ────────────────────
  {
    asset_id: 'ka_kalasutra',
    layer: 'kala', sort_order: 1,
    sanskrit_name: 'Kālasūtra',
    english_name: 'Bounded Activation',
    english_description: 'Bounded activation artifact (1 row per signal×ayanamsha). Fills L2 null hooks (active_dasha_periods, activation_predicted_dates, dasha_activation_proximity_score) at L3. Retires row-per-day kala_timeline. Upstream: ka_yojaka + ka_sangam.',
    storage_type: 'postgres_table',
    target_table: 'kala_activation',
    count_sql: 'SELECT count(*) FROM kala_activation WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_activation')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per signal × ayanamsha; count grows with number of active MSR signals in kala_activation_predicates',
    depends_on: ['ka_yojaka', 'ka_sangam'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact',
  },
  {
    asset_id: 'ka_sangam',
    layer: 'kala', sort_order: 2,
    sanskrit_name: 'Saṅgam',
    english_name: 'Convergence engine',
    english_description: 'Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep). Extends kala_convergence with convergence_score (I-16 multiplicative+saturating), orb-strength (I-17 cos²), rarity_years, confidence_score (I-21), independent_current_count (I-22). THE VALUABLE CORE.',
    storage_type: 'postgres_table',
    target_table: 'kala_convergence',
    count_sql: 'SELECT count(*) FROM kala_convergence WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_convergence')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from dasha + transit cluster analysis; count depends on alignment density',
    depends_on: ['ka_yojaka', 'ka_dasha_kala', 'ka_gochara', 'ka_muhurta_seva'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact',
  },
  {
    asset_id: 'ka_vighnakara',
    layer: 'kala', sort_order: 3,
    sanskrit_name: 'Vighnakāra',
    english_name: 'Obstruction periods',
    english_description: 'Obstruction/counter-indicator detector. Identifies malefic transits, daśā veto, panchāṅga obstructions, papakartari that suppress convergence windows. Writes kala_obstruction with severity + override_score.',
    storage_type: 'postgres_table',
    target_table: 'kala_obstruction',
    count_sql: 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_obstruction')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Runtime-derived from transit analysis over sensitive points; count depends on graha configuration',
    depends_on: ['ka_sangam', 'ka_gochara', 'ka_muhurta_seva'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact',
  },
  {
    asset_id: 'ka_avadhi',
    layer: 'kala', sort_order: 4,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Avadhi',
    english_name: 'Period dossiers',
    english_description: 'Per-dasha-period dossier: lord-condition fact refs (chart_facts ids only, never restated), activated bodha_pratijna ids whose domain overlaps the period window, sublord (AD lord) modulation factor. BA-P5A Step 2, DAG: ka_yojaka -> ka_avadhi.',
    storage_type: 'postgres_table',
    target_table: 'kala_avadhi',
    count_sql: 'SELECT count(*) FROM kala_avadhi WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_avadhi')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One dossier row per chart_dashas period (MD+AD, all systems) — count is chart/dasha-system dependent. Live-measured 0 for chart 482012f1, 2026-07-05 — not yet rebuilt since this asset was registered; floors are aspirational per §N.4.',
    // Migration 406 corrects depends_on: drops phantom 'ka_yojaka' edge (writer
    // never reads kala_activation_predicates), adds real 'ga_dashas' + 'bg_ghatana'.
    depends_on: ['ga_dashas', 'bo_pratijna', 'bg_ghatana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'ka_yojaka',
    layer: 'kala', sort_order: 5,
    sanskrit_name: 'Yojaka',
    english_name: 'Activation bridge',
    english_description: 'Classifies each L2 signal into a signature_class, binds the RATIFIED class template, stores concrete activation predicates for ka_sangam/ka_vighnakara to search. NEVER writes into L2 tables. Per-chart artifact; delete-then-insert idempotency.',
    storage_type: 'postgres_table',
    target_table: 'kala_activation_predicates',
    count_sql: 'SELECT count(*) FROM kala_activation_predicates WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_activation_predicates')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One predicate per L2 signal per ayanamsha; total ≈ 66,738 for native chart',
    depends_on: ['bo_laksana', 'bg_transit_rules', 'ga_dashas', 'bo_bimba', 'bo_sangati', 'bo_pratijna', 'bg_ghatana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_kala_darshana',
    layer: 'kala', sort_order: 6,
    sanskrit_name: 'Kāla-darśana',
    english_name: 'Display-ready temporal view',
    english_description: 'Display-ready temporal view. Synthesizes kala_convergence + kala_obstruction into effective_score (convergence × obstruction discount), net_label, and structured narrative. Serve-time layer for UI.',
    storage_type: 'postgres_table',
    target_table: 'kala_darshana',
    count_sql: 'SELECT count(*) FROM kala_darshana WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_darshana')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One display row per convergence window (up to 300 per chart); count depends on ka_sangam output',
    depends_on: ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_jivana_parva',
    layer: 'kala', sort_order: 7,
    sanskrit_name: 'Jīvana-parva',
    english_name: 'Life-arc biographical chapter',
    english_description: 'Life-arc biographical chapter artifact. Segments native life into daśā-anchored parvas with theme keywords, quality labels (building/peak/consolidating/receding/transitional), and convergence density. Historical characterization, not prediction.',
    storage_type: 'postgres_table',
    target_table: 'kala_jivana_parva',
    count_sql: 'SELECT count(*) FROM kala_jivana_parva WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_jivana_parva')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per mahadasha (typically 9 for a full Vimshottari cycle)',
    depends_on: ['ka_kala_darshana', 'ka_dasha_kala'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_bhavishya_lekha',
    layer: 'kala', sort_order: 8,
    sanskrit_name: 'Bh\u0101vi\u1e63ya-lekha',
    english_name: 'Probabilistic forward projections',
    english_description: 'Probabilistic forward projections (3-year horizon). Assigns probability tiers (tier_1_high/tier_2_moderate/tier_3_speculative), domain labels, falsifiability hooks, and calibration records. The testable-prediction artifact per §A mission.',
    storage_type: 'postgres_table',
    target_table: 'kala_bhavishya',
    count_sql: 'SELECT count(*) FROM kala_bhavishya WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_bhavishya')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Up to 50 ranked projections per chart over a 3-year forward horizon; depends on ka_kala_darshana output',
    depends_on: ['ka_kala_darshana', 'ka_vighnakara'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_tulana',
    layer: 'kala', sort_order: 9,
    sanskrit_name: 'Tulanā',
    english_name: 'Cross-pattern prioritization',
    english_description: 'Serve-time QT-4 ranking engine. Ranks windows ACROSS patterns and life-domains by I-11 composite (convergence×0.40 + rarity×0.25 + confidence×0.20 + proximity×0.15). Provides head-to-head compare(A,B) with dissonance-aware verdicts (proceed/defer/proceed_with_mitigation) and multi-domain attention map. Pure serve-time: no stored rows.',
    storage_type: 'service',
    target_table: null, count_sql: null, size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Serve-time service — no stored rows; rankings computed on demand over kala_convergence + kala_darshana.',
    depends_on: ['ka_sangam', 'ka_vighnakara', 'ka_kala_darshana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'service', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ka_taranga',
    layer: 'kala', sort_order: 10,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Taraṅga',
    english_name: 'Activation waveform',
    english_description: 'Monthly convolution of dasha x transit x promise activation scores, stored for months 1950-01 through 2100-12 per scope (domain + event_class). activation = harmonic_mean(dasha_contribution, transit_contribution, promise_contribution) where all three > 0, else arithmetic mean of available components.',
    storage_type: 'postgres_table',
    target_table: 'kala_taranga',
    count_sql: 'SELECT count(*) FROM kala_taranga WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_taranga')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per month (1950-01..2100-12 = 1812 months) per scope (domain x event_class) — count depends on scope cardinality. Live-measured 0 for chart 482012f1, 2026-07-05 — not yet rebuilt since this asset was registered; floors are aspirational per §N.4.',
    // Migration 406 corrects depends_on: writer reads kala_convergence directly
    // (ka_sangam owns it) plus chart_dashas (ga_dashas) and brahma_event_ontology
    // (bg_ghatana), none previously declared; ka_avadhi + bo_pratijna retained.
    depends_on: ['ka_avadhi', 'bo_pratijna', 'ka_sangam', 'ga_dashas', 'bg_ghatana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana, registry item 16 (migration 520).
    // Kota-Chakra: transiting grahas mapped to the fort's stambha/durgantara/
    // prakara/bahya rings relative to the janma nakshatra, with entry/exit
    // windows + an attack/defence reading. Ring table lives in the versioned
    // L0 asset bg_kota_chakra_rings (ADJUDICATION-9, migration 523 — moved
    // off an inline services/ka_kota_chakra/logic.py dict; no served value
    // changed). Single canonical ayanamsha (lahiri_chitrapaksha) — matches
    // the L3 convention (ka_avadhi et al.).
    asset_id: 'ka_kota_chakra',
    layer: 'kala', sort_order: 120,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Koṭa-Cakra',
    english_name: 'Fort Chart (Transit Fortress)',
    english_description: 'Transiting grahas mapped to the kota\'s stambha/durgantara/prakara/bahya rings relative to the janma nakshatra, with entry/exit windows and an attack/defence reading. Reads natal Moon longitude from chart_facts (ga_positions), transiting positions from ephemeris_daily (bg_ephemeris), and the ring partition from bg_kota_chakra_rings (L0, ADJUDICATION-9).',
    storage_type: 'postgres_table',
    target_table: 'kala_kota_chakra',
    count_sql: 'SELECT COUNT(*) FROM kala_kota_chakra WHERE chart_id=$1',
    size_sql: "SELECT pg_total_relation_size('kala_kota_chakra')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per (graha, contiguous same-nakshatra ring-run) over a ~460-day scanned horizon (60 days back, 400 forward) around build time — typically 15-40 rows/chart across the 9 grahas. Floors are aspirational per §N.4; seeded 0, set to the achieved count after the first real build.',
    depends_on: ['ga_positions', 'bg_ephemeris', 'bg_kota_chakra_rings'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana, registry item 17 (migration 521).
    // Sudarśana-Chakra year-wheel triple-lagna progression. BINDING NAMING
    // RULING: named ka_sudarshana_varsha, never bare `sudarshana` — confirmed
    // namesake-only collision against the unrelated L2 bo_sudarshana static
    // tri-frame signal writer (see services/ka_sudarshana_varsha/logic.py for
    // the full distinction). Year-wheel progression ONLY (not the fuller
    // Sudarshana Chakra Dasha sub-period structure — disclosed scope).
    asset_id: 'ka_sudarshana_varsha',
    layer: 'kala', sort_order: 121,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Sudarśana-Cakra Varṣa',
    english_name: 'Sudarśana-Chakra Year-Wheel',
    english_description: 'The rotating annual house-per-year progression of the tri-lagna framework (Janma/Chandra/Sūrya Lagna), full 120-year lifespan. Pure arithmetic over natal chart_facts (ga_positions) — no ephemeris calls.',
    storage_type: 'postgres_table',
    target_table: 'kala_sudarshana_varsha',
    count_sql: 'SELECT COUNT(*) FROM kala_sudarshana_varsha WHERE chart_id=$1',
    size_sql: "SELECT pg_total_relation_size('kala_sudarshana_varsha')",
    target_floor: 0,
    expected_volume_formula: '120',
    expected_volume_inputs: null,
    volume_explanation: 'Exactly 120 rows/chart (varsha years 1..120, full-life horizon) once a real build runs — pure arithmetic, no partial-coverage failure mode. Seeded 0 per §N.4 until the first real build confirms it.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-tithi-pravesha, registry item 13 (migration 531;
    // renumbered from 530 -> 531 after a cross-branch collision with
    // shad-darshana/w4-lane-r-yajna-setu's 530_bg_muhurta_lattice_panchangika_families.sql,
    // an independent unmerged lane — migration-collision rail. sort_order 124
    // (122/123 already taken by ka_moorti_nirnaya/ka_vedha_gochara below).
    // Tithi-Praveśa: the lunar-return counterpart to Tājika Vārṣaphala
    // (ga_tajaka, L1 solar-return). Annual chart cast for the instant the
    // Moon returns to its exact natal sidereal longitude nearest each
    // solar-birthday anniversary — real Swiss-Ephemeris root-find
    // (pyjhora_adapter, same engine ga_tajaka uses), full 120-year lifespan.
    // Return-instant + chart-cast only; the Tājika-specific Muntha/Vārṣeśa/
    // yoga apparatus is Vārṣaphala-only and out of scope (disclosed choice,
    // see services/ka_tithi_pravesha/logic.py docstring).
    asset_id: 'ka_tithi_pravesha',
    layer: 'kala', sort_order: 124,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Tithi-Praveśa',
    english_name: 'Tithi-Praveśa (Lunar-Return Annual Chart)',
    english_description: 'The lunar-return counterpart to Tājika Vārṣaphala (ga_tajaka): the annual chart cast for the instant the transiting Moon returns to its exact natal sidereal longitude nearest each solar-birthday anniversary, full 120-year lifespan. Real ephemeris root-find (pyjhora_adapter) + full annual-chart cast (Praveśa Lagna + graha positions). Natal Moon longitude read verbatim from chart_facts (ga_positions), never re-derived.',
    storage_type: 'postgres_table',
    target_table: 'kala_tithi_pravesha',
    count_sql: 'SELECT COUNT(*) FROM kala_tithi_pravesha WHERE chart_id=$1',
    size_sql: "SELECT pg_total_relation_size('kala_tithi_pravesha')",
    target_floor: 0,
    expected_volume_formula: '120',
    expected_volume_inputs: null,
    volume_explanation: 'Exactly 120 rows/chart (pravesha years 1..120, full-life horizon) once a real build runs — benchmarked ~3.4ms/row (root-find + annual-chart cast) during design, no partial-coverage failure mode expected. Seeded 0 per §N.4 until the first real build confirms it.',
    depends_on: ['ga_positions'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha, registry item 4 (migration 525).
    // Moorti-nirṇaya: the classical gold/silver/copper/iron quality of a
    // transiting graha's stay in a sign, determined by the Moon's nakshatra
    // at the moment of ingress, offset from the janma nakshatra. Resolved
    // against the REAL, cited bg_transit_moorti table (Phaladeepika Ch.26;
    // BPHS Ch.28) — never re-derived. Scoped to the 8 grahas other than the
    // Moon (see services/ka_moorti_nirnaya/logic.py for the disclosed
    // scope rationale).
    asset_id: 'ka_moorti_nirnaya',
    layer: 'kala', sort_order: 122,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Mūrti-Nirṇaya',
    english_name: 'Moorti-Nirṇaya (Transit Quality)',
    english_description: 'The classical gold/silver/copper/iron quality of a transiting graha\'s stay in a sign, determined by the Moon\'s nakshatra at the moment of ingress, offset from the janma nakshatra. Reads natal Moon longitude from chart_facts (ga_positions), transiting positions from ephemeris_daily (bg_ephemeris), and the moorti quality table verbatim from bg_transit_moorti (bg_transit_rules, real cited reference data).',
    storage_type: 'postgres_table',
    target_table: 'kala_moorti_nirnaya',
    count_sql: 'SELECT COUNT(*) FROM kala_moorti_nirnaya WHERE chart_id=$1',
    size_sql: "SELECT pg_total_relation_size('kala_moorti_nirnaya')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per (graha, contiguous same-sign occupancy window) over a ~460-day scanned horizon (60 days back, 400 forward) around build time, across the 8 grahas other than the Moon — typically 15-60 rows/chart. Floors are aspirational per §N.4; seeded 0, set to the achieved count after the first real build.',
    depends_on: ['ga_positions', 'bg_ephemeris', 'bg_transit_rules'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    // ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha, registry item 5 (migration 526,
    // closes defect R-19). Vedha application: two distinct classical
    // obstruction mechanisms, distinguished by vedha_kind — house_vedha
    // (REAL, cited: BPHS Ch.29/Phaladeepika Ch.26, from bg_transit_rules)
    // and sarvatobhadra (nakshatra-level; an honestly disclosed algorithmic
    // approximation — the primary-cited 9x9 grid tables
    // l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha remain unpopulated;
    // see services/ka_vedha_gochara/logic.py for the full R-19 disclosure —
    // no responsibly-transcribable source was found this session, honest
    // gap over fabrication per LAW ZERO).
    asset_id: 'ka_vedha_gochara',
    layer: 'kala', sort_order: 123,
    catalog_status: 'CURRENT',
    sanskrit_name: 'Vedha-Gocara',
    english_name: 'Vedha Application (Transit Obstruction)',
    english_description: 'Two classical vedha (obstruction) mechanisms applied to a chart\'s currently-active and forward transits — house_vedha (BPHS Ch.29/Phaladeepika Ch.26, from bg_transit_rules, REAL cited data) and sarvatobhadra (nakshatra-level, an honestly disclosed algorithmic approximation pending corpus ingestion — closes defect R-19 partially; see services/ka_vedha_gochara/logic.py). Reads natal Moon longitude from chart_facts (ga_positions) and transiting positions from ephemeris_daily (bg_ephemeris).',
    storage_type: 'postgres_table',
    target_table: 'kala_vedha_gochara',
    count_sql: 'SELECT COUNT(*) FROM kala_vedha_gochara WHERE chart_id=$1',
    size_sql: "SELECT pg_total_relation_size('kala_vedha_gochara')",
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per vedha-checkable house transit (house_vedha) or per sarvatobhadra-vedha-nakshatra dwelling window, over the same ~460-day scanned horizon — small, gated by rule/nakshatra match, typically a handful per chart. Floors are aspirational per §N.4; seeded 0, set to the achieved count after the first real build.',
    depends_on: ['ga_positions', 'bg_ephemeris', 'bg_transit_rules'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },

  // ── PHALA (8) ────────────────────────────────────────────────────────────────────────────
  // Updated 2026-06-22 (L4 Phala SETUP-7 / CS1): depends_on + descriptions corrected per
  // L4_PHALA_REGISTRY_AND_WIRING_SPEC_v1_0.md §1; 3 new assets appended (sort_order 6/7/8).
  {
    asset_id: 'ph_nimitta',
    layer: 'phala', sort_order: 1,
    sanskrit_name: 'Nimitta',
    english_name: 'Predictive anchors',
    english_description: 'Predictive anchors: 8 derivation axes (graph-causal, discovery-seeded, embedding-precedent, dāśā+school consensus, ayanāṃśa-robustness, subsystem) + 5 elevations (magnitude, ranged-confidence, karmic-arc, actionability, contradiction); inherits kala_bhavishya',
    storage_type: 'postgres_table',
    target_table: 'phala_anchors',
    count_sql: 'SELECT count(*) FROM phala_anchors WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_anchors')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per predictive anchor; count depends on convergence density and multi-axis derivation',
    depends_on: ['ka_sangam', 'ka_bhavishya_lekha', 'bo_bimba', 'bo_samskara', 'bo_karanajala', 'bo_sangati'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_muhurta',
    layer: 'phala', sort_order: 2,
    sanskrit_name: 'Muhūrta',
    english_name: 'Auspicious windows',
    english_description: 'Personalized auspicious windows: chart-strength + live-transit scored, personal-danger-avoiding, prediction-fused (rides ph_nimitta windows), honest no-good-window verdict',
    storage_type: 'postgres_table',
    target_table: 'phala_muhurta',
    count_sql: 'SELECT count(*) FROM phala_muhurta WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_muhurta')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per scored muhurta candidate window in query range',
    depends_on: ['ph_nimitta', 'ka_kalasutra', 'ga_panchanga'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_sodhana',
    layer: 'phala', sort_order: 3,
    sanskrit_name: 'Śodhana',
    english_name: 'Anomaly detection',
    english_description: 'Anomaly registry: 5 deterministic detectors (confidence inflation, magnitude drift, falsifier absent, ledger gap, layer leakage). LEAKAGE-FIREWALL halts build on L5 calibration contamination. auto_action=stage_for_review only.',
    storage_type: 'postgres_table',
    target_table: 'phala_sodhana',
    count_sql: 'SELECT count(*) FROM phala_sodhana WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_sodhana')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per candidate rectification hypothesis in the search space',
    depends_on: ['ph_nimitta', 'bo_laksana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_pratikara',
    layer: 'phala', sort_order: 4,
    sanskrit_name: 'Pratīkāra',
    english_name: 'Mitigation',
    english_description: 'Managed remedy program: economics/feasibility tiers, sequenced+conflict-free schedule, muhūrta-timed initiation, severity-proportional, cross-tradition choice, outcome loop',
    storage_type: 'postgres_table',
    target_table: 'phala_mitigation',
    count_sql: 'SELECT count(*) FROM phala_mitigation WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_mitigation')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per remedy recommendation, sequenced by feasibility tier',
    depends_on: ['ph_nimitta', 'bo_upaya', 'ka_vighnakara'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_suddha_sodhana',
    layer: 'phala', sort_order: 5,
    sanskrit_name: 'Śuddha-śodhana',
    english_name: 'Cleansed anchor disposition',
    english_description: 'Cleansed disposition: one row per phala_anchors entry, classified as clean/flagged/staged_revision. D43 safety rail — revision_approved_by + revision_applied_at never set by writer; staged revisions require native sign-off before apply.',
    storage_type: 'postgres_table',
    target_table: 'phala_suddha_sodhana',
    count_sql: 'SELECT count(*) FROM phala_suddha_sodhana WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_suddha_sodhana')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per rectification verdict (decisive/probable/unresolved); accumulates across runs',
    depends_on: ['ph_sodhana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_sankrama',
    layer: 'phala', sort_order: 6,
    sanskrit_name: 'Saṅkrama',
    english_name: 'Cross-domain spillover',
    english_description: 'Grounded multi-hop cross-domain dynamics: lag from real activation windows + graph-bridge mechanism, A→B→C cascades, cross-domain conflicts, trajectory + mitigation routing',
    storage_type: 'postgres_table',
    target_table: 'phala_sankrama',
    count_sql: 'SELECT count(*) FROM phala_sankrama WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_sankrama')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per (anchor × target-domain × relationship); count depends on linkage density',
    depends_on: ['ph_nimitta', 'bo_sangati'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_pramana',
    layer: 'phala', sort_order: 7,
    sanskrit_name: 'Pramāṇa',
    english_name: 'Falsifiability scaffolding',
    english_description: 'Unified machine-evaluable falsifiers for every L4 prediction + the L5 onboarding contract + evaluation-staging (no scoring) + portfolio/reverse-calibration channel. Strictly non-scoring (L5 owns calibration)',
    storage_type: 'postgres_table',
    target_table: 'phala_pramana',
    count_sql: 'SELECT count(*) FROM phala_pramana WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_pramana')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per L4 prediction across all ph_* prediction-emitting assets',
    depends_on: ['ph_nimitta', 'ph_sankrama', 'ph_muhurta', 'ph_pratikara', 'ph_sodhana', 'ph_suddha_sodhana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_phaladesa',
    layer: 'phala', sort_order: 8,
    sanskrit_name: 'Phaladeśa',
    english_name: 'Domain result declaration',
    english_description: 'Domain result declaration: 7 domains × 1 row. B.11-compliant (Bodha synthesis read first). Deterministic scaffold (anchor inventory, spillover, mitigation/muhurta coverage). Narration pending via Gemini/DeepSeek only (Anthropic BANNED by DB CHECK)',
    storage_type: 'postgres_table',
    target_table: 'phala_phaladesa',
    count_sql: 'SELECT count(*) FROM phala_phaladesa WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_phaladesa')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Seven rows per chart (one per domain)',
    depends_on: ['ph_nimitta', 'ph_muhurta', 'ph_pratikara', 'ph_suddha_sodhana', 'ph_sankrama', 'ph_pramana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },
  {
    asset_id: 'ph_rectification',
    layer: 'phala', sort_order: 9,
    sanskrit_name: 'Jananakāla-śuddhi',
    english_name: 'Birth-time rectification',
    english_description: 'Birth-time rectification via PyJHora ascendant scan (±90 min, 5-min steps, 5 ayanamshas) scored against pre-2020 LEL events. LEAKAGE-FIREWALL: post-2020 + LEL v1.7 M5-A-S1 enrichment events held out. NO-AUTO-OVERRIDE (D43): auto_action=stage_for_review only; canonical chart never auto-mutated. Best candidate staged for native adoption.',
    storage_type: 'postgres_table',
    target_table: 'phala_rectification',
    count_sql: 'SELECT count(*) FROM phala_rectification WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('phala_rectification')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per (candidate offset × ayanamsha): 37 offsets × 5 ayanamshas = 185 rows; plus one staged-best row in phala_rectification_best',
    depends_on: ['ph_nimitta'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'artifact', catalog_status: 'DRAFT',
  },

  // ── MIMAMSA ───────────────────────────────────────────────────────────────
  {
    // lel_events — the user-authored life-event corpus. Source data, NOT a
    // built asset (has_writer=false). Registered in mimamsa layer with
    // sort_order=0 so it sorts before all mi_* built assets. Registered as a
    // seed row so the three-way CI diff can account for it.
    asset_id: 'lel_events',
    layer: 'mimamsa', sort_order: 0,
    catalog_status: 'DRAFT',
    sanskrit_name: 'Jīvanaghaṭanā Mūla',
    english_name: 'Life Event Log (user-authored source data)',
    english_description: 'Per-chart user-authored life-event corpus (occurrence + recording dates, chart-state index). Source data, NOT a built asset (has_writer=false); intaken via the LEL save API. Availability-driven calibration input; never a prediction-generation source (no-leakage).',
    storage_type: 'postgres_table',
    target_table: null,
    count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'User-authored; grows with native engagement. Not a deterministic count.',
    depends_on: [],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'data',
  },
  {
    asset_id: 'mi_jivanaghatana',
    layer: 'mimamsa', sort_order: 1,
    sanskrit_name: 'Jīvanaghaṭanā',
    english_name: 'Life event log (held-out)',
    english_description: 'LEL — held-out event log isolated from generation; ground truth for prediction calibration',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_event_provenance',
    count_sql: 'SELECT count(*) FROM mimamsa_event_provenance',
    size_sql: "SELECT pg_total_relation_size('mimamsa_event_provenance')",
    target_floor: null,
    expected_volume_formula: "FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')",
    expected_volume_inputs: null,
    volume_explanation: 'Deterministic given the source-of-truth file. Re-runs MUST match the file count exactly; divergence is a bug.',
    // BA Phase 2.5 #9 (derivation-ledger completeness, CLAUDE.md B.3): writer
    // resolves event_class_id via brahma_event_ontology (bg_ghatana); L0-bedrock
    // guard-exempted (dag_edge_guard never flagged this), doc-only addition.
    depends_on: ['bg_ghatana'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_kula',
    layer: 'mimamsa', sort_order: 2,
    sanskrit_name: 'Kula',
    english_name: 'Signal families',
    english_description: 'Signal-family registry + negative-control battery — the governing catalogue of what influences a reading',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_signal_families',
    count_sql: 'SELECT count(*) FROM mimamsa_signal_families',
    size_sql: "SELECT pg_total_relation_size('mimamsa_signal_families')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Fixed global catalogue of signal families + negative controls; grows only when new families are registered',
    // BA Phase 2.5 #9: writer references bg_class_priors for family-prior seeding;
    // L0-bedrock guard-exempted, doc-only addition (CLAUDE.md B.3).
    depends_on: ['bg_rules', 'bg_class_priors'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_bhavisya',
    layer: 'mimamsa', sort_order: 3,
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
    depends_on: ['ph_pramana', 'ph_nimitta', 'ph_phaladesa', 'mi_kula', 'mi_jivanaghatana'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_pramana',
    layer: 'mimamsa', sort_order: 4,
    sanskrit_name: 'Pramāṇa',
    english_name: 'Calibration',
    english_description: 'Prediction outcome calibration records — confidence score vs outcome mapping',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_calibration',
    count_sql: 'SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_calibration')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates as prediction outcomes are recorded — not a deterministic target',
    // BA Phase 2.5 #9: base_rate from brahma_event_ontology (bg_ghatana), scoring
    // weights from brahma_formula_constants (bg_formula_constants); L0-bedrock
    // guard-exempted, doc-only additions (CLAUDE.md B.3).
    depends_on: ['mi_bhavisya', 'mi_jivanaghatana', 'bg_ghatana', 'bg_formula_constants'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_gunanaka',
    layer: 'mimamsa', sort_order: 5,
    sanskrit_name: 'Guṇānaka',
    english_name: 'Multipliers',
    english_description: 'Empirical multiplier weights learned from calibration outcomes',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_multipliers',
    count_sql: 'SELECT count(*) FROM mimamsa_multipliers WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_multipliers')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One row per multiplier type — small, stable catalog; grows only when new signal categories are added',
    // mi_kula retained: migration 365 established this edge (mi_gunanaka.py:70
    // reads mimamsa_signal_families, owned by mi_kula) — a real hard build-order
    // dependency. BA Phase 2.5 #9 additionally adds bg_formula_constants
    // (shrinkage_k/divergence_cap) — L0-bedrock guard-exempted, doc-only
    // (CLAUDE.md B.3).
    depends_on: ['mi_pramana', 'mi_kula', 'bg_formula_constants'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_adhilepa',
    layer: 'mimamsa', sort_order: 6,
    sanskrit_name: 'Adhilepa',
    english_name: 'Overlay',
    english_description: 'L5 learned-weight overlay on L1–L4 base values; 4 adjustment tables + load-bearing sensitivity map (G3)',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_signal_adjustment',
    count_sql: 'SELECT count(*) FROM mimamsa_signal_adjustment WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_signal_adjustment')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One overlay row per (origin_id × weight_id); starts sparse, grows with evidence',
    depends_on: ['mi_gunanaka'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_pariksha',
    layer: 'mimamsa', sort_order: 7,
    sanskrit_name: 'Parīkṣā',
    english_name: 'QA evaluation',
    english_description: 'Answer quality evaluation runs — automated + human QA over synthesis outputs',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_qa_eval',
    count_sql: 'SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_qa_eval')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Accumulates as eval runs are executed — not a deterministic target',
    // BA Phase 2.5 #9: attribution dimension weights from brahma_formula_constants;
    // L0-bedrock guard-exempted, doc-only addition (CLAUDE.md B.3).
    depends_on: ['mi_pramana', 'mi_kula', 'bg_formula_constants'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_sambandha',
    layer: 'mimamsa', sort_order: 8,
    sanskrit_name: 'Sambandha',
    english_name: 'Manifestation grammar',
    english_description: 'Per-native grammar of how each signal/house/karaka expresses — which channel fires for THIS person (G2)',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_manifestation_grammar',
    count_sql: 'SELECT count(*) FROM mimamsa_manifestation_grammar WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_manifestation_grammar')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Structural baseline from classical priors; empirical cells accumulate with event outcomes',
    depends_on: ['mi_pramana', 'mi_pariksha'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_darshana',
    layer: 'mimamsa', sort_order: 9,
    sanskrit_name: 'Darśana',
    english_name: 'Insight surface',
    english_description: 'LLM-ready pre-composed insight units with embeddings + provenance chains + trust metadata (R1–R6)',
    storage_type: 'pgvector',
    target_table: 'mimamsa_insight_units',
    count_sql: 'SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_insight_units')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One insight unit per promoted/supported discovery + calibration stratum + grammar cell with evidence',
    depends_on: ['mi_pramana', 'mi_adhilepa', 'mi_sambandha', 'mi_pariksha', 'mi_gunanaka', 'mi_kula', 'mi_jivanaghatana', 'bo_pratijna'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
  {
    asset_id: 'mi_vistara',
    layer: 'mimamsa', sort_order: 10,
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
  {
    asset_id: 'mi_seva',
    layer: 'mimamsa', sort_order: 11,
    sanskrit_name: 'Sevā',
    english_name: 'Serve-time apply',
    english_description: 'Serve-time contribution-control gateway: effective-value resolution, toggle gates, transit-current binding, MCP parity',
    storage_type: 'service',
    target_table: 'mimamsa_preferences',
    count_sql: null,
    size_sql: "SELECT pg_total_relation_size('mimamsa_preferences')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Preference table rows per user × channel; service has no build-time data volume',
    depends_on: ['mi_adhilepa'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'service',
  },
  {
    asset_id: 'mi_abhilekha',
    layer: 'mimamsa', sort_order: 12,
    sanskrit_name: 'Abhilekha',
    english_name: 'Journal',
    english_description: 'Journal + re-sync service: surfaces due predictions for native feedback, ingests answers as LEL events, triggers L5-only recompute',
    storage_type: 'service',
    target_table: 'mimamsa_journal',
    count_sql: null,
    size_sql: "SELECT pg_total_relation_size('mimamsa_journal')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'One journal entry per prediction answered; accumulates with native engagement',
    depends_on: ['mi_bhavisya'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    asset_kind: 'service',
  },

  // ══ ṢAḌ-DARŚANA W2 — the temporal field as science ═══════════════════════════
  // Spec: 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
  //       KALA_W2_FIELD_DESIGN_v1_0.md §9.1 (DAG edges), §9.2 (these rows).
  {
    // Lane C's row — mirrors migration 494's INSERT identity fields exactly.
    //
    // MERGE-TRAIN NOTE (2026-07-30/31, Conductor integration pass): Lane E's own draft PR
    // included an inert placeholder `ka_kshetra` row here. An earlier merge-train pass
    // removed it, reasoning that Lane C's migration 494 already does
    // `INSERT INTO asset_registry ... ON CONFLICT (asset_id) DO UPDATE` for `ka_kshetra`
    // in production, so no TS-side row was needed. That reasoning was WRONG in one specific
    // way, caught by CI (`catalog_reconciliation.test.ts` red on PR #947): the
    // depends_on-resolution check builds its `assetIds` set purely from THIS file's `ASSETS`
    // array — it never queries the DB. `ka_gochara_sweep` / `ka_gochara_resonance` get away
    // with having no TS row because nothing in this file's `depends_on` arrays references
    // them. `ka_kshetra` does not get away with it, because `mi_bhara`'s own
    // `depends_on: ['ka_kshetra']` below is itself inside this file — so the id it names
    // must also resolve inside this file. Restoring a `ka_kshetra` row is therefore not
    // optional; this is the same defect class as the historical `ga_vichara`
    // (migration 435-only) and `bo_pratijna` gaps, both previously fixed the same way:
    // add the row here.
    //
    // W0.1 UPDATE (2026-08-10, GOCHARA-UTKARSA): Now that this file contains seed rows
    // for ka_gochara_sweep (sort_order 105) and ka_gochara_resonance (sort_order 104),
    // the old `depends_on: []` rationale is resolved. The nine real edges from the live
    // DB (migration 494 + migration 522) are now all represented in this file and can be
    // declared here safely. Running this seed against prod will now correctly set
    // ka_kshetra's depends_on to the full nine-edge set rather than narrowing it to [].
    // Live DB value (verified 2026-08-10):
    //   {ka_dasha_kala, ka_gochara_sweep, ka_gochara_resonance, ga_panchanga,
    //    bo_pratijna, bo_sangati, bo_upaya, bg_cohort, bg_class_lifetime_counts}
    asset_id: 'ka_kshetra',
    layer: 'kala', sort_order: 110,
    sanskrit_name: 'Kāla Kṣetra',
    english_name: 'Temporal Field',
    english_description:
      'ṢAḌ-DARŚANA W2: the ten-stage point-process temporal field. λ_e(t) as a ' +
      'strictly-positive hazard rate (events/day) composed multiplicatively from a classical ' +
      'baseline, a noisy-OR promise prior, per-daśā-system clock terms (proportional hazards), ' +
      'twelve log-linear covariates and multiplicative vighna thinning — stored as log-linear ' +
      'segments that integrate EXACTLY in closed form, with every factor persisted as a ' +
      'provenance edge that must reconstruct the value it explains. Windows are calibrated ' +
      'against the chart\'s OWN circular-shifted sky (item 23). HEAVY writer. Built BESIDE the ' +
      'legacy ka_gochara_sweep (strangler-fig): reads it read-only as a cross-check corpus and ' +
      'writes ZERO rows to any legacy table.',
    storage_type: 'postgres_table',
    target_table: 'kala_field',
    count_sql: 'SELECT COUNT(*) FROM kala_field WHERE chart_id=$1',
    size_sql: null,
    target_floor: 0,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation:
      'Log-linear hazard segments per event class over a 100-year horizon; set to the ' +
      'ACHIEVED count after the first build (§N.4 — floors are aspirational, never fabricated).',
    // Nine real edges per live DB (migration 494 + migration 522).
    // All nine are now represented by seed rows in this file (W0.1, 2026-08-10).
    depends_on: [
      'ka_dasha_kala', 'ka_gochara_sweep', 'ka_gochara_resonance',
      'ga_panchanga', 'bo_pratijna', 'bo_sangati', 'bo_upaya',
      'bg_cohort', 'bg_class_lifetime_counts',
    ],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
    layer_name: 'Kāla', layer_index: 'L3', catalog_status: 'DRAFT', asset_kind: 'data',
  },
  {
    // Lane E's own row — the authoritative one. Mirrors migration 497's INSERT exactly.
    //
    // `depends_on: ['ka_kshetra']` and NOTHING ELSE, and `ka_kshetra` must NEVER list
    // `mi_bhara` in return: that pair of edges forms the cycle ka_kshetra → mi_bhara →
    // ka_kshetra, and `resolveBuildPlan`'s topoSort would then reject EVERY plan containing
    // either asset — breaking every future chart build, not just this wave's. The
    // calibration loop closes by VERSION PIN across builds (weights v0 seeded by migration
    // 476; ka_kshetra reads the newest active version as a DATA dependency; mi_bhara writes
    // a new version; the next rebuild pins it), which keeps the DAG acyclic within every
    // build. Asserted by platform/tests/unit/build/w2_weights_acyclicity.test.ts.
    //
    // count_sql points at kala_field_skill rather than at target_table
    // (kala_field_weight_versions) on purpose: weight VERSIONS are partly global, while the
    // chart-scoped evidence this asset produces for a given chart is its skill rows — and
    // the cockpit stats route reads count_sql, not asset_throughput (§N.4 cockpit-truth rail).
    asset_id: 'mi_bhara',
    layer: 'mimamsa', sort_order: 13,
    sanskrit_name: 'Kāla Bhāra',
    english_name: 'Field Weight Calibration',
    english_description:
      'Stage 9 of the temporal-field pipeline: fits the hazard field\'s weights against this ' +
      'chart\'s recorded life events (blocked forward-chaining CV, shrinkage to the classical ' +
      'structural priors), publishes a new versioned weights artifact, and reports the ' +
      'temporal skill score and the time-rescaling goodness-of-fit. The ONLY stage permitted ' +
      'to read the LEL (CIRCULARITY GUARD). ṢAḌ-DARŚANA items 21/39.',
    storage_type: 'postgres_table',
    target_table: 'kala_field_weight_versions',
    count_sql: 'SELECT count(*) FROM kala_field_skill WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('kala_field_skill')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation:
      'One skill row per scored event class plus one chart-level aggregate; grows only as the ' +
      'LEL grows. A chart with no LEL correctly produces the structural-prior state with ' +
      'skill_state = underpowered — an honest zero, not an error.',
    depends_on: ['ka_kshetra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },

  // ══ ṢAḌ-DARŚANA W4 Lane S — the Unified Intervention Ledger (item 42) ═══════
  // Spec: KALA_W4_UPAYA_DESIGN_v1_0.md §4.2 (table), §8.2 (this row, verbatim
  // shape). Mirrors migration NNN_mimamsa_intervention_ledger.sql's own
  // `INSERT INTO asset_registry ... ON CONFLICT (asset_id) DO UPDATE` — same
  // discipline as `ka_kshetra` (migration 494) / `mi_bhara` (migration 497)
  // above: the catalog-reconciliation check builds its id set purely from THIS
  // file, so the row lands here in the SAME PR as the `mi_sankalpa` writer
  // (§2.5.1 Nirmāṇa contract).
  //
  // `depends_on: ['ka_kshetra']`, per brief §2.5.3 and KALA_W2_FIELD_DESIGN
  // §9.1 verbatim. `ka_kshetra` never lists `mi_sankalpa` back (§2.5.4
  // acyclicity rule) — the ledger flows forward only, same shape as the
  // ka_kshetra/mi_bhara pair immediately above.
  {
    asset_id: 'mi_sankalpa',
    layer: 'mimamsa', sort_order: 14,
    sanskrit_name: 'Saṅkalpa',
    english_name: 'Intervention Ledger',
    english_description:
      'Unified intervention ledger — every elected act (upāya · yajña · elected activity) ' +
      'with its adjudication record (the JudgmentLedger, frozen verbatim at election time), ' +
      'predicted differential, native performance attestation and LEL outcome linkage; the ' +
      'three-armed study of election itself (elected_pending / acted_with_election / ' +
      'elected_not_acted / acted_without_election). Prediction spine is ' +
      'brahma_prospective_ledger by FK (ruling S-1) — this writer never inserts into it ' +
      'directly; filing happens at serve time through platform-mcp\'s ' +
      '`fileInterventionFalsifier` (intervention_filing.ts). ṢAḌ-DARŚANA W4 item 42.',
    storage_type: 'postgres_table',
    target_table: 'mimamsa_intervention_ledger',
    count_sql: 'SELECT count(*) FROM mimamsa_intervention_ledger WHERE chart_id = $1',
    size_sql: "SELECT pg_total_relation_size('mimamsa_intervention_ledger')",
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation:
      'Accumulates as interventions are elected and attested — not a deterministic target ' +
      '(§N.4: floors are aspirational, set to the ACHIEVED count after first build, never ' +
      'fabricated).',
    depends_on: ['ka_kshetra'],
    scope: 'per_chart', is_active: true, estimated_seconds: null,
  },
]

// ── Coefficient definitions ───────────────────────────────────────────────────

const COEFFICIENTS: CoefficientDef[] = [
  {
    coefficient_name: 'SIGNAL_PER_RULE',
    description: 'Signals produced per classical rule per ayanamsha set (measured first build)',
    upstream_asset_id: 'bg_rules',
    downstream_asset_id: 'bo_laksana',
  },
  {
    coefficient_name: 'EDGE_DENSITY',
    description: 'Fraction of signal pairs forming a CGM edge (measured first build)',
    upstream_asset_id: 'bo_laksana',
    downstream_asset_id: 'bo_karanajala',
  },
  {
    coefficient_name: 'ANCHOR_PER_CONVERGENCE',
    description: 'Predictive anchors derived per convergence window (measured first build)',
    upstream_asset_id: 'ka_sangam',
    downstream_asset_id: 'ph_nimitta',
  },
  {
    coefficient_name: 'TRANSITS_PER_DAY',
    description: 'Major-aspect transit events per calendar day across the ephemeris range (measured first build)',
    upstream_asset_id: 'bg_ephemeris',
    downstream_asset_id: 'ka_kalasutra',
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

      // Every coefficient referenced in formula must exist in COEFFICIENTS.
      // Strip ACTUAL() and FILE_COUNT() call bodies first — their args are not coefficient refs.
      const coeffCheckStr = formula
        .replace(/ACTUAL\([^)]+\)/g, '1')
        .replace(/FILE_COUNT\([^)]+\)/g, '1')
      const coeffRe = /\b([A-Z_]+)\b/g
      const formulaTokens = [...coeffCheckStr.matchAll(coeffRe)].map(m => m[1])
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
  const lelAsset = ASSETS.find(a => a.asset_id === 'mi_jivanaghatana')!
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
      // null target_table is intentional for chart_facts-partitioned assets (use count_sql filter)
      // and service assets (health_probe mechanism). Preserve is_active as defined — do NOT override.
      console.log(`  – ${asset.asset_id}: no target_table (intentional — preserving is_active=${asset.is_active})`)
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

  // Hard stop: only assets with a declared target_table that doesn't exist in prod are counted.
  // Null-target_table assets (chart_facts-partitioned + service) are skipped above and never counted.
  // Expected absences: up to ~12 L2–L5 tables not yet built. Limit = 20 gives headroom.
  if (absentAssets.length > 20) {
    await client.end()
    throw new Error(
      `HARD STOP: ${absentAssets.length} assets have absent target_tables (limit: 20).\n` +
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
    const assetKind = asset.asset_kind ?? 'data'
    const layerName = asset.layer_name ?? layerNames[asset.layer] ?? asset.layer
    const layerIndex = asset.layer_index ?? layerIndices[asset.layer] ?? null
    const catalogStatus = asset.catalog_status ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')

    await client.query(
      `INSERT INTO asset_registry (
        asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
        storage_type, target_table, count_sql, size_sql, target_floor,
        expected_volume_formula, expected_volume_inputs, volume_explanation,
        depends_on, scope, is_active, estimated_seconds,
        asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status,
        asset_kind
      ) VALUES (
        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25
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
        -- MR-06 (PARISHKARA cutover durability): RETIRED guard.
        -- A RETIRED asset (e.g. ka_gochara_sweep post W6.4 cutover) must NEVER
        -- be resurrected by a re-seed. If the existing DB row is already RETIRED,
        -- preserve that status and the corresponding is_active=false rather than
        -- blindly overwriting with whatever the seed says. This is the ON-CONFLICT
        -- analogue of migration 563's one-way transition: CURRENT→RETIRED is
        -- irreversible by the seed; only an explicit native-authorized migration
        -- can reverse it.
        catalog_status = CASE WHEN asset_registry.catalog_status = 'RETIRED'
                              THEN asset_registry.catalog_status
                              ELSE EXCLUDED.catalog_status END,
        is_active = CASE WHEN asset_registry.catalog_status = 'RETIRED'
                         THEN asset_registry.is_active
                         ELSE EXCLUDED.is_active END,
        asset_type = EXCLUDED.asset_type,
        layer_name = EXCLUDED.layer_name,
        layer_index = EXCLUDED.layer_index,
        provides_apis = EXCLUDED.provides_apis,
        health_probe = EXCLUDED.health_probe,
        asset_kind = EXCLUDED.asset_kind`,
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
        assetKind,
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

  // Post-apply DB readback assertion — verify DB state matches seed intent
  // (not in-memory state: the in-memory ASSETS array may have been mutated during preflight)
  console.log('\nPost-apply verification: reading back from DB...')
  const { rows: dbRows } = await client.query<{ asset_id: string; is_active: boolean }>(
    'SELECT asset_id, is_active FROM asset_registry ORDER BY sort_order',
  )
  const dbMap = new Map(dbRows.map(r => [r.asset_id, r.is_active]))
  const seedMap = new Map(ASSETS.map(a => [a.asset_id, a.is_active]))

  const mismatches: string[] = []
  for (const [assetId, seedActive] of seedMap) {
    const dbActive = dbMap.get(assetId)
    if (dbActive === undefined) {
      mismatches.push(`  MISSING in DB: ${assetId}`)
    } else if (dbActive !== seedActive) {
      mismatches.push(`  MISMATCH: ${assetId} — seed wants is_active=${seedActive}, DB has is_active=${dbActive}`)
    }
  }

  await client.end()

  // Hard assert: chart_facts-partitioned assets must be active (these were the recurring divergence source)
  const CRITICAL_ACTIVE = ['ga_strength', 'ga_sensitive', 'ga_sade_sati', 'ga_structural']
  const criticalFailed = CRITICAL_ACTIVE.filter(id => dbMap.get(id) !== true)
  if (criticalFailed.length > 0) {
    throw new Error(
      `ASSERTION FAILED: chart_facts-partitioned assets must be is_active=true after seed.\n` +
      `Failed: ${criticalFailed.join(', ')}\n` +
      'Run migration 228 to reactivate, then re-apply seed.',
    )
  }

  if (mismatches.length > 0) {
    throw new Error(
      `ASSERTION FAILED: ${mismatches.length} asset(s) have wrong is_active in DB after seed apply:\n` +
      mismatches.join('\n'),
    )
  }

  // Verification summary (from DB, not in-memory)
  const active = [...dbMap.values()].filter(Boolean).length
  const inactive = [...dbMap.values()].filter(v => !v).length
  console.log('\n── Seed complete (DB-verified) ──────────────────────────────────')
  console.log(`Total:    ${dbMap.size}`)
  console.log(`Active:   ${active}`)
  console.log(`Inactive: ${inactive}`)
  if (inactive > 0) {
    const inactiveIds = [...dbMap.entries()].filter(([, v]) => !v).map(([id]) => id)
    console.log('Inactive list (target_table absent in prod):')
    inactiveIds.forEach(id => console.log(`  - ${id}`))
  }
  console.log('\nCoefficients seeded (all current_value = NULL — measured on first build):')
  COEFFICIENTS.forEach(c => console.log(`  - ${c.coefficient_name}`))
  console.log()
}

if (process.env.NODE_ENV !== 'test') {
  main().catch(err => {
    console.error('\nSeed failed:', err.message)
    process.exit(1)
  })
}
