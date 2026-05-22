/**
 * bootstrap_chart_facts_kp.ts
 *
 * MCPT v3.3-S2 — KP System ingestion (FORENSIC mode)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 *   §4.1 KP Cusp Mirror  — 12 cusps × 3 roles (cusp_lord, star_lord, sub_lord) = 36 rows
 *   §4.2 KP Planetary Positions — 9 planets × 3 roles = 27 rows
 *   §4.3 KP House Significators — 7 houses with significator lists = 7 rows (with JSON arrays)
 *
 * Note on §4.3: FORENSIC records significators for houses 1, 2, 6, 7, 10, 11, 12 only.
 * Houses 3, 4, 5, 8, 9 are not listed — B.10 discipline: mark as not-in-FORENSIC.
 *
 * B.10 compliance: All values read directly from FORENSIC v8.0. No values fabricated.
 *
 * Usage:
 *   cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
 *   DATABASE_URL=postgresql://... npx tsx platform/scripts/bootstrap/bootstrap_chart_facts_kp.ts
 *
 * Prerequisites:
 *   DATABASE_URL in environment (via .env.local or direct export)
 *   The chart_facts table must exist (migration 014).
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { makePool, upsertChartFacts, insertBuildManifest } from './lib/chart_facts_ingester'
import type { ChartFactRow } from './lib/chart_facts_ingester'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── Build ID ────────────────────────────────────────────────────────────────

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const BUILD_ID = `mcpt-v33-s2-kp-${TIMESTAMP}`

// ── Provenance ──────────────────────────────────────────────────────────────

const PROVENANCE = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  extracted_at: new Date().toISOString(),
  extraction_method: 'manual_extraction_from_forensic_v8_0',
}

// ── §4.1 KP Cusp Mirror ─────────────────────────────────────────────────────
//
// FORENSIC §4.1 table: 12 houses with columns:
//   Cusp | Degree | Sign | Star Lord | Sub Lord | Sub-Sub Lord
//
// Subkey format: `<house_num>.<role>` per brief §5
// We map: Star Lord → cusp_lord, Sub Lord → star_lord, Sub-Sub Lord → sub_lord
// (The column labeled "Star Lord" in FORENSIC is the cusp/star-lord in KP parlance)
//
// Note: FORENSIC §4.1 header reads "Star Lord | Sub Lord | Sub-Sub Lord"
// which maps to KP roles cusp_lord / star_lord / sub_lord respectively.
// In KP nomenclature: the nakshatra star lord of the cusp degree is the "Star Lord".
// For ingestion we preserve the FORENSIC column names as roles.

const KP_CUSP_DATA: Array<{
  house: number
  description: string
  degree: string
  sign: string
  star_lord: string
  sub_lord: string
  sub_sub_lord: string
}> = [
  // FORENSIC §4.1 — KP.CUSP.1 through KP.CUSP.12
  { house: 1,  description: 'Lagna',      degree: '12°29′19″', sign: 'Aries',       star_lord: 'Ketu',    sub_lord: 'Mercury', sub_sub_lord: 'Mars'    },
  { house: 2,  description: 'Wealth',     degree: '12°29′01″', sign: 'Taurus',      star_lord: 'Moon',    sub_lord: 'Rahu',    sub_sub_lord: 'Saturn'  },
  { house: 3,  description: 'Effort',     degree: '08°00′37″', sign: 'Gemini',      star_lord: 'Rahu',    sub_lord: 'Rahu',    sub_sub_lord: 'Venus'   },
  { house: 4,  description: 'Home',       degree: '03°03′44″', sign: 'Cancer',      star_lord: 'Jupiter', sub_lord: 'Rahu',    sub_sub_lord: 'Moon'    },
  { house: 5,  description: 'Creativity', degree: '01°07′36″', sign: 'Leo',         star_lord: 'Ketu',    sub_lord: 'Venus',   sub_sub_lord: 'Venus'   },
  { house: 6,  description: 'Service',    degree: '04°47′17″', sign: 'Virgo',       star_lord: 'Sun',     sub_lord: 'Saturn',  sub_sub_lord: 'Rahu'    },
  { house: 7,  description: 'Spouse',     degree: '12°29′19″', sign: 'Libra',       star_lord: 'Rahu',    sub_lord: 'Saturn',  sub_sub_lord: 'Jupiter' },
  { house: 8,  description: 'Change',     degree: '12°29′01″', sign: 'Scorpio',     star_lord: 'Saturn',  sub_lord: 'Mars',    sub_sub_lord: 'Saturn'  },
  { house: 9,  description: 'Fortune',    degree: '08°00′37″', sign: 'Sagittarius', star_lord: 'Ketu',    sub_lord: 'Jupiter', sub_sub_lord: 'Saturn'  },
  { house: 10, description: 'Career',     degree: '03°03′44″', sign: 'Capricorn',   star_lord: 'Sun',     sub_lord: 'Saturn',  sub_sub_lord: 'Saturn'  },
  { house: 11, description: 'Gain',       degree: '01°07′36″', sign: 'Aquarius',    star_lord: 'Mars',    sub_lord: 'Mercury', sub_sub_lord: 'Rahu'    },
  { house: 12, description: 'Loss',       degree: '04°47′17″', sign: 'Pisces',      star_lord: 'Saturn',  sub_lord: 'Saturn',  sub_sub_lord: 'Mars'    },
]

function buildKPCuspRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []
  for (const cusp of KP_CUSP_DATA) {
    const h = cusp.house
    // Three role rows per cusp
    rows.push({
      fact_id: `KP.CUSP.${h}.STAR_LORD`,
      category: 'kp_cusp',
      divisional_chart: 'D1',
      value_text: cusp.star_lord,
      value_number: null,
      value_json: {
        house: h,
        house_description: cusp.description,
        sign: cusp.sign,
        degree: cusp.degree,
        role: 'star_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.1',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
    rows.push({
      fact_id: `KP.CUSP.${h}.SUB_LORD`,
      category: 'kp_cusp',
      divisional_chart: 'D1',
      value_text: cusp.sub_lord,
      value_number: null,
      value_json: {
        house: h,
        house_description: cusp.description,
        sign: cusp.sign,
        degree: cusp.degree,
        role: 'sub_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.1',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
    rows.push({
      fact_id: `KP.CUSP.${h}.SUB_SUB_LORD`,
      category: 'kp_cusp',
      divisional_chart: 'D1',
      value_text: cusp.sub_sub_lord,
      value_number: null,
      value_json: {
        house: h,
        house_description: cusp.description,
        sign: cusp.sign,
        degree: cusp.degree,
        role: 'sub_sub_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.1',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
  }
  return rows
}

// ── §4.2 KP Planetary Positions ─────────────────────────────────────────────
//
// FORENSIC §4.2 table: 9 planets with columns:
//   Planet | Degree | Star Lord | Sub Lord | Sub-Sub Lord

const KP_PLANET_DATA: Array<{
  planet: string
  degree: string
  star_lord: string
  sub_lord: string
  sub_sub_lord: string
}> = [
  // FORENSIC §4.2 — KP.PLN.SUN through KP.PLN.KETU
  { planet: 'Sun',     degree: '22°02′', star_lord: 'Moon',    sub_lord: 'Venus',   sub_sub_lord: 'Saturn'  },
  { planet: 'Moon',    degree: '27°08′', star_lord: 'Jupiter', sub_lord: 'Venus',   sub_sub_lord: 'Moon'    },
  { planet: 'Mars',    degree: '18°37′', star_lord: 'Rahu',    sub_lord: 'Moon',    sub_sub_lord: 'Saturn'  },
  { planet: 'Mercury', degree: '00°55′', star_lord: 'Sun',     sub_lord: 'Rahu',    sub_sub_lord: 'Sun'     },
  { planet: 'Jupiter', degree: '09°53′', star_lord: 'Ketu',    sub_lord: 'Saturn',  sub_sub_lord: 'Mercury' },
  { planet: 'Venus',   degree: '19°15′', star_lord: 'Venus',   sub_lord: 'Rahu',    sub_sub_lord: 'Mercury' },
  { planet: 'Saturn',  degree: '22°32′', star_lord: 'Jupiter', sub_lord: 'Saturn',  sub_sub_lord: 'Venus'   },
  { planet: 'Rahu',    degree: '19°07′', star_lord: 'Moon',    sub_lord: 'Mercury', sub_sub_lord: 'Jupiter' },
  { planet: 'Ketu',    degree: '19°07′', star_lord: 'Mercury', sub_lord: 'Ketu',    sub_sub_lord: 'Saturn'  },
]

function buildKPPlanetRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []
  for (const pln of KP_PLANET_DATA) {
    const key = pln.planet.toUpperCase()
    rows.push({
      fact_id: `KP.PLN.${key}.STAR_LORD`,
      category: 'kp_planet',
      divisional_chart: 'D1',
      value_text: pln.star_lord,
      value_number: null,
      value_json: {
        planet: pln.planet,
        degree: pln.degree,
        role: 'star_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.2',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
    rows.push({
      fact_id: `KP.PLN.${key}.SUB_LORD`,
      category: 'kp_planet',
      divisional_chart: 'D1',
      value_text: pln.sub_lord,
      value_number: null,
      value_json: {
        planet: pln.planet,
        degree: pln.degree,
        role: 'sub_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.2',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
    rows.push({
      fact_id: `KP.PLN.${key}.SUB_SUB_LORD`,
      category: 'kp_planet',
      divisional_chart: 'D1',
      value_text: pln.sub_sub_lord,
      value_number: null,
      value_json: {
        planet: pln.planet,
        degree: pln.degree,
        role: 'sub_sub_lord',
      },
      source_section: 'FORENSIC_v8_0_§4.2',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
  }
  return rows
}

// ── §4.3 KP House Significators ─────────────────────────────────────────────
//
// FORENSIC §4.3 records significators for 7 houses only:
//   1, 2, 6, 7, 10, 11, 12
// Houses 3, 4, 5, 8, 9 are NOT in FORENSIC — B.10: not fabricated.
// Per brief §5: subkey = `<planet>.significator_houses`, value_json = array of houses.
// Here we store per-planet significator arrays from the house perspective.

const KP_SIGNIFICATOR_DATA: Array<{
  house: number
  house_description: string
  significators: string[]
  kp_logic: string
}> = [
  // FORENSIC §4.3 — KP.SIG.1 through KP.SIG.12 (partial)
  { house: 1,  house_description: 'Self',            significators: ['Mars', 'Ketu'],                                        kp_logic: 'Mars (Lord); Ketu (agent for Mars)'                                                                       },
  { house: 2,  house_description: 'Wealth',          significators: ['Rahu', 'Venus'],                                       kp_logic: 'Rahu (occupant); Venus (lord)'                                                                             },
  { house: 6,  house_description: 'Job/Debt',        significators: ['Mars', 'Ketu', 'Mercury'],                             kp_logic: 'Mars and Ketu (in star of lord Mercury); Mercury (lord)'                                                  },
  { house: 7,  house_description: 'Partners',        significators: ['Moon', 'Saturn', 'Venus'],                             kp_logic: 'Moon (in star of occupant Saturn); Saturn (occupant); Venus (lord)'                                        },
  { house: 10, house_description: 'Career',          significators: ['Mercury', 'Venus', 'Mars', 'Ketu', 'Sun', 'Saturn'],   kp_logic: 'Mercury and Venus (in star of occupant Sun); Mars and Ketu (in star of occupant Mercury); Sun and Mercury (occupants); Saturn (lord)' },
  { house: 11, house_description: 'Gains',           significators: ['Sun', 'Rahu', 'Moon', 'Saturn'],                      kp_logic: 'Sun and Rahu (in star of occupant Moon); Moon (occupant); Saturn (lord)'                                  },
  { house: 12, house_description: 'Loss/Investment', significators: ['Saturn', 'Jupiter'],                                   kp_logic: 'Saturn (in star of lord Jupiter); Jupiter (lord)'                                                         },
]

function buildKPSignificatorRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []
  for (const sig of KP_SIGNIFICATOR_DATA) {
    rows.push({
      fact_id: `KP.SIG.${sig.house}`,
      category: 'kp_significator',
      divisional_chart: 'D1',
      value_text: sig.significators.join(', '),
      value_number: null,
      value_json: {
        house: sig.house,
        house_description: sig.house_description,
        significators: sig.significators,
        kp_logic: sig.kp_logic,
      },
      source_section: 'FORENSIC_v8_0_§4.3',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
  }
  return rows
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const pool = makePool()
  try {
    const cuspRows = buildKPCuspRows()
    const planetRows = buildKPPlanetRows()
    const sigRows = buildKPSignificatorRows()

    console.log(`[KP Bootstrap] build_id = ${BUILD_ID}`)
    console.log(`[KP Bootstrap] kp_cusp rows:        ${cuspRows.length}  (expected ≥ 36)`)
    console.log(`[KP Bootstrap] kp_planet rows:      ${planetRows.length}  (expected ≥ 27)`)
    console.log(`[KP Bootstrap] kp_significator rows: ${sigRows.length}   (expected ≥ 7)`)

    const allRows = [...cuspRows, ...planetRows, ...sigRows]
    console.log(`[KP Bootstrap] total rows:           ${allRows.length}`)

    // Insert build_manifests row first (chart_facts.build_id FK requires it)
    await insertBuildManifest(pool, {
      build_id: BUILD_ID,
      triggered_by: 'manual:mcpt-v33-s2',
      registry_fingerprint: 'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      pipeline_image_uri: 'mcpt-depth-bootstrap:v3.3-S2',
      embedding_model: 'none',
      embedding_dim: 0,
      chunk_count: allRows.length,
      embedding_count: 0,
      status: 'live',
      manifest_uri: 'local://mcpt-v33-s2-kp',
      notes: 'KP ingestion from FORENSIC v8.0 §4.1+§4.2+§4.3; mode=FORENSIC; 36 cusp + 27 planet + 7 sig rows',
    })
    console.log(`[KP Bootstrap] build_manifests row inserted`)

    const inserted = await upsertChartFacts(pool, allRows)
    console.log(`[KP Bootstrap] upserted: ${inserted} rows — DONE`)
  } finally {
    await pool.end()
  }
}

main().catch((err) => {
  console.error('[KP Bootstrap] FATAL:', err)
  process.exit(1)
})
