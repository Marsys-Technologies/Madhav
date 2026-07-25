#!/usr/bin/env tsx
/**
 * evals/k2/auditor.ts — the DB-verifying auditor pass, LAW per TWO_PASS_GRADING_LAW_v1_0.md
 * (EL-10). Every grader pass (evals/k2/consumption_grader.ts) gets a second, methodologically
 * independent pass here. Disagreements are logged — never silently resolved in the grader's
 * favor.
 *
 * Independence of METHOD (not just a second run of the same code):
 *   - Grader:   fast substring search — `resultText.includes(factId)`.
 *   - Auditor:  parses each result as JSON and walks the object graph for an EXACT leaf-value
 *               match. This catches the grader's specific false-positive class (a fact_id that
 *               happens to be a substring of an unrelated longer token) and is a genuinely
 *               different technique, not a relabeled rerun.
 *   - Auditor (bonus tier): when DATABASE_URL is configured, cross-checks a sample of
 *               disagreement fact_ids directly against the live `chart_facts` table — truly
 *               "DB-verifying." Degrades gracefully (same best-effort pattern as
 *               platform/scripts/answer_eval.ts's gate1 auto-hook) when no DB is reachable —
 *               the structural-walk pass alone still satisfies "independent means."
 *
 * Usage:
 *   npx tsx evals/k2/auditor.ts <transcript.json> <domain> <chart_id> [--ledger-out <dir>] [--no-write]
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import { loadAccounting, loadTranscript, bareToolName, REPO_ROOT, lenientParseJson } from './transcript_utils.js'
import { scoreConceptHits, type ConceptHitResult } from './consumption_grader.js'
import type { AccountingRow, NormalizedTranscript, TranscriptCall } from './types.js'

// ─────────────────────────────────────────────────────────────────────────────
// Independent structural-walk pass
// ─────────────────────────────────────────────────────────────────────────────

/** Recursively collects every string leaf value out of a parsed JSON structure. */
function collectStringLeaves(node: unknown, out: Set<string>, depth = 0): void {
  if (depth > 64) return // guard against pathological cyclic-looking structures
  if (typeof node === 'string') {
    out.add(node)
    return
  }
  if (Array.isArray(node)) {
    for (const item of node) collectStringLeaves(item, out, depth + 1)
    return
  }
  if (node && typeof node === 'object') {
    for (const v of Object.values(node as Record<string, unknown>)) collectStringLeaves(v, out, depth + 1)
  }
}

export interface AuditRow {
  concept_id: string
  grader_hit: boolean
  grader_reason: ConceptHitResult['reason']
  auditor_hit: boolean
  auditor_method: 'exact_leaf_match' | 'exact_leaf_match_fallback_substring' | 'no_evidence_on_record'
  agree: boolean
}

