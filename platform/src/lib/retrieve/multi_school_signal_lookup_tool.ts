/**
 * RetrievalTool wrapper for multi_school_signal_lookup (Tool 27).
 * Wraps the L9 multi-school signal coverage query as a pipeline-compatible RetrievalTool.
 * Phase 2A — M9 wiring 2026-05-18.
 */

import crypto from 'crypto'
import { multi_school_signal_lookup } from '@/lib/tools/multi_school_signal_lookup'
import type { MultiSchoolSignalLookupInput } from '@/lib/tools/multi_school_signal_lookup'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'multi_school_signal_lookup'
const TOOL_VERSION = '1.0.0'

function coverageToConfidence(coverage_type: string): number {
  if (coverage_type === 'primary') return 0.95
  if (coverage_type === 'secondary') return 0.75
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
      data_asset_id: 'school_signal_coverage',
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
  // Coerce params → MultiSchoolSignalLookupInput
  const topic =
    (params?.topic as string | undefined) ??
    (params?.signal_ids as string[] | undefined)?.[0] ??
    plan.query_text

  const rawDomains = params?.domains as string[] | undefined
  const rawDomain = params?.domain as string | undefined
  const domains = rawDomains ?? (rawDomain ? [rawDomain] : undefined)

  const rawSchools = params?.schools as string[] | undefined
  const rawSchool = params?.school as string | undefined
  const schools = rawSchools ?? (rawSchool ? [rawSchool] : undefined)

  const input: MultiSchoolSignalLookupInput = { topic, domains, schools }
  const output = await multi_school_signal_lookup(input)

  const results: ToolBundleResult[] = output.results_by_school.map(r => ({
    content: JSON.stringify({
      school: r.school,
      coverage_type: r.coverage_type,
      confidence: r.confidence,
      matching_signals: r.matching_signals,
    }),
    source_canonical_id: 'school_signal_coverage',
    source_version: '1.0',
    confidence: coverageToConfidence(r.coverage_type),
    significance: 0.8,
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
    invocation_params: { topic, domains, schools },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `multi_school_signal_lookup: ToolBundle validation failed: ${JSON.stringify(validation.errors)}`
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
    data_asset_id: 'school_signal_coverage',
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
    'Queries all 7 Jyotish schools (Parashari, Jaimini, Tajika, KP, Nadi, BNN, Yogini) for ' +
    'their signal coverage on a topic or domain. Returns per-school coverage_type ' +
    '(primary/secondary/silent), matching MSR signals, and attribution references. ' +
    'Use when the query requires multi-school comparison, inter-tradition triangulation, or ' +
    'to surface which schools agree or disagree on a domain or signal cluster. ' +
    'Triggers query_class=multi_school_triangulation.',
  retrieve,
}
