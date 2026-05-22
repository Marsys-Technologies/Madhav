#!/usr/bin/env npx tsx
/**
 * bootstrap_chart_facts_bhava_bala.ts — Ingest Bhava Bala into chart_facts (v3.3-S1)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §6.4
 * Produces: 12 rows in chart_facts WHERE category='bhava_bala'
 *
 * NOTE: Rows were already ingested in a prior session under
 *   build_id='build-865dd96e-3cad-4715-be47-fc8005ef95b5'
 *   (varga-etl-full-s1-reingest). Script is idempotent; re-running skips existing rows.
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts [--dry-run]
 */

import { Pool } from 'pg'

const DATABASE_URL = process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'
const BUILD_ID = 'mcpt-v33-s1-chart-facts-20260522'
const pool = new Pool({ connectionString: DATABASE_URL })

// FORENSIC §6.4 — Bhava Bala totals (virupa) per house
export const BHAVA_BALA_DATA: { house: number; virupa: number; rank: number }[] = [
  { house:  1, virupa: 340.08, rank: 10 },
  { house:  2, virupa: 266.26, rank: 11 },
  { house:  3, virupa: 447.37, rank:  7 },
  { house:  4, virupa: 474.87, rank:  6 },
  { house:  5, virupa: 486.86, rank:  2 },
  { house:  6, virupa: 486.38, rank:  3 },
  { house:  7, virupa: 486.00, rank:  4 },
  { house:  8, virupa: 228.37, rank: 12 },
  { house:  9, virupa: 485.63, rank:  5 },
  { house: 10, virupa: 494.53, rank:  1 },
  { house: 11, virupa: 370.24, rank:  9 },
  { house: 12, virupa: 380.83, rank:  8 },
]

export function buildRows() {
  const prov = { source: 'FORENSIC_ASTROLOGICAL_DATA_v8_0', method: 'manual_extraction', extracted_by: 'mcpt-v33-s1' }
  return BHAVA_BALA_DATA.map(d => ({
    fact_id: `BVB.FORENSIC.H${String(d.house).padStart(2, '0')}`,
    category: 'bhava_bala',
    divisional_chart: 'D1',
    value_number: d.virupa,
    value_text: `House ${d.house} — ${d.virupa} virupa (rank ${d.rank})`,
    source_section: `§6.4 row ${d.rank}`,
    build_id: BUILD_ID,
    provenance: prov,
  }))
}

async function main(): Promise<void> {
  const dryRun = process.argv.includes('--dry-run')
  if (dryRun) console.log('[bhava_bala] DRY-RUN mode — no DB writes')

  if (!dryRun) {
    // Ensure build manifest exists (idempotent — shared with shadbala/ashtakavarga)
    await pool.query(`
      INSERT INTO build_manifests
        (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
         embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri, notes)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      ON CONFLICT (build_id) DO NOTHING
    `, [BUILD_ID, 'mcpt-v33-s1-direct-ingest', 'FORENSIC_v8_0_manual_extraction', 'n/a:direct-ingest',
        'n/a', 0, 0, 0, 'live',
        'gs://madhav-marsys-build-artifacts/mcpt-v33-s1/manifest-stub.json',
        'MCPT v3.3-S1: Shadbala + Ashtakavarga direct ingest from FORENSIC §6.1/§6.2/§7.1/§7.2/§7.3'])
  }

  const rows = buildRows()
  let inserted = 0; let skipped = 0
  for (const r of rows) {
    if (dryRun) { console.log(`[dry-run] ${r.fact_id} → ${r.value_text}`); inserted++; continue }
    const { rowCount } = await pool.query(`
      INSERT INTO chart_facts
        (fact_id, category, divisional_chart, value_text, value_number, source_section, build_id, provenance)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT (fact_id) DO NOTHING
    `, [r.fact_id, r.category, r.divisional_chart, r.value_text, r.value_number, r.source_section, r.build_id, JSON.stringify(r.provenance)])
    if ((rowCount ?? 0) > 0) inserted++
    else skipped++
  }

  console.log(`[bhava_bala] inserted=${inserted} skipped=${skipped}`)

  if (!dryRun) {
    const { rows: cnt } = await pool.query<{ count: string }>(`SELECT count(*) FROM chart_facts WHERE category='bhava_bala'`)
    const count = parseInt(cnt[0].count, 10)
    if (count >= 12) console.log(`[AC.S1.4] ✓ PASS — ${count} bhava_bala rows (≥12)`)
    else console.error(`[AC.S1.4] ✗ FAIL — need 12, have ${count}`)
  }
}

main().catch(e => { console.error(e); process.exit(1) }).finally(() => pool.end())
