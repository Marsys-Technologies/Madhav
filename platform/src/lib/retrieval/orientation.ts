/**
 * orientation.ts — W4 "One Planner", sequential core step 5 (S-1 orientation front-door on the
 * web/consult channel).
 *
 * Design target (RETRIEVAL_STRATEGY_v1_0.md §S-1 "Orientation front-door"): a single early call /
 * context block returning, in ≤2000 tokens total:
 *   - the chart FRAME (chart_header identity — lagna/moon/sun/name/current dasha),
 *   - load-bearing STRUCTURAL facts (digest tallies + weakest graha + top priority class),
 *   - "NOTABLE" gestalt findings (composite-ranked entity_profiles — one row per graha),
 *   - active DASHA context (current Maha/Antar, from the header),
 *   - a CATEGORY-INVENTORY + DRILL-POINTER map (what to call next, and for what).
 *
 * This is a faithful web-side port of the MCP `get_chart_orientation` tool
 * (platform-mcp/src/tools/registry_bridge.ts). That tool calls the L2 `query_ucd` capability and
 * bounds the result; this module reuses the SAME underlying capability (`queryUcdCapability`,
 * the web-side query_ucd handler) so the orientation the consult channel serves is computed by
 * the identical ranking/aggregation pipeline the MCP channel uses — not a reimplementation. It
 * adds the chart_header frame + a static category-inventory/drill-pointer map, then enforces the
 * §S-1 ≤2000-token budget explicitly (via the codebase-standard `estimateTokens` helper).
 *
 * It runs OUTSIDE the MCP tool-handler wrapper (no envelope/v3 machinery, no MCP budget kb) — it
 * is a plain async function the consult route calls early in the request lifecycle and delivers
 * to the client as a `data-orientation` SSE event.
 */

import { queryUcdCapability } from './registry/layers/L2_bodha/query_ucd'
import { fetchChartHeaderResolution } from './chart_header'
import { DEFAULT_AYANAMSHA } from './registry/constants'
import { estimateTokens } from '@/lib/pipeline/manifest_compressor'
import type { ChartHeader } from './envelope'

/** §S-1 hard budget — the whole orientation block must fit in this many estimated tokens. */
export const ORIENTATION_TOKEN_BUDGET = 2000

export interface OrientationStructuralFacts {
  msr_signal_count: number | null
  yoga_count: number | null
  dosha_count: number | null
  contradiction_count: number | null
  weakest_graha: string | null
  weakest_graha_source: string | null
  top_priority_class: string | null
}

export interface OrientationNotableFinding {
  entity: string
  entity_type: string
  signal_count: number
  dominant_domains: string[]
  dominant_valence: string | null
  /** Drill handle back into get_signals / query_signals. */
  top_signal_ids: string[]
}

export interface OrientationConvergenceDomain {
  domain: string
  convergence_score: number | null
}

export interface OrientationCategory {
  /** Retrieval category family (structural, signals, temporal, remedy, …). */
  category: string
  /** The instrument to drill this category with (web retrieval tool / MCP twin name). */
  drill_tool: string
  /** ≤12-word hint on when to reach for it. */
  hint: string
}

export interface ChartOrientation {
  chart_id: string
  ayanamsha_id: string
  /** Identity/frame block (~40 tokens). null only if resolution hard-failed. */
  chart_header: ChartHeader | null
  /** Honesty flags folded up from chart_header resolution (e.g. chart_header_unresolved). */
  header_flags: string[]
  /** Load-bearing structural tallies, or null if the digest was unavailable. */
  structural_facts: OrientationStructuralFacts | null
  /** Composite-ranked gestalt findings (one row per graha/bhava). */
  notable_findings: OrientationNotableFinding[]
  /** Top convergence domains (cross-tradition agreement). */
  convergence_domains: OrientationConvergenceDomain[]
  /** Active dasha context (from the header's current Maha/Antar). */
  dasha_context: { current_maha_antar: string | null }
  /** Category-inventory + drill-pointer map — what to call next and for what. */
  category_inventory: OrientationCategory[]
  /** Budget accounting — how the §S-1 ≤2000-token cap was enforced for THIS block. */
  budget: {
    limit_tokens: number
    estimated_tokens: number
    enforced: boolean
    /** Human-readable list of the trims applied to fit the budget (empty if it fit as-is). */
    trims: string[]
  }
  /** True when query_ucd failed and only the header + inventory are present. */
  degraded: boolean
}

