#!/usr/bin/env npx tsx
/**
 * bootstrap_chart_facts_ashtakavarga.ts — Ingest Ashtakavarga into chart_facts (v3.3-S1)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §7.1 (BAV bindus), §7.2 (SAV), §7.3 (Shuddha Pinda)
 * Produces:
 *   category='ashtakavarga_sav' — 12 rows (one per sign)
 *   category='ashtakavarga_bav' — 105 rows (84 bindu + 21 pinda)
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts [--dry-run]
 */

import { Pool } from 'pg'

const DATABASE_URL = process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'
const BUILD_ID = 'mcpt-v33-s1-chart-facts-20260522'
const pool = new Pool({ connectionString: DATABASE_URL })

// ── Source data ───────────────────────────────────────────────────────────────

const PLANETS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN'] as const
type Planet = typeof PLANETS[number]
const PLANET_LABELS: Record<Planet, string> = {
  SUN: 'Sun', MOON: 'Moon', MARS: 'Mars', MERCURY: 'Mercury',
  JUPITER: 'Jupiter', VENUS: 'Venus', SATURN: 'Saturn',
}

const SIGNS = ['AR', 'TA', 'GE', 'CN', 'LE', 'VI', 'LI', 'SC', 'SG', 'CP', 'AQ', 'PI'] as const
type Sign = typeof SIGNS[number]
const SIGN_LABELS: Record<Sign, string> = {
  AR: 'Aries', TA: 'Taurus', GE: 'Gemini', CN: 'Cancer',
  LE: 'Leo', VI: 'Virgo', LI: 'Libra', SC: 'Scorpio',
  SG: 'Sagittarius', CP: 'Capricorn', AQ: 'Aquarius', PI: 'Pisces',
}

// FORENSIC §7.1 BAV bindus per planet per sign (order: AR TA GE CN LE VI LI SC SG CP AQ PI)
const BAV_BINDUS: Record<Planet, number[]> = {
  SUN:     [5, 5, 5, 5, 4, 3, 5, 6, 2, 4, 2, 2],  // total=48
  MOON:    [3, 1, 5, 5, 6, 3, 4, 5, 4, 2, 5, 6],  // total=49
  MARS:    [4, 6, 4, 4, 2, 2, 5, 5, 1, 3, 1, 2],  // total=39
  MERCURY: [4, 7, 4, 6, 3, 4, 5, 7, 4, 5, 2, 3],  // total=54
  JUPITER: [5, 4, 3, 4, 5, 6, 7, 3, 4, 6, 5, 4],  // total=56
  VENUS:   [4, 4, 5, 4, 6, 5, 3, 3, 6, 4, 4, 4],  // total=52
  SATURN:  [4, 2, 2, 4, 4, 3, 4, 4, 4, 2, 4, 2],  // total=39
}

// FORENSIC §7.2 SAV bindus per sign (FORENSIC canonical; total=337)
const SAV_BINDUS: number[] = [29, 29, 28, 32, 30, 26, 33, 33, 25, 26, 23, 23]

// FORENSIC §7.3 Shuddha Pinda (Rasi Pinda, Graha Pinda, Shuddha Pinda)
const PINDA: Record<Planet, { rasi: number; graha: number; shuddha: number; rank: number }> = {
  MARS:    { rasi: 136, graha:  62, shuddha: 198, rank: 1 },
  SUN:     { rasi: 123, graha:  49, shuddha: 172, rank: 2 },
  MERCURY: { rasi:  92, graha:  66, shuddha: 158, rank: 3 },
  JUPITER: { rasi:  74, graha:  82, shuddha: 156, rank: 4 },
  VENUS:   { rasi:  78, graha:  39, shuddha: 117, rank: 5 },
  MOON:    { rasi:  80, graha:  32, shuddha: 112, rank: 6 },
  SATURN:  { rasi:  44, graha:  36, shuddha:  80, rank: 7 },
}

// ── Build manifest (idempotent — shared with shadbala script) ─────────────────

