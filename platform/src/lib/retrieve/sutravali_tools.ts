/**
 * sutravali_tools.ts — RetrievalTool definitions for Sūtravali pattern extraction
 *
 * Four SQL-only tools over sutravali_rules table.
 * Zero LLM — all queries are deterministic SQL via Python sidecar.
 *
 * Tools registered:
 *   1. query_rules            — flexible JSONB query over antecedent
 *   2. query_rules_for_planet — planet + optional house filter
 *   3. read_rule              — single rule by UUID
 *   4. list_rules_by_text     — all rules from a given text_id
 *
 * BRAHMA L0 Stream D — Sūtravali Pattern Extraction (2026-06-07)
 */

import { createHash } from 'crypto'
import type { RetrievalTool, ToolBundle, ToolBundleResult, QueryPlan } from './types'

function sha256(data: string): string {
  return 'sha256:' + createHash('sha256').update(data).digest('hex')
}

function getSidecarUrl(): string {
  return (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
}

function getSidecarKey(): string {
  return process.env.PYTHON_SIDECAR_API_KEY ?? ''
}

async function sidecarGet(path: string): Promise<unknown> {
  const url = getSidecarUrl() + path
  const res = await fetch(url, {
    headers: { 'x-api-key': getSidecarKey() },
    signal: AbortSignal.timeout(10_000),
  })
  if (!res.ok) {
    throw new Error(`Sidecar ${path} returned ${res.status}: ${await res.text()}`)
  }
  return res.json()
}

async function sidecarPost(path: string, body: unknown): Promise<unknown> {
  const url = getSidecarUrl() + path
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': getSidecarKey(),
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  })
  if (!res.ok) {
    throw new Error(`Sidecar POST ${path} returned ${res.status}: ${await res.text()}`)
  }
  return res.json()
}

function rulesArrayToBundle(
  toolName: string,
  toolVersion: string,
  params: Record<string, unknown>,
  rows: unknown[],
  startMs: number,
): ToolBundle {
  const results: ToolBundleResult[] = (rows as Record<string, unknown>[]).map(r => ({
    content: JSON.stringify(r),
    confidence: typeof r.confidence === 'number' ? r.confidence : undefined,
  }))
  const resultJson = JSON.stringify(results)
  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: toolName,
    tool_version: toolVersion,
    invocation_params: params,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - startMs,
    result_hash: sha256(resultJson),
    schema_version: '1.0',
  }
}

// ── Tool 1: query_rules ────────────────────────────────────────────────────────

export const queryRulesTool: RetrievalTool = {
  name: 'query_rules',
  version: '1.0',
  description:
    'Query sutravali_rules by antecedent JSONB pattern. ' +
    'Supports planet, house, sign filters. SQL-only, zero LLM.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {},
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const body: Record<string, unknown> = {}
    if (typeof params.antecedent_pattern === 'string') body.antecedent_pattern = params.antecedent_pattern
    if (typeof params.planet === 'string') body.planet = params.planet
    if (typeof params.house === 'number') body.house = params.house
    if (typeof params.sign === 'string') body.sign = params.sign
    if (typeof params.limit === 'number') body.limit = params.limit

    const rows = (await sidecarPost('/api/brahma/sutravali/query_rules', body)) as unknown[]
    return rulesArrayToBundle('query_rules', '1.0', body, rows, startMs)
  },
}

// ── Tool 2: query_rules_for_planet ────────────────────────────────────────────

export const queryRulesForPlanetTool: RetrievalTool = {
  name: 'query_rules_for_planet',
  version: '1.0',
  description:
    'Query sutravali_rules for a specific planet, optionally filtered by house. ' +
    'Returns all classical rules referencing the planet in its antecedent. SQL-only.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {},
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const planet = typeof params.planet === 'string' ? params.planet : ''
    if (!planet) throw new Error('query_rules_for_planet: params.planet is required')

    const qs = new URLSearchParams({ planet })
    if (typeof params.house === 'number') qs.set('house', String(params.house))
    if (typeof params.limit === 'number') qs.set('limit', String(params.limit))

    const rows = (await sidecarGet(
      `/api/brahma/sutravali/query_rules_for_planet?${qs.toString()}`,
    )) as unknown[]

    const effectiveParams = { planet, ...(params.house !== undefined ? { house: params.house } : {}), ...(params.limit !== undefined ? { limit: params.limit } : {}) }
    return rulesArrayToBundle('query_rules_for_planet', '1.0', effectiveParams, rows, startMs)
  },
}

// ── Tool 3: read_rule ──────────────────────────────────────────────────────────

export const readRuleTool: RetrievalTool = {
  name: 'read_rule',
  version: '1.0',
  description:
    'Fetch a single sutravali rule by its UUID rule_id. ' +
    'Returns antecedent, predicate, prediction, confidence, and provenance. SQL-only.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {},
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const ruleId = typeof params.rule_id === 'string' ? params.rule_id : ''
    if (!ruleId) throw new Error('read_rule: params.rule_id is required')

    const row = await sidecarGet(
      `/api/brahma/sutravali/read_rule/${encodeURIComponent(ruleId)}`,
    )

    const results: ToolBundleResult[] = [{ content: JSON.stringify(row) }]
    const resultJson = JSON.stringify(results)
    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'read_rule',
      tool_version: '1.0',
      invocation_params: { rule_id: ruleId },
      results,
      served_from_cache: false,
      latency_ms: Date.now() - startMs,
      result_hash: sha256(resultJson),
      schema_version: '1.0',
    }
  },
}

// ── Tool 4: list_rules_by_text ────────────────────────────────────────────────

export const listRulesByTextTool: RetrievalTool = {
  name: 'list_rules_by_text',
  version: '1.0',
  description:
    'List all sutravali rules sourced from a given text_id (e.g. "bphs", "hora_sara"). ' +
    'Paginated via limit + offset params. SQL-only.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {},
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const textId = typeof params.text_id === 'string' ? params.text_id : ''
    if (!textId) throw new Error('list_rules_by_text: params.text_id is required')

    const qs = new URLSearchParams()
    if (typeof params.limit === 'number') qs.set('limit', String(params.limit))
    if (typeof params.offset === 'number') qs.set('offset', String(params.offset))

    const qsStr = qs.toString()
    const path = `/api/brahma/sutravali/list_rules_by_text/${encodeURIComponent(textId)}${qsStr ? '?' + qsStr : ''}`
    const rows = (await sidecarGet(path)) as unknown[]

    const effectiveParams: Record<string, unknown> = { text_id: textId }
    if (typeof params.limit === 'number') effectiveParams.limit = params.limit
    if (typeof params.offset === 'number') effectiveParams.offset = params.offset
    return rulesArrayToBundle('list_rules_by_text', '1.0', effectiveParams, rows, startMs)
  },
}

// ── Exported array ─────────────────────────────────────────────────────────────

export const SUTRAVALI_RETRIEVAL_TOOLS: RetrievalTool[] = [
  queryRulesTool,
  queryRulesForPlanetTool,
  readRuleTool,
  listRulesByTextTool,
]