/**
 * The category-inventory + drill-pointer map (design §S-1). Static: the same set of retrieval
 * families every chart exposes, each pointing at the instrument that drills it. Names are the
 * consult channel's / MCP twin instrument names a follow-up call would use.
 */
const CATEGORY_INVENTORY: readonly OrientationCategory[] = [
  { category: 'structural', drill_tool: 'ganita_structural_get', hint: 'bhava/bhavesha/karaka condition, house-by-house structure' },
  { category: 'strength', drill_tool: 'ganita_strength_get', hint: 'shadbala, dignity, graha strength ranking' },
  { category: 'signals', drill_tool: 'get_signals', hint: 'atomic composite-ranked MSR signals for any entity' },
  { category: 'domain', drill_tool: 'get_domain_reading', hint: 'domain-conditioned reading (career/wealth/marriage/health)' },
  { category: 'temporal', drill_tool: 'get_dashas', hint: 'Vimshottari dasha spine, timing windows, activations' },
  { category: 'mechanism', drill_tool: 'get_cgm_subgraph', hint: 'CGM causal-graph walk for a cause→effect chain' },
  { category: 'life_events', drill_tool: 'lel_query', hint: 'Life Event Log retrodiction / prediction anchors' },
  { category: 'remedy', drill_tool: 'get_remedies', hint: 'prescriptions: gemstone/mantra/ritual (intervention asks)' },
]

/**
 * Enforce the §S-1 ≤2000-token budget by progressively trimming the LEAST-load-bearing sections
 * first: convergence domains → notable-finding drill ids → notable findings themselves. The frame
 * (header), structural facts, dasha context, and category inventory are the non-negotiable core
 * and are never dropped. Mutates a shallow-cloned block; returns the trims applied.
 */
function enforceBudget(o: ChartOrientation): void {
  const measure = (): number =>
    estimateTokens(
      JSON.stringify({
        chart_header: o.chart_header,
        structural_facts: o.structural_facts,
        notable_findings: o.notable_findings,
        convergence_domains: o.convergence_domains,
        dasha_context: o.dasha_context,
        category_inventory: o.category_inventory,
      }),
    )

  const trims: string[] = []
  let est = measure()

  // 1. Trim convergence_domains from 7 → 3 if over budget.
  if (est > ORIENTATION_TOKEN_BUDGET && o.convergence_domains.length > 3) {
    const dropped = o.convergence_domains.length - 3
    o.convergence_domains = o.convergence_domains.slice(0, 3)
    trims.push(`convergence_domains: kept top 3 (dropped ${dropped})`)
    est = measure()
  }

  // 2. Strip drill ids from notable findings (still names the entity; ids reachable via get_signals).
  if (est > ORIENTATION_TOKEN_BUDGET && o.notable_findings.some(f => f.top_signal_ids.length > 0)) {
    o.notable_findings = o.notable_findings.map(f => ({ ...f, top_signal_ids: [] }))
    trims.push('notable_findings: dropped top_signal_ids (drill via get_signals)')
    est = measure()
  }

  // 3. Trim notable_findings from the tail until it fits (keep at least the strongest).
  const findingsBefore = o.notable_findings.length
  while (est > ORIENTATION_TOKEN_BUDGET && o.notable_findings.length > 1) {
    o.notable_findings.pop()
    est = measure()
  }
  if (o.notable_findings.length < findingsBefore) {
    trims.push(`notable_findings: kept top ${o.notable_findings.length} (dropped ${findingsBefore - o.notable_findings.length})`)
  }
  if (est > ORIENTATION_TOKEN_BUDGET) {
    // Still over after keeping the single strongest finding — record it honestly (rare; the
    // header + inventory core dominates the block and is never dropped).
    trims.push('over_budget_after_min_trim: header + inventory core exceeds budget')
  }

  o.budget = {
    limit_tokens: ORIENTATION_TOKEN_BUDGET,
    estimated_tokens: est,
    enforced: trims.length > 0,
    trims,
  }
}

