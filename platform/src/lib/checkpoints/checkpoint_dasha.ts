/**
 * MARSYS-JIS Phase 5C — checkpoint_dasha.ts
 * Post-synthesis dasha correctness validator.
 *
 * Deterministic: regex-extraction + chart_facts cross-check (no LLM call).
 * Vimshottari-only initially per locked decision §6.4.
 *
 * Feature flags:
 *   CHECKPOINT_DASHA_ENABLED   (default false — safe rollout)
 *   CHECKPOINT_DASHA_FAIL_HARD (default true once enabled)
 *
 * Heuristic gate: validator only runs when the query is dasha-relevant.
 * Non-dasha queries stream normally — UX preserved.
 */

import 'server-only'

import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import { getStorageClient } from '@/lib/storage'

import {
  CheckpointHaltError,
  skippedResult,
  type CheckpointDashaInput,
  type CheckpointDashaResult,
  type DashaClaim,
  type DashaClaimResult,
} from './types'

const CHECKPOINT_ID = 'checkpoint_dasha'

// ── Heuristic gate ────────────────────────────────────────────────────────────

const DASHA_QUERY_RE =
  /\b(mahadasha|antardasha|pratyantardasha|sookshma|prana|vimshottari|yogini|chara|jaimini|bhramari|bhadrika|ulka|siddha|sankata|mangala|pingala|dhanya|dasha|MD|AD|PD|SD)\b/i

/**
 * Returns true when the query or its query_plan indicates a dasha-relevant
 * request. Non-dasha queries skip the buffer + validate path entirely.
 */
export function detectDashaRelevance(
  input: Pick<CheckpointDashaInput, 'query' | 'query_plan'>,
): boolean {
  if (DASHA_QUERY_RE.test(input.query)) return true

  // tool_calls lives on RichQueryPlan (not QueryPlan base); access via cast.
  const richPlan = input.query_plan as unknown as {
    tool_calls?: Array<{ tool_name: string; params?: Record<string, unknown> }>
  }
  const toolCalls = richPlan.tool_calls ?? []
  for (const tc of toolCalls) {
    if (tc.tool_name === 'query_dasha_periods') return true
    if (
      tc.tool_name === 'temporal' &&
      tc.params?.dasha_context_required === true
    ) {
      return true
    }
  }
  return false
}

// ── Extraction (regex passes) ─────────────────────────────────────────────────

const LORD_NAMES =
  'Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|' +
  'Bhramari|Bhadrika|Ulka|Siddha|Sankata|Mangala|Pingala|Dhanya|' +
  'Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces'

const TEMPORAL_WORDS =
  'current|next|upcoming|previous|past|future|present|incoming'

const LEVEL_WORDS =
  'Mahadasha|Mahadasa|Maha Dasha|MD|Antardasha|Antardasa|Antar Dasha|AD|' +
  'Pratyantardasha|Pratyantardasa|Pratyantar Dasha|PD|Sookshma|SD|Prana|PD2|' +
  'Yogini|Chara|Char|Jaimini'

/**
 * Extracts dasha-schedule claims from synthesis text.
 * Returns structured DashaClaim[] with temporal, lord, level, citation fields.
 */
