/**
 * Tool 28: convergence_score_lookup
 * Full implementation M9-D-S1 (2026-05-14). Replaces M9-A stub.
 *
 * Returns convergence_scores rows for requested domains.
 * Used by synthesis stage to append inter-school convergence context to domain answers.
 *
 * Falls back to JSON file when DB unavailable (proxy/connection issue per M9-C deferred AC.M9C.2).
 */

import 'server-only'
import { query } from '@/lib/db/client'

export interface ConvergenceScoreLookupInput {
  domains: string[]  // e.g. ['CAREER', 'HEALTH']
}

export interface ConvergenceScoreRow {
  domain: string
  schools_agreeing: number
  schools_total: number                    // 7 normally; 6 if Tajika [VARSHA_KUNDALI_PENDING]
  convergence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  mean_domain_score: number
  std_domain_score: number
  direction: 'positive' | 'negative' | 'neutral' | 'mixed'
  per_school_scores: Record<string, number | null>
  convergence_narrative: string | null
  computed_at: string                      // ISO 8601
}

export interface ConvergenceScoreLookupOutput {
  domains_requested: string[]
  convergence_scores: ConvergenceScoreRow[]
  summary: {
    high_convergence_domains: string[]
    medium_convergence_domains: string[]
    low_convergence_domains: string[]
    overall_agreement_signal: string
  }
}

interface ConvergenceRow {
  domain: string
  schools_agreeing: string
  schools_total: string
  convergence_level: string
  mean_domain_score: string
  std_domain_score: string
  direction: string
  per_school_scores: Record<string, number | null>
  convergence_narrative: string | null
  computed_at: string
}

function buildSummary(scores: ConvergenceScoreRow[]): ConvergenceScoreLookupOutput['summary'] {
  const high = scores.filter(s => s.convergence_level === 'HIGH').map(s => s.domain)
  const medium = scores.filter(s => s.convergence_level === 'MEDIUM').map(s => s.domain)
  const low = scores.filter(s => s.convergence_level === 'LOW').map(s => s.domain)

  let signal: string
  if (high.length === scores.length) {
    signal = `ALL ${scores.length} domains HIGH — strongest possible inter-school agreement`
  } else if (high.length > 0 && low.length === 0) {
    signal = `${high.length}/${scores.length} HIGH, ${medium.length}/${scores.length} MEDIUM — strong agreement`
  } else if (low.length > 0) {
    signal = `${low.length}/${scores.length} LOW convergence domains — mixed inter-school agreement`
  } else {
    signal = `Mixed convergence: ${high.length} HIGH / ${medium.length} MEDIUM / ${low.length} LOW`
  }

  return {
    high_convergence_domains: high,
    medium_convergence_domains: medium,
    low_convergence_domains: low,
    overall_agreement_signal: signal,
  }
}

async function lookupFromDB(domains: string[]): Promise<ConvergenceScoreRow[]> {
  const sql = `
    SELECT
      domain,
      schools_agreeing,
      schools_total,
      convergence_level,
      mean_domain_score,
      std_domain_score,
      direction,
      per_school_scores,
      convergence_narrative,
      computed_at
    FROM convergence_scores
    WHERE domain = ANY($1::text[])
    ORDER BY domain
  `
  const { rows } = await query<ConvergenceRow>(sql, [domains])
  return rows.map(row => ({
    domain: row.domain,
    schools_agreeing: Number(row.schools_agreeing),
    schools_total: Number(row.schools_total),
    convergence_level: row.convergence_level as ConvergenceScoreRow['convergence_level'],
    mean_domain_score: Number(row.mean_domain_score),
    std_domain_score: Number(row.std_domain_score),
    direction: row.direction as ConvergenceScoreRow['direction'],
    per_school_scores: row.per_school_scores ?? {},
    convergence_narrative: row.convergence_narrative,
    computed_at: row.computed_at,
  }))
}

async function lookupFromJSON(domains: string[]): Promise<ConvergenceScoreRow[]> {
  const path = require('path')
  const fs = require('fs')
  const jsonPath = path.resolve(
    process.cwd(),
    '09_MULTI_SCHOOL_TRIANGULATION/convergence/convergence_scores.json'
  )
  if (!fs.existsSync(jsonPath)) {
    return []
  }
  const raw = JSON.parse(fs.readFileSync(jsonPath, 'utf8'))
  const scores: ConvergenceScoreRow[] = (raw.scores ?? [])
    .filter((s: { domain: string }) => domains.includes(s.domain))
    .map((s: {
      domain: string
      schools_agreeing: number
      schools_total: number
      convergence_level: string
      mean_domain_score: number
      std_domain_score: number
      direction: string
      per_school_scores: Record<string, number | null>
      convergence_narrative: string | null
      computed_at: string
    }) => ({
      domain: s.domain,
      schools_agreeing: s.schools_agreeing,
      schools_total: s.schools_total,
      convergence_level: s.convergence_level as ConvergenceScoreRow['convergence_level'],
      mean_domain_score: s.mean_domain_score,
      std_domain_score: s.std_domain_score,
      direction: s.direction as ConvergenceScoreRow['direction'],
      per_school_scores: s.per_school_scores ?? {},
      convergence_narrative: s.convergence_narrative,
      computed_at: s.computed_at,
    }))
  return scores
}

export async function convergence_score_lookup(
  input: ConvergenceScoreLookupInput
): Promise<ConvergenceScoreLookupOutput> {
  const { domains } = input

  if (domains.length === 0) {
    return {
      domains_requested: [],
      convergence_scores: [],
      summary: {
        high_convergence_domains: [],
        medium_convergence_domains: [],
        low_convergence_domains: [],
        overall_agreement_signal: 'No domains requested',
      },
    }
  }

  let scores: ConvergenceScoreRow[]
  try {
    scores = await lookupFromDB(domains)
    if (scores.length === 0) {
      scores = await lookupFromJSON(domains)
    }
  } catch {
    scores = await lookupFromJSON(domains)
  }

  return {
    domains_requested: domains,
    convergence_scores: scores,
    summary: buildSummary(scores),
  }
}
