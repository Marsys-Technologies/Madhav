/**
 * bundle_adapters.ts — Platform-side bundle execution adapters.
 *
 * Re-exports the bundle execution functions from the platform-mcp package
 * with the same interface, but adapted for the platform's internal call
 * path (bypasses HTTP, calls platform primitives directly).
 *
 * Used by: /api/mcp/bundles/[name]/route.ts (SSE endpoint)
 *
 * Architecture note: the platform-mcp server is a separate process; when
 * the platform itself needs to execute bundles (for SSE streaming), it
 * uses these adapters which call primitives via the existing platform
 * service layer rather than HTTP.
 *
 * MCPT v3.1.0-S2
 */

import { createHash } from 'crypto'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
const SUB_TOOL_TIMEOUT_MS = 8_000

// ── Cache key helper ───────────────────────────────────────────────────────────

function computeCacheKey(params: {
  bundleName: string
  queryText: string
  compositionParams: Record<string, unknown>
  tier: string
  chartId: string
}): string {
  const raw = JSON.stringify({
    b: params.bundleName,
    q: params.queryText,
    p: params.compositionParams,
    t: params.tier,
    c: params.chartId,
  })
  return createHash('sha256').update(raw).digest('hex')
}

// ── Primitive caller ───────────────────────────────────────────────────────────