/** Independent second pass: exact structural match rather than the grader's substring search. */
export function auditConceptHits(
  rows: AccountingRow[],
  transcript: NormalizedTranscript,
  graderResults: ConceptHitResult[],
): AuditRow[] {
  const byTool = new Map<string, string[]>() // bare tool -> raw result strings (one per call)
  for (const c of transcript.calls) {
    const bare = bareToolName(c.tool)
    const arr = byTool.get(bare) ?? []
    arr.push(c.result_raw ?? '')
    byTool.set(bare, arr)
  }
  // Pre-parse each tool's raw results into leaf-string sets (once per tool, not per concept).
  const leafSetByTool = new Map<string, Set<string>>()
  const fallbackTextByTool = new Map<string, string>()
  for (const [tool, texts] of byTool) {
    const leaves = new Set<string>()
    let anyParsed = false
    for (const text of texts) {
      try {
        const parsed = lenientParseJson<unknown>(text)
        collectStringLeaves(parsed, leaves)
        anyParsed = true
      } catch {
        // not JSON — leave for the fallback path below
      }
    }
    if (anyParsed) leafSetByTool.set(tool, leaves)
    fallbackTextByTool.set(tool, texts.join('\n'))
  }

  const graderByConceptId = new Map(graderResults.map((r) => [r.concept_id, r]))

  return rows.map((row): AuditRow => {
    const grader = graderByConceptId.get(row.concept_id)
    const tool = row.evidence?.tool ? bareToolName(row.evidence.tool) : undefined
    const factIds = row.evidence?.fact_ids ?? []

    if (!tool || factIds.length === 0) {
      return {
        concept_id: row.concept_id,
        grader_hit: grader?.hit ?? false,
        grader_reason: grader?.reason ?? 'no_evidence_on_record',
        auditor_hit: false,
        auditor_method: 'no_evidence_on_record',
        agree: (grader?.hit ?? false) === false,
      }
    }

    const leaves = leafSetByTool.get(tool)
    let auditorHit: boolean
    let method: AuditRow['auditor_method']
    if (leaves) {
      auditorHit = factIds.some((fid) => leaves.has(fid))
      method = 'exact_leaf_match'
    } else {
      // No calls to this tool parsed as JSON (either never called, or non-JSON payload) — fall
      // back to substring search ONLY as a last resort, explicitly labeled as such so a reader
      // never mistakes this row for the strict exact-match pass.
      const text = fallbackTextByTool.get(tool) ?? ''
      auditorHit = factIds.some((fid) => text.includes(fid))
      method = 'exact_leaf_match_fallback_substring'
    }

    const graderHit = grader?.hit ?? false
    return {
      concept_id: row.concept_id,
      grader_hit: graderHit,
      grader_reason: grader?.reason ?? 'no_evidence_on_record',
      auditor_hit: auditorHit,
      auditor_method: method,
      agree: graderHit === auditorHit,
    }
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Bonus tier: live DB cross-check (best-effort, degrades gracefully)
// ─────────────────────────────────────────────────────────────────────────────

export interface DbCheckResult {
  status: 'confirmed' | 'contradicted' | 'skipped_no_database_url' | 'skipped_no_pg_module' | 'skipped_query_error'
  detail?: string
}

/**
 * Cross-checks a sample of disagreement fact_ids directly against the live `chart_facts` table.
 * This is the "DB-verifying" half of EL-10's "grader + DB-verifying auditor" language, kept
 * strictly best-effort (same degrade-gracefully pattern as answer_eval.ts's gate1 auto-hook) —
 * a sandboxed/offline run still produces a complete, LAW-compliant two-pass result via the
 * structural-walk pass alone; the DB tier only adds confidence when reachable.
 */
export async function dbVerifySample(
  factIds: string[],
  chartId: string,
  sampleSize = 25,
): Promise<Record<string, DbCheckResult>> {
  const out: Record<string, DbCheckResult> = {}
  const sample = factIds.slice(0, sampleSize)
  if (sample.length === 0) return out

  if (!process.env.DATABASE_URL) {
    for (const fid of sample) out[fid] = { status: 'skipped_no_database_url' }
    return out
  }

  let PoolCtor: typeof import('pg').Pool
  try {
    // Dynamic import so evals/k2 has zero hard dependency on `pg` being installed — the two-pass
    // law's structural-walk tier works with no external packages at all.
    const pg = await import('pg')
    PoolCtor = pg.Pool
  } catch {
    for (const fid of sample) out[fid] = { status: 'skipped_no_pg_module' }
    return out
  }

  const pool = new PoolCtor({ connectionString: process.env.DATABASE_URL, max: 2 })
  try {
    const res = await pool.query(
      'SELECT fact_id FROM chart_facts WHERE chart_id = $1 AND fact_id = ANY($2::text[])',
      [chartId, sample],
    )
    const confirmedSet = new Set((res.rows as Array<{ fact_id: string }>).map((r) => r.fact_id))
    for (const fid of sample) {
      out[fid] = confirmedSet.has(fid)
        ? { status: 'confirmed' }
        : { status: 'contradicted', detail: 'fact_id not found in chart_facts for this chart_id' }
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    for (const fid of sample) out[fid] = { status: 'skipped_query_error', detail: msg.slice(0, 200) }
  } finally {
    await pool.end().catch(() => {})
  }
  return out
}

// ─────────────────────────────────────────────────────────────────────────────
// Two-pass result + disagreement ledger
// ─────────────────────────────────────────────────────────────────────────────

export interface DisagreementEntry {
  concept_id: string
  grader_verdict: boolean
  grader_reason: string
  auditor_verdict: boolean
  auditor_method: string
  db_check?: DbCheckResult
  resolution: 'UNRESOLVED_LOGGED'
  resolved_by: null
  resolved_at: null
}

export interface TwoPassResult {
  two_pass_complete: true
  domain: string
  chart_id: string
  generated_at: string
  total_concepts_assessed: number
  agreements: number
  disagreements_count: number
  audit_overturn_rate: number
  disagreement_ledger: DisagreementEntry[]
  db_check_tier: 'ran' | 'skipped'
}

export async function runTwoPass(
  domain: string,
  chartId: string,
  transcript: NormalizedTranscript,
): Promise<TwoPassResult> {
  const accounting = loadAccounting(domain, chartId)
  const servable = accounting.rows.filter((r) => r.state === 'served')
  const graderResults = scoreConceptHits(servable, transcript)
  const auditRows = auditConceptHits(servable, transcript, graderResults)

  const disagreementRows = auditRows.filter((r) => !r.agree)
  const disagreementFactIds = disagreementRows
    .map((r) => servable.find((s) => s.concept_id === r.concept_id)?.evidence?.fact_ids?.[0])
    .filter((x): x is string => Boolean(x))
  const dbChecks = await dbVerifySample(disagreementFactIds, chartId)
  const dbTierRan = Object.values(dbChecks).some((c) => c.status === 'confirmed' || c.status === 'contradicted')

  const ledger: DisagreementEntry[] = disagreementRows.map((r) => {
    const row = servable.find((s) => s.concept_id === r.concept_id)
    const fid = row?.evidence?.fact_ids?.[0]
    return {
      concept_id: r.concept_id,
      grader_verdict: r.grader_hit,
      grader_reason: r.grader_reason,
      auditor_verdict: r.auditor_hit,
      auditor_method: r.auditor_method,
      db_check: fid ? dbChecks[fid] : undefined,
      resolution: 'UNRESOLVED_LOGGED',
      resolved_by: null,
      resolved_at: null,
    }
  })

  return {
    two_pass_complete: true,
    domain,
    chart_id: chartId,
    generated_at: new Date().toISOString(),
    total_concepts_assessed: auditRows.length,
    agreements: auditRows.length - disagreementRows.length,
    disagreements_count: disagreementRows.length,
    audit_overturn_rate: auditRows.length > 0 ? disagreementRows.length / auditRows.length : 0,
    disagreement_ledger: ledger,
    db_check_tier: dbTierRan ? 'ran' : 'skipped',
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  void (async () => {
    const [transcriptPath, domain, chartId, ...rest] = process.argv.slice(2)
    if (!transcriptPath || !domain || !chartId) {
      console.error(
        'Usage: npx tsx evals/k2/auditor.ts <transcript.json> <domain> <chart_id> [--ledger-out <dir>] [--no-write]',
      )
      process.exit(1)
    }
    const transcript = loadTranscript(transcriptPath)
    const result = await runTwoPass(domain, chartId, transcript)

    // Print a summary first (full ledger can be long on real runs).
    console.log(
      JSON.stringify(
        {
          ...result,
          disagreement_ledger: `${result.disagreement_ledger.length} entries (see written ledger file / pass --verbose)`,
        },
        null,
        2,
      ),
    )
    if (process.argv.includes('--verbose')) {
      console.log('\nFull disagreement ledger:')
      console.log(JSON.stringify(result.disagreement_ledger, null, 2))
    }

    if (!process.argv.includes('--no-write')) {
      const outFlagIdx = rest.indexOf('--ledger-out')
      const outDir = outFlagIdx >= 0 ? rest[outFlagIdx + 1] : join(REPO_ROOT, 'evals/k2/disagreement_ledger')
      if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true })
      const chart8 = chartId.slice(0, 8)
      const ts = result.generated_at.replace(/[:.]/g, '-')
      const outPath = join(outDir, `${domain}_${chart8}_${ts}.json`)
      writeFileSync(outPath, JSON.stringify(result, null, 2))
      console.log(`\nLAW-compliant two-pass ledger written: ${outPath}`)
    }

    console.log(
      `\naudit_overturn_rate: ${(result.audit_overturn_rate * 100).toFixed(2)}%  ` +
        `(EL-10 baseline to compare against: ~22%)`,
    )
  })()
}
