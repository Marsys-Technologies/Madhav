/**
 * INF7-S2: Cross-Ayanamsha Consensus Tool
 * cross_ayanamsha_consensus(chart_id, topic, ayanamshas?) → ConsensusResult
 *
 * Identifies which chart facts are stable across ayanamshas (consensus) and
 * which diverge significantly (divergence). Used by the agentic loop to
 * surface cross-system confidence before synthesis.
 *
 * [BUILD-ORCH-J-07] INF7-S2
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ConsensusPoint {
  fact_category: string
  fact_subject: string
  fact_key: string
  agreed_value: string
  ayanamsha_count: number
}

export interface DivergencePoint {
  fact_category: string
  fact_subject: string
  fact_key: string
  values_by_ayanamsha: Record<string, string>
  max_delta_deg: number | null
}

export interface AyanamshaBreakdownEntry {
  ayanamsha_id: string
  total_facts: number
  facts_in_consensus: number
  facts_diverging: number
}

export interface ConsensusResult {
  chart_id: string
  topic: string
  ayanamshas_queried: string[]
  consensus_points: ConsensusPoint[]
  divergence_points: DivergencePoint[]
  ayanamsha_breakdown: AyanamshaBreakdownEntry[]
  overall_divergence_score: number | null
  generated_at: string
}

// ── Constants ─────────────────────────────────────────────────────────────────

const DIVERGENCE_DEG_THRESHOLD = 1.0

const TOPIC_CATEGORY_MAP: Record<string, string[]> = {
  planets: ['planet_positions', 'planet'],
  houses: ['house_positions', 'house'],
  dasha: ['dasha_vimshottari', 'dasha_chara'],
  yogas: ['yoga_', 'yoga'],
  panchanga: ['panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra'],
  sensitive_points: ['sensitive_points', 'sensitive_point'],
  all: [],
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function cross_ayanamsha_consensus(
  chart_id: string,
  topic: string,
  ayanamshas?: string[],
): Promise<ConsensusResult> {
  const now = new Date().toISOString()
  const targetAyas = ayanamshas ?? (await getChartAyanamshas(chart_id))

  if (targetAyas.length < 2) {
    return emptyResult(chart_id, topic, targetAyas, now)
  }

  const [factRows, reportRows] = await Promise.all([
    fetchFactsForTopic(chart_id, topic, targetAyas),
    fetchReports(chart_id),
  ])

  const { consensus_points, divergence_points } = classifyFacts(factRows, targetAyas)
  const ayanamsha_breakdown = buildBreakdown(targetAyas, factRows, consensus_points, divergence_points)
  const overall_divergence_score = computeOverallScore(reportRows, targetAyas)

  return {
    chart_id,
    topic,
    ayanamshas_queried: targetAyas,
    consensus_points,
    divergence_points,
    ayanamsha_breakdown,
    overall_divergence_score,
    generated_at: now,
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function getChartAyanamshas(chart_id: string): Promise<string[]> {
  try {
    const { rows } = await query<{ ayanamsha_id: string }>(
      `SELECT DISTINCT ayanamsha_id FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id != 'INVARIANT' AND is_stale = false
        LIMIT 10`,
      [chart_id],
    )
    return rows.map((r) => r.ayanamsha_id)
  } catch {
    return ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']
  }
}

interface FactRow {
  fact_category: string
  fact_subject: string
  fact_key: string
  ayanamsha_id: string
  fact_value_text: string | null
  fact_value_num: number | null
}

async function fetchFactsForTopic(
  chart_id: string,
  topic: string,
  ayanamshas: string[],
): Promise<FactRow[]> {
  const cats = TOPIC_CATEGORY_MAP[topic] ?? TOPIC_CATEGORY_MAP['all']!

  let whereExtra = ''
  const params: unknown[] = [chart_id, [...ayanamshas, 'INVARIANT']]

  if (cats.length > 0) {
    const conditions = cats.map((_, i) => `fact_category LIKE $${i + 3}`).join(' OR ')
    whereExtra = `AND (${conditions})`
    params.push(...cats.map((c) => `${c}%`))
  }

  const { rows } = await query<FactRow>(
    `SELECT fact_category, fact_subject, fact_key, ayanamsha_id,
            fact_value_text, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1
        AND (ayanamsha_id = ANY($2::text[]))
        AND is_stale = false
        ${whereExtra}
      LIMIT 1000`,
    params,
  )
  return rows
}

interface ReportRow {
  ayanamsha_id_1: string
  ayanamsha_id_2: string
  divergence_score: number | null
}

async function fetchReports(chart_id: string): Promise<ReportRow[]> {
  try {
    const { rows } = await query<ReportRow>(
      `SELECT ayanamsha_id_1, ayanamsha_id_2, divergence_score
         FROM chart_ayanamsha_reports
        WHERE chart_id = $1`,
      [chart_id],
    )
    return rows
  } catch {
    return []
  }
}

function classifyFacts(
  rows: FactRow[],
  ayanamshas: string[],
): { consensus_points: ConsensusPoint[]; divergence_points: DivergencePoint[] } {
  // Group rows by (fact_category, fact_subject, fact_key)
  const map = new Map<string, Map<string, string>>()

  for (const r of rows) {
    if (r.ayanamsha_id === 'INVARIANT') continue
    const key = `${r.fact_category}||${r.fact_subject}||${r.fact_key}`
    if (!map.has(key)) map.set(key, new Map())
    const val = r.fact_value_text ?? (r.fact_value_num != null ? String(r.fact_value_num) : '')
    map.get(key)!.set(r.ayanamsha_id, val)
  }

  const consensus_points: ConsensusPoint[] = []
  const divergence_points: DivergencePoint[] = []

  for (const [key, ayaValues] of map) {
    if (ayaValues.size < 2) continue
    const [cat, subj, fkey] = key.split('||') as [string, string, string]
    const values = [...ayaValues.values()]
    const unique = new Set(values)

    if (unique.size === 1) {
      consensus_points.push({
        fact_category: cat,
        fact_subject: subj,
        fact_key: fkey,
        agreed_value: values[0]!,
        ayanamsha_count: ayaValues.size,
      })
    } else {
      // Check if divergence is above threshold for numeric (degree) values
      let max_delta: number | null = null
      const nums = values.map((v) => parseFloat(v)).filter((n) => !isNaN(n))
      if (nums.length >= 2) {
        max_delta = Math.max(...nums) - Math.min(...nums)
        if (max_delta < DIVERGENCE_DEG_THRESHOLD) continue // minor numeric drift — ignore
      }

      divergence_points.push({
        fact_category: cat,
        fact_subject: subj,
        fact_key: fkey,
        values_by_ayanamsha: Object.fromEntries(ayaValues),
        max_delta_deg: max_delta,
      })
    }
  }

  return { consensus_points, divergence_points }
}

function buildBreakdown(
  ayanamshas: string[],
  rows: FactRow[],
  consensus: ConsensusPoint[],
  divergence: DivergencePoint[],
): AyanamshaBreakdownEntry[] {
  const consensusKeys = new Set(
    consensus.map((c) => `${c.fact_category}||${c.fact_subject}||${c.fact_key}`),
  )
  const divergenceKeys = new Set(
    divergence.map((d) => `${d.fact_category}||${d.fact_subject}||${d.fact_key}`),
  )

  return ayanamshas.map((aya) => {
    const ayaRows = rows.filter((r) => r.ayanamsha_id === aya)
    let inConsensus = 0
    let inDivergence = 0
    for (const r of ayaRows) {
      const k = `${r.fact_category}||${r.fact_subject}||${r.fact_key}`
      if (consensusKeys.has(k)) inConsensus++
      else if (divergenceKeys.has(k)) inDivergence++
    }
    return {
      ayanamsha_id: aya,
      total_facts: ayaRows.length,
      facts_in_consensus: inConsensus,
      facts_diverging: inDivergence,
    }
  })
}

function computeOverallScore(reports: ReportRow[], ayanamshas: string[]): number | null {
  const relevant = reports.filter(
    (r) => ayanamshas.includes(r.ayanamsha_id_1) && ayanamshas.includes(r.ayanamsha_id_2),
  )
  if (relevant.length === 0) return null
  const scores = relevant.map((r) => r.divergence_score ?? 0)
  return scores.reduce((a, b) => a + b, 0) / scores.length
}

function emptyResult(
  chart_id: string,
  topic: string,
  ayanamshas: string[],
  now: string,
): ConsensusResult {
  return {
    chart_id,
    topic,
    ayanamshas_queried: ayanamshas,
    consensus_points: [],
    divergence_points: [],
    ayanamsha_breakdown: ayanamshas.map((a) => ({
      ayanamsha_id: a,
      total_facts: 0,
      facts_in_consensus: 0,
      facts_diverging: 0,
    })),
    overall_divergence_score: null,
    generated_at: now,
  }
}
