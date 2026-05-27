/**
 * multi_school_bundle.ts — Tier 2 composite bundle: cross-school convergence.
 *
 * Deterministic parallel fan-out. NO LLM calls. Per-sub-tool error isolation.
 * Sub-tool timeout: 8 seconds. Cache: 5-minute content-addressable.
 *
 * Composition:
 *   1. cross_school_lookup(claim, schools)
 *   2. Per-school targeted primitive query
 *   3. read_classical_text for most-cited classical reference
 *
 * MCPT v3.1.0-S2
 */

import { computeCacheKey, cacheLookup, cacheStore } from './cache.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
const SUB_TOOL_TIMEOUT_MS = 8_000

export type SchoolName = 'parashara' | 'jaimini' | 'kp' | 'tajaka'
const ALL_SCHOOLS: SchoolName[] = ['parashara', 'jaimini', 'kp', 'tajaka']

// ── Event types ────────────────────────────────────────────────────────────────

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
}

export interface SubToolErrorEvent {
  type: 'bundle.sub_tool.error'
  sub_tool: string
  ok: false
  error_class: string
}

export interface MultiSchoolBundleCompletedEvent {
  type: 'bundle.completed'
  envelope: MultiSchoolBundleEnvelope
}

export type MultiSchoolBundleEvent =
  | SubToolStartedEvent
  | SubToolCompletedEvent
  | SubToolErrorEvent
  | MultiSchoolBundleCompletedEvent

// ── Entry types ────────────────────────────────────────────────────────────────

export interface MultiSchoolBundleEntry {
  sub_tool: string
  errored: boolean
  error_class?: string
  attempted_params?: Record<string, unknown>
  data?: unknown
  rows_returned?: number
  latency_ms: number
}

// ── Envelope ───────────────────────────────────────────────────────────────────

export interface MultiSchoolBundleEnvelope {
  ok: true
  bundle_name: 'multi_school_bundle'
  served_from_cache: boolean
  claim: string
  schools: SchoolName[]
  bundle_entries: MultiSchoolBundleEntry[]
  provenance: {
    sub_tools_fired: string[]
    sub_tools_errored: string[]
    convergence_score?: number
  }
  cached_at?: string
  expires_at?: string
}

// ── Params ─────────────────────────────────────────────────────────────────────

export interface MultiSchoolBundleParams {
  claim: string
  schools?: SchoolName[]
  tier: string
  chart_id?: string
}

// ── Primitive caller ───────────────────────────────────────────────────────────

