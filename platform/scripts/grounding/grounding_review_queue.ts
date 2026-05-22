#!/usr/bin/env npx tsx
/**
 * grounding_review_queue.ts — Operator review surface (Track A)
 *
 * Reads the candidate CSV produced by msr_grounding_pipeline.ts and generates:
 *   1. A summary report: how many signals, how many with strong candidates
 *   2. Optionally an HTML review page (--html flag) for easier review
 *
 * LLM-as-suggester variant:
 *   Pass --auto-accept to auto-fill accepted_candidate based on cosine distance
 *   threshold (< 0.25 = accept candidate 1; 0.25–0.40 = defer; > 0.40 = reject).
 *   This is the semi-automated path. Operator still reviews the CSV before applying.
 *
 * Usage:
 *   npx tsx scripts/grounding/grounding_review_queue.ts \
 *     --csv 00_ARCHITECTURE/grounding_review/msr_grounding_candidates_<ts>.csv \
 *     [--auto-accept] [--html]
 */

import * as fs from 'fs'
import * as path from 'path'

const ACCEPT_DISTANCE_THRESHOLD = 0.25  // cosine distance < this → auto-accept c1
const DEFER_DISTANCE_THRESHOLD  = 0.40  // above this → reject; between → defer

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

function parseCsv(filePath: string): CsvRow[] {
  const text = fs.readFileSync(filePath, 'utf8')
  const lines = text.split('\n').filter(Boolean)
  if (lines.length < 2) return []

  const headers = lines[0].split(',')
  const rows: CsvRow[] = []

  for (let i = 1; i < lines.length; i++) {
    const values = splitCsvLine(lines[i])
    const obj: Record<string, string> = {}
    headers.forEach((h, idx) => { obj[h] = values[idx] ?? '' })
    rows.push(obj as unknown as CsvRow)
  }
  return rows
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

function autoAccept(rows: CsvRow[]): CsvRow[] {
  return rows.map((row) => {
    if (row.accepted_candidate) return row  // already filled by operator
    const score = parseFloat(row.candidate_1_score)
    if (isNaN(score)) return { ...row, accepted_candidate: 'defer' }
    if (score < ACCEPT_DISTANCE_THRESHOLD) return { ...row, accepted_candidate: '1' }
    if (score < DEFER_DISTANCE_THRESHOLD)  return { ...row, accepted_candidate: 'defer' }
    return { ...row, accepted_candidate: 'reject' }
  })
}

function writeSummary(rows: CsvRow[], csvPath: string): void {
  const total = rows.length
  const filled = rows.filter(r => r.accepted_candidate !== '').length
  const accepted = rows.filter(r => ['1','2','3'].includes(r.accepted_candidate)).length
  const deferred = rows.filter(r => r.accepted_candidate === 'defer').length
  const rejected = rows.filter(r => r.accepted_candidate === 'reject').length
  const pending  = rows.filter(r => r.accepted_candidate === '').length

  const byDomain: Record<string, number> = {}
  for (const r of rows) {
    if (!['1','2','3'].includes(r.accepted_candidate)) continue
    byDomain[r.domain] = (byDomain[r.domain] ?? 0) + 1
  }

  const summary = [
    '# Grounding Review Queue Summary',
    `CSV: ${csvPath}`,
    `Generated: ${new Date().toISOString()}`,
    '',
    `## Totals`,
    `Total signals: ${total}`,
    `Filled (any decision): ${filled}`,
    `  Accepted (candidate 1/2/3): ${accepted}`,
    `  Deferred: ${deferred}`,
    `  Rejected: ${rejected}`,
    `  Pending (no decision yet): ${pending}`,
    '',
    '## Accepted by domain',
    ...Object.entries(byDomain).sort((a,b) => b[1]-a[1]).map(([d,c]) => `  ${d}: ${c}`),
    '',
    '## Next step',
    `Run: npx tsx scripts/grounding/apply_grounded_citations.ts --csv "${csvPath}"`,
  ].join('\n')

  const summaryPath = csvPath.replace('.csv', '_summary.md')
  fs.writeFileSync(summaryPath, summary, 'utf8')
  console.log('[summary] written →', summaryPath)
  console.log(summary)
}

function escapeHtml(s: string): string {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
}

function writeHtml(rows: CsvRow[], csvPath: string): void {
  const pending = rows.filter(r => !r.accepted_candidate)
  const htmlPath = csvPath.replace('.csv', '_review.html')

  const tableRows = pending.map((r, i) => `
    <tr>
      <td>${escapeHtml(r.signal_id)}</td>
      <td>${escapeHtml(r.domain)}</td>
      <td class="claim">${escapeHtml(r.claim_excerpt)}</td>
      <td>
        <div class="candidate ${parseFloat(r.candidate_1_score) < 0.25 ? 'strong' : ''}">
          <b>[${r.candidate_1_score}]</b> ${escapeHtml(r.candidate_1_source.split('/').pop() ?? '')} §${escapeHtml(r.candidate_1_section)}<br>
          <small>${escapeHtml(r.candidate_1_excerpt)}</small>
        </div>
      </td>
      <td>
        <select onchange="updateAccepted(${i}, this.value)" id="sel_${i}">
          <option value="">-- choose --</option>
          <option value="1">Accept C1</option>
          <option value="2">Accept C2</option>
          <option value="3">Accept C3</option>
          <option value="defer">Defer</option>
          <option value="reject">Reject</option>
        </select>
      </td>
    </tr>
  `).join('')

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>MSR Grounding Review</title>
  <style>
    body { font-family: monospace; font-size: 13px; }
    table { border-collapse: collapse; width: 100%; }
    td,th { border: 1px solid #ccc; padding: 4px 8px; vertical-align: top; }
    .claim { max-width: 200px; word-break: break-word; }
    .candidate { max-width: 300px; }
    .strong { background: #d4edda; }
    h2 { margin-top: 24px; }
  </style>
</head>
<body>
  <h1>MSR Grounding Review Queue</h1>
  <p><b>Source CSV:</b> ${escapeHtml(csvPath)}</p>
  <p><b>Pending decisions:</b> ${pending.length} of ${rows.length}</p>
  <table>
    <thead>
      <tr><th>Signal</th><th>Domain</th><th>Claim</th><th>Top Candidate</th><th>Decision</th></tr>
    </thead>
    <tbody>${tableRows}</tbody>
  </table>
  <script>
    const rows = ${JSON.stringify(rows)};
    function updateAccepted(i, val) { rows[i].accepted_candidate = val; }
    function exportCsv() {
      const headers = Object.keys(rows[0]);
      const lines = [headers.join(','), ...rows.map(r => headers.map(h => {
        const v = String(r[h] ?? '');
        return v.includes(',') || v.includes('"') || v.includes('\\n')
          ? '"' + v.replace(/"/g, '""') + '"' : v;
      }).join(','))];
      const a = document.createElement('a');
      a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(lines.join('\\n'));
      a.download = '${escapeHtml(path.basename(csvPath))}';
      a.click();
    }
  </script>
  <br>
  <button onclick="exportCsv()">Export updated CSV</button>
</body>
</html>`

  fs.writeFileSync(htmlPath, html, 'utf8')
  console.log('[html] review page written →', htmlPath)
}

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const csvFlag = args.indexOf('--csv')
  const csvPath = csvFlag !== -1 ? args[csvFlag + 1] : ''
  const doAutoAccept = args.includes('--auto-accept')
  const doHtml = args.includes('--html')

  if (!csvPath) {
    console.error('Usage: npx tsx grounding_review_queue.ts --csv <path> [--auto-accept] [--html]')
    process.exit(1)
  }

  const absPath = path.resolve(csvPath)
  if (!fs.existsSync(absPath)) {
    console.error(`CSV not found: ${absPath}`)
    process.exit(1)
  }

  let rows = parseCsv(absPath)
  console.log(`[review] loaded ${rows.length} rows from ${absPath}`)

  if (doAutoAccept) {
    rows = autoAccept(rows)
    // Write auto-accepted back to CSV
    const headers = Object.keys(rows[0]) as (keyof CsvRow)[]
    function escapeCsvVal(v: string): string {
      if (v.includes('"') || v.includes(',') || v.includes('\n')) return `"${v.replace(/"/g,'""')}"`
      return v
    }
    const lines = [
      headers.join(','),
      ...rows.map(r => headers.map(h => escapeCsvVal(r[h])).join(',')),
    ]
    fs.writeFileSync(absPath, lines.join('\n'), 'utf8')
    console.log('[auto-accept] CSV updated with suggested decisions')
  }

  writeSummary(rows, absPath)

  if (doHtml) {
    writeHtml(rows, absPath)
  }
}

main().catch((e) => { console.error(e); process.exit(1) })
