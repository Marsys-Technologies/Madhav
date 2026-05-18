/**
 * RetrievalTool wrapper for convergence_score_lookup (Tool 28).
 * Wraps the L9 inter-school convergence scores as a pipeline-compatible RetrievalTool.
 * Phase 2A — M9 wiring 2026-05-18.
 */

import crypto from 'crypto'
import { convergence_score_lookup } from '@/lib/tools/convergence_score_lookup'
import type { ConvergenceScoreLookupInput } from '@/lib/tools/convergence_score_lookup'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'convergence_score_lookup'
const TOOL_VERSION = '1.0.0'

const ALL_DOMAINS = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL'] as const

function convergenceLevelToConfidence(level: string): number {
  if (level === 'HIGH') return 0.95
  if (level === 'MEDIUM') return 0.75
  return 0.50
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'convergence_scores',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  // Coerce params → ConvergenceScoreLookupInput
  const rawDomains = params?.domains as string[] | undefined
  const rawDomain = params?.domain as string | undefined
  const minLevel = params?.min_level as string | undefined

  const domains: string[] = rawDomains ?? (rawDomain ? [rawDomain] : [...ALL_DOMAINS])

  const input: ConvergenceScoreLookupInput = { domains }
  const output = await convergence_score_lookup(input)

  // Apply optional min_level post-filter
  const filteredScores = minLevel
    ? output.convergence_scores.filter(s => {
        if (minLevel === 'HIGH') return s.convergence_level === 'HIGH'
        if (minLevel === 'MEDIUM') return s.convergence_level !== 'LOW'
        return true
      })
    : output.convergence_scores

  const results: ToolBundleResult[] = filteredScores.map(s => ({
    content: JSON.stringify({
      domain: s.domain,
      schools_agreeing: s.schools_agreeing,
      schools_total: s.schools_total,
      convergence_level: s.convergence_level,
      mean_domain_score: s.mean_domain_score,
      std_domain_score: s.std_domain_score,
      direction: s.direction,
      per_school_scores: s.per_school_scores,
      convergence_narrative: s.convergence_narrative,
      computed_at: s.computed_at,
    }),
    source_canonical_id: 'convergence_scores',
    source_version: '1.0',
    confidence: convergenceLevelToConfidence(s.convergence_level),
    significance: 0.9,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { domains, min_level: minLevel },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `convergence_score_lookup: ToolBundle validation failed: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: results.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: results.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'convergence_scores',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Returns inter-school convergence scores across 5 life domains (CAREER, HEALTH, ' +
    'RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL). Each score reports schools_agreeing / schools_total, ' +
    'convergence_level (HIGH/MEDIUM/LOW), mean direction, and a narrative. Use when the query ' +
    'requires cross-school agreement context or to show the user where the 7 Jyotish schools ' +
    'converge or diverge on domain-level assessments.',
  retrieve,
}
