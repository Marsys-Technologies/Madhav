#!/usr/bin/env npx tsx
/**
 * bootstrap_chart_facts_varshphal.ts — Ingest Tajaka Varshphal into chart_facts (v3.3-S3)
 *
 * Source: Tajaka Neelakanthi (classical_texts/TAJAKA) for deterministic muntha_sign rule.
 *         FORENSIC_ASTROLOGICAL_DATA_v8_0.md — Natal Lagna = Cancer (established fact).
 *
 * Produces: 18 rows × 87 years (1984–2070) = 1566 rows in chart_facts WHERE category='varshphal'
 *
 * B.10 DISCIPLINE:
 *   COMPUTED deterministically (Tajaka rule): muntha_sign, muntha_house, varsha_number
 *   [EXTERNAL_COMPUTATION_REQUIRED]: year_lord, annual_lagna, sahams (12 types), pancha_vargiya_bala
 *     → Reason: these require the exact weekday of the solar return and full annual chart positions,
 *       which require Jyotish software (Jagannatha Hora, Parashara's Light, Shri Jyoti Star).
 *
 * Rows per year (18 total):
 *   1.  <year>.muntha              — muntha sign (computed, deterministic)
 *   2.  <year>.muntha_house        — muntha house relative to Cancer natal lagna (computed)
 *   3.  <year>.varsha_number       — ordinal varsha number since birth (computed)
 *   4.  <year>.year_lord           — varshapati / year-lord [EXTERNAL_COMPUTATION_REQUIRED]
 *   5.  <year>.annual_lagna        — annual chart lagna [EXTERNAL_COMPUTATION_REQUIRED]
 *   6.  <year>.saham.punya         — Punya saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   7.  <year>.saham.vidya         — Vidya saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   8.  <year>.saham.yasas         — Yasas saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   9.  <year>.saham.mitra         — Mitra saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   10. <year>.saham.mahatmya      — Mahatmya saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   11. <year>.saham.aasha         — Aasha saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   12. <year>.saham.sameera       — Sameera saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   13. <year>.saham.karma         — Karma saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   14. <year>.saham.kali          — Kali saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   15. <year>.saham.badhaka       — Badhaka saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   16. <year>.saham.kama          — Kama saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   17. <year>.saham.shree         — Shree saham [EXTERNAL_COMPUTATION_REQUIRED]
 *   18. <year>.pancha_vargiya_bala — Pancha-vargiya bala [EXTERNAL_COMPUTATION_REQUIRED]
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx scripts/bootstrap/bootstrap_chart_facts_varshphal.ts [--dry-run]
 */

import { Pool } from 'pg'

const DATABASE_URL = process.env.DATABASE_URL_PROD
  ?? process.env.DATABASE_URL
  ?? 'postgresql://amjis_app@127.0.0.1:5433/amjis'

const BUILD_ID = 'mcpt-v33-s3-varshphal-20260522'
const pool = new Pool({ connectionString: DATABASE_URL })

// ── Tajaka computation constants ──────────────────────────────────────────────

/**
 * All 12 zodiac signs in order (0 = Aries, 1 = Taurus, ..., 11 = Pisces).
 * This ordering is canonical for Jyotish (same as Parashara + Tajaka convention).
 */
export const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

export type Sign = typeof SIGNS[number]

/** Native's birth year (Gregorian). */
export const BIRTH_YEAR = 1984

/**
 * Native's natal Lagna sign = Cancer.
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md — Lagna = Cancer 4th sign (0-indexed = 3).
 */
export const NATAL_LAGNA_INDEX = 3 // Cancer

/** Year range to ingest: Varsha 1 (1984) through Varsha 87 (2070). */
export const YEAR_START = 1984
export const YEAR_END = 2070

// ── Tajaka muntha computation (deterministic) ─────────────────────────────────

/**
 * Compute the muntha sign for a given Gregorian year.
 *
 * Tajaka rule (Neelakanthi ch. 2): the muntha advances 1 sign per solar year,
 * starting at the natal Lagna sign in the first varsha (birth year).
 *
 * Formula: muntha_sign_index = (NATAL_LAGNA_INDEX + (varshaNumber - 1)) mod 12
 * where varshaNumber = year - BIRTH_YEAR + 1
 *
 * Verification:
 *   1984 (Varsha 1) → index 3 + 0 = 3 → Cancer ✓
 *   1985 (Varsha 2) → index 3 + 1 = 4 → Leo ✓
 *   1986 (Varsha 3) → index 3 + 2 = 5 → Virgo ✓
 *   1996 (Varsha 13) → index 3 + 12 = 15 mod 12 = 3 → Cancer (12-year cycle) ✓
 *   2070 (Varsha 87) → index 3 + 86 = 89 mod 12 = 5 → Virgo ✓
 */
