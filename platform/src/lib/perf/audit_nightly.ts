/**
 * audit_nightly.ts — Operator-side nightly audit job.
 *
 * Runs at 03:00 UTC via Cloud Run scheduler. Examines the last 24h of
 * tool_execution_log rows. Applies 6 heuristic checks to each row.
 * Opens mcp_audit_findings rows for violations. NO LLM calls.
 *
 * 6 audit checks (per perf brief §5.1):
 *   1. citation_presence     — non-factual responses must have ≥1 citation
 *   2. numerical_grounding   — numerical claims should reference L1 data
 *   3. forward_looking_logged — forward-looking responses should have a prediction logged
 *   4. sanskrit_glossing     — client-tier responses must gloss Sanskrit terms
 *   5. layer_attribution     — L1 facts and L2.5 signals must be correctly attributed
 *   6. non_factual_shape     — non-factual responses must be ≥3 sentences + citation
 *
 * CRITICAL: No LLM calls in this file or in any heuristic it imports.
 * Verification: grep -rn "openai\|anthropic\|gemini" platform/src/lib/perf/heuristics/ must return nothing.
 *
 * MCPT v3.1.0-S4
 */

import { extractCitations, hasCitation } from './heuristics/extract_citations'
import { hasNumericalClaims } from './heuristics/extract_numerical_claims'
import { isForwardLooking, extractForwardLookingPhrases } from './heuristics/forward_looking'
import { checkSanskritGlossing } from './heuristics/sanskrit_glossing'
import { detectLayerMixing } from './heuristics/layer_attribution'
import { isNonFactualResponse, meetsNonFactualShape } from './heuristics/is_non_factual'

// ── DB client interface ────────────────────────────────────────────────────────
// We use a minimal fetch-based DB client to avoid server-only/edge runtime issues
// in the test environment. Production uses the existing @/lib/db/client.
// Note: env vars are read at call time (not module load) to support test stubbing.

async function dbQuery(sql: string, params?: unknown[]): Promise<unknown[]> {
  const DB_URL = process.env['SUPABASE_URL'] ?? ''
  const DB_SERVICE_KEY = process.env['SUPABASE_SERVICE_ROLE_KEY'] ?? ''

  if (!DB_URL || !DB_SERVICE_KEY) {
    console.warn('[audit:nightly] DB credentials not set; skipping DB operations.')
    return []
  }

  const response = await fetch(`${DB_URL}/rest/v1/rpc/exec_sql`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': DB_SERVICE_KEY,
      'Authorization': `Bearer ${DB_SERVICE_KEY}`,
    },
    body: JSON.stringify({ sql, params }),
  })

  if (!response.ok) return []
  return (await response.json()) as unknown[]
}

// ── Audit finding types ────────────────────────────────────────────────────────

type CheckClass =
  | 'citation_presence'
  | 'numerical_grounding'
  | 'forward_looking_logged'
  | 'sanskrit_glossing'
  | 'layer_attribution'
  | 'non_factual_shape'

interface AuditFinding {
  trace_id: string
  tool_name: string
  check_class: CheckClass
  severity: 'warn' | 'error'
  description: string
  evidence: Record<string, unknown>
}

// ── Log row type ───────────────────────────────────────────────────────────────

export interface ToolExecutionRow {
  id: string
  trace_id: string
  tool_name: string
  audience_tier: string
  response_text: string | null
  status: string
}

// ── The 6 audit checks ────────────────────────────────────────────────────────

