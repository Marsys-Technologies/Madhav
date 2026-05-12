'use client'

import type { KpiResponse, Source } from './kpi_aggregator'

export interface QueryLogRow {
  id: string
  source: 'consume' | 'eval'
  created_at: string
  query_text: string | null
  query_class: string | null
  plan_type: string | null
  plan_accuracy_label: string | null
  validator_verdict: string | null
  b10_violation: boolean | null
  b11_violation: boolean | null
  citations_present: boolean | null
  citation_count: number | null
  latency_total_ms: number | null
  synthesis_status: string | null
  audit_event_id: string | null
  eval_run_id: string | null
  judge_verdict_summary: { verdict: string; reasoning: string; model: string; created_at: string } | null
}

export interface QueryLogResponse {
  page: number
  page_size: number
  total: number
  rows: QueryLogRow[]
}

export interface EvalRunRow {
  id: string
  created_at: string
  finished_at: string | null
  golden_set_version: string
  planner_prompt_version: string | null
  synthesis_prompt_version: string | null
  triggered_by: string | null
  query_count: number | null
  plan_accuracy_recall: number | null
  plan_accuracy_precision: number | null
  citation_rate: number | null
  avg_latency_total_ms: number | null
  synthesis_pass_rate: number | null
  retrieval_hit_rate: number | null
  b10_compliance_rate: number | null
  b11_compliance_rate: number | null
  notes: string | null
}

export interface EvalRunListResponse {
  page: number
  page_size: number
  total: number
  rows: EvalRunRow[]
}

export interface EvalRunDetailResponse {
  run: EvalRunRow
  queries_summary: {
    n: number
    by_plan_accuracy: { correct: number; wrong: number; ambiguous: number }
    by_synthesis_status: { success: number; failure: number }
    by_validator_verdict: { pass: number; warn: number; fail: number }
  }
}

export interface JudgeRunResponse {
  judge_run_id: string
  judged_count: number
  breakdown: { correct: number; wrong: number; ambiguous: number }
  model: string
}

export interface KpiFilters {
  window_start: string
  window_end: string
  source: Source
}

export async function fetchKpis(filters: KpiFilters): Promise<KpiResponse> {
  const url = new URL('/api/performance/kpis', window.location.origin)
  url.searchParams.set('window_start', filters.window_start)
  url.searchParams.set('window_end', filters.window_end)
  url.searchParams.set('source', filters.source)
  const r = await fetch(url.toString(), { credentials: 'include' })
  if (!r.ok) throw new Error(`KPIs fetch failed: ${r.status}`)
  return r.json()
}

export interface QueryLogFilters extends KpiFilters {
  query_class?: string[]
  validator_verdict?: string[]
  plan_accuracy_label?: string[]
  b10_violation?: boolean
  b11_violation?: boolean
  eval_run_id?: string
  page?: number
  page_size?: number
}

export async function fetchQueryLog(filters: QueryLogFilters): Promise<QueryLogResponse> {
  const url = new URL('/api/performance/queries', window.location.origin)
  url.searchParams.set('window_start', filters.window_start)
  url.searchParams.set('window_end', filters.window_end)
  url.searchParams.set('source', filters.source)
  for (const qc of filters.query_class ?? []) url.searchParams.append('query_class', qc)
  for (const vv of filters.validator_verdict ?? []) url.searchParams.append('validator_verdict', vv)
  for (const pa of filters.plan_accuracy_label ?? []) url.searchParams.append('plan_accuracy_label', pa)
  if (typeof filters.b10_violation === 'boolean') url.searchParams.set('b10_violation', String(filters.b10_violation))
  if (typeof filters.b11_violation === 'boolean') url.searchParams.set('b11_violation', String(filters.b11_violation))
  if (filters.eval_run_id) url.searchParams.set('eval_run_id', filters.eval_run_id)
  if (filters.page) url.searchParams.set('page', String(filters.page))
  if (filters.page_size) url.searchParams.set('page_size', String(filters.page_size))
  const r = await fetch(url.toString(), { credentials: 'include' })
  if (!r.ok) throw new Error(`query log fetch failed: ${r.status}`)
  return r.json()
}

export async function fetchEvalRuns(page = 1, pageSize = 20): Promise<EvalRunListResponse> {
  const url = new URL('/api/performance/eval-runs', window.location.origin)
  url.searchParams.set('page', String(page))
  url.searchParams.set('page_size', String(pageSize))
  const r = await fetch(url.toString(), { credentials: 'include' })
  if (!r.ok) throw new Error(`eval-runs fetch failed: ${r.status}`)
  return r.json()
}

export async function fetchEvalRunDetail(id: string): Promise<EvalRunDetailResponse> {
  const r = await fetch(`/api/performance/eval-runs/${id}`, { credentials: 'include' })
  if (!r.ok) throw new Error(`eval-run detail fetch failed: ${r.status}`)
  return r.json()
}

export async function runJudge(input: {
  window_start: string
  window_end: string
  limit: number
}): Promise<JudgeRunResponse> {
  const r = await fetch('/api/performance/judge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(input),
  })
  if (r.status === 409) throw new Error('judge_run_in_progress')
  if (!r.ok) throw new Error(`judge POST failed: ${r.status}`)
  return r.json()
}