async function callPrimitive(
  toolName: string,
  params: Record<string, unknown>,
  principal: { user_uid: string; audience_tier: string; key_id: string }
): Promise<unknown> {
  const url = `${PLATFORM_URL}/api/mcp/primitives/${toolName}`
  const response = await fetch(url, {
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

interface BundleEntry {
  sub_tool: string
  errored: boolean
  error_class?: string
  attempted_params?: Record<string, unknown>
  data?: unknown
  rows_returned?: number
  signal_ids_available?: string[]
  latency_ms: number
}

type BundleEventType =
  | { type: 'bundle.sub_tool.started'; sub_tool: string; started_at: string }
  | { type: 'bundle.sub_tool.completed'; sub_tool: string; ok: true; rows_returned?: number; signal_ids?: string[] }
  | { type: 'bundle.sub_tool.error'; sub_tool: string; ok: false; error_class: string }
  | { type: 'bundle.completed'; envelope: unknown }

function extractRowCount(data: unknown): number | undefined {
  if (!data || typeof data !== 'object') return undefined
  const d = data as Record<string, unknown>
  const result = d['result']
  if (result && typeof result === 'object') {
    const r = result as Record<string, unknown>
    for (const key of ['signals', 'events', 'steps', 'rows', 'results', 'school_positions']) {
      if (Array.isArray(r[key])) return (r[key] as unknown[]).length
    }
  }
  return undefined
}

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

async function runSubTool(
  label: string,
  toolName: string,
  params: Record<string, unknown>,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEventType) => void
): Promise<BundleEntry> {
  const started_at = new Date().toISOString()
  onEvent?.({ type: 'bundle.sub_tool.started', sub_tool: label, started_at })

  const t0 = Date.now()
  try {
    const data = await callPrimitive(toolName, params, principal)
    const latency_ms = Date.now() - t0
    const signal_ids = extractSignalIds(data)
    const rows_returned = extractRowCount(data)

    onEvent?.({ type: 'bundle.sub_tool.completed', sub_tool: label, ok: true, rows_returned, signal_ids })
    return { sub_tool: label, errored: false, data, rows_returned, signal_ids_available: signal_ids, latency_ms }
  } catch (err) {
    const latency_ms = Date.now() - t0
    const error_class = err instanceof Error ? (err.name === 'TimeoutError' ? 'timeout' : 'tool_error') : 'unknown'
    onEvent?.({ type: 'bundle.sub_tool.error', sub_tool: label, ok: false, error_class })
    return { sub_tool: label, errored: true, error_class, attempted_params: params, latency_ms }
  }
}

// ── Cache store ────────────────────────────────────────────────────────────────

async function storeCache(params: {
  cacheKey: string
  bundleName: string
  audienceTier: string
  chartId: string
  envelope: unknown
}): Promise<void> {
  try {
    await fetch(`${PLATFORM_URL}/api/mcp/bundles/cache/store`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      body: JSON.stringify({
        cache_key: params.cacheKey,
        bundle_name: params.bundleName,
        audience_tier: params.audienceTier,
        chart_id: params.chartId,
        envelope_json: params.envelope,
      }),
      signal: AbortSignal.timeout(5_000),
    })
  } catch {
    // Non-fatal
  }
}

// ── Holistic bundle ────────────────────────────────────────────────────────────

const HOLISTIC_SUB_TOOLS = ['MSR', 'CGM', 'UCN', 'RM', 'CDLM', 'LEL', 'PANCHANG', 'DASHA'] as const
type HolisticSubTool = (typeof HOLISTIC_SUB_TOOLS)[number]

function buildHolisticParams(
  name: HolisticSubTool,
  queryText: string,
  focusDomains?: string[],
  timeWindow?: { start?: string; end?: string }
): { toolName: string; params: Record<string, unknown> } {
  switch (name) {
    case 'MSR':
      return {
        toolName: 'query_signals',
        params: { ...(focusDomains?.length ? { domain: focusDomains[0] } : {}), limit: 100 },
      }
    case 'CGM':
      return { toolName: 'get_cgm_subgraph', params: { query: queryText, hops: 3 } }
    case 'UCN':
      return { toolName: 'vector_search', params: { query: queryText, source_filter: 'UCN_v4_1', top_k: 25 } }
    case 'RM':
      return { toolName: 'vector_search', params: { query: queryText, source_filter: 'RM_v2_2', top_k: 15 } }
    case 'CDLM':
      return { toolName: 'vector_search', params: { query: queryText, source_filter: 'CDLM_v1_3', top_k: 15 } }
    case 'LEL':
      return { toolName: 'lel_query', params: timeWindow ?? {} }
    case 'PANCHANG':
      return { toolName: 'query_panchanga', params: { date: new Date().toISOString().slice(0, 10) } }
    case 'DASHA':
      return { toolName: 'query_dasha_periods', params: { active_only: true } }
  }
}

export interface HolisticBundleParams {
  query_text: string
  focus_domains?: string[]
  time_window?: { start?: string; end?: string }
  subset?: string[]
  tier: string
  chart_id?: string
}

export async function executeHolisticBundle(
  params: HolisticBundleParams,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEventType) => void
): Promise<void> {
  const activeTools: HolisticSubTool[] = params.subset?.length
    ? HOLISTIC_SUB_TOOLS.filter(t => params.subset!.map(s => s.toUpperCase()).includes(t))
    : [...HOLISTIC_SUB_TOOLS]

  const cacheKey = computeCacheKey({
    bundleName: 'holistic_bundle',
    queryText: params.query_text,
    compositionParams: { focus_domains: params.focus_domains, time_window: params.time_window, subset: params.subset },
    tier: params.tier,
    chartId: params.chart_id ?? 'default',
  })

  const tasks = activeTools.map(name => {
    const spec = buildHolisticParams(name, params.query_text, params.focus_domains, params.time_window)
    return runSubTool(name, spec.toolName, spec.params, principal, onEvent)
  })

  const results = await Promise.allSettled(tasks)
  const bundle_entries: BundleEntry[] = results.map((r, i) =>
    r.status === 'fulfilled'
      ? r.value
      : { sub_tool: activeTools[i]!, errored: true, error_class: 'promise_rejection', attempted_params: {}, latency_ms: 0 }
  )

  const allSignalIds: string[] = []
  const sub_tools_fired: string[] = []
  const sub_tools_errored: string[] = []
  for (const e of bundle_entries) {
    if (!e.errored) { sub_tools_fired.push(e.sub_tool); allSignalIds.push(...(e.signal_ids_available ?? [])) }
    else sub_tools_errored.push(e.sub_tool)
  }

  const envelope = {
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

  await storeCache({ cacheKey, bundleName: 'holistic_bundle', audienceTier: params.tier, chartId: params.chart_id ?? 'default', envelope })
  onEvent?.({ type: 'bundle.completed', envelope })
}

// ── Multi-school bundle ────────────────────────────────────────────────────────

const ALL_SCHOOLS = ['parashara', 'jaimini', 'kp', 'tajaka'] as const
type SchoolName = (typeof ALL_SCHOOLS)[number]

export interface MultiSchoolBundleParams {
  claim: string
  schools?: SchoolName[]
  tier: string
  chart_id?: string
}

function buildSchoolSpec(school: SchoolName): { toolName: string; params: Record<string, unknown> } | null {
  switch (school) {
    case 'parashara': return { toolName: 'query_signals', params: { limit: 20 } }
    case 'jaimini': return { toolName: 'query_chart_facts', params: { category: 'strength_extra', limit: 20 } }
    case 'kp': return { toolName: 'query_chart_facts', params: { category: 'kp_cusp', limit: 20 } }
    case 'tajaka': return { toolName: 'query_chart_facts', params: { category: 'varshphal', limit: 20 } }
  }
}

export async function executeMultiSchoolBundle(
  params: MultiSchoolBundleParams,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEventType) => void
): Promise<void> {
  const schools: SchoolName[] = params.schools?.length ? params.schools : [...ALL_SCHOOLS]

  const cacheKey = computeCacheKey({
    bundleName: 'multi_school_bundle',
    queryText: params.claim,
    compositionParams: { schools },
    tier: params.tier,
    chartId: params.chart_id ?? 'default',
  })

  const tasks: Promise<BundleEntry>[] = [
    runSubTool('cross_school_lookup', 'cross_school_lookup', { claim: params.claim, schools }, principal, onEvent),
    ...schools.map(school => {
      const spec = buildSchoolSpec(school)
      return spec
        ? runSubTool(`${school}_evidence`, spec.toolName, spec.params, principal, onEvent)
        : Promise.resolve<BundleEntry>({ sub_tool: `${school}_evidence`, errored: true, error_class: 'no_spec', attempted_params: {}, latency_ms: 0 })
    }),
  ]

  const results = await Promise.allSettled(tasks)
  const entries: BundleEntry[] = results.map((r, i) =>
    r.status === 'fulfilled'
      ? r.value
      : { sub_tool: i === 0 ? 'cross_school_lookup' : `school_${i}`, errored: true, error_class: 'promise_rejection', attempted_params: {}, latency_ms: 0 }
  )

  const sub_tools_fired: string[] = []
  const sub_tools_errored: string[] = []
  for (const e of entries) {
    if (!e.errored) sub_tools_fired.push(e.sub_tool)
    else sub_tools_errored.push(e.sub_tool)
  }

  const envelope = {
    ok: true,
    bundle_name: 'multi_school_bundle',
    served_from_cache: false,
    claim: params.claim,
    schools,
    bundle_entries: entries,
    provenance: { sub_tools_fired, sub_tools_errored },
  }

  await storeCache({ cacheKey, bundleName: 'multi_school_bundle', audienceTier: params.tier, chartId: params.chart_id ?? 'default', envelope })
  onEvent?.({ type: 'bundle.completed', envelope })
}
