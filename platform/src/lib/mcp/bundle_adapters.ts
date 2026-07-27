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
 * R4 — Multi-LLM Exposure:
 *   - response_format: 'minimal' | 'standard' | 'detailed' branching
 *   - model_family: MARO surface applied per-family at bundle entry
 *   - behavioral_overrides: caller JSON-patch override for per-family shaping
 *
 * MCPT v3.1.0-S2 / R4
 */

import { createHash } from 'crypto'
import { getMcpSurfaceSpec } from '@/lib/retrieval/maro'
import type { ModelFamily } from '@/lib/retrieval/maro'
import { computeBundleHealth } from './bundle_status'

// ── Response format type ──────────────────────────────────────────────────────

/**
 * Bundle-elasticity format enum (R4).
 *
 * minimal  — top-3 signals (MSR only) + active dasha; no citations.
 *            Smallest payload; suitable for narrow-context models (DeepSeek worker).
 * standard — all 8 holistic sub-tools; current default behavior.
 *            Balanced; suitable for mid/premium tier on all families.
 * detailed — all sub-tools + judgment_flags + contradiction markers in envelope.
 *            Largest payload; requires premium context budget (≥200K tokens).
 *
 * MARO surface spec is applied at entry: max_tools from getMcpSurfaceSpec(family)
 * caps the sub-tool count independently of this enum.
 */
export type ResponseFormat = 'minimal' | 'standard' | 'detailed'

/**
 * Per-family MARO behavioral override patch (R4).
 * Caller passes a JSON-patch object keyed by family to override MARO defaults.
 * Most callers leave this unset; MARO uses family defaults.
 *
 * Example: { deepseek: { strip_mcp_constructs: false } }
 * Example: { gemini: { max_tokens_hint: 4096 } }
 */
export type BehavioralOverridesPatch = {
  anthropic?: Record<string, unknown>
  gemini?: Record<string, unknown>
  openai?: Record<string, unknown>
  deepseek?: Record<string, unknown>
}

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
const SUB_TOOL_TIMEOUT_MS = 8_000

// ── MARO surface application ──────────────────────────────────────────────────

/**
 * Apply MARO surface constraints at bundle entry (R4).
 *
 * Calls getMcpSurfaceSpec(family) to get per-family constraints:
 *   - max_tools: caps how many sub-tools the bundle may fire
 *   - strip_mcp_constructs: signals DeepSeek — MCP constructs must be omitted
 *
 * Returns the effective max_tools ceiling for this family.
 * Called once per bundle execution before any sub-tools run.
 */
function applyMaroSurface(family: ModelFamily): { max_tools: number; strip_mcp_constructs: boolean } {
  const spec = getMcpSurfaceSpec(family)
  return {
    max_tools: spec.max_tools,
    strip_mcp_constructs: spec.strip_mcp_constructs,
  }
}

/**
 * Resolve effective sub-tool list given response_format + MARO surface cap (R4).
 *
 * minimal  → MSR + DASHA only (2 tools; smallest payload)
 * standard → all tools up to surface max_tools cap (current default)
 * detailed → all tools; cap still applies (MARO surface is authoritative)
 *
 * The MARO surface cap is a hard ceiling regardless of format. If max_tools < the
 * format's desired count, the surface cap wins (cross-family safety guarantee).
 */
function resolveSubToolCeiling(
  format: ResponseFormat,
  allTools: readonly string[],
  maroMaxTools: number,
): number {
  switch (format) {
    case 'minimal':
      // MSR + DASHA: positions 0 and 7 in HOLISTIC_SUB_TOOLS
      return Math.min(2, maroMaxTools)
    case 'standard':
      return Math.min(allTools.length, maroMaxTools)
    case 'detailed':
      return Math.min(allTools.length, maroMaxTools)
  }
}

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
  /** R4: Bundle-elasticity format. Default: 'standard'. */
  response_format?: ResponseFormat
  /** R4: Declared model family for MARO surface constraints. Default: 'universal'. */
  model_family?: ModelFamily
  /** R4: Per-family behavioral override patch (applied on top of MARO family defaults). */
  behavioral_overrides?: BehavioralOverridesPatch
}