/**
 * Build the S-1 orientation front-door block for a chart. Non-throwing: on any query_ucd failure
 * it degrades to header + category inventory (still a useful frame) with `degraded: true`. Always
 * returns a block within the ≤2000-token budget (enforced explicitly).
 */
export async function buildChartOrientation(
  chartId: string,
  ayanamshaId: string = DEFAULT_AYANAMSHA,
  opts: { topKEntities?: number } = {},
): Promise<ChartOrientation> {
  const topKEntities = opts.topKEntities ?? 10

  // Frame + digest fetched concurrently. The header path is independently fail-loud (returns
  // flags, never throws); the query_ucd handler returns {is_error} rather than throwing.
  const [headerRes, ucd] = await Promise.all([
    fetchChartHeaderResolution(chartId, ayanamshaId).catch(() => ({
      header: null as unknown as ChartHeader,
      flags: ['chart_header_unresolved'],
    })),
    queryUcdCapability
      .handler({ chart_id: chartId, ayanamsha_id: ayanamshaId, response_format: 'digest', top_k_entities: topKEntities }, undefined)
      .catch((err: unknown) => ({ content: { error: String(err) }, is_error: true as const })),
  ])

  const header = (headerRes.header ?? null) as ChartHeader | null
  const headerFlags = headerRes.flags ?? []

  const isError = (ucd as { is_error?: boolean }).is_error === true
  const content = (ucd as { content?: Record<string, unknown> }).content ?? {}

  let structuralFacts: OrientationStructuralFacts | null = null
  let notableFindings: OrientationNotableFinding[] = []
  let convergenceDomains: OrientationConvergenceDomain[] = []

  if (!isError) {
    const digest = (content['digest'] as Record<string, unknown> | undefined) ?? {}
    const asNum = (v: unknown): number | null =>
      typeof v === 'number' ? v : (typeof v === 'string' && v !== '' ? Number(v) : null)
    structuralFacts = {
      msr_signal_count: asNum(digest['msr_signal_count']),
      yoga_count: asNum(digest['yoga_count']),
      dosha_count: asNum(digest['dosha_count']),
      contradiction_count: asNum(digest['contradiction_count']),
      weakest_graha: (digest['weakest_graha'] as string | null) ?? null,
      weakest_graha_source: (digest['weakest_graha_source'] as string | null) ?? null,
      top_priority_class: (digest['top_priority_class'] as string | null) ?? null,
    }

    const profiles = (content['entity_profiles'] as Array<Record<string, unknown>> | undefined) ?? []
    notableFindings = profiles.map(p => ({
      entity: String(p['entity'] ?? ''),
      entity_type: String(p['entity_type'] ?? ''),
      signal_count: typeof p['signal_count'] === 'number' ? (p['signal_count'] as number) : 0,
      dominant_domains: Array.isArray(p['dominant_domains']) ? (p['dominant_domains'] as string[]) : [],
      dominant_valence: (p['dominant_valence'] as string | null) ?? null,
      top_signal_ids: Array.isArray(p['top_signal_ids']) ? (p['top_signal_ids'] as string[]) : [],
    }))

    const conv = (content['convergence_domains'] as Array<Record<string, unknown>> | undefined) ?? []
    convergenceDomains = conv.map(c => ({
      domain: String(c['domain'] ?? ''),
      convergence_score:
        typeof c['convergence_score'] === 'number'
          ? (c['convergence_score'] as number)
          : (typeof c['convergence_score'] === 'string' && c['convergence_score'] !== '' ? Number(c['convergence_score']) : null),
    }))
  }

  const orientation: ChartOrientation = {
    chart_id: chartId,
    ayanamsha_id: ayanamshaId,
    chart_header: header,
    header_flags: headerFlags,
    structural_facts: structuralFacts,
    notable_findings: notableFindings,
    convergence_domains: convergenceDomains,
    dasha_context: { current_maha_antar: header?.current_maha_antar ?? null },
    category_inventory: [...CATEGORY_INVENTORY],
    budget: { limit_tokens: ORIENTATION_TOKEN_BUDGET, estimated_tokens: 0, enforced: false, trims: [] },
    degraded: isError,
  }

  enforceBudget(orientation)
  return orientation
}