/** Exported for unit testing — runs the 6 heuristic checks on a single row. */
export function runAuditChecks(row: ToolExecutionRow): AuditFinding[] {
  const findings: AuditFinding[] = []
  const { trace_id, tool_name, audience_tier, response_text } = row

  if (!response_text) return findings

  const isNonFactual = isNonFactualResponse(response_text, tool_name)

  // Check 1: citation_presence
  // Non-factual responses must have ≥1 citation
  if (isNonFactual && !hasCitation(response_text)) {
    findings.push({
      trace_id,
      tool_name,
      check_class: 'citation_presence',
      severity: 'warn',
      description: 'Non-factual response contains no citation references (SIG.MSR.NNN, [^N], LEL.E.NNN, FORENSIC.§N)',
      evidence: {
        response_length: response_text.length,
        citations_found: [],
        is_non_factual: true,
      },
    })
  }

  // Check 2: numerical_grounding
  // Numerical claims should be present for responses about strengths/positions
  // (This check is advisory — flags absence of numerical claims in responses that discuss positions)
  const NUMERICAL_TOOL_NAMES = ['query_chart_facts', 'ask_madhav']
  if (NUMERICAL_TOOL_NAMES.includes(tool_name) && isNonFactual) {
    // We flag if the response talks about positions/strength but has no numerical values
    const mentionsStrength = /shadbala|virupa|degree|strength|position/i.test(response_text)
    const hasNumerical = hasNumericalClaims(response_text)
    if (mentionsStrength && !hasNumerical) {
      findings.push({
        trace_id,
        tool_name,
        check_class: 'numerical_grounding',
        severity: 'warn',
        description: 'Response discusses strength/position but contains no numerical values (degrees, virupa, etc.)',
        evidence: { mentions_strength: true, numerical_claims_count: 0 },
      })
    }
  }

  // Check 3: forward_looking_logged
  // Forward-looking responses should have PPL log (we can't verify PPL from text alone;
  // we flag the response for operator review)
  if (isForwardLooking(response_text)) {
    const phrases = extractForwardLookingPhrases(response_text)
    findings.push({
      trace_id,
      tool_name,
      check_class: 'forward_looking_logged',
      severity: 'warn',
      description: 'Response contains forward-looking language. Verify that log_prediction was called for each prospective claim.',
      evidence: {
        forward_looking_phrases: phrases.slice(0, 3),
        phrase_count: phrases.length,
      },
    })
  }

  // Check 4: sanskrit_glossing
  // Client-tier responses must gloss Sanskrit terms in English
  if (audience_tier === 'client') {
    const glossingResult = checkSanskritGlossing(response_text, 'client')
    if (!glossingResult.compliant) {
      findings.push({
        trace_id,
        tool_name,
        check_class: 'sanskrit_glossing',
        severity: 'warn',
        description: `Client-tier response contains unglossed Sanskrit terms: ${glossingResult.violations.join(', ')}`,
        evidence: {
          violations: glossingResult.violations,
          glossed: glossingResult.glossed,
        },
      })
    }
  }

  // Check 5: layer_attribution
  // L2.5 interpretive claims must have citations; detect mixing
  if (isNonFactual) {
    const mixingInstances = detectLayerMixing(response_text)
    if (mixingInstances.length > 0) {
      findings.push({
        trace_id,
        tool_name,
        check_class: 'layer_attribution',
        severity: 'warn',
        description: `Response contains ${mixingInstances.length} potential L1/L2.5 mixing instance(s): interpretive claims without citation`,
        evidence: {
          mixing_instances: mixingInstances.slice(0, 3),
          total_instances: mixingInstances.length,
        },
      })
    }
  }

  // Check 6: non_factual_shape
  // Non-factual responses must be ≥3 sentences + have ≥1 citation
  if (isNonFactual && !meetsNonFactualShape(response_text)) {
    const citations = extractCitations(response_text)
    const sentenceCount = (response_text.match(/[.!?]+/g) ?? []).length
    findings.push({
      trace_id,
      tool_name,
      check_class: 'non_factual_shape',
      severity: 'warn',
      description: `Non-factual response does not meet shape requirements: ${sentenceCount} sentences, ${citations.length} citation(s). Minimum: 3 sentences + 1 citation.`,
      evidence: { sentence_count: sentenceCount, citation_count: citations.length },
    })
  }

  return findings
}