export async function executeHolisticBundle(
  params: HolisticBundleParams,
  principal: { user_uid: string; audience_tier: string; key_id: string },
  onEvent?: (event: BundleEventType) => void
): Promise<void> {
  // R4: Resolve response_format + model_family
  const responseFormat: ResponseFormat = params.response_format ?? 'standard'
  const modelFamily: ModelFamily = params.model_family ?? 'universal'

  // R4: Apply MARO surface constraints at bundle entry
  const maroSurface = applyMaroSurface(modelFamily)

  // R4: Apply behavioral_overrides patch on top of family defaults (informational;
  // stored in envelope so the caller can observe what overrides were applied)
  const effectiveOverrides = params.behavioral_overrides?.[modelFamily as keyof BehavioralOverridesPatch] ?? null

  // Resolve candidate sub-tool list (subset filter first, then format + surface ceiling)
  const candidateTools: HolisticSubTool[] = params.subset?.length
    ? HOLISTIC_SUB_TOOLS.filter(t => params.subset!.map(s => s.toUpperCase()).includes(t))
    : [...HOLISTIC_SUB_TOOLS]

  // R4: For minimal format, prefer MSR (index 0) + DASHA (index 7) over arbitrary head-slice
  let activeTools: HolisticSubTool[]
  if (responseFormat === 'minimal') {
    const ceiling = resolveSubToolCeiling(responseFormat, candidateTools, maroSurface.max_tools)
    // Always include MSR first, DASHA second for minimal format
    const preferred: HolisticSubTool[] = []
    if (candidateTools.includes('MSR')) preferred.push('MSR')
    if (candidateTools.includes('DASHA') && preferred.length < ceiling) preferred.push('DASHA')
    // Fill remaining slots from candidates if ceiling allows
    for (const t of candidateTools) {
      if (!preferred.includes(t) && preferred.length < ceiling) preferred.push(t)
    }
    activeTools = preferred.slice(0, ceiling)
  } else {
    const ceiling = resolveSubToolCeiling(responseFormat, candidateTools, maroSurface.max_tools)
    activeTools = candidateTools.slice(0, ceiling)
  }

  const cacheKey = computeCacheKey({
    bundleName: 'holistic_bundle',
    queryText: params.query_text,
    compositionParams: {
      focus_domains: params.focus_domains,
      time_window: params.time_window,
      subset: params.subset,
      response_format: responseFormat,
      model_family: modelFamily,
    },
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

  // R4: detailed format adds judgment_flags + contradiction marker fields to envelope
  const detailedExtras = responseFormat === 'detailed'
    ? {
        judgment_flags: bundle_entries
          .filter(e => !e.errored && e.rows_returned !== undefined && e.rows_returned > 0)
          .map(e => ({ sub_tool: e.sub_tool, rows: e.rows_returned, flag: 'present' })),
        contradiction_marker: 'see_bo_samvada',  // populated by bo_samvada when available
      }
    : undefined

  // MC-002: top-level health from errored/total ratio; `ok` derived from `status`.
  const health = computeBundleHealth(sub_tools_errored.length, bundle_entries.length)

  const envelope = {
    ok: health.ok,
    status: health.status,
    bundle_name: 'holistic_bundle',
    served_from_cache: false,
    // R4 metadata in envelope
    response_format: responseFormat,
    model_family: modelFamily,
    maro_surface: {
      max_tools: maroSurface.max_tools,
      strip_mcp_constructs: maroSurface.strip_mcp_constructs,
    },
    behavioral_overrides_applied: effectiveOverrides,
    bundle_entries,
    provenance: {
      signal_ids_available: [...new Set(allSignalIds)],
      sub_tools_fired,
      sub_tools_errored,
    },
    ...(detailedExtras ?? {}),
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
  /** R4: Bundle-elasticity format. Default: 'standard'. */
  response_format?: ResponseFormat
  /** R4: Declared model family for MARO surface constraints. Default: 'universal'. */
  model_family?: ModelFamily
  /** R4: Per-family behavioral override patch (applied on top of MARO family defaults). */
  behavioral_overrides?: BehavioralOverridesPatch
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
  // R4: Resolve response_format + model_family
  const responseFormat: ResponseFormat = params.response_format ?? 'standard'
  const modelFamily: ModelFamily = params.model_family ?? 'universal'

  // R4: Apply MARO surface constraints at bundle entry
  const maroSurface = applyMaroSurface(modelFamily)

  // R4: Apply behavioral_overrides patch
  const effectiveOverrides = params.behavioral_overrides?.[modelFamily as keyof BehavioralOverridesPatch] ?? null

  // Resolve active schools
  const allSchools: SchoolName[] = params.schools?.length ? params.schools : [...ALL_SCHOOLS]

  // R4: minimal format = cross_school_lookup only (1 tool); standard/detailed = all schools
  const schoolsToRun: SchoolName[] = responseFormat === 'minimal'
    ? allSchools.slice(0, Math.min(2, maroSurface.max_tools - 1))  // reserve 1 slot for cross_school_lookup
    : allSchools.slice(0, Math.max(0, maroSurface.max_tools - 1))  // -1 for cross_school_lookup

  const cacheKey = computeCacheKey({
    bundleName: 'multi_school_bundle',
    queryText: params.claim,
    compositionParams: { schools: schoolsToRun, response_format: responseFormat, model_family: modelFamily },
    tier: params.tier,
    chartId: params.chart_id ?? 'default',
  })

  const tasks: Promise<BundleEntry>[] = [
    runSubTool('cross_school_lookup', 'cross_school_lookup', { claim: params.claim, schools: schoolsToRun }, principal, onEvent),
    ...schoolsToRun.map(school => {
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

  // R4: detailed format adds school_verdicts structure to envelope
  const detailedExtras = responseFormat === 'detailed'
    ? {
        school_verdicts: schoolsToRun.map(s => ({ school: s, verdict_available: sub_tools_fired.includes(`${s}_evidence`) })),
        contradiction_marker: 'see_bo_samvada',
      }
    : undefined

  // MC-002: top-level health from errored/total ratio; `ok` derived from `status`.
  const health = computeBundleHealth(sub_tools_errored.length, entries.length)

  const envelope = {
    ok: health.ok,
    status: health.status,
    bundle_name: 'multi_school_bundle',
    served_from_cache: false,
    claim: params.claim,
    schools: schoolsToRun,
    // R4 metadata
    response_format: responseFormat,
    model_family: modelFamily,
    maro_surface: {
      max_tools: maroSurface.max_tools,
      strip_mcp_constructs: maroSurface.strip_mcp_constructs,
    },
    behavioral_overrides_applied: effectiveOverrides,
    bundle_entries: entries,
    provenance: { sub_tools_fired, sub_tools_errored },
    ...(detailedExtras ?? {}),
  }

  await storeCache({ cacheKey, bundleName: 'multi_school_bundle', audienceTier: params.tier, chartId: params.chart_id ?? 'default', envelope })
  onEvent?.({ type: 'bundle.completed', envelope })
}
