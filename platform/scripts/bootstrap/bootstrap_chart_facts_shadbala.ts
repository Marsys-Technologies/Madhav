#!/usr/bin/env npx tsx
/**
 * bootstrap_chart_facts_shadbala.ts — Ingest Shadbala into chart_facts (v3.3-S1)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §6.1 (components) + §6.2 (totals)
 * Produces: 63 rows (9 rows × 7 planets) in chart_facts WHERE category='shadbala'
 *
 * Rows per planet:
 *   SBL.{PLANET}.UCCHA         — Uccha Bala (virupa, subcomponent of Sthana)
 *   SBL.{PLANET}.STHANA        — Sthana Bala total (virupa)
 *   SBL.{PLANET}.DIG           — Dig Bala total (virupa)
 *   SBL.{PLANET}.KALA          — Kala Bala total (virupa)
 *   SBL.{PLANET}.CHESTA        — Chesta Bala total (virupa)
 *   SBL.{PLANET}.NAISARG       — Naisargika Bala total (virupa)
 *   SBL.{PLANET}.DRIK          — Drik Bala total (virupa)
 *   SBL.{PLANET}.TOTAL_VP      — Total Shadbala in virupas (FORENSIC §6.2)
 *   SBL.{PLANET}.TOTAL_RP      — Total Shadbala in rupas (FORENSIC §6.2)
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx scripts/bootstrap/bootstrap_chart_facts_shadbala.ts [--dry-run]
 */

import { Pool } from 'pg'

const DATABASE_URL = process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'
const BUILD_ID = 'mcpt-v33-s1-chart-facts-20260522'
const pool = new Pool({ connectionString: DATABASE_URL })

// ── Source data (FORENSIC §6.1 + §6.2) ───────────────────────────────────────

const PLANETS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN'] as const
type Planet = typeof PLANETS[number]

const PLANET_LABELS: Record<Planet, string> = {
  SUN: 'Sun', MOON: 'Moon', MARS: 'Mars', MERCURY: 'Mercury',
  JUPITER: 'Jupiter', VENUS: 'Venus', SATURN: 'Saturn',
}

// All values in virupas from FORENSIC §6.1; order: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
const DATA: Record<Planet, {
  uccha: number; sthana: number; dig: number; kala: number
  chesta: number; naisarg: number; drik: number; total_vp: number; total_rp: number
}> = {
  SUN:     { uccha: 33.99, sthana: 191.49, dig:  53.67, kala: 225.58, chesta:  15.20, naisarg:  60.00, drik: -35.08, total_vp: 510.85, total_rp: 8.51 },
  MOON:    { uccha: 38.02, sthana: 206.77, dig:  18.02, kala: 149.46, chesta:  11.70, naisarg:  51.42, drik:  -1.85, total_vp: 435.51, total_rp: 7.26 },
  MARS:    { uccha: 26.84, sthana: 176.84, dig:  35.18, kala:  65.08, chesta:  36.17, naisarg:  17.16, drik: -14.20, total_vp: 316.23, total_rp: 5.27 },
  MERCURY: { uccha: 24.72, sthana: 182.22, dig:  26.15, kala: 165.25, chesta:  17.83, naisarg:  25.74, drik: -23.92, total_vp: 393.26, total_rp: 6.55 },
  JUPITER: { uccha:  8.40, sthana: 233.40, dig:  19.14, kala: 170.47, chesta:  13.79, naisarg:  34.26, drik:  -6.98, total_vp: 464.07, total_rp: 7.73 },
  VENUS:   { uccha: 27.39, sthana: 151.14, dig:   4.60, kala:  66.15, chesta:  19.51, naisarg:  42.84, drik:  -8.24, total_vp: 276.01, total_rp: 4.60 },
  SATURN:  { uccha: 59.18, sthana: 257.93, dig:  56.65, kala: 106.01, chesta:  31.63, naisarg:   8.58, drik: -12.81, total_vp: 447.98, total_rp: 7.47 },
}

// ── Build manifest ────────────────────────────────────────────────────────────

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

// ── Row builder ───────────────────────────────────────────────────────────────

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

