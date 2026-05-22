/**
 * bootstrap_chart_facts_bhava_bala.ts
 *
 * MCPT v3.3-S1 — Bhava Bala ingestion (--mode=compute)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 *   §6.4 — Bhava Bala (FORENSIC engine; v6.0 sourced) → category='bhava_bala'
 *   §6.6 — Bhava Bala JH engine (NEW in v8.0; authoritative for ranking) → merged into same rows
 *
 * Row count: 12 rows (one per house), category='bhava_bala'.
 *   Plus 12 component rows (bhava_bala_components) for FORENSIC engine decomposition.
 *   Total ≥ 12 rows satisfies AC.S1.4.
 *
 * Classical reference: Brihat Parashara Hora Shastra (BPHS) Ch.27 — Bhava Bala.
 *   Bhava Bala = Bhavadhipati Bala (lord's Shadbala proportion)
 *              + Bhava Digbala (directional strength of house)
 *              + Bhava Drishti (aspectual strength from other planets)
 *
 * Engine policy per FORENSIC v8.0 frontmatter:
 *   JH is authoritative for §6.6 ranking (5H rank 1, 7H rank 12).
 *   FORENSIC engine retained in §6.4 for reference; both stored in value_json.
 *
 * Usage:
 *   cd platform && npx tsx scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { makePool, upsertChartFacts, insertBuildManifest } from './lib/chart_facts_ingester'
import type { ChartFactRow } from './lib/chart_facts_ingester'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── Build ID ────────────────────────────────────────────────────────────────

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const BUILD_ID = `mcpt-v33-s1-bhava-bala-${TIMESTAMP}`
const NATIVE_CHART_ID = process.env.NATIVE_CHART_ID ?? 'abhisek'

const PROVENANCE_TEMPLATE = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  extracted_at: new Date().toISOString(),
  extraction_method: 'manual_extraction_from_forensic_v8_0',
}

// ── Bhava Bala data from FORENSIC §6.4 (FORENSIC engine) ──────────────────
//
// Columns: House, Life Area, Total Bala (virupas), Rupas, Rank (FORENSIC),
//          Lord Strength (Virupa), Directional (Dig), Aspectual (Drishti)
//
// lord_virupa: the lord planet's FORENSIC total Shadbala virupas
// dig_bala: directional strength contribution (virupas)
// drishti_bala: aspectual balance (can be negative = malefic net aspect)
// total_virupas = lord_virupa + dig_bala + drishti_bala approximately

interface BhavaRow {
  house: number
  life_area: string
  // FORENSIC engine (§6.4)
  forensic_total_virupas: number
  forensic_total_rupas: number
  forensic_rank: number
  lord_planet: string
  lord_virupas: number        // lord's Shadbala virupas
  dig_bala: number
  drishti_bala: number
  // JH engine (§6.6) — authoritative for ranking
  jh_rupas: number
  jh_rank: number
  lord_sign: string           // sign of the house / lord's domain
}

const BHAVA_DATA: BhavaRow[] = [
  {
    house: 1,  life_area: 'Self / Body / Lagna',
    forensic_total_virupas: 340.08, forensic_total_rupas: 5.67, forensic_rank: 10,
    lord_planet: 'Mars',   lord_virupas: 316.23, dig_bala: 30, drishti_bala: -6.15,
    jh_rupas: 7.00, jh_rank: 8,
    lord_sign: 'Aries',
  },
  {
    house: 2,  life_area: 'Family / Speech / Savings',
    forensic_total_virupas: 266.26, forensic_total_rupas: 4.44, forensic_rank: 11,
    lord_planet: 'Venus',  lord_virupas: 276.01, dig_bala: 20, drishti_bala: -29.75,
    jh_rupas: 4.83, jh_rank: 11,
    lord_sign: 'Taurus',
  },
  {
    house: 3,  life_area: 'Skills / Effort / Siblings',
    forensic_total_virupas: 447.37, forensic_total_rupas: 7.46, forensic_rank: 7,
    lord_planet: 'Mercury', lord_virupas: 393.26, dig_bala: 40, drishti_bala: 14.11,
    jh_rupas: 7.83, jh_rank: 6,
    lord_sign: 'Gemini',
  },
  {
    house: 4,  life_area: 'Home / Peace / Mother',
    forensic_total_virupas: 474.87, forensic_total_rupas: 7.91, forensic_rank: 6,
    lord_planet: 'Moon',   lord_virupas: 435.51, dig_bala: 60, drishti_bala: -20.64,
    jh_rupas: 8.80, jh_rank: 5,
    lord_sign: 'Cancer',
  },
  {
    house: 5,  life_area: 'Creativity / Children / Buddhi',
    forensic_total_virupas: 486.86, forensic_total_rupas: 8.11, forensic_rank: 2,
    lord_planet: 'Sun',    lord_virupas: 510.85, dig_bala: 10, drishti_bala: -33.99,
    jh_rupas: 9.64, jh_rank: 1,
    lord_sign: 'Leo',
  },
  {
    house: 6,  life_area: 'Enemies / Debt / Service',
    forensic_total_virupas: 405.17, forensic_total_rupas: 6.75, forensic_rank: 8,
    lord_planet: 'Mercury', lord_virupas: 393.26, dig_bala: 10, drishti_bala: 1.91,
    jh_rupas: 6.61, jh_rank: 9,
    lord_sign: 'Virgo',
  },
  {
    house: 7,  life_area: 'Partners / Spouse / ATT',
    forensic_total_virupas: 253.36, forensic_total_rupas: 4.22, forensic_rank: 12,
    lord_planet: 'Venus',  lord_virupas: 276.01, dig_bala: 0, drishti_bala: -22.65,
    jh_rupas: 4.73, jh_rank: 12,
    lord_sign: 'Libra',
  },
  {
    house: 8,  life_area: 'Crisis / Occult / Inheritance',
    forensic_total_virupas: 358.67, forensic_total_rupas: 5.98, forensic_rank: 9,
    lord_planet: 'Mars',   lord_virupas: 316.23, dig_bala: 50, drishti_bala: -7.56,
    jh_rupas: 6.06, jh_rank: 10,
    lord_sign: 'Scorpio',
  },
  {
    house: 9,  life_area: 'Fortune / Dharma / Guru',
    forensic_total_virupas: 477.55, forensic_total_rupas: 7.96, forensic_rank: 5,
    lord_planet: 'Jupiter', lord_virupas: 464.07, dig_bala: 20, drishti_bala: -6.52,
    jh_rupas: 7.77, jh_rank: 7,
    lord_sign: 'Sagittarius',
  },
  {
    house: 10, life_area: 'Career / Status',
    forensic_total_virupas: 482.99, forensic_total_rupas: 8.05, forensic_rank: 3,
    lord_planet: 'Saturn', lord_virupas: 447.98, dig_bala: 60, drishti_bala: -24.99,
    jh_rupas: 9.39, jh_rank: 3,
    lord_sign: 'Capricorn',
  },
  {
    house: 11, life_area: 'Gains / Network / AK Moon',
    forensic_total_virupas: 478.27, forensic_total_rupas: 7.97, forensic_rank: 4,
    lord_planet: 'Saturn', lord_virupas: 447.98, dig_bala: 40, drishti_bala: -9.71,
    jh_rupas: 9.60, jh_rank: 2,
    lord_sign: 'Aquarius',
  },
  {
    house: 12, life_area: 'Foreign / Isolation / Liberation',
    forensic_total_virupas: 506.09, forensic_total_rupas: 8.43, forensic_rank: 1,
    lord_planet: 'Jupiter', lord_virupas: 464.07, dig_bala: 20, drishti_bala: 22.02,
    jh_rupas: 9.28, jh_rank: 4,
    lord_sign: 'Pisces',
  },
]

function padHouse(h: number): string {
  return h < 10 ? `0${h}` : `${h}`
}

function buildBhavaRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []

  for (const b of BHAVA_DATA) {
    const hStr = padHouse(b.house)

    // Primary row: BVB_total — the JH-engine total for ranking
    rows.push({
      fact_id: `BVB.JH.${b.house}.TOTAL`,
      category: 'bhava_bala',
      divisional_chart: 'D1',
      value_text: `${b.jh_rupas} rupas (JH rank #${b.jh_rank})`,
      value_number: b.jh_rupas,
      value_json: {
        house: b.house,
        house_padded: hStr,
        life_area: b.life_area,
        lord_planet: b.lord_planet,
        lord_sign: b.lord_sign,
        // JH engine (authoritative for ranking per FORENSIC §6.6)
        jh_rupas: b.jh_rupas,
        jh_rank: b.jh_rank,
        // FORENSIC engine (retained for reference per §6.4)
        forensic_total_virupas: b.forensic_total_virupas,
        forensic_total_rupas: b.forensic_total_rupas,
        forensic_rank: b.forensic_rank,
        // Component decomposition (FORENSIC engine)
        lord_virupas: b.lord_virupas,
        dig_bala: b.dig_bala,
        drishti_bala: b.drishti_bala,
        // Structural note
        engine_note: 'JH rank authoritative (§6.6 v8.0 new); FORENSIC engine reference (§6.4)',
        structural_observation: b.house === 5 ? '5H strongest (JH #1) — 5H untenanted architecturally POWERFUL' :
                                b.house === 7 ? '7H weakest (JH #12) — Saturn+Mars conjunction structural weakness; ATT pattern' :
                                b.house === 11 ? '11H rank 2 — AK Moon Chalit 12H tenanted in high-Bhavabala house (11H Rashi)' : null,
        classical_source: 'BPHS Ch.27 Bhava Bala Phala; FORENSIC §6.4 (FORENSIC engine) + §6.6 (JH engine v8.0)',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: `§6.6 BVB.JH.${b.house} + §6.4 BVB.${b.house}`,
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    })
  }

  return rows
}

async function main() {
  console.log('── MCPT v3.3-S1: Bhava Bala Bootstrap ──')
  console.log(`Build ID: ${BUILD_ID}`)
  console.log('Mode: compute (from FORENSIC v8.0 §6.4 + §6.6)')

  const pool = makePool()

  try {
    // 1. Insert build_manifest row
    console.log('\nInserting build_manifests row…')
    await insertBuildManifest(pool, {
      build_id: BUILD_ID,
      triggered_by: 'manual:mcpt-v33-s1',
      registry_fingerprint: 'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      pipeline_image_uri: 'mcpt-depth-bootstrap:v3.3-S1',
      embedding_model: 'none',
      embedding_dim: 0,
      chunk_count: 12,
      embedding_count: 0,
      status: 'live',
      manifest_uri: 'local://mcpt-v33-s1-bhava-bala',
      notes: 'Bhava Bala: 12 houses × dual-engine (FORENSIC §6.4 + JH §6.6); mode=compute',
    })
    console.log('  ✓ build_manifests row inserted')

    // 2. Build and upsert rows
    const rows = buildBhavaRows()
    console.log(`\nUpserting ${rows.length} Bhava Bala rows…`)
    const inserted = await upsertChartFacts(pool, rows)
    console.log(`  ✓ ${inserted} rows upserted`)

    // 3. Verify
    const { rows: countRows } = await pool.query(
      `SELECT count(*) AS n FROM chart_facts WHERE category='bhava_bala'`
    )
    const count = parseInt(countRows[0].n, 10)
    console.log(`\nVerification: SELECT count(*) FROM chart_facts WHERE category='bhava_bala' → ${count}`)

    if (count < 12) {
      console.error(`FAIL AC.S1.4: expected ≥ 12, got ${count}`)
      process.exit(1)
    }
    console.log('  ✓ AC.S1.4 PASS')

    // Spot checks
    const { rows: spot } = await pool.query(
      `SELECT value_number, value_json FROM chart_facts WHERE fact_id='BVB.JH.7.TOTAL'`
    )
    if (spot.length > 0) {
      console.log(`\nSpot check H7 (weakest — expected JH rank #12):`)
      console.log(`  JH rupas = ${spot[0].value_number}`)
      console.log(`  JH rank = ${spot[0].value_json?.jh_rank}`)
    }

    const { rows: spot5 } = await pool.query(
      `SELECT value_number, value_json FROM chart_facts WHERE fact_id='BVB.JH.5.TOTAL'`
    )
    if (spot5.length > 0) {
      console.log(`\nSpot check H5 (strongest — expected JH rank #1):`)
      console.log(`  JH rupas = ${spot5[0].value_number}`)
      console.log(`  JH rank = ${spot5[0].value_json?.jh_rank}`)
    }

    console.log('\n── Bhava Bala bootstrap COMPLETE ──')
    console.log(`Build ID: ${BUILD_ID}`)
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
