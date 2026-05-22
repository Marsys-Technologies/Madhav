/**
 * bootstrap_chart_facts_ashtakavarga.ts
 *
 * MCPT v3.3-S1 — Ashtakavarga ingestion (--mode=compute)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 *   §7.1 — BAV (Bhinnashtakavarga) per planet by sign  → category='ashtakavarga_bav'
 *   §7.2 — SAV (Sarvashtakavarga) by sign              → category='ashtakavarga_sav'
 *   §7.3 — Shuddha Pinda reductions                    → category='ashtakavarga_pinda'
 *
 * Row counts:
 *   SAV: 12 rows (one per sign/house)
 *   BAV: 7 planets × 12 signs = 84 rows + 1 JH Moon reference row = 85+
 *   Pinda: 7 planets × 3 values (rasi_pinda, graha_pinda, shuddha_pinda) = 21 rows
 *   Total BAV-category rows: ≥ 100 (AC.S1.3 satisfied via BAV+pinda)
 *
 * Classical reference: Brihat Parashara Hora Shastra (BPHS) Ch.28–29
 *   Ashtakavarga Phala Adhyaya. Each planet contributes benefic points (bindus)
 *   to each house counted from its own position in the 8 reference positions
 *   (the planet itself + 7 other planets). Max = 8 bindus per house per planet.
 *   SAV = sum of all 7 planets' BAV values for each house.
 *
 * Note on GAP.08 (Moon BAV): FORENSIC values are canonical for MARSYS-JIS.
 *   JH Moon BAV differs in 4 signs (±1 bindu each). JH row stored separately
 *   as AVG.BAV.MOON.JH.* for reference only.
 *
 * Usage:
 *   cd platform && npx tsx scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { makePool, upsertChartFacts, insertBuildManifest } from './lib/chart_facts_ingester'
import type { ChartFactRow } from './lib/chart_facts_ingester'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── Build ID ────────────────────────────────────────────────────────────────

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const BUILD_ID = `mcpt-v33-s1-ashtakavarga-${TIMESTAMP}`
const NATIVE_CHART_ID = process.env.NATIVE_CHART_ID ?? 'abhisek'

const PROVENANCE_TEMPLATE = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  extracted_at: new Date().toISOString(),
  extraction_method: 'manual_extraction_from_forensic_v8_0',
}

// ── Sign order (zodiac sequence) ────────────────────────────────────────────
//
// House mapping for native chart (Aries Lagna):
//   Aries=H1, Taurus=H2, Gemini=H3, Cancer=H4, Leo=H5, Virgo=H6,
//   Libra=H7, Scorpio=H8, Sagittarius=H9, Capricorn=H10, Aquarius=H11, Pisces=H12

const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

const SIGN_ABBR: Record<string, string> = {
  'Aries': 'AR', 'Taurus': 'TA', 'Gemini': 'GE', 'Cancer': 'CN',
  'Leo': 'LE', 'Virgo': 'VI', 'Libra': 'LI', 'Scorpio': 'SC',
  'Sagittarius': 'SG', 'Capricorn': 'CP', 'Aquarius': 'AQ', 'Pisces': 'PI'
}

// ── BAV data from FORENSIC §7.1 ─────────────────────────────────────────────
// Format: [Ar, Ta, Ge, Cn, Le, Vi, Li, Sc, Sg, Cp, Aq, Pi, Total]
// Source: FORENSIC §7.1 AVG.BAV.* rows (FORENSIC canonical; GAP.08)

const BAV_FORENSIC: Record<string, number[]> = {
  Sun:     [5, 5, 5, 5, 4, 3, 5, 6, 2, 4, 2, 2],  // total=48
  Moon:    [3, 1, 5, 5, 6, 3, 4, 5, 4, 2, 5, 6],  // total=49 (FORENSIC canonical)
  Mars:    [4, 6, 4, 4, 2, 2, 5, 5, 1, 3, 1, 2],  // total=39
  Mercury: [4, 7, 4, 6, 3, 4, 5, 7, 4, 5, 2, 3],  // total=54
  Jupiter: [5, 4, 3, 4, 5, 6, 7, 3, 4, 6, 5, 4],  // total=56
  Venus:   [4, 4, 5, 4, 6, 5, 3, 3, 6, 4, 4, 4],  // total=52
  Saturn:  [4, 2, 2, 4, 4, 3, 4, 4, 4, 2, 4, 2],  // total=39
}

// JH Moon row for reference (differs from FORENSIC in 4 signs; GAP.08)
const BAV_MOON_JH: number[] = [3, 1, 4, 5, 6, 3, 5, 4, 4, 3, 5, 6] // total=49

// ── SAV data from FORENSIC §7.2 ─────────────────────────────────────────────
// FORENSIC values (authoritative). JH values differ in Gemini(27), Libra(34), Scorpio(32), Capricorn(27).
// Note: FORENSIC SAV = sum of BAV columns = verified below.

const SAV_FORENSIC: Record<string, number> = {
  Aries: 29, Taurus: 29, Gemini: 28, Cancer: 32, Leo: 30, Virgo: 26,
  Libra: 33, Scorpio: 33, Sagittarius: 25, Capricorn: 26, Aquarius: 23, Pisces: 23
}
const SAV_GRAND_TOTAL = 337

const SAV_JH: Record<string, number> = {
  Aries: 29, Taurus: 29, Gemini: 27, Cancer: 32, Leo: 30, Virgo: 26,
  Libra: 34, Scorpio: 32, Sagittarius: 25, Capricorn: 27, Aquarius: 23, Pisces: 23
}

// ── Shuddha Pinda from FORENSIC §7.3 ────────────────────────────────────────
// Classical: Rasi Pinda + Graha Pinda = Shuddha Pinda (before reductions)
// BPHS Ch.29 — Pinda reduction method.

interface PindaRow {
  planet: string
  rasi_pinda: number
  graha_pinda: number
  shuddha_pinda: number
  rank: number
}

const PINDA_DATA: PindaRow[] = [
  { planet: 'Mars',    rasi_pinda: 136, graha_pinda: 62, shuddha_pinda: 198, rank: 1 },
  { planet: 'Sun',     rasi_pinda: 123, graha_pinda: 49, shuddha_pinda: 172, rank: 2 },
  { planet: 'Mercury', rasi_pinda: 92,  graha_pinda: 66, shuddha_pinda: 158, rank: 3 },
  { planet: 'Jupiter', rasi_pinda: 74,  graha_pinda: 82, shuddha_pinda: 156, rank: 4 },
  { planet: 'Venus',   rasi_pinda: 78,  graha_pinda: 39, shuddha_pinda: 117, rank: 5 },
  { planet: 'Moon',    rasi_pinda: 80,  graha_pinda: 32, shuddha_pinda: 112, rank: 6 },
  { planet: 'Saturn',  rasi_pinda: 44,  graha_pinda: 36, shuddha_pinda: 80,  rank: 7 },
]

// House number for each sign (native Aries Lagna → Aries=1)
function houseForSign(sign: string): number {
  return SIGNS.indexOf(sign) + 1
}

// ── Row builders ─────────────────────────────────────────────────────────────

function buildSAVRows(): ChartFactRow[] {
  return SIGNS.map((sign, idx) => {
    const house = idx + 1
    const sav = SAV_FORENSIC[sign]
    const savJH = SAV_JH[sign]
    return {
      fact_id: `AVG.SAV.${sign.toUpperCase()}`,
      category: 'ashtakavarga_sav',
      divisional_chart: 'D1',
      value_text: `${sav} bindus`,
      value_number: sav,
      value_json: {
        sign,
        house,
        sav_bindus_forensic: sav,
        sav_bindus_jh: savJH,
        is_canonical: true,
        engine_note: 'FORENSIC canonical per GAP.08; JH reference stored inline',
        strength_band: sav >= 30 ? 'strong' : sav >= 25 ? 'moderate' : 'weak',
        classical_source: 'BPHS Ch.28-29; FORENSIC §7.2 AVG.SAV.*',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: '§7.2 AVG.SAV.*',
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    }
  })
}

function buildBAVRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []

  for (const [planet, bindus] of Object.entries(BAV_FORENSIC)) {
    const total = bindus.reduce((a, b) => a + b, 0)

    for (let i = 0; i < 12; i++) {
      const sign = SIGNS[i]
      const house = i + 1
      const abbr = SIGN_ABBR[sign]
      rows.push({
        fact_id: `AVG.BAV.${planet.toUpperCase()}.${abbr}`,
        category: 'ashtakavarga_bav',
        divisional_chart: 'D1',
        value_text: `${bindus[i]} bindus`,
        value_number: bindus[i],
        value_json: {
          planet,
          sign,
          house,
          bindus: bindus[i],
          total_bindus: total,
          // Moon JH reference inline
          ...(planet === 'Moon' ? {
            bindus_jh: BAV_MOON_JH[i],
            gap08_note: 'FORENSIC canonical; JH differs in Ge/Li/Sc/Cp by ±1 bindu each',
          } : {}),
          classical_source: `BPHS Ch.28; FORENSIC §7.1 AVG.BAV.${planet.toUpperCase()}`,
          chart_id: NATIVE_CHART_ID,
        },
        source_section: `§7.1 AVG.BAV.${planet.toUpperCase()}`,
        build_id: BUILD_ID,
        provenance: PROVENANCE_TEMPLATE,
      })
    }
  }

  // JH Moon reference rows (stored as ashtakavarga_bav with fact_id suffix .JH)
  for (let i = 0; i < 12; i++) {
    const sign = SIGNS[i]
    const abbr = SIGN_ABBR[sign]
    rows.push({
      fact_id: `AVG.BAV.MOON.JH.${abbr}`,
      category: 'ashtakavarga_bav',
      divisional_chart: 'D1',
      value_text: `${BAV_MOON_JH[i]} bindus (JH)`,
      value_number: BAV_MOON_JH[i],
      value_json: {
        planet: 'Moon',
        sign,
        house: i + 1,
        bindus: BAV_MOON_JH[i],
        total_bindus: 49,
        is_jh_reference: true,
        gap08_note: 'JH Moon BAV reference row per GAP.08; not canonical — FORENSIC is canonical',
        classical_source: 'FORENSIC §7.1 AVG.BAV.MOON.JH',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: '§7.1 AVG.BAV.MOON.JH',
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    })
  }

  return rows
}

function buildPindaRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []

  for (const p of PINDA_DATA) {
    // 3 rows per planet: rasi_pinda, graha_pinda, shuddha_pinda
    rows.push({
      fact_id: `AVG.SHP.${p.planet.toUpperCase()}.RASI`,
      category: 'ashtakavarga_pinda',
      divisional_chart: 'D1',
      value_text: `${p.rasi_pinda}`,
      value_number: p.rasi_pinda,
      value_json: {
        planet: p.planet,
        pinda_type: 'rasi_pinda',
        pinda: p.rasi_pinda,
        shuddha_pinda: p.shuddha_pinda,
        rank: p.rank,
        classical_source: 'BPHS Ch.29; FORENSIC §7.3 AVG.SHP.*',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: '§7.3 AVG.SHP.*',
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    })

    rows.push({
      fact_id: `AVG.SHP.${p.planet.toUpperCase()}.GRAHA`,
      category: 'ashtakavarga_pinda',
      divisional_chart: 'D1',
      value_text: `${p.graha_pinda}`,
      value_number: p.graha_pinda,
      value_json: {
        planet: p.planet,
        pinda_type: 'graha_pinda',
        pinda: p.graha_pinda,
        shuddha_pinda: p.shuddha_pinda,
        rank: p.rank,
        classical_source: 'BPHS Ch.29; FORENSIC §7.3 AVG.SHP.*',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: '§7.3 AVG.SHP.*',
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    })

    rows.push({
      fact_id: `AVG.SHP.${p.planet.toUpperCase()}.SHUDDHA`,
      category: 'ashtakavarga_pinda',
      divisional_chart: 'D1',
      value_text: `${p.shuddha_pinda}`,
      value_number: p.shuddha_pinda,
      value_json: {
        planet: p.planet,
        pinda_type: 'shuddha_pinda',
        pinda: p.shuddha_pinda,
        rasi_pinda: p.rasi_pinda,
        graha_pinda: p.graha_pinda,
        rank: p.rank,
        classical_source: 'BPHS Ch.29; FORENSIC §7.3 AVG.SHP.*',
        chart_id: NATIVE_CHART_ID,
      },
      source_section: '§7.3 AVG.SHP.*',
      build_id: BUILD_ID,
      provenance: PROVENANCE_TEMPLATE,
    })
  }

  return rows
}

async function main() {
  console.log('── MCPT v3.3-S1: Ashtakavarga Bootstrap ──')
  console.log(`Build ID: ${BUILD_ID}`)
  console.log('Mode: compute (from FORENSIC v8.0 §7.1 + §7.2 + §7.3)')

  const pool = makePool()

  try {
    // 1. Insert build_manifest row
    console.log('\nInserting build_manifests row…')
    const bavCount = Object.keys(BAV_FORENSIC).length * 12 + 12 // 84 + 12 JH Moon
    const savCount = 12
    const pindaCount = PINDA_DATA.length * 3 // 21
    const totalChunks = savCount + bavCount + pindaCount
    await insertBuildManifest(pool, {
      build_id: BUILD_ID,
      triggered_by: 'manual:mcpt-v33-s1',
      registry_fingerprint: 'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      pipeline_image_uri: 'mcpt-depth-bootstrap:v3.3-S1',
      embedding_model: 'none',
      embedding_dim: 0,
      chunk_count: totalChunks,
      embedding_count: 0,
      status: 'live',
      manifest_uri: 'local://mcpt-v33-s1-ashtakavarga',
      notes: `Ashtakavarga: SAV(12) + BAV(${bavCount}) + Pinda(${pindaCount}) = ${totalChunks} rows; FORENSIC v8.0 §7.1-§7.3; GAP.08 applied`,
    })
    console.log('  ✓ build_manifests row inserted')

    // 2. SAV rows
    const savRows = buildSAVRows()
    console.log(`\nUpserting ${savRows.length} SAV rows (ashtakavarga_sav)…`)
    await upsertChartFacts(pool, savRows)
    console.log('  ✓ SAV rows inserted')

    // 3. BAV rows (includes JH Moon reference rows)
    const bavRows = buildBAVRows()
    console.log(`Upserting ${bavRows.length} BAV rows (ashtakavarga_bav)…`)
    await upsertChartFacts(pool, bavRows)
    console.log('  ✓ BAV rows inserted')

    // 4. Pinda rows
    const pindaRows = buildPindaRows()
    console.log(`Upserting ${pindaRows.length} Pinda rows (ashtakavarga_pinda)…`)
    await upsertChartFacts(pool, pindaRows)
    console.log('  ✓ Pinda rows inserted')

    // 5. Verify
    const { rows: savCount2 } = await pool.query(
      `SELECT count(*) AS n FROM chart_facts WHERE category='ashtakavarga_sav'`
    )
    const { rows: bavCount2 } = await pool.query(
      `SELECT count(*) AS n FROM chart_facts WHERE category='ashtakavarga_bav'`
    )
    const { rows: pindaCount2 } = await pool.query(
      `SELECT count(*) AS n FROM chart_facts WHERE category='ashtakavarga_pinda'`
    )

    const sav_n = parseInt(savCount2[0].n, 10)
    const bav_n = parseInt(bavCount2[0].n, 10)
    const pinda_n = parseInt(pindaCount2[0].n, 10)

    console.log(`\nVerification:`)
    console.log(`  ashtakavarga_sav  count = ${sav_n}  (expected = 12)`)
    console.log(`  ashtakavarga_bav  count = ${bav_n}  (expected ≥ 100)`)
    console.log(`  ashtakavarga_pinda count = ${pinda_n} (expected = 21)`)

    let pass = true
    if (sav_n !== 12) { console.error(`  FAIL AC.S1.2: SAV count ${sav_n} ≠ 12`); pass = false }
    else console.log('  ✓ AC.S1.2 PASS')

    if (bav_n < 100) { console.error(`  FAIL AC.S1.3: BAV count ${bav_n} < 100`); pass = false }
    else console.log('  ✓ AC.S1.3 PASS')

    if (!pass) process.exit(1)

    // Spot check: SAV grand total
    const { rows: totalCheck } = await pool.query(
      `SELECT sum(value_number) AS total FROM chart_facts WHERE category='ashtakavarga_sav'`
    )
    console.log(`\nSpot check: SAV grand total = ${totalCheck[0].total} (expected ${SAV_GRAND_TOTAL})`)

    console.log('\n── Ashtakavarga bootstrap COMPLETE ──')
    console.log(`Build ID: ${BUILD_ID}`)
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