export function getMunthaSign(year: number): Sign {
  const varshaNumber = year - BIRTH_YEAR + 1
  const signIndex = (NATAL_LAGNA_INDEX + (varshaNumber - 1)) % 12
  return SIGNS[signIndex]
}

/**
 * Compute the muntha house for a given year.
 *
 * The muntha house is the house number counting from the natal Lagna.
 * Since natal Lagna = Cancer (sign 3 = house 1), the muntha house equals:
 *   munthaHouse = ((munthaSignIndex - NATAL_LAGNA_INDEX) + 12) % 12 + 1
 *
 * Simplifies to:
 *   munthaHouse = (varshaNumber - 1) % 12 + 1
 *
 * Verification:
 *   1984 (Varsha 1): muntha=Cancer=H1 → house 1 ✓
 *   1985 (Varsha 2): muntha=Leo=H2 → house 2 ✓
 *   1996 (Varsha 13): muntha=Cancer=H1 → house 1 ✓
 */
export function getMunthaHouse(year: number): number {
  const varshaNumber = year - BIRTH_YEAR + 1
  return (varshaNumber - 1) % 12 + 1
}

/**
 * Compute the varsha (annual) number for a given year.
 * Varsha 1 = birth year (1984).
 */
export function getVarshaNumber(year: number): number {
  return year - BIRTH_YEAR + 1
}

// ── Row builders ──────────────────────────────────────────────────────────────

interface ChartFactRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
  build_id: string
  provenance: {
    source_uri: string
    source_version: string
    source_canonical_id: string
    extracted_at: string
    extraction_method: string
  }
}

const EXTRACTED_AT = new Date().toISOString()

function provenanceTajaka(): ChartFactRow['provenance'] {
  return {
    source_uri: 'classical_texts/TAJAKA',
    source_version: 'TAJAKA_NEELAKANTHI_v1',
    source_canonical_id: 'TAJAKA_NEELAKANTHI',
    extracted_at: EXTRACTED_AT,
    extraction_method: 'deterministic_formula',
  }
}

function provenanceExternal(subkey: string): ChartFactRow['provenance'] {
  return {
    source_uri: 'EXTERNAL_COMPUTATION_REQUIRED',
    source_version: 'n/a',
    source_canonical_id: 'FORENSIC',
    extracted_at: EXTRACTED_AT,
    extraction_method: `B10_placeholder:${subkey}`,
  }
}