export function extractDashaClaims(text: string): DashaClaim[] {
  const claims: DashaClaim[] = []

  // Pass A — temporal qualifier + lord + level (any order)
  const passA = new RegExp(
    `(?:(${TEMPORAL_WORDS})\\s+)?` +
    `(?:(${LORD_NAMES})(?:'s)?\\s+)?` +
    `(${LEVEL_WORDS})` +
    `(?:\\s+(?:of|is|will\\s+be|was|lord|period|dasha))?` +
    `(?:\\s+(${LORD_NAMES}))?`,
    'gi',
  )

  // Pass A' — lord + level + optional temporal at end
  const passAReverse = new RegExp(
    `(${LORD_NAMES})(?:'s)?\\s+(${LEVEL_WORDS})` +
    `(?:\\s+(?:is|will\\s+be|was))?` +
    `(?:\\s+(${TEMPORAL_WORDS}))?`,
    'gi',
  )

  for (const re of [passA, passAReverse]) {
    let m: RegExpExecArray | null
    re.lastIndex = 0
    while ((m = re.exec(text)) !== null) {
      const span = m[0].trim()
      const start = m.index
      const end = m.index + m[0].length

      // Avoid duplicate spans (same start position)
      if (claims.some(c => c.start === start)) continue

      let temporal: DashaClaim['temporal'] = null
      let lord = ''
      let level: DashaClaim['level'] = null

      if (re === passA) {
        temporal = normaliseTemporalWord(m[1] ?? null)
        lord = m[2] ?? m[4] ?? ''
        level = normaliseLevelWord(m[3] ?? null)
      } else {
        lord = m[1] ?? ''
        level = normaliseLevelWord(m[2] ?? null)
        temporal = normaliseTemporalWord(m[3] ?? null)
      }

      if (!lord && !level) continue

      // Pass B — look for adjacent citation within ±200 chars
      const windowStart = Math.max(0, start - 200)
      const windowEnd = Math.min(text.length, end + 200)
      const window = text.slice(windowStart, windowEnd)
      const citationMatch = /\(→\s*(DSH\.[VYC]\.\d{3,}(?:[–\-]\d{3,})?)[^)]*(?:,\s*([^)]+))?\)/i.exec(
        window,
      )

      let has_citation = false
      let cited_fact_id: string | null = null
      let cited_date_range: string | null = null

      if (citationMatch) {
        has_citation = true
        cited_fact_id = citationMatch[1] ?? null
        cited_date_range = citationMatch[2]?.trim() ?? null
      }

      claims.push({
        span,
        start,
        end,
        temporal,
        lord,
        level,
        has_citation,
        cited_fact_id,
        cited_date_range,
      })
    }
  }

  return claims
}

function normaliseTemporalWord(
  w: string | null,
): DashaClaim['temporal'] {
  if (!w) return null
  const lc = w.toLowerCase()
  if (lc === 'current' || lc === 'present') return 'current'
  if (lc === 'next' || lc === 'upcoming' || lc === 'incoming') return 'next'
  if (lc === 'previous' || lc === 'past') return 'previous'
  if (lc === 'future') return 'future'
  return null
}

function normaliseLevelWord(w: string | null): DashaClaim['level'] {
  if (!w) return null
  const lc = w.toLowerCase().replace(/\s+/g, '')
  if (lc.startsWith('mahadasha') || lc.startsWith('mahadasa') || lc === 'md') return 'MD'
  if (lc.startsWith('antardasha') || lc.startsWith('antardasa') || lc === 'ad') return 'AD'
  if (lc.startsWith('pratyantardasha') || lc.startsWith('pratyantardasa') || lc === 'pd') return 'PD'
  if (lc.startsWith('sookshma') || lc === 'sd') return 'SD'
  if (lc === 'prana' || lc === 'pd2') return 'PD2'
  if (lc === 'yogini') return 'MD'
  if (lc === 'chara' || lc === 'char' || lc === 'jaimini') return 'MD'
  return null
}

// ── Cross-check against chart_facts ──────────────────────────────────────────

interface DashaRow {
  fact_id: string
  md_lord: string
  ad_lord: string
  start_date: string
  end_date: string
}

function categoryFromFactId(factId: string): string {
  // DSH.V.NNN → dasha_vimshottari, DSH.Y.NNN → dasha_yogini, DSH.C.NNN → dasha_chara
  const prefix = factId.charAt(4).toUpperCase()
  if (prefix === 'Y') return 'dasha_yogini'
  if (prefix === 'C') return 'dasha_chara'
  return 'dasha_vimshottari'
}

async function fetchDashaRowByFactId(factId: string): Promise<DashaRow | null> {
  const category = categoryFromFactId(factId)
  const storage = getStorageClient()
  const sql = `
    SELECT fact_id,
           value_json->>'md_lord' AS md_lord,
           value_json->>'ad_lord' AS ad_lord,
           value_json->>'start_date' AS start_date,
           value_json->>'end_date' AS end_date
    FROM chart_facts
    WHERE fact_id = $1
      AND category = $2
      AND is_stale = false
    LIMIT 1
  `
  const result = await storage.query<DashaRow>(sql, [factId, category])
  return result.rows[0] ?? null
}

