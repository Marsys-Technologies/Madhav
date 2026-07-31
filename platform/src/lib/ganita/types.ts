/**
 * ganita/types.ts — Typed schema for the Gaṇita L1 Fact Store
 *
 * The Fact Store is a composite, chart_id-keyed aggregation of all L1 domain
 * slices written by the ganita.engine JSONL writer. All reads go through
 * query_chart_facts(); the write path is the Python pipeline writers.
 *
 * Domain coverage maps 1-to-1 to FORENSIC v8.0 §0–§27
 * (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md).
 *
 * [BRAHMA-GA-1-8]
 */

// The settled verification vocabulary is declared once, in the retrieval envelope
// (which is the zero-import module the serve side and the codegen both read).
import type { VerificationPassStatus } from '@/lib/retrieval/envelope'

export type { VerificationPassStatus }

// ─── Provenance envelope (every fact carries this) ────────────────────────────

export interface FactProvenance {
  source_uri: string        // e.g. 'gs://madhav-marsys-sources/99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md'
  source_version: string    // e.g. '8.0'
  source_canonical_id: string  // e.g. 'FORENSIC'
  extracted_at: string      // ISO-8601
  extraction_method: string // 'pyjhora_v3' | 'manual_v8' | 'computed'
}

// ─── Base row shape (mirrors chart_facts table) ───────────────────────────────

export interface ChartFactRow {
  id?: string
  fact_id: string           // namespace.SUBJECT.KEY  (e.g. PLN.SUN.LON_DEG)
  chart_id?: string         // UUID of the chart (nullable for global/native-only)
  ayanamsha_id?: string     // 'lahiri' | 'kp' | 'raman' | 'true_chitra' | 'surya_siddhanta' | 'INVARIANT'
  category: string          // see CHART_FACTS_CATEGORIES
  divisional_chart: string  // 'D1' | 'D9' | 'D10' | … | 'INVARIANT'
  fact_category?: string    // A3 schema field (mirrors category in new schema)
  fact_key?: string         // A3 schema field
  fact_subject?: string     // A3 schema field
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string    // '§2.1' | '§4' | …
  build_id: string
  provenance: FactProvenance
  is_stale?: boolean
  created_at?: string
  engine_version?: string
  /** SAMĀPTI Ruling 13: was a hand-written 4-value union — a FIFTH definition of the
   *  vocabulary, and a false one: chart_facts legitimately stores 10 distinct values
   *  (documented_approximation, floored, computed_extension, …), so this type told
   *  callers a row shape the database never had. Now the settled union. */
  verification_pass_status?: VerificationPassStatus
  citation_ref?: string
  citation_human?: string
  unit?: string
}

// ─── Domain section types (mirrors FORENSIC v8.0 §N structure) ───────────────

export interface MetadataSection {
  birth_date: string | null          // '1984-02-05'
  birth_time: string | null          // '10:43:00 IST'
  birth_place: string | null         // 'Bhubaneswar, Odisha, India'
  latitude: string | null
  longitude: string | null
  timezone: string | null
  ayanamsha: string | null
  ayanamsha_value: string | null
  house_system: string | null
  lagna_sign: string | null
  lagna_degree: string | null
  lagna_nakshatra: string | null
  lagna_pada: string | null
}

export interface PlanetPlacementRow {
  planet: string            // 'Sun' | 'Moon' | 'Mars' | 'Mercury' | 'Jupiter' | 'Venus' | 'Saturn' | 'Rahu' | 'Ketu'
  sign: string
  house_rashi: number
  house_chalit: number | null
  degree_dms: string | null // '12°23′55″'
  degree_decimal: number | null
  nakshatra: string | null
  nakshatra_pada: number | null
  nakshatra_lord: string | null
  sub_lord: string | null   // KP sub-lord
  dignity: string | null    // 'exalted' | 'own' | 'moolatrikona' | 'friend' | 'neutral' | 'enemy' | 'debilitated'
  retrograde: boolean
  combusted: boolean | null
}

export interface HouseRow {
  house: number
  sign: string
  cusp_degree: string | null
  cusp_nakshatra: string | null
  cusp_lord: string | null
  sub_lord: string | null   // KP cusp sub-lord
  planets_rashi: string[]   // planet names in this house (rashi placement)
  planets_chalit: string[]  // planet names in this house (chalit placement)
}

export interface DivisionalChartRow {
  varga: string             // 'D9' | 'D10' | 'D12' | …
  planet: string
  sign: string
  house: number | null
  lord: string | null
}

export interface DashaRow {
  system: string            // 'vimshottari' | 'yogini' | 'jaimini_chara' | 'kalachakra' | …
  level: 'MD' | 'AD' | 'PD' | 'SD' | 'PD2'
  lord: string
  start_date: string        // ISO-8601
  end_date: string          // ISO-8601
  duration_days: number | null
}