export function buildRows(): Row[] {
  const rows: Row[] = []
  const prov = { source: 'FORENSIC_ASTROLOGICAL_DATA_v8_0', method: 'manual_extraction', extracted_by: 'mcpt-v33-s1' }

  for (const planet of PLANETS) {
    const d = DATA[planet]
    const lbl = PLANET_LABELS[planet]

    rows.push({ fact_id: `SBL.FORENSIC.${planet}.UCCHA`,   category: 'shadbala', divisional_chart: 'D1', value_number: d.uccha,    value_text: `${lbl} Uccha Bala — ${d.uccha} virupa`,              source_section: '§6.1.uccha',   build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.STHANA`,  category: 'shadbala', divisional_chart: 'D1', value_number: d.sthana,   value_text: `${lbl} Sthana Bala — ${d.sthana} virupa`,            source_section: '§6.1.sthana',  build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.DIG`,     category: 'shadbala', divisional_chart: 'D1', value_number: d.dig,      value_text: `${lbl} Dig Bala — ${d.dig} virupa`,                  source_section: '§6.1.dig',     build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.KALA`,    category: 'shadbala', divisional_chart: 'D1', value_number: d.kala,     value_text: `${lbl} Kala Bala — ${d.kala} virupa`,                source_section: '§6.1.kala',    build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.CHESTA`,  category: 'shadbala', divisional_chart: 'D1', value_number: d.chesta,   value_text: `${lbl} Chesta Bala — ${d.chesta} virupa`,            source_section: '§6.1.chesta',  build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.NAISARG`, category: 'shadbala', divisional_chart: 'D1', value_number: d.naisarg,  value_text: `${lbl} Naisargika Bala — ${d.naisarg} virupa`,       source_section: '§6.1.naisarg', build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.DRIK`,    category: 'shadbala', divisional_chart: 'D1', value_number: d.drik,     value_text: `${lbl} Drik Bala — ${d.drik} virupa`,                source_section: '§6.1.drik',    build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.TOTAL_VP`,category: 'shadbala', divisional_chart: 'D1', value_number: d.total_vp, value_text: `${lbl} Shadbala Total — ${d.total_vp} virupa`,       source_section: '§6.2.total_vp',build_id: BUILD_ID, provenance: prov })
    rows.push({ fact_id: `SBL.FORENSIC.${planet}.TOTAL_RP`,category: 'shadbala', divisional_chart: 'D1', value_number: d.total_rp, value_text: `${lbl} Shadbala Total — ${d.total_rp} rupa`,         source_section: '§6.2.total_rp',build_id: BUILD_ID, provenance: prov })
  }
  return rows
}

// ── Ingest ────────────────────────────────────────────────────────────────────

async function ingest(dryRun: boolean): Promise<void> {
  const rows = buildRows()
  console.log(`[shadbala] ${rows.length} rows to ingest`)

  let inserted = 0
  let skipped = 0

  for (const r of rows) {
    if (dryRun) {
      console.log(`[dry-run] ${r.fact_id} → ${r.value_text}`)
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
    else { skipped++; console.warn(`[shadbala] skipped (already exists): ${r.fact_id}`) }
  }

  console.log(`[shadbala] inserted=${inserted} skipped=${skipped}`)
}

// ── Spot-check ────────────────────────────────────────────────────────────────

async function spotCheck(): Promise<void> {
  const { rows } = await pool.query<{ fact_id: string; value_number: string }>(
    `SELECT fact_id, value_number FROM chart_facts WHERE fact_id IN ($1, $2, $3) ORDER BY fact_id`,
    ['SBL.FORENSIC.SATURN.UCCHA', 'SBL.FORENSIC.SUN.TOTAL_VP', 'SBL.FORENSIC.JUPITER.TOTAL_RP']
  )
  for (const r of rows) {
    console.log(`[spot-check] ${r.fact_id} = ${r.value_number}`)
  }
  const sat = rows.find(r => r.fact_id === 'SBL.FORENSIC.SATURN.UCCHA')
  if (sat && parseFloat(sat.value_number) === 59.18) {
    console.log('[spot-check] PASS — Saturn Uccha Bala = 59.18 virupa matches FORENSIC §6.1')
  } else {
    console.error('[spot-check] FAIL — Saturn Uccha Bala mismatch')
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const dryRun = process.argv.includes('--dry-run')
  if (dryRun) console.log('[shadbala] DRY-RUN mode — no DB writes')

  await ensureBuildManifest(dryRun)
  await ingest(dryRun)

  if (!dryRun) {
    const { rows } = await pool.query<{ count: string }>(
      `SELECT count(*) FROM chart_facts WHERE category='shadbala'`
    )
    const count = parseInt(rows[0].count, 10)
    console.log(`[AC.S1.2] shadbala row count: ${count}`)
    if (count >= 63) console.log('[AC.S1.2] ✓ PASS — ≥63 shadbala rows')
    else console.error(`[AC.S1.2] ✗ FAIL — need 63, have ${count}`)

    await spotCheck()
  }
}

if (process.env.NODE_ENV !== 'test') {
  main().catch(e => { console.error(e); process.exit(1) }).finally(() => pool.end())
}