async function callPrimitive(
  toolName: string,
  params: Record<string, unknown>,
  principal: { user_uid: string; key_id: string }
): Promise<unknown> {
  const response = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${toolName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      // X-MCP-Audience-Tier removed (Stream A 3.tier_excision 2026-05-28).
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
  label: string,
  toolName: string,
  params: Record<string, unknown>,
  principal: { user_uid: string; key_id: string },
  onEvent?: (event: MultiSchoolBundleEvent) => void
): Promise<MultiSchoolBundleEntry> {
  const started_at = new Date().toISOString()
  onEvent?.({ type: 'bundle.sub_tool.started', sub_tool: label, started_at })

  const t0 = Date.now()
  try {
    const data = await callPrimitive(toolName, params, principal)
    const latency_ms = Date.now() - t0
    const rows_returned = extractRowCount(data)

    onEvent?.({ type: 'bundle.sub_tool.completed', sub_tool: label, ok: true, rows_returned })

    return { sub_tool: label, errored: false, data, rows_returned, latency_ms }
  } catch (err) {
    const latency_ms = Date.now() - t0
    const error_class = err instanceof Error
      ? (err.name === 'TimeoutError' ? 'timeout' : 'tool_error')
      : 'unknown'

    onEvent?.({ type: 'bundle.sub_tool.error', sub_tool: label, ok: false, error_class })

    return { sub_tool: label, errored: true, error_class, attempted_params: params, latency_ms }
  }
}

function extractRowCount(data: unknown): number | undefined {
  if (!data || typeof data !== 'object') return undefined
  const d = data as Record<string, unknown>
  const result = d['result']
  if (result && typeof result === 'object') {
    const r = result as Record<string, unknown>
    for (const key of ['school_positions', 'signals', 'rows', 'results', 'records']) {
      if (Array.isArray(r[key])) return (r[key] as unknown[]).length
    }
  }
  return undefined
}

// ── Per-school primitive params ────────────────────────────────────────────────

function buildSchoolParams(
  school: SchoolName,
  claim: string
): { toolName: string; params: Record<string, unknown> } | null {
  switch (school) {
    case 'parashara':
      return {
        toolName: 'query_signals',
        params: { domain: extractDomainFromClaim(claim), limit: 20 },
      }
    case 'jaimini':
      return {
        toolName: 'query_chart_facts',
        params: { category: 'strength_extra', limit: 20 },
      }
    case 'kp':
      return {
        toolName: 'query_chart_facts',
        params: { category: 'kp_cusp', limit: 20 },
      }
    case 'tajaka':
      return {
        toolName: 'query_chart_facts',
        params: { category: 'varshphal', limit: 20 },
      }
  }
}

function extractDomainFromClaim(claim: string): string | undefined {
  const domainKeywords: Record<string, string[]> = {
    career: ['career', 'work', 'profession', 'job', '10th', 'tenth'],
    health: ['health', 'illness', 'disease', '6th', 'sixth'],
    relationships: ['relationship', 'marriage', 'partner', '7th', 'seventh'],
    spiritual: ['spiritual', 'moksha', 'liberation', '12th', 'twelfth'],
    wealth: ['wealth', 'money', 'finance', '2nd', 'second', '11th', 'eleventh'],
  }
  const lowerClaim = claim.toLowerCase()
  for (const [domain, keywords] of Object.entries(domainKeywords)) {
    if (keywords.some(kw => lowerClaim.includes(kw))) return domain
  }
  return undefined
}

// ── Extract classical reference from cross_school_lookup result ────────────────

function extractClassicalReference(crossSchoolData: unknown): string | null {
  if (!crossSchoolData || typeof crossSchoolData !== 'object') return null
  const d = crossSchoolData as Record<string, unknown>
  const result = d['result']
  if (!result || typeof result !== 'object') return null
  const r = result as Record<string, unknown>

  // Look for citations in school_positions
  const positions = r['school_positions']
  if (!Array.isArray(positions)) return null

  for (const pos of positions) {
    if (pos && typeof pos === 'object') {
      const p = pos as Record<string, unknown>
      if (typeof p['citation'] === 'string' && p['citation']) {
        return p['citation']
      }
    }
  }
  return null
}

function extractConvergenceScore(crossSchoolData: unknown): number | undefined {
  if (!crossSchoolData || typeof crossSchoolData !== 'object') return undefined
  const d = crossSchoolData as Record<string, unknown>
  const result = d['result']
  if (result && typeof result === 'object') {
    const r = result as Record<string, unknown>
    if (typeof r['convergence_score'] === 'number') return r['convergence_score']
  }
  return undefined
}

// ── Main executor ──────────────────────────────────────────────────────────────

export async function executeMultiSchoolBundle(
  params: MultiSchoolBundleParams,
  principal: { user_uid: string; key_id: string },
  onEvent?: (event: MultiSchoolBundleEvent) => void
): Promise<MultiSchoolBundleEnvelope> {
  const schools = params.schools?.length ? params.schools : ALL_SCHOOLS

  // Cache lookup
  const cacheKey = computeCacheKey({
    bundleName: 'multi_school_bundle',
    queryText: params.claim,
    compositionParams: { schools },
    tier: params.tier,
    chartId: params.chart_id ?? 'default',
  })

  const cached = await cacheLookup(cacheKey)
  if (cached.hit) {
    const cachedEnv = cached.envelope as MultiSchoolBundleEnvelope
    onEvent?.({
      type: 'bundle.completed',
      envelope: { ...cachedEnv, served_from_cache: true },
    })
    return { ...cachedEnv, served_from_cache: true }
  }

  // Build task list
  const tasks: Promise<MultiSchoolBundleEntry>[] = []

  // Task 1: cross_school_lookup
  tasks.push(
    runSubTool('cross_school_lookup', 'cross_school_lookup', { claim: params.claim, schools }, principal, onEvent)
  )

  // Tasks 2..N: per-school evidence queries (run in parallel with cross_school_lookup)
  for (const school of schools) {
    const schoolSpec = buildSchoolParams(school, params.claim)
    if (schoolSpec) {
      tasks.push(
        runSubTool(
          `${school}_evidence`,
          schoolSpec.toolName,
          schoolSpec.params,
          principal,
          onEvent
        )
      )
    }
  }

  // Wait for all tasks; get cross_school_lookup result for classical text lookup
  const results = await Promise.allSettled(tasks)
  const entries: MultiSchoolBundleEntry[] = results.map((r, i) => {
    if (r.status === 'fulfilled') return r.value
    return {
      sub_tool: i === 0 ? 'cross_school_lookup' : `school_${i}`,
      errored: true,
      error_class: 'promise_rejection',
      attempted_params: {},
      latency_ms: 0,
    }
  })

  // Task 3: read_classical_text from cross_school_lookup citation
  const crossSchoolEntry = entries[0]
  if (crossSchoolEntry && !crossSchoolEntry.errored) {
    const citation = extractClassicalReference(crossSchoolEntry.data)
    if (citation) {
      const classicalEntry = await runSubTool(
        'read_classical_text',
        'read_asset',
        { path: citation },
        principal,
        onEvent
      )
      entries.push(classicalEntry)
    }
  }

  // Build provenance
  const sub_tools_fired: string[] = []
  const sub_tools_errored: string[] = []
  for (const entry of entries) {
    if (!entry.errored) sub_tools_fired.push(entry.sub_tool)
    else sub_tools_errored.push(entry.sub_tool)
  }

  const convergence_score = crossSchoolEntry && !crossSchoolEntry.errored
    ? extractConvergenceScore(crossSchoolEntry.data)
    : undefined

  const envelope: MultiSchoolBundleEnvelope = {
    ok: true,
    bundle_name: 'multi_school_bundle',
    served_from_cache: false,
    claim: params.claim,
    schools,
    bundle_entries: entries,
    provenance: {
      sub_tools_fired,
      sub_tools_errored,
      ...(convergence_score !== undefined ? { convergence_score } : {}),
    },
  }

  await cacheStore({
    cacheKey,
    bundleName: 'multi_school_bundle',
    audienceTier: params.tier,
    chartId: params.chart_id ?? 'default',
    envelope,
  })

  onEvent?.({ type: 'bundle.completed', envelope })
  return envelope
}