async function ensureBuildManifest(dryRun: boolean): Promise<void> {
  if (dryRun) { console.log(`[dry-run] WOULD upsert build_manifests: ${BUILD_ID}`); return }
  await pool.query(`
    INSERT INTO build_manifests
      (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
       embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri, notes)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (build_id) DO NOTHING
  `, [
    BUILD_ID,
    'mcpt-v33-s1-direct-ingest',
    'FORENSIC_v8_0_manual_extraction',
    'n/a:direct-ingest',
    'n/a',
    0,
    0,
    0,
    'live',
    'gs://madhav-marsys-build-artifacts/mcpt-v33-s1/manifest-stub.json',
    'MCPT v3.3-S1: Shadbala + Ashtakavarga direct ingest from FORENSIC §6.1/§6.2/§7.1/§7.2/§7.3',
  ])
  console.log(`[manifest] ensured build_manifests entry: ${BUILD_ID}`)
}

// ── Row types ─────────────────────────────────────────────────────────────────

interface Row {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string
  value_number: number
  source_section: string
  build_id: string
  provenance: object
}

// ── SAV rows ──────────────────────────────────────────────────────────────────

export function buildSavRows(): Row[] {
  const prov = { source: 'FORENSIC_ASTROLOGICAL_DATA_v8_0', method: 'manual_extraction', extracted_by: 'mcpt-v33-s1' }
  return SIGNS.map((sign, i) => ({
    fact_id: `SAV.FORENSIC.H${String(i + 1).padStart(2, '0')}`,
    category: 'ashtakavarga_sav',
    divisional_chart: 'D1',
    value_number: SAV_BINDUS[i],
    value_text: `${SIGN_LABELS[sign]} (H${i + 1}) SAV — ${SAV_BINDUS[i]} bindus`,
    source_section: `§7.2.${sign.toLowerCase()}`,
    build_id: BUILD_ID,
    provenance: prov,
  }))
}

// ── BAV rows (84 bindu + 21 pinda = 105) ─────────────────────────────────────

export function buildBavRows(): Row[] {
  const prov = { source: 'FORENSIC_ASTROLOGICAL_DATA_v8_0', method: 'manual_extraction', extracted_by: 'mcpt-v33-s1' }
  const rows: Row[] = []

  // Bindu rows: 7 × 12 = 84
  for (const planet of PLANETS) {
    const bindus = BAV_BINDUS[planet]
    for (let i = 0; i < SIGNS.length; i++) {
      const sign = SIGNS[i]
      rows.push({
        fact_id: `BAV.FORENSIC.${planet}.${sign}`,
        category: 'ashtakavarga_bav',
        divisional_chart: 'D1',
        value_number: bindus[i],
        value_text: `${PLANET_LABELS[planet]} ${SIGN_LABELS[sign]} — ${bindus[i]} bindus`,
        source_section: `§7.1.${planet.toLowerCase()}.${sign.toLowerCase()}`,
        build_id: BUILD_ID,
        provenance: prov,
      })
    }
  }

  // Pinda rows: 7 × 3 = 21
  for (const planet of PLANETS) {
    const p = PINDA[planet]
    rows.push({
      fact_id: `BAV.FORENSIC.${planet}.PINDA_RASI`,
      category: 'ashtakavarga_bav',
      divisional_chart: 'D1',
      value_number: p.rasi,
      value_text: `${PLANET_LABELS[planet]} Rasi Pinda — ${p.rasi}`,
      source_section: `§7.3.${planet.toLowerCase()}.rasi`,
      build_id: BUILD_ID,
      provenance: prov,
    })
    rows.push({
      fact_id: `BAV.FORENSIC.${planet}.PINDA_GRAHA`,
      category: 'ashtakavarga_bav',
      divisional_chart: 'D1',
      value_number: p.graha,
      value_text: `${PLANET_LABELS[planet]} Graha Pinda — ${p.graha}`,
      source_section: `§7.3.${planet.toLowerCase()}.graha`,
      build_id: BUILD_ID,
      provenance: prov,
    })
    rows.push({
      fact_id: `BAV.FORENSIC.${planet}.PINDA_SHUDDHA`,
      category: 'ashtakavarga_bav',
      divisional_chart: 'D1',
      value_number: p.shuddha,
      value_text: `${PLANET_LABELS[planet]} Shuddha Pinda — ${p.shuddha} (rank ${p.rank})`,
      source_section: `§7.3.${planet.toLowerCase()}.shuddha`,
      build_id: BUILD_ID,
      provenance: prov,
    })
  }

  return rows
}