function buildVarshphalRows(year: number): ChartFactRow[] {
  const munthaSign = getMunthaSign(year)
  const munthaHouse = getMunthaHouse(year)
  const varshaNumber = getVarshaNumber(year)

  const base = {
    category: 'varshphal',
    divisional_chart: 'D1',
    build_id: BUILD_ID,
  }

  const rows: ChartFactRow[] = [
    // 1. Muntha sign — COMPUTED (deterministic Tajaka rule)
    {
      ...base,
      fact_id: `VPH.${year}.MUNTHA`,
      value_text: munthaSign,
      value_number: null,
      value_json: null,
      source_section: `TAJAKA_NEELAKANTHI.ch2.muntha_rule`,
      provenance: provenanceTajaka(),
    },
    // 2. Muntha house — COMPUTED
    {
      ...base,
      fact_id: `VPH.${year}.MUNTHA_HOUSE`,
      value_text: null,
      value_number: munthaHouse,
      value_json: { muntha_sign: munthaSign, muntha_house: munthaHouse, from_lagna: 'Cancer' },
      source_section: `TAJAKA_NEELAKANTHI.ch2.muntha_house`,
      provenance: provenanceTajaka(),
    },
    // 3. Varsha number — COMPUTED
    {
      ...base,
      fact_id: `VPH.${year}.VARSHA_NUMBER`,
      value_text: null,
      value_number: varshaNumber,
      value_json: null,
      source_section: `TAJAKA_NEELAKANTHI.general.varsha_number`,
      provenance: provenanceTajaka(),
    },
    // 4. Year-lord (Varshapati) — [EXTERNAL_COMPUTATION_REQUIRED]
    //    Needs: weekday of solar return for this year → determines varshapati per Tajaka rules.
    //    Software: Jagannatha Hora / Parashara's Light / Shri Jyoti Star — chart for solar return date.
    {
      ...base,
      fact_id: `VPH.${year}.YEAR_LORD`,
      value_text: '[EXTERNAL_COMPUTATION_REQUIRED]',
      value_number: null,
      value_json: {
        requires: 'varshapati_calculation',
        method: 'weekday_of_solar_return',
        software: 'Jagannatha_Hora_or_equivalent',
        year,
      },
      source_section: `TAJAKA_NEELAKANTHI.ch3.varshapati`,
      provenance: provenanceExternal(`${year}.year_lord`),
    },
    // 5. Annual Lagna — [EXTERNAL_COMPUTATION_REQUIRED]
    //    Needs: exact time of solar return → compute lagna at that moment.
    {
      ...base,
      fact_id: `VPH.${year}.ANNUAL_LAGNA`,
      value_text: '[EXTERNAL_COMPUTATION_REQUIRED]',
      value_number: null,
      value_json: {
        requires: 'annual_lagna_calculation',
        method: 'lagna_at_solar_return_moment',
        software: 'Jagannatha_Hora_or_equivalent',
        year,
      },
      source_section: `TAJAKA_NEELAKANTHI.ch2.annual_lagna`,
      provenance: provenanceExternal(`${year}.annual_lagna`),
    },
  ]

  // 6–17. Sahams — [EXTERNAL_COMPUTATION_REQUIRED]
  //   Each saham = (Lord + Planet - House) mod 12 in the annual chart, or per specific Tajaka formulae.
  //   All require full annual chart planetary positions (needs solar return calculation).
  const sahams = [
    { key: 'PUNYA',    ref: 'ch8.saham_punya',    desc: 'fortune and merit saham' },
    { key: 'VIDYA',    ref: 'ch8.saham_vidya',    desc: 'learning and education saham' },
    { key: 'YASAS',    ref: 'ch8.saham_yasas',    desc: 'fame and reputation saham' },
    { key: 'MITRA',    ref: 'ch8.saham_mitra',    desc: 'friends and allies saham' },
    { key: 'MAHATMYA', ref: 'ch8.saham_mahatmya', desc: 'greatness and honour saham' },
    { key: 'AASHA',    ref: 'ch8.saham_aasha',    desc: 'hope and desire saham' },
    { key: 'SAMEERA',  ref: 'ch8.saham_sameera',  desc: 'wind/air saham (travel, change)' },
    { key: 'KARMA',    ref: 'ch8.saham_karma',    desc: 'action and profession saham' },
    { key: 'KALI',     ref: 'ch8.saham_kali',     desc: 'strife and discord saham' },
    { key: 'BADHAKA',  ref: 'ch8.saham_badhaka',  desc: 'obstructions and badhaka saham' },
    { key: 'KAMA',     ref: 'ch8.saham_kama',     desc: 'desires and passions saham' },
    { key: 'SHREE',    ref: 'ch8.saham_shree',    desc: 'prosperity and lakshmi saham' },
  ]

  for (const saham of sahams) {
    rows.push({
      ...base,
      fact_id: `VPH.${year}.SAHAM.${saham.key}`,
      value_text: '[EXTERNAL_COMPUTATION_REQUIRED]',
      value_number: null,
      value_json: {
        requires: 'saham_calculation',
        method: 'annual_chart_planetary_positions',
        saham_name: saham.key.toLowerCase(),
        description: saham.desc,
        software: 'Jagannatha_Hora_or_equivalent',
        year,
      },
      source_section: `TAJAKA_NEELAKANTHI.${saham.ref}`,
      provenance: provenanceExternal(`${year}.saham.${saham.key.toLowerCase()}`),
    })
  }

  // 18. Pancha-vargiya bala — [EXTERNAL_COMPUTATION_REQUIRED]
  //   Strength score from 5 divisional charts in annual chart. Requires full annual chart.
  rows.push({
    ...base,
    fact_id: `VPH.${year}.PANCHA_VARGIYA_BALA`,
    value_text: '[EXTERNAL_COMPUTATION_REQUIRED]',
    value_number: null,
    value_json: {
      requires: 'pancha_vargiya_bala_calculation',
      method: 'five_divisional_charts_of_annual',
      divisions: ['D1', 'D2', 'D3', 'D9', 'D12'],
      software: 'Jagannatha_Hora_or_equivalent',
      year,
    },
    source_section: `TAJAKA_NEELAKANTHI.ch5.pancha_vargiya_bala`,
    provenance: provenanceExternal(`${year}.pancha_vargiya_bala`),
  })

  return rows
}

// ── Build manifest ────────────────────────────────────────────────────────────