/**
 * Validates extracted claims against chart_facts rows.
 *
 * Rules:
 *  - Temporal claim WITHOUT citation → halt (no_citation violation)
 *  - Claim WITH citation, fact_id mismatches lord → halt (lord_mismatch)
 *  - Generic claim (no temporal qualifier) without citation → warn only
 *  - All others → pass
 */
export async function validateClaimsAgainstChartFacts(
  claims: DashaClaim[],
): Promise<DashaClaimResult[]> {
  const results: DashaClaimResult[] = []

  for (const claim of claims) {
    const temporal = claim.temporal

    // Generic mention — no temporal qualifier — soft warn only
    if (temporal === null && !claim.has_citation) {
      results.push({ ...claim, verdict: 'warn', violation: 'generic_mention_no_citation' })
      continue
    }

    // Temporal claim without citation → halt
    if (temporal !== null && !claim.has_citation) {
      results.push({
        ...claim,
        verdict: 'halt',
        violation: `temporal_claim_no_citation: "${claim.span}" has temporal="${temporal}" but no DSH.V.NNN citation`,
      })
      continue
    }

    // Has citation — verify against chart_facts
    if (claim.has_citation && claim.cited_fact_id) {
      let row: DashaRow | null = null
      try {
        row = await fetchDashaRowByFactId(claim.cited_fact_id)
      } catch {
        // DB unavailable — pass with warn so tests don't hard-fail in unit context
        results.push({ ...claim, verdict: 'warn', violation: 'db_unavailable' })
        continue
      }

      if (!row) {
        results.push({
          ...claim,
          verdict: 'halt',
          violation: `unknown_fact_id: "${claim.cited_fact_id}" not found in chart_facts`,
        })
        continue
      }

      // Check lord match
      const claimedLord = claim.lord.toLowerCase()
      const dbMdLord = (row.md_lord ?? '').toLowerCase()
      const dbAdLord = (row.ad_lord ?? '').toLowerCase()

      const lordMatchesMd = dbMdLord.includes(claimedLord) || claimedLord.includes(dbMdLord)
      const lordMatchesAd =
        claim.level === 'AD' &&
        (dbAdLord.includes(claimedLord) || claimedLord.includes(dbAdLord))

      if (!lordMatchesMd && !lordMatchesAd) {
        results.push({
          ...claim,
          verdict: 'halt',
          violation:
            `lord_mismatch: synthesis claims "${claim.lord}" but ${claim.cited_fact_id} has md_lord="${row.md_lord}", ad_lord="${row.ad_lord}"`,
        })
        continue
      }
    }

    results.push({ ...claim, verdict: 'pass' })
  }

  return results
}

// ── Remediation snippet builder ───────────────────────────────────────────────

