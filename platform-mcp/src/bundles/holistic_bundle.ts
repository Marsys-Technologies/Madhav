/**
 * holistic_bundle.ts — Tier 2 composite bundle: 8-tool parallel holistic read.
 *
 * Deterministic parallel fan-out across 8 primitives. NO LLM calls. Per-sub-tool
 * error isolation: timeout or error produces an `{errored: true}` slot — the bundle
 * never fails because one tool failed.
 *
 * Sub-tool timeout: 8 seconds per tool.
 * Cache: 5-minute content-addressable (migration 072).
 *
 * MCPT v3.1.0-S2
 */

import { computeCacheKey, cacheLookup, cacheStore } from './cache.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
const SUB_TOOL_TIMEOUT_MS = 8_000

// ── Sub-tool names ─────────────────────────────────────────────────────────────

const SUB_TOOLS = ['MSR', 'CGM', 'UCN', 'RM', 'CDLM', 'LEL', 'PANCHANG', 'DASHA'] as const
type SubToolName = (typeof SUB_TOOLS)[number]

// ── Sub-tool event types (for SSE) ────────────────────────────────────────────

export interface SubToolStartedEvent {
  type: 'bundle.sub_tool.started'
  sub_tool: string
  started_at: string
}

export interface SubToolCompletedEvent {
  type: 'bundle.sub_tool.completed'
  sub_tool: string
  ok: true
  rows_returned?: number
  signal_ids?: string[]
}

export interface SubToolErrorEvent {
  type: 'bundle.sub_tool.error'
  sub_tool: string
  ok: false
  error_class: string
}

export interface BundleCompletedEvent {
  type: 'bundle.completed'
  envelope: HolisticBundleEnvelope
}

export type BundleEvent =
  | SubToolStartedEvent
  | SubToolCompletedEvent
  | SubToolErrorEvent
  | BundleCompletedEvent

// ── Bundle entry result ────────────────────────────────────────────────────────

export interface BundleEntrySuccess {
  sub_tool: SubToolName
  errored: false
  data: unknown
  rows_returned?: number
  signal_ids_available?: string[]
  latency_ms: number
}

export interface BundleEntryError {
  sub_tool: SubToolName
  errored: true
  error_class: string
  attempted_params: Record<string, unknown>
  latency_ms: number
}

export type BundleEntry = BundleEntrySuccess | BundleEntryError

// ── Bundle envelope ────────────────────────────────────────────────────────────

export interface HolisticBundleEnvelope {
  ok: true
  bundle_name: 'holistic_bundle'
  served_from_cache: boolean
  bundle_entries: BundleEntry[]
  provenance: {
    signal_ids_available: string[]
    sub_tools_fired: string[]
    sub_tools_errored: string[]
  }
  cached_at?: string
  expires_at?: string
}

// ── Params ─────────────────────────────────────────────────────────────────────

export interface HolisticBundleParams {
  query_text: string
  focus_domains?: string[]
  time_window?: { start?: string; end?: string }
  subset?: string[]
  tier: string
  chart_id?: string
}

// ── Primitive caller helper ────────────────────────────────────────────────────