// ── Job config ────────────────────────────────────────────────────────────────

export interface AuditJobConfig {
  lookback_hours?: number       // default: 24
  dry_run?: boolean             // if true: run checks but don't write findings
  max_rows?: number             // default: 500
}

export interface AuditJobResult {
  status: 'complete' | 'failed'
  traces_examined: number
  findings_opened: number
  findings_by_class: Record<CheckClass, number>
  errors: string[]
  dry_run: boolean
}

// ── Main job ───────────────────────────────────────────────────────────────────

/**
 * Run the nightly audit job.
 *
 * INVARIANT: No LLM calls. All checks are heuristic (regex/keyword only).
 * Verify: grep -rn "openai\|anthropic\|gemini" platform/src/lib/perf/heuristics/
 */
export async function runNightlyAudit(config: AuditJobConfig = {}): Promise<AuditJobResult> {
  const lookback_hours = config.lookback_hours ?? 24
  const dry_run = config.dry_run ?? false
  const max_rows = config.max_rows ?? 500

  const result: AuditJobResult = {
    status: 'complete',
    traces_examined: 0,
    findings_opened: 0,
    findings_by_class: {
      citation_presence: 0,
      numerical_grounding: 0,
      forward_looking_logged: 0,
      sanskrit_glossing: 0,
      layer_attribution: 0,
      non_factual_shape: 0,
    },
    errors: [],
    dry_run,
  }

  try {
    // Fetch un-audited rows from the last N hours
    const rows = await dbQuery(`
      SELECT id, trace_id, tool_name, audience_tier, response_text, status
      FROM tool_execution_log
      WHERE created_at > NOW() - INTERVAL '${lookback_hours} hours'
        AND status = 'ok'
        AND response_text IS NOT NULL
        AND (audit_flagged IS NULL OR audit_flagged = false)
      ORDER BY created_at DESC
      LIMIT ${max_rows}
    `) as ToolExecutionRow[]

    result.traces_examined = rows.length

    const allFindings: AuditFinding[] = []

    for (const row of rows) {
      const findings = runAuditChecks(row)
      allFindings.push(...findings)
    }

    result.findings_opened = allFindings.length
    for (const f of allFindings) {
      result.findings_by_class[f.check_class]++
    }

    if (!dry_run && allFindings.length > 0) {
      // Write findings to mcp_audit_findings
      for (const finding of allFindings) {
        await dbQuery(`
          INSERT INTO mcp_audit_findings (trace_id, tool_name, check_class, severity, description, evidence)
          VALUES ($1, $2, $3, $4, $5, $6)
        `, [
          finding.trace_id,
          finding.tool_name,
          finding.check_class,
          finding.severity,
          finding.description,
          JSON.stringify(finding.evidence),
        ])
      }

      // Mark rows as audited
      const traceIds = [...new Set(rows.map(r => r.trace_id))]
      if (traceIds.length > 0) {
        await dbQuery(`
          UPDATE tool_execution_log
          SET audit_flagged = true
          WHERE trace_id = ANY($1)
        `, [traceIds])
      }
    }

  } catch (err) {
    result.status = 'failed'
    result.errors.push(err instanceof Error ? err.message : String(err))
  }

  return result
}

/**
 * Cron entry point for Cloud Run scheduler.
 * Expected to be called at 03:00 UTC.
 */
export async function auditCronHandler(): Promise<void> {
  console.log('[audit:nightly] Starting nightly audit job')
  const started_at = new Date().toISOString()

  const result = await runNightlyAudit({ lookback_hours: 24, dry_run: false })

  console.log('[audit:nightly] Completed', {
    started_at,
    completed_at: new Date().toISOString(),
    status: result.status,
    traces_examined: result.traces_examined,
    findings_opened: result.findings_opened,
    findings_by_class: result.findings_by_class,
  })
}