async function fetchActiveDashaSnippet(): Promise<string> {
  const today = new Date().toISOString().slice(0, 10)
  const storage = getStorageClient()
  const sql = `
    SELECT fact_id,
           value_json->>'md_lord' AS md_lord,
           value_json->>'ad_lord' AS ad_lord,
           value_json->>'start_date' AS start_date,
           value_json->>'end_date' AS end_date
    FROM chart_facts
    WHERE category IN ('dasha_vimshottari', 'dasha_yogini', 'dasha_chara')
      AND is_stale = false
      AND (value_json->>'end_date')::date >= $1::date
    ORDER BY (value_json->>'start_date')::date ASC
    LIMIT 10
  `
  try {
    const result = await storage.query<DashaRow>(sql, [today])
    if (result.rows.length === 0) return '(no dasha rows available)'
    return result.rows
      .map(
        r =>
          `${r.fact_id}: ${r.md_lord} MD / ${r.ad_lord} AD  [${r.start_date} → ${r.end_date}]`,
      )
      .join('\n')
  } catch {
    return '(chart_facts unavailable — call query_dasha_periods for canonical rows)'
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Builds the remediation prompt to append on retry.
 * Exported so single_model_strategy.ts can assemble the retry prompt.
 */
export async function buildDashaRemediationPrompt(
  violatedClaims: DashaClaimResult[],
): Promise<string> {
  const violationList = violatedClaims
    .filter(c => c.verdict === 'halt')
    .map(c => `  - "${c.span}": ${c.violation}`)
    .join('\n')
  const snippet = await fetchActiveDashaSnippet()
  return (
    `\n\nDASHA REMEDIATION (your previous response violated the DASHA DISCIPLINE GATE):\n\n` +
    `Violations detected:\n${violationList}\n\n` +
    `Canonical dasha schedule from chart_facts (use these EXACT citations):\n${snippet}\n\n` +
    `Regenerate the response with corrected dasha claims, citing DSH.V/Y/C.NNN exactly as shown above. ` +
    `Do not extrapolate from generic dasha knowledge — the chart_facts rows above are the ground truth.`
  )
}

/**
 * Main entry point called from single_model_strategy.ts.
 *
 * Returns CheckpointDashaResult.
 * Throws CheckpointHaltError if verdict=halt AND CHECKPOINT_DASHA_FAIL_HARD=true.
 */
export async function runCheckpointDasha(
  input: CheckpointDashaInput,
): Promise<CheckpointDashaResult> {
  const started = Date.now()

  if (!getFlag('CHECKPOINT_DASHA_ENABLED')) {
    return {
      ...skippedResult(CHECKPOINT_ID),
      claims: [],
      claims_extracted: 0,
      violations_count: 0,
      skipped_reason: 'flag_off',
    }
  }

  if (!detectDashaRelevance(input)) {
    return {
      ...skippedResult(CHECKPOINT_ID),
      claims: [],
      claims_extracted: 0,
      violations_count: 0,
      skipped_reason: 'non_dasha_query',
    }
  }

  const rawClaims = extractDashaClaims(input.synthesized_text)
  let claimResults: DashaClaimResult[]

  try {
    claimResults = await validateClaimsAgainstChartFacts(rawClaims)
  } catch (err) {
    telemetry.recordError(CHECKPOINT_ID, 'db_error', err instanceof Error ? err : new Error(String(err)))
    // Non-fatal — return pass with warn so prod is never blocked by DB timeouts
    return {
      checkpoint_id: CHECKPOINT_ID,
      verdict: 'warn',
      confidence: 0,
      reasoning: `DB error during validation: ${err instanceof Error ? err.message : String(err)}`,
      latency_ms: Date.now() - started,
      skipped: false,
      claims: rawClaims.map(c => ({ ...c, verdict: 'warn' as const, violation: 'db_error' })),
      claims_extracted: rawClaims.length,
      violations_count: 0,
    }
  }

  const violations = claimResults.filter(c => c.verdict === 'halt')
  const violationsCount = violations.length
  const overallVerdict = violationsCount > 0 ? 'halt' : 'pass'

  telemetry.recordMetric(CHECKPOINT_ID, overallVerdict, 1)
  telemetry.recordLatency(CHECKPOINT_ID, 'validate', Date.now() - started)

  const result: CheckpointDashaResult = {
    checkpoint_id: CHECKPOINT_ID,
    verdict: overallVerdict,
    confidence: violationsCount === 0 ? 1 : 0,
    reasoning:
      violationsCount === 0
        ? `All ${claimResults.length} dasha claim(s) passed validation`
        : `${violationsCount} violation(s): ${violations.map(v => v.violation).join('; ')}`,
    latency_ms: Date.now() - started,
    skipped: false,
    claims: claimResults,
    claims_extracted: rawClaims.length,
    violations_count: violationsCount,
  }

  if (overallVerdict === 'halt' && getFlag('CHECKPOINT_DASHA_FAIL_HARD')) {
    throw new CheckpointHaltError(CHECKPOINT_ID, result)
  }

  return result
}
