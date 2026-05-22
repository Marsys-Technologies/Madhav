#!/usr/bin/env npx tsx
/**
 * apply_grounded_citations.ts — Apply operator-reviewed citations (Track A)
 *
 * Reads operator-edited CSV (accepted_candidate column filled).
 * For each row with accepted_candidate in {1, 2, 3}:
 *   - Looks up the chunk_id → source_file + section_label from the CSV
 *   - Builds source_citation string: "<source_file>#<section_label>"
 *   - UPDATEs msr_signals: source_citation, grounded_at, grounded_by
 *
 * Override path: if override_citation column is non-empty, uses that instead.
 * Defer/reject: skipped (operator can re-process later).
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@127.0.0.1:5433/amjis" \
 *   npx tsx scripts/grounding/apply_grounded_citations.ts \
 *     --csv 00_ARCHITECTURE/grounding_review/msr_grounding_candidates_<ts>.csv \
 *     [--dry-run]
 */

import { Pool } from 'pg'
import * as fs from 'fs'
import * as path from 'path'

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'

const pool = new Pool({ connectionString: DATABASE_URL })

// ── CSV parsing (same logic as review queue) ──────────────────────────────────

interface CsvRow {
  signal_id: string
  domain: string
  planet: string
  claim_excerpt: string
  candidate_1_chunk_id: string
  candidate_1_source: string
  candidate_1_section: string
  candidate_1_score: string
  candidate_1_excerpt: string
  candidate_2_chunk_id: string
  candidate_2_source: string
  candidate_2_section: string
  candidate_2_score: string
  candidate_2_excerpt: string
  candidate_3_chunk_id: string
  candidate_3_source: string
  candidate_3_section: string
  candidate_3_score: string
  candidate_3_excerpt: string
  accepted_candidate: string
  override_citation: string
}

function splitCsvLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') { current += '"'; i++ }
      else { inQuotes = !inQuotes }
    } else if (ch === ',' && !inQuotes) {
      result.push(current); current = ''
    } else {
      current += ch
    }
  }
  result.push(current)
  return result
}

function parseCsv(filePath: string): CsvRow[] {
  const text = fs.readFileSync(filePath, 'utf8')
  const lines = text.split('\n').map(l => l.replace(/\r$/, '')).filter(Boolean)
  if (lines.length < 2) return []
  const headers = lines[0].split(',')
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line)
    const obj: Record<string, string> = {}
    headers.forEach((h, i) => { obj[h] = values[i] ?? '' })
    return obj as unknown as CsvRow
  })
}

// ── Citation builder ──────────────────────────────────────────────────────────

function buildCitation(row: CsvRow): string | null {
  if (row.override_citation?.trim()) return row.override_citation.trim()

  const n = row.accepted_candidate
  if (!['1','2','3'].includes(n)) return null

  const source = row[`candidate_${n}_source` as keyof CsvRow]
  const section = row[`candidate_${n}_section` as keyof CsvRow]
  const chunkId = row[`candidate_${n}_chunk_id` as keyof CsvRow]

  const base = path.basename(source as string).replace(/\.md$/, '')
  const sect = (section as string)?.trim() ? `#${section}` : ''
  const suffix = chunkId ? ` [${(chunkId as string).substring(0, 8)}]` : ''

  return `${base}${sect}${suffix}`
}

// ── Apply to DB ───────────────────────────────────────────────────────────────

export interface ApplyResult {
  applied: number
  skipped_defer: number
  skipped_reject: number
  skipped_no_decision: number
  errors: string[]
}

export async function applyGroundedCitations(
  csvPath: string,
  dryRun = false
): Promise<ApplyResult> {
  const rows = parseCsv(csvPath)
  console.log(`[apply] loaded ${rows.length} rows from ${path.basename(csvPath)}`)

  const result: ApplyResult = {
    applied: 0,
    skipped_defer: 0,
    skipped_reject: 0,
    skipped_no_decision: 0,
    errors: [],
  }

  const groundedAt = new Date().toISOString()
  const groundedBy = 'mcpt-v34-s1'

  for (const row of rows) {
    if (row.accepted_candidate === 'defer') { result.skipped_defer++; continue }
    if (row.accepted_candidate === 'reject') { result.skipped_reject++; continue }
    if (!row.accepted_candidate.trim()) { result.skipped_no_decision++; continue }

    const citation = buildCitation(row)
    if (!citation) { result.skipped_no_decision++; continue }

    if (dryRun) {
      console.log(`[dry-run] WOULD UPDATE signal_id=${row.signal_id} → citation="${citation}"`)
      result.applied++
      continue
    }

    try {
      const { rowCount } = await pool.query(
        `UPDATE msr_signals
           SET source_citation = $1,
               grounded_at     = $2,
               grounded_by     = $3
         WHERE signal_id = $4
           AND (source_citation IS NULL OR source_citation = '')`,
        [citation, groundedAt, groundedBy, row.signal_id]
      )
      if ((rowCount ?? 0) > 0) {
        result.applied++
      } else {
        console.warn(`[apply] no row updated for signal_id=${row.signal_id} (already grounded or not found)`)
      }
    } catch (err) {
      const msg = `signal_id=${row.signal_id}: ${(err as Error).message}`
      result.errors.push(msg)
      console.error(`[apply] ERROR ${msg}`)
    }
  }

  return result
}

// ── Post-apply stats ──────────────────────────────────────────────────────────

export async function queryGroundingStats(): Promise<{
  total: number
  grounded: number
  grounding_pct: number
}> {
  const { rows } = await pool.query<{ total: string; grounded: string }>(`
    SELECT
      count(*)                                              AS total,
      count(*) FILTER (WHERE source_citation IS NOT NULL
                         AND source_citation != '')        AS grounded
    FROM msr_signals
    WHERE native_id = 'abhisek_mohanty'
  `)
  const total   = parseInt(rows[0].total, 10)
  const grounded = parseInt(rows[0].grounded, 10)
  return { total, grounded, grounding_pct: total > 0 ? grounded / total : 0 }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const csvFlag = args.indexOf('--csv')
  const csvPath = csvFlag !== -1 ? args[csvFlag + 1] : ''
  const dryRun  = args.includes('--dry-run')

  if (!csvPath) {
    console.error('Usage: npx tsx apply_grounded_citations.ts --csv <path> [--dry-run]')
    process.exit(1)
  }

  const absPath = path.resolve(csvPath)
  if (!fs.existsSync(absPath)) {
    console.error(`CSV not found: ${absPath}`)
    process.exit(1)
  }

  if (dryRun) console.log('[apply] DRY-RUN mode — no DB writes')

  const result = await applyGroundedCitations(absPath, dryRun)

  console.log('\n[apply] Results:')
  console.log(`  Applied:            ${result.applied}`)
  console.log(`  Skipped (defer):    ${result.skipped_defer}`)
  console.log(`  Skipped (reject):   ${result.skipped_reject}`)
  console.log(`  Skipped (no decision): ${result.skipped_no_decision}`)
  console.log(`  Errors:             ${result.errors.length}`)

  if (!dryRun) {
    const stats = await queryGroundingStats()
    const pct = (stats.grounding_pct * 100).toFixed(1)
    console.log(`\n[stats] msr_signals grounding: ${stats.grounded}/${stats.total} (${pct}%)`)
    if (stats.grounding_pct >= 0.95) {
      console.log('[AC.S1.1] ✓ PASS — ≥95% grounded')
    } else {
      console.log(`[AC.S1.1] ✗ NOT YET — need ${Math.ceil(stats.total * 0.95)} grounded (have ${stats.grounded})`)
    }
  }
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(() => pool.end())