export interface StrengthRow {
  planet: string
  system: string            // 'shadbala' | 'ashtakavarga' | 'bhava_bala' | 'vimsopaka'
  value: number | null
  unit: string | null       // 'rupas' | 'bindus' | 'points'
  category: string | null   // sub-strength category
}

export interface SensitivePointRow {
  type: string              // 'upagraha' | 'special_lagna' | 'saham' | 'arudha' | 'karaka' | 'yogi'
  name: string              // 'Gulika' | 'Hora Lagna' | 'Punya Saham' | 'Atmakaraka' | …
  sign: string | null
  house: number | null
  degree: string | null
  lord: string | null
}

export interface PanchangaRow {
  component: string         // 'tithi' | 'vara' | 'nakshatra' | 'yoga' | 'karana' | …
  value: string | null
  lord: string | null
  pada: number | null
  start_iso: string | null
  end_iso: string | null
}

export interface YogaRow {
  yoga_name: string
  type: string              // 'rajayoga' | 'dhanyoga' | 'aristha' | 'yoga' | …
  planets_involved: string[]
  houses_involved: number[]
  strength: string | null   // 'strong' | 'medium' | 'weak'
  source_rule: string | null
}

export interface AspectRow {
  aspector: string          // planet name
  aspected_body: string     // planet | house | point
  aspect_type: string       // 'full' | '3/4' | '1/2' | '1/4' | 'jaimini' | 'western_trine' | …
  orb_degrees: number | null
  strength: string | null
}

// ─── Composite Fact Store (top-level return type of query_chart_facts) ────────

export interface GanitaFactStore {
  chart_id: string | null
  ayanamsha_id: string
  build_id: string
  generated_at: string      // ISO-8601
  coverage_score: number    // 0–1, fraction of non-null domain sections

  // §1 — Core Identity / Metadata
  metadata: MetadataSection

  // §2 — D1 Rashi Chart planets
  planets: PlanetPlacementRow[]

  // §3 — Houses (Rashi + Chalit)
  houses: HouseRow[]

  // §4 — Divisional Charts D1–D60
  divisionals: DivisionalChartRow[]

  // §5 — Dasha Systems (Vimshottari, Yogini, Jaimini Chara, …)
  dashas: DashaRow[]

  // §6 — Strength Metrics (Shadbala, Ashtakavarga, Bhava Bala)
  strengths: StrengthRow[]

  // §7–§13 — Sensitive Points (Upagrahas, Special Lagnas, Sahams, Arudhas, Karakas)
  sensitive_points: SensitivePointRow[]

  // §15 — Panchanga DNA
  panchanga: PanchangaRow[]

  // §16–§17 — Yogas and Aspects
  yogas: YogaRow[]
  aspects: AspectRow[]

  // §22–§23 — Sade Sati and Varshphal (stored as raw rows)
  sade_sati: ChartFactRow[]
  varshphal: ChartFactRow[]

  // All raw rows indexed by category (for extensibility)
  rows_by_category: Record<string, ChartFactRow[]>

  // Domain presence flags (for coverage assertion)
  domains_present: string[]
  domains_missing: string[]
}

// ─── Query input schema ───────────────────────────────────────────────────────

export interface QueryChartFactsInput {
  chart_id?: string
  ayanamsha_id?: string
  category?: string | string[]
  categories?: string[]
  planet?: string
  house?: number
  sign?: string
  nakshatra?: string
  divisional_chart?: string
  keyword?: string
  limit?: number
  as_of_date?: string
  from_date?: string
  to_date?: string
  batched?: boolean
  [key: string]: unknown
}

// ─── All valid category values ────────────────────────────────────────────────

export const CHART_FACTS_CATEGORIES = [
  'metadata',
  'planet',
  'house',
  'divisional',
  'dasha_vimshottari',
  'dasha_yogini',
  'dasha_jaimini',
  'dasha_kalachakra',
  'dasha_balance',
  'shadbala',
  'ashtakavarga',
  'bhava_bala',
  'vimsopaka',
  'upagraha',
  'special_lagna',
  'saham',
  'arudha',
  'karaka',
  'yoga',
  'aspect',
  'panchanga',
  'sensitive_point',
  'sade_sati',
  'varshphal',
  'kp',
  'transit',
] as const

export type ChartFactCategory = (typeof CHART_FACTS_CATEGORIES)[number]

// ─── Domain sections that must be non-null for full coverage ─────────────────

export const FORENSIC_V8_REQUIRED_DOMAINS = [
  'metadata',
  'planet',
  'house',
  'divisional',
  'dasha_vimshottari',
  'shadbala',
  'ashtakavarga',
  'upagraha',
  'saham',
  'special_lagna',
  'arudha',
  'karaka',
  'yoga',
  'aspect',
  'panchanga',
  'sade_sati',
  'varshphal',
  'kp',
] as const

export type ForensicV8Domain = (typeof FORENSIC_V8_REQUIRED_DOMAINS)[number]