async function ensureBuildManifest(dryRun: boolean): Promise<void> {
  const totalRows = (YEAR_END - YEAR_START + 1) * 18 // 87 × 18 = 1566
  if (dryRun) {
    console.log(`[dry-run] WOULD upsert build_manifests: ${BUILD_ID} (${totalRows} rows planned)`)
    return
  }
  await pool.query(
    `INSERT INTO build_manifests
       (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
        embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri, notes)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
     ON CONFLICT (build_id) DO NOTHING`,
    [
      BUILD_ID,
      'mcpt-v33-s3-direct-ingest',
      'TAJAKA_NEELAKANTHI_deterministic+B10_placeholders',
      'n/a:direct-ingest',
      'n/a',
      0,
      0,
      0,
      'live',
      'gs://madhav-marsys-build-artifacts/mcpt-v33-s3/manifest-stub.json',
      `MCPT v3.3-S3: Varshphal ingestion 1984-2070 (${totalRows} rows). ` +
      'muntha_sign computed from Tajaka rule; year_lord/annual_lagna/sahams/pancha_vargiya_bala ' +
      'marked [EXTERNAL_COMPUTATION_REQUIRED] per B.10 discipline.',
    ]
  )
  console.log(`[manifest] ensured build_manifests entry: ${BUILD_ID}`)
}

// ── Upsert helper ─────────────────────────────────────────────────────────────

async function upsertRows(rows: ChartFactRow[], dryRun: boolean): Promise<number> {
  if (dryRun) {
    console.log(`[dry-run] WOULD upsert ${rows.length} chart_facts rows`)
    return rows.length
  }

  let inserted = 0
  for (const row of rows) {
    await pool.query(
      `INSERT INTO chart_facts
         (fact_id, category, divisional_chart, value_text, value_number, value_json,
          source_section, build_id, provenance, is_stale)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false)
       ON CONFLICT (fact_id) DO UPDATE SET
         category        = EXCLUDED.category,
         divisional_chart = EXCLUDED.divisional_chart,
         value_text      = EXCLUDED.value_text,
         value_number    = EXCLUDED.value_number,
         value_json      = EXCLUDED.value_json,
         source_section  = EXCLUDED.source_section,
         build_id        = EXCLUDED.build_id,
         provenance      = EXCLUDED.provenance,
         is_stale        = false`,
      [
        row.fact_id,
        row.category,
        row.divisional_chart,
        row.value_text,
        row.value_number,
        row.value_json !== null ? JSON.stringify(row.value_json) : null,
        row.source_section,
        row.build_id,
        JSON.stringify(row.provenance),
      ]
    )
    inserted++
  }
  return inserted
}

// ── Exported test surface ─────────────────────────────────────────────────────

/**
 * Build all varshphal rows for years YEAR_START..YEAR_END.
 * Exported for unit testing without DB dependency.
 */
export function buildAllRows(): ChartFactRow[] {
  const allRows: ChartFactRow[] = []
  for (let year = YEAR_START; year <= YEAR_END; year++) {
    allRows.push(...buildVarshphalRows(year))
  }
  return allRows
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const dryRun = process.argv.includes('--dry-run')
  if (dryRun) console.log('[dry-run] Mode active — no DB writes will occur')

  // Build all rows
  const allRows: ChartFactRow[] = []
  for (let year = YEAR_START; year <= YEAR_END; year++) {
    allRows.push(...buildVarshphalRows(year))
  }

  const yearCount = YEAR_END - YEAR_START + 1
  console.log(`[varshphal] Built ${allRows.length} rows for ${yearCount} years (${YEAR_START}–${YEAR_END})`)
  console.log(`[varshphal] 18 subkeys per year: 3 computed + 15 [EXTERNAL_COMPUTATION_REQUIRED]`)

  // Spot-check log
  const sample1984 = allRows.filter(r => r.fact_id.startsWith('VPH.1984.'))
  console.log(`[spot-check] 1984 rows: ${sample1984.length}`)
  const muntha1984 = sample1984.find(r => r.fact_id === 'VPH.1984.MUNTHA')
  const muntha1996 = allRows.find(r => r.fact_id === 'VPH.1996.MUNTHA')
  const muntha2070 = allRows.find(r => r.fact_id === 'VPH.2070.MUNTHA')
  console.log(`[spot-check] muntha 1984 = ${muntha1984?.value_text} (expected: Cancer)`)
  console.log(`[spot-check] muntha 1996 = ${muntha1996?.value_text} (expected: Cancer — 12-year cycle)`)
  console.log(`[spot-check] muntha 2070 = ${muntha2070?.value_text}`)

  try {
    await ensureBuildManifest(dryRun)
    const inserted = await upsertRows(allRows, dryRun)
    console.log(`[varshphal] Upserted ${inserted} rows OK`)

    if (!dryRun) {
      // Verify
      const res = await pool.query(
        `SELECT count(*) as cnt FROM chart_facts WHERE category='varshphal' AND is_stale=false`
      )
      console.log(`[verify] chart_facts WHERE category='varshphal': ${res.rows[0].cnt} rows`)
      if (parseInt(res.rows[0].cnt) < 1500) {
        console.error(`[ERROR] Row count below 1500 threshold!`)
        process.exit(1)
      }
      console.log(`[verify] AC.S3.1 PASS — row count ≥ 1500`)
    }
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error('[FATAL]', err)
  process.exit(1)
})