async function callPrimitive(
  toolName: string,
  params: Record<string, unknown>,
  principal: { user_uid: string; audience_tier: string; key_id: string }
): Promise<unknown> {
  const response = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${toolName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Audience-Tier': principal.audience_tier,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify(params),
    signal: AbortSignal.timeout(SUB_TOOL_TIMEOUT_MS),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

// ── Sub-tool runner ────────────────────────────────────────────────────────────

async function runSubTool(
  name: SubToolName,
  params: Record<string, unknown>,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEvent) => void
): Promise<BundleEntry> {
  const started_at = new Date().toISOString()
  onEvent?.({ type: 'bundle.sub_tool.started', sub_tool: name, started_at })

  const t0 = Date.now()
  try {
    const data = await callPrimitive(getToolRouteFor(name), params, principal)
    const latency_ms = Date.now() - t0
    const signal_ids = extractSignalIds(data)
    const rows_returned = extractRowCount(data)

    onEvent?.({
      type: 'bundle.sub_tool.completed',
      sub_tool: name,
      ok: true,
      rows_returned,
      signal_ids,
    })

    return {
      sub_tool: name,
      errored: false,
      data,
      rows_returned,
      signal_ids_available: signal_ids,
      latency_ms,
    }
  } catch (err) {
    const latency_ms = Date.now() - t0
    const error_class = err instanceof Error
      ? (err.name === 'TimeoutError' ? 'timeout' : 'tool_error')
      : 'unknown'

    onEvent?.({ type: 'bundle.sub_tool.error', sub_tool: name, ok: false, error_class })

    return {
      sub_tool: name,
      errored: true,
      error_class,
      attempted_params: params,
      latency_ms,
    }
  }
}

// ── Tool route mapping ─────────────────────────────────────────────────────────

function getToolRouteFor(name: SubToolName): string {
  const routes: Record<SubToolName, string> = {
    MSR: 'query_signals',
    CGM: 'get_cgm_subgraph',
    UCN: 'vector_search',
    RM: 'vector_search',
    CDLM: 'vector_search',
    LEL: 'lel_query',
    PANCHANG: 'query_panchanga',
    DASHA: 'query_dasha_periods',
  }
  return routes[name]
}

// ── Param builder per sub-tool ─────────────────────────────────────────────────

function buildParams(
  name: SubToolName,
  bundleParams: HolisticBundleParams
): Record<string, unknown> {
  switch (name) {
    case 'MSR':
      return {
        ...(bundleParams.focus_domains?.length
          ? { domain: bundleParams.focus_domains[0] }
          : {}),
        limit: 100,
      }
    case 'CGM':
      return { query: bundleParams.query_text, hops: 3 }
    case 'UCN':
      return { query: bundleParams.query_text, source_filter: 'UCN_v4_1', top_k: 25 }
    case 'RM':
      return { query: bundleParams.query_text, source_filter: 'RM_v2_2', top_k: 15 }
    case 'CDLM':
      return { query: bundleParams.query_text, source_filter: 'CDLM_v1_3', top_k: 15 }
    case 'LEL':
      return bundleParams.time_window ?? {}
    case 'PANCHANG':
      return { date: new Date().toISOString().slice(0, 10) }
    case 'DASHA':
      return { active_only: true }
  }
}

// ── Signal ID + row count extraction helpers ───────────────────────────────────

function extractSignalIds(data: unknown): string[] {
  if (!data || typeof data !== 'object') return []
  const d = data as Record<string, unknown>
  const result = d['result']
  if (result && typeof result === 'object') {
    const r = result as Record<string, unknown>
    const signals = r['signals']
    if (Array.isArray(signals)) {
      return signals
        .map((s: unknown) => (s && typeof s === 'object' ? (s as Record<string, unknown>)['signal_id'] : null))
        .filter((id): id is string => typeof id === 'string')
    }
  }
  return []
}

function extractRowCount(data: unknown): number | undefined {
  if (!data || typeof data !== 'object') return undefined
  const d = data as Record<string, unknown>
  const result = d['result']
  if (result && typeof result === 'object') {
    const r = result as Record<string, unknown>
    if (typeof r['count'] === 'number') return r['count']
    for (const key of ['signals', 'events', 'steps', 'rows', 'results']) {
      if (Array.isArray(r[key])) return (r[key] as unknown[]).length
    }
  }
  return undefined
}

// ── Main bundle executor ───────────────────────────────────────────────────────

/**
 * Execute the holistic bundle. Returns the full envelope.
 * Optionally accepts an `onEvent` callback for SSE streaming — each sub-tool
 * start/complete/error event is emitted as it settles.
 */
export async function executeHolisticBundle(
  params: HolisticBundleParams,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEvent) => void
): Promise<HolisticBundleEnvelope> {
  // Determine which sub-tools to fire
  const activeTools: SubToolName[] = params.subset?.length
    ? SUB_TOOLS.filter(t => params.subset!.map(s => s.toUpperCase()).includes(t))
    : [...SUB_TOOLS]

  // Cache lookup
  const cacheKey = computeCacheKey({
    bundleName: 'holistic_bundle',
    queryText: params.query_text,
    compositionParams: {
      focus_domains: params.focus_domains,
      time_window: params.time_window,
      subset: params.subset,
    },
    tier: params.tier,
    chartId: params.chart_id ?? 'default',
  })

  const cached = await cacheLookup(cacheKey)
  if (cached.hit) {
    const cachedEnv = cached.envelope as HolisticBundleEnvelope
    onEvent?.({
      type: 'bundle.completed',
      envelope: { ...cachedEnv, served_from_cache: true },
    })
    return { ...cachedEnv, served_from_cache: true }
  }

  // Fan-out: run all active tools in parallel via Promise.allSettled
  const tasks = activeTools.map(name =>
    runSubTool(name, buildParams(name, params), principal, onEvent)
  )

  const results = await Promise.allSettled(tasks)

  const bundle_entries: BundleEntry[] = results.map((r, i) => {
    if (r.status === 'fulfilled') return r.value
    // Promise itself rejected (shouldn't happen given internal try/catch)
    return {
      sub_tool: activeTools[i]!,
      errored: true,
      error_class: 'promise_rejection',
      attempted_params: {},
      latency_ms: 0,
    }
  })

  // Build provenance: union of all signal IDs from successful tools
  const allSignalIds: string[] = []
  const sub_tools_fired: string[] = []
  const sub_tools_errored: string[] = []

  for (const entry of bundle_entries) {
    if (!entry.errored) {
      sub_tools_fired.push(entry.sub_tool)
      if (entry.signal_ids_available) {
        allSignalIds.push(...entry.signal_ids_available)
      }
    } else {
      sub_tools_errored.push(entry.sub_tool)
    }
  }

  const envelope: HolisticBundleEnvelope = {
    ok: true,
    bundle_name: 'holistic_bundle',
    served_from_cache: false,
    bundle_entries,
    provenance: {
      signal_ids_available: [...new Set(allSignalIds)],
      sub_tools_fired,
      sub_tools_errored,
    },
  }

  // Store in cache (non-fatal if it fails)
  await cacheStore({
    cacheKey,
    bundleName: 'holistic_bundle',
    audienceTier: params.tier,
    chartId: params.chart_id ?? 'default',
    envelope,
  })

  onEvent?.({ type: 'bundle.completed', envelope })
  return envelope
}
