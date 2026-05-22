/**
 * bootstrap_chart_facts_shadbala.ts
 *
 * MCPT v3.3-S1 — Shadbala ingestion (--mode=compute)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §6.1 (component breakdown)
 *         and §6.2 (totals + ranking, DUAL-ENGINE).
 *
 * Inserts 63 rows (9 planets × 7 measures) into chart_facts
 * with category='shadbala'. Saturn entry spot-check:
 *   Saturn.Ucha = 59.18 virupas (FORENSIC §6.1 SBL.UCHA col Saturn)
 *   Saturn.Total = 447.98 virupas (FORENSIC §6.2 SBL.TOTAL.SATURN)
 *   → JH Total = 8.79 rupas (rank #1; authoritative for ranking per GAP.07)
 *
 * Note on Rahu/Ketu: Classical Shadbala in Brihat Parashara Hora Shastra
 * (BPHS Ch.27) covers only the seven classical planets (Sun through Saturn).
 * Rahu and Ketu do not have individual Shadbala in the classical formulation.
 * Their rows are inserted as zero-valued placeholders with a note in value_json.
 * Total rows = 7 classical planets × 7 measures + 2 nodes × 7 = 63.
 *
 * Usage:
 *   cd platform && npx tsx scripts/bootstrap/bootstrap_chart_facts_shadbala.ts
 *
 * Prerequisites:
 *   DATABASE_URL in environment (via .env.local or direct export)
 *   The chart_facts and build_manifests tables must exist (migration 014).
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { makePool, upsertChartFacts, insertBuildManifest } from './lib/chart_facts_ingester'
import type { ChartFactRow } from './lib/chart_facts_ingester'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── Build ID ────────────────────────────────────────────────────────────────

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const BUILD_ID = `mcpt-v33-s1-shadbala-${TIMESTAMP}`
const NATIVE_CHART_ID = process.env.NATIVE_CHART_ID ?? 'abhisek'

// ── Provenance ──────────────────────────────────────────────────────────────

const PROVENANCE_TEMPLATE = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  extracted_at: new Date().toISOString(),
  extraction_method: 'manual_extraction_from_forensic_v8_0',
}

// ── Shadbala Data from FORENSIC v8.0 §6.1 + §6.2 ─────────────────────────
//
// Classical reference: Brihat Parashara Hora Shastra (BPHS) Chapter 27
//   — Shadbala Phala Adhyaya. Six sources of strength:
//   1. Sthana Bala (positional): Uccha + Saptavargaja + Ojayugmarasyamsa + Kendra + Drekkana
//   2. Dig Bala (directional)
//   3. Kala Bala (temporal): Nathonnatha + Paksha + Thribhaga + Abda + Masa + Vara + Hora + Ayana + Yuddha
//   4. Chesta Bala (motional)
//   5. Naisargika Bala (natural/fixed)
//   6. Drik Bala (aspectual)
//
// Values extracted directly from FORENSIC §6.1 table (engine: FORENSIC).
// Totals from §6.2. JH rupas from §6.2 (authoritative for ranking per GAP.07).

interface PlanetShadbala {
  planet: string
  sthana_ucha: number       // Uccha Bala (exaltation proximity)
  sthana_sapt: number       // Saptavargaja Bala (septenary)
  sthana_ojay: number       // Ojayugmarasyamsa Bala (odd/even sign)
  sthana_kend: number       // Kendra Bala (angular)
  sthana_drek: number       // Drekkana Bala
  sthana_total: number      // Total Sthana Bala
  dig_total: number         // Total Dig Bala
  kala_nath: number         // Nathonnatha Bala (day/night)
  kala_paksha: number       // Paksha Bala (lunar phase)
  kala_tribh: number        // Thribhaga Bala (day-third)
  kala_abda: number         // Abda Bala (yearly lord)
  kala_masa: number         // Masa Bala (monthly lord)
  kala_vara: number         // Vara Bala (day lord)
  kala_hora: number         // Hora Bala (hour lord)
  kala_ayana: number        // Ayana Bala (solstice-based)
  kala_yuddha: number       // Yuddha Bala (planetary war)
  kala_total: number        // Total Kala Bala
  chesta_total: number      // Total Chesta Bala (motional)
  naisarg_total: number     // Total Naisargika Bala (fixed natural)
  drik_total: number        // Total Drik Bala (aspectual; can be negative)
  total_virupas: number     // Grand total in virupas (FORENSIC engine)
  total_rupas_forensic: number  // Total in rupas (virupas / 60)
  total_rupas_jh: number    // JH engine rupas (authoritative for ranking)
  jh_rank: number           // JH ranking (1=strongest)
  min_required_rupas: number // Minimum required Shadbala
  classical_source: string  // BPHS citation
  is_node: boolean          // true for Rahu/Ketu (no classical Shadbala)
}

// Data extracted from FORENSIC §6.1 and §6.2
// Columns: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
const SHADBALA_DATA: PlanetShadbala[] = [
  {
    planet: 'Sun',
    sthana_ucha: 33.99, sthana_sapt: 97.50, sthana_ojay: 0.00, sthana_kend: 60.00, sthana_drek: 1.00,
    sthana_total: 191.49,
    dig_total: 53.67,
    kala_nath: 53.53, kala_paksha: 48.30, kala_tribh: 60.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 45.00, kala_hora: 0.00, kala_ayana: 18.74, kala_yuddha: 0.00,
    kala_total: 225.58,
    chesta_total: 15.20,
    naisarg_total: 60.00,
    drik_total: -35.08,
    total_virupas: 510.85,
    total_rupas_forensic: 8.51,
    total_rupas_jh: 8.18,
    jh_rank: 2,
    min_required_rupas: 5.00,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.SUN; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Moon',
    sthana_ucha: 38.02, sthana_sapt: 123.75, sthana_ojay: 0.00, sthana_kend: 30.00, sthana_drek: 1.00,
    sthana_total: 206.77,
    dig_total: 18.02,
    kala_nath: 6.47, kala_paksha: 48.30, kala_tribh: 0.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 0.00, kala_hora: 60.00, kala_ayana: 34.69, kala_yuddha: 0.00,
    kala_total: 149.46,
    chesta_total: 11.70,
    naisarg_total: 51.42,
    drik_total: -1.85,
    total_virupas: 435.51,
    total_rupas_forensic: 7.26,
    total_rupas_jh: 6.44,
    jh_rank: 4,
    min_required_rupas: 6.00,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.MOON; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Mars',
    sthana_ucha: 26.84, sthana_sapt: 75.00, sthana_ojay: 15.00, sthana_kend: 60.00, sthana_drek: 1.00,
    sthana_total: 176.84,
    dig_total: 35.18,
    kala_nath: 6.47, kala_paksha: 48.30, kala_tribh: 0.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 0.00, kala_hora: 0.00, kala_ayana: 10.30, kala_yuddha: 0.00,
    kala_total: 65.08,
    chesta_total: 36.17,
    naisarg_total: 17.16,
    drik_total: -14.20,
    total_virupas: 316.23,
    total_rupas_forensic: 5.27,
    total_rupas_jh: 5.34,
    jh_rank: 6,
    min_required_rupas: 5.00,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.MARS; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Mercury',
    sthana_ucha: 24.72, sthana_sapt: 97.50, sthana_ojay: 0.00, sthana_kend: 60.00, sthana_drek: 1.00,
    sthana_total: 182.22,
    dig_total: 26.15,
    kala_nath: 60.00, kala_paksha: 48.30, kala_tribh: 0.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 0.00, kala_hora: 0.00, kala_ayana: 56.94, kala_yuddha: 0.00,
    kala_total: 165.25,
    chesta_total: 17.83,
    naisarg_total: 25.74,
    drik_total: -23.92,
    total_virupas: 393.26,
    total_rupas_forensic: 6.55,
    total_rupas_jh: 6.09,
    jh_rank: 5,
    min_required_rupas: 7.00,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.MERCURY; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Jupiter',
    sthana_ucha: 8.40, sthana_sapt: 165.00, sthana_ojay: 30.00, sthana_kend: 15.00, sthana_drek: 1.00,
    sthana_total: 233.40,
    dig_total: 19.14,
    kala_nath: 53.53, kala_paksha: 11.70, kala_tribh: 60.00, kala_abda: 15.00, kala_masa: 30.00,
    kala_vara: 0.00, kala_hora: 0.00, kala_ayana: 0.25, kala_yuddha: 0.00,
    kala_total: 170.47,
    chesta_total: 13.79,
    naisarg_total: 34.26,
    drik_total: -6.98,
    total_virupas: 464.07,
    total_rupas_forensic: 7.73,
    total_rupas_jh: 7.68,
    jh_rank: 3,
    min_required_rupas: 6.50,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.JUPITER; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Venus',
    sthana_ucha: 27.39, sthana_sapt: 93.75, sthana_ojay: 15.00, sthana_kend: 15.00, sthana_drek: 1.00,
    sthana_total: 151.14,
    dig_total: 4.60,
    kala_nath: 53.53, kala_paksha: 11.70, kala_tribh: 0.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 0.00, kala_hora: 0.00, kala_ayana: 0.92, kala_yuddha: 0.00,
    kala_total: 66.15,
    chesta_total: 19.51,
    naisarg_total: 42.84,
    drik_total: -8.24,
    total_virupas: 276.01,
    total_rupas_forensic: 4.60,
    total_rupas_jh: 4.80,
    jh_rank: 7,
    min_required_rupas: 5.50,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.VENUS; JH rank per GAP.07',
    is_node: false,
  },
  {
    planet: 'Saturn',
    sthana_ucha: 59.18, sthana_sapt: 108.75, sthana_ojay: 30.00, sthana_kend: 60.00, sthana_drek: 1.00,
    sthana_total: 257.93,
    dig_total: 56.65,
    kala_nath: 6.47, kala_paksha: 48.30, kala_tribh: 0.00, kala_abda: 0.00, kala_masa: 0.00,
    kala_vara: 0.00, kala_hora: 0.00, kala_ayana: 51.23, kala_yuddha: 0.00,
    kala_total: 106.01,
    chesta_total: 31.63,
    naisarg_total: 8.58,
    drik_total: -12.81,
    total_virupas: 447.98,
    total_rupas_forensic: 7.47,
    total_rupas_jh: 8.79,
    jh_rank: 1,
    min_required_rupas: 5.00,
    classical_source: 'BPHS Ch.27; FORENSIC §6.1 SBL.TOTAL.SATURN; JH rank #1 per GAP.07; Uccha 59.18 = near-max exaltation (Libra 20° exact exaltation point)',
    is_node: false,
  },
  // Rahu and Ketu: no classical Shadbala in BPHS Ch.27 — insert zero placeholders
  {
    planet: 'Rahu',
    sthana_ucha: 0, sthana_sapt: 0, sthana_ojay: 0, sthana_kend: 0, sthana_drek: 0,
    sthana_total: 0, dig_total: 0,
    kala_nath: 0, kala_paksha: 0, kala_tribh: 0, kala_abda: 0, kala_masa: 0,
    kala_vara: 0, kala_hora: 0, kala_ayana: 0, kala_yuddha: 0,
    kala_total: 0, chesta_total: 0, naisarg_total: 0, drik_total: 0,
    total_virupas: 0, total_rupas_forensic: 0, total_rupas_jh: 0,
    jh_rank: 0, min_required_rupas: 0,
    classical_source: 'BPHS Ch.27 does not include Rahu in Shadbala; placeholder row only',
    is_node: true,
  },
  {
    planet: 'Ketu',
    sthana_ucha: 0, sthana_sapt: 0, sthana_ojay: 0, sthana_kend: 0, sthana_drek: 0,
    sthana_total: 0, dig_total: 0,
    kala_nath: 0, kala_paksha: 0, kala_tribh: 0, kala_abda: 0, kala_masa: 0,
    kala_vara: 0, kala_hora: 0, kala_ayana: 0, kala_yuddha: 0,
    kala_total: 0, chesta_total: 0, naisarg_total: 0, drik_total: 0,
    total_virupas: 0, total_rupas_forensic: 0, total_rupas_jh: 0,
    jh_rank: 0, min_required_rupas: 0,
    classical_source: 'BPHS Ch.27 does not include Ketu in Shadbala; placeholder row only',
    is_node: true,
  },
]

// Component label map for sub-row generation
const MEASURES = [
  { key: 'Sthana', label: 'Total Sthana Bala', field: 'sthana_total' as const, source: '§6.1 SBL.STHANA.TOTAL' },
  { key: 'Dig',    label: 'Total Dig Bala',    field: 'dig_total' as const,    source: '§6.1 SBL.DIG.TOTAL' },
  { key: 'Kala',   label: 'Total Kala Bala',   field: 'kala_total' as const,   source: '§6.1 SBL.KALA.TOTAL' },
  { key: 'Chesta', label: 'Total Chesta Bala', field: 'chesta_total' as const, source: '§6.1 SBL.CHESTA.TOTAL' },
  { key: 'Naisargika', label: 'Total Naisargika Bala', field: 'naisarg_total' as const, source: '§6.1 SBL.NAISARG.TOTAL' },
  { key: 'Drik',   label: 'Total Drik Bala',   field: 'drik_total' as const,   source: '§6.1 SBL.DRIK.TOTAL' },
  { key: 'Total',  label: 'Grand Total Shadbala', field: 'total_virupas' as const, source: '§6.2 SBL.TOTAL.*' },
]

function buildRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []

  for (const p of SHADBALA_DATA) {
    for (const m of MEASURES) {
      const factId = `SBL.${p.planet.toUpperCase()}.${m.key.toUpperCase()}`
      const value = p[m.field] as number

      rows.push({
        fact_id: factId,
        category: 'shadbala',
        divisional_chart: 'D1',
        value_text: `${value} virupas`,
        value_number: value,
        value_json: {
          planet: p.planet,
          measure: m.key,
          measure_label: m.label,
          value_virupas: value,
          unit: 'virupa',
          is_node: p.is_node,
          ...(m.key === 'Total' ? {
            forensic_rupas: p.total_rupas_forensic,
            jh_rupas: p.total_rupas_jh,
            jh_rank: p.jh_rank,
            min_required_rupas: p.min_required_rupas,
            above_minimum: p.jh_rank > 0 && p.total_rupas_jh >= p.min_required_rupas,
          } : {}),
          // Sthana sub-components for the Sthana row
          ...(m.key === 'Sthana' && !p.is_node ? {
            ucha_bala: p.sthana_ucha,
            saptavargaja_bala: p.sthana_sapt,
            ojayugmarasyamsa_bala: p.sthana_ojay,
            kendra_bala: p.sthana_kend,
            drekkana_bala: p.sthana_drek,
          } : {}),
          // Kala sub-components for the Kala row
          ...(m.key === 'Kala' && !p.is_node ? {
            nathonnatha_bala: p.kala_nath,
            paksha_bala: p.kala_paksha,
            thribhaga_bala: p.kala_tribh,
            abda_bala: p.kala_abda,
            masa_bala: p.kala_masa,
            vara_bala: p.kala_vara,
            hora_bala: p.kala_hora,
            ayana_bala: p.kala_ayana,
            yuddha_bala: p.kala_yuddha,
          } : {}),
          classical_source: p.classical_source,
          chart_id: NATIVE_CHART_ID,
        },
        source_section: m.source,
        build_id: BUILD_ID,
        provenance: PROVENANCE_TEMPLATE,
      })
    }
  }

  return rows
}

async function main() {
  console.log('── MCPT v3.3-S1: Shadbala Bootstrap ──')
  console.log(`Build ID: ${BUILD_ID}`)
  console.log(`Mode: compute (from FORENSIC v8.0 §6.1 + §6.2)`)

  const pool = makePool()

  try {
    // 1. Register build_manifest row FIRST (chart_facts.build_id FK requires it)
    console.log('\nInserting build_manifests row…')
    await insertBuildManifest(pool, {
      build_id: BUILD_ID,
      triggered_by: 'manual:mcpt-v33-s1',
      registry_fingerprint: 'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      pipeline_image_uri: 'mcpt-depth-bootstrap:v3.3-S1',
      embedding_model: 'none',
      embedding_dim: 0,
      chunk_count: 63,
      embedding_count: 0,
      status: 'live',
      manifest_uri: 'local://mcpt-v33-s1-shadbala',
      notes: 'Shadbala ingestion from FORENSIC v8.0 §6.1+§6.2; mode=compute; 9 planets × 7 measures = 63 rows',
    })
    console.log('  ✓ build_manifests row inserted')

    // 2. Build and upsert all rows
    const rows = buildRows()
    console.log(`\nUpserting ${rows.length} shadbala rows…`)
    const inserted = await upsertChartFacts(pool, rows)
    console.log(`  ✓ ${inserted} rows upserted`)

    // 3. Verify count
    const { rows: countRows } = await pool.query(
      `SELECT count(*) AS n FROM chart_facts WHERE category='shadbala'`
    )
    const count = parseInt(countRows[0].n, 10)
    console.log(`\nVerification: SELECT count(*) FROM chart_facts WHERE category='shadbala' → ${count}`)

    if (count < 63) {
      console.error(`FAIL: expected ≥ 63, got ${count}`)
      process.exit(1)
    }
    console.log('  ✓ AC.S1.1 PASS')

    // 4. Spot-check Saturn.Total
    const { rows: saturnRows } = await pool.query(
      `SELECT value_number, value_json FROM chart_facts WHERE fact_id='SBL.SATURN.TOTAL'`
    )
    if (saturnRows.length > 0) {
      console.log(`\nSpot check Saturn.Total:`)
      console.log(`  value_number = ${saturnRows[0].value_number} virupas`)
      const jh = saturnRows[0].value_json?.jh_rupas
      const rank = saturnRows[0].value_json?.jh_rank
      console.log(`  JH rupas = ${jh} (rank #${rank})`)
      console.log(`  Expected: 447.98 virupas, 8.79 JH rupas, rank #1`)
    }

    console.log('\n── Shadbala bootstrap COMPLETE ──')
    console.log(`Build ID: ${BUILD_ID}`)
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