// ── Ingest ────────────────────────────────────────────────────────────────────

async function ingestRows(rows: Row[], label: string, dryRun: boolean): Promise<{ inserted: number; skipped: number }> {
  let inserted = 0
  let skipped = 0

  for (const r of rows) {
    if (dryRun) {
      console.log(`[dry-run][${label}] ${r.fact_id} → ${r.value_text}`)
      inserted++
      continue
    }
    const { rowCount } = await pool.query(`
      INSERT INTO chart_facts
        (fact_id, category, divisional_chart, value_text, value_number, source_section, build_id, provenance)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT (fact_id) DO NOTHING
    `, [r.fact_id, r.category, r.divisional_chart, r.value_text, r.value_number, r.source_section, r.build_id, JSON.stringify(r.provenance)])
    if ((rowCount ?? 0) > 0) inserted++
    else { skipped++; console.warn(`[${label}] skipped (already exists): ${r.fact_id}`) }
  }

  return { inserted, skipped }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const dryRun = process.argv.includes('--dry-run')
  if (dryRun) console.log('[ashtakavarga] DRY-RUN mode — no DB writes')

  await ensureBuildManifest(dryRun)

  const savRows = buildSavRows()
  const bavRows = buildBavRows()
  console.log(`[ashtakavarga] SAV rows: ${savRows.length}, BAV rows: ${bavRows.length}`)

  const savResult = await ingestRows(savRows, 'sav', dryRun)
  console.log(`[sav] inserted=${savResult.inserted} skipped=${savResult.skipped}`)

  const bavResult = await ingestRows(bavRows, 'bav', dryRun)
  console.log(`[bav] inserted=${bavResult.inserted} skipped=${bavResult.skipped}`)

  if (!dryRun) {
    const { rows: savCount } = await pool.query<{ count: string }>(
      `SELECT count(*) FROM chart_facts WHERE category='ashtakavarga_sav'`
    )
    const { rows: bavCount } = await pool.query<{ count: string }>(
      `SELECT count(*) FROM chart_facts WHERE category='ashtakavarga_bav'`
    )
    const sav = parseInt(savCount[0].count, 10)
    const bav = parseInt(bavCount[0].count, 10)

    console.log(`\n[AC.S1.3] ashtakavarga_sav: ${sav} rows`)
    if (sav === 12) console.log('[AC.S1.3] ✓ PASS — exactly 12 SAV rows')
    else console.error(`[AC.S1.3] ✗ FAIL — need 12, have ${sav}`)

    console.log(`[AC.S1.3] ashtakavarga_bav: ${bav} rows`)
    if (bav >= 100) console.log('[AC.S1.3] ✓ PASS — ≥100 BAV rows')
    else console.error(`[AC.S1.3] ✗ FAIL — need 100, have ${bav}`)

    // Spot-check: FORENSIC §7.1 Moon Pisces = 6 bindus
    const { rows: sc } = await pool.query<{ value_number: string }>(
      `SELECT value_number FROM chart_facts WHERE fact_id='BAV.FORENSIC.MOON.PI'`
    )
    if (sc.length && parseInt(sc[0].value_number, 10) === 6) {
      console.log('[spot-check] PASS — Moon Pisces BAV = 6 bindus matches FORENSIC §7.1')
    } else {
      console.error('[spot-check] FAIL — Moon Pisces BAV mismatch')
    }

    // Spot-check: FORENSIC §7.3 Mars Shuddha Pinda = 198 (rank 1)
    const { rows: sc2 } = await pool.query<{ value_number: string }>(
      `SELECT value_number FROM chart_facts WHERE fact_id='BAV.FORENSIC.MARS.PINDA_SHUDDHA'`
    )
    if (sc2.length && parseInt(sc2[0].value_number, 10) === 198) {
      console.log('[spot-check] PASS — Mars Shuddha Pinda = 198 matches FORENSIC §7.3')
    } else {
      console.error('[spot-check] FAIL — Mars Shuddha Pinda mismatch')
    }
  }
}

if (process.env.NODE_ENV !== 'test') {
  main().catch(e => { console.error(e); process.exit(1) }).finally(() => pool.end())
}
