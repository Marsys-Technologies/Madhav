/**
 * verify_classical_texts_data.ts
 * Confirms classical_texts + classical_chunks are populated in the running DB.
 * Run: npx tsx platform/scripts/verify_classical_texts_data.ts
 * Requires: DATABASE_URL env var.
 *
 * Acceptance criteria:
 *   - classical_texts: >= 4 rows (BPHS, jaimini_sutra, kp_reader, tajaka_neelakanthi minimum)
 *   - classical_chunks: >= 4000 rows total
 *   - Every classical_texts row has non-null text_key, title, tradition, school
 *   - Spot-check: BPHS text present with chunk_count > 0
 */
import { query } from '../src/lib/db/client'

async function main() {
  console.log('=== classical_texts data verification ===\n')
  let allPass = true

  // 1. Row counts
  const textCount = await query<{ count: string }>(
    'SELECT count(*)::text AS count FROM classical_texts'
  )
  const chunkCount = await query<{ count: string }>(
    'SELECT count(*)::text AS count FROM classical_chunks'
  )
  const texts = parseInt(textCount.rows[0]?.count ?? '0', 10)
  const chunks = parseInt(chunkCount.rows[0]?.count ?? '0', 10)

  console.log(`classical_texts rows: ${texts}  (floor: 4)`)
  console.log(`classical_chunks rows: ${chunks}  (floor: 4000)`)

  if (texts < 4) { console.log('FAIL: classical_texts below floor'); allPass = false }
  if (chunks < 4000) { console.log('FAIL: classical_chunks below floor'); allPass = false }

  // 2. Null guard
  const nullCheck = await query<{ bad: string }>(
    `SELECT count(*)::text AS bad FROM classical_texts
     WHERE text_key IS NULL OR title IS NULL OR tradition IS NULL OR school IS NULL`
  )
  const nullRows = parseInt(nullCheck.rows[0]?.bad ?? '0', 10)
  if (nullRows > 0) { console.log(`FAIL: ${nullRows} rows with NULL required fields`); allPass = false }
  else { console.log('PASS: no null required fields') }

  // 3. BPHS spot-check
  const bphs = await query<{ text_key: string; chunk_count: number }>(
    `SELECT text_key, chunk_count FROM classical_texts WHERE text_key = 'bphs'`
  )
  if (bphs.rows.length === 0) { console.log('FAIL: BPHS not found in classical_texts'); allPass = false }
  else if ((bphs.rows[0]?.chunk_count ?? 0) < 1) {
    console.log('FAIL: BPHS has chunk_count=0'); allPass = false
  } else {
    console.log(`PASS: BPHS present, chunk_count=${bphs.rows[0]?.chunk_count}`)
  }

  // 4. Per-text breakdown
  const perText = await query<{ text_key: string; chunk_count: number }>(
    `SELECT t.text_key, count(c.id)::int AS chunk_count
     FROM classical_texts t
     LEFT JOIN classical_chunks c ON c.text_id = t.id
     GROUP BY t.text_key ORDER BY chunk_count DESC`
  )
  console.log('\nPer-text chunk counts:')
  for (const row of perText.rows) {
    console.log(`  ${row.text_key}: ${row.chunk_count}`)
  }

  console.log(`\n=== ${allPass ? 'ALL PASS' : 'FAILURES DETECTED — run ingestion before acceptance'} ===`)
  process.exit(allPass ? 0 : 1)
}

main().catch(e => { console.error(e); process.exit(1) })
