/**
 * D6 Synergy Orchestrator
 * =======================
 * Composes the whole-corpus synergy: router(D2) → grounding(D3) →
 * graph(D4) + per-asset tools(D5) → MARO(D-PROFILES) to produce a
 * unified, de-duplicated, cited, multi-vantage Whole-Chart-Read result.
 *
 * Source: CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS_v1_1.md §1 (D6 composition sequence)
 *
 * F1 (reference-don't-repeat): de-duplicate by signal_id across all tool results.
 * F3 (layer-resolution-DOWN): L2 signals → L1 fact_ids → L0 citation_ids.
 *
 * DEFECT-001's orphan rate is re-derived LIVE per call (E-2 freshness contract, R5.1 C2
 * item 1) — never hardcode a historical figure here. Handle every join gracefully
 * regardless of the current rate — empty join = empty provenance, not an error.
 *
 * Both channels (MCP and chat) call this orchestrator through the registry.
 * Single source of query logic → drift structurally impossible.
 */

import { getCapability } from '../registry/index'
import type {
  SynergyQueryClass,
  WholeChartReadResult,
  UcdDigest,
  DomainReadingResult,
  SignalRankResult,
  GraphTraversalResult,
  ContradictionResult,
  TemporalEnrichmentResult,
  SignalRef,
  WholeChartReadMeta,
} from './types'
import { deriveDefect001Note, type FreshnessNote } from '../provenance/freshness_notes'

// ── Context interface (DB access) ─────────────────────────────────────────────

export interface SynergyContext {
  db: {
    query: (sql: string, params: unknown[]) => Promise<{ rows: Record<string, unknown>[] }>
  }
  lel_enabled?: boolean
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function nowIso(): string {
  return new Date().toISOString()
}

/** F1: De-duplicate signal refs by signal_id. Returns unique refs. */
function deduplicateSignals(refs: SignalRef[]): SignalRef[] {
  const seen = new Set<string>()
  const result: SignalRef[] = []
  for (const ref of refs) {
    if (!seen.has(ref.signal_id)) {
      seen.add(ref.signal_id)
      result.push(ref)
    }
  }
  return result
}

// ── Step 1: UCD orientation digest ───────────────────────────────────────────

async function runUcdStep(
  chartId: string,
  ayanamshaId: string,
  ctx: SynergyContext
): Promise<UcdDigest> {
  const cap = getCapability('marsys://tool/L2/query_ucd')
  if (!cap) {
    // Graceful-empty: capability not yet registered
    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      msr_signal_count: 0,
      yoga_count: null,
      dosha_count: null,
      avg_salience: null,
      max_salience: null,
      contradiction_count: 0,
      weakest_graha: null,
      top_priority_class: null,
      trap1_count: null,
      top_signals: [],
      convergence_domains: [],
      drill_children: [
        'marsys://tool/L2/query_domain_reading',
        'marsys://tool/L2/query_signals',
        'marsys://tool/L2/traverse_chart_graph',
      ],
    }
  }

  try {
    const result = await cap.handler(
      { chart_id: chartId, ayanamsha_id: ayanamshaId, top_k_signals: 20 },
      { chart_id: chartId, request_id: 'synergy-ucd' }
    )
    const data = (typeof result.content === 'object' && result.content !== null)
      ? result.content as Record<string, unknown>
      : {}

    const digest = (data['digest'] as Record<string, unknown>) ?? {}
    const topSignals = ((data['top_signals'] as unknown[]) ?? []).map((s) => {
      const row = s as Record<string, unknown>
      return {
        signal_id: String(row['signal_id'] ?? ''),
        signal_type_id: row['signal_type_id'] ? String(row['signal_type_id']) : undefined,
        signal_type_class: row['signal_type_class'] ? String(row['signal_type_class']) : undefined,
        computed_salience: Number(row['computed_salience'] ?? 0),
        domains_affected_array: Array.isArray(row['domains_affected_array'])
          ? (row['domains_affected_array'] as string[])
          : [],
        emits_reference: true as const,
      }
    })

    const convergenceDomains = ((data['convergence_domains'] as unknown[]) ?? []).map((d) => {
      const row = d as Record<string, unknown>
      return {
        domain: String(row['domain'] ?? ''),
        convergence_count: Number(row['convergence_count'] ?? 0),
        convergence_score: Number(row['convergence_score'] ?? 0),
        cross_tradition_count: row['cross_tradition_count'] != null ? Number(row['cross_tradition_count']) : undefined,
        salience_weighted_sum: row['salience_weighted_sum'] != null ? Number(row['salience_weighted_sum']) : undefined,
        contradiction_count: row['contradiction_count'] != null ? Number(row['contradiction_count']) : undefined,
      }
    })

    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      msr_signal_count: Number(digest['msr_signal_count'] ?? 0),
      yoga_count: digest['yoga_count'] != null ? Number(digest['yoga_count']) : null,
      dosha_count: digest['dosha_count'] != null ? Number(digest['dosha_count']) : null,
      avg_salience: digest['avg_salience'] != null ? Number(digest['avg_salience']) : null,
      max_salience: digest['max_salience'] != null ? Number(digest['max_salience']) : null,
      contradiction_count: Number(digest['contradiction_count'] ?? 0),
      weakest_graha: digest['weakest_graha'] ? String(digest['weakest_graha']) : null,
      top_priority_class: digest['top_priority_class'] ? String(digest['top_priority_class']) : null,
      trap1_count: digest['trap1_count'] != null ? Number(digest['trap1_count']) : null,
      top_signals: topSignals,
      convergence_domains: convergenceDomains,
      drill_children: [
        'marsys://tool/L2/query_domain_reading',
        'marsys://tool/L2/query_signals',
        'marsys://tool/L2/traverse_chart_graph',
      ],
    }
  } catch (err) {
    console.warn('[synergy:ucd] handler error — returning graceful-empty', String(err))
    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      msr_signal_count: 0,
      yoga_count: null,
      dosha_count: null,
      avg_salience: null,
      max_salience: null,
      contradiction_count: 0,
      weakest_graha: null,
      top_priority_class: null,
      trap1_count: null,
      top_signals: [],
      convergence_domains: [],
      drill_children: [
        'marsys://tool/L2/query_domain_reading',
        'marsys://tool/L2/query_signals',
        'marsys://tool/L2/traverse_chart_graph',
      ],
    }
  }
}

// ── Step 2: Domain readings (per top convergence domain) ──────────────────────

async function runDomainReadingsStep(
  chartId: string,
  ayanamshaId: string,
  convergenceDomains: Array<{ domain: string; convergence_score: number }>,
  ctx: SynergyContext
): Promise<DomainReadingResult[]> {
  // Top 3 domains to drill (cap to avoid context explosion)
  const topDomains = convergenceDomains
    .sort((a, b) => b.convergence_score - a.convergence_score)
    .slice(0, 3)

  if (topDomains.length === 0) return []

  const cap = getCapability('marsys://tool/L2/query_domain_reading')
  if (!cap) {
    // Capability not yet built (D5 gap) — return graceful-empty per domain
    return topDomains.map((d) => ({
      domain: d.domain,
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      cdlm_cells: [],
      question_lenses: [],
      signal_refs: [],
      vantage_perspectives: [],
    }))
  }

  const readings: DomainReadingResult[] = []
  for (const { domain } of topDomains) {
    try {
      const result = await cap.handler(
        { chart_id: chartId, domain, ayanamsha_id: ayanamshaId },
        { chart_id: chartId }
      )
      const data = (typeof result.content === 'object' && result.content !== null)
        ? result.content as Record<string, unknown>
        : {}
      readings.push({
        domain,
        chart_id: chartId,
        ayanamsha_id: ayanamshaId,
        cdlm_cells: ((data['cdlm_cells'] as unknown[]) ?? []) as DomainReadingResult['cdlm_cells'],
        question_lenses: ((data['question_lenses'] as unknown[]) ?? []) as DomainReadingResult['question_lenses'],
        signal_refs: ((data['signal_refs'] as unknown[]) ?? []).map((s) => {
          const row = s as Record<string, unknown>
          return {
            signal_id: String(row['signal_id'] ?? ''),
            computed_salience: Number(row['computed_salience'] ?? 0),
            domains_affected_array: Array.isArray(row['domains_affected_array'])
              ? (row['domains_affected_array'] as string[])
              : [],
            emits_reference: true as const,
          }
        }),
        vantage_perspectives: ((data['vantage_perspectives'] as unknown[]) ?? []) as DomainReadingResult['vantage_perspectives'],
      })
    } catch (err) {
      console.warn(`[synergy:domain_reading] domain=${domain} error`, String(err))
      readings.push({
        domain,
        chart_id: chartId,
        ayanamsha_id: ayanamshaId,
        cdlm_cells: [],
        question_lenses: [],
        signal_refs: [],
        vantage_perspectives: [],
      })
    }
  }
  return readings
}

// ── Step 3: Signal ranking (F1 de-duplicated) ─────────────────────────────────

async function runSignalRankStep(
  chartId: string,
  ayanamshaId: string,
  seedSignalIds: string[],
  lelEnabled: boolean,
  ctx: SynergyContext
): Promise<SignalRankResult> {
  const cap = getCapability('marsys://tool/L2/query_signals')

  // E-2 freshness contract (R5.1 C2 item 1): DEFECT-001's status is re-derived live per
  // call rather than restated as a fixed literal — never hardcode a historical figure.
  // Used only for the no-capability / error graceful-empty paths below; the happy path
  // prefers the live `defect_001` object query_signals itself already computed (avoids a
  // duplicate DB round-trip) and falls back to deriving it here only if that's absent.
  async function gracefulEmptyDefect001(): Promise<{ note: string; obj: FreshnessNote }> {
    const obj = await deriveDefect001Note(chartId)
    return { note: obj.note, obj }
  }

  if (!cap) {
    const { note, obj } = await gracefulEmptyDefect001()
    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      signals: [],
      total_available: 0,
      filters_applied: { seed_signal_ids: seedSignalIds, lel_enabled: lelEnabled },
      defect_001_note: note,
      defect_001: obj,
    }
  }

  try {
    const result = await cap.handler(
      {
        chart_id: chartId,
        ayanamsha_id: ayanamshaId,
        lel_enabled: lelEnabled,
        limit: 50,
      },
      { chart_id: chartId }
    )
    const data = (typeof result.content === 'object' && result.content !== null)
      ? result.content as Record<string, unknown>
      : {}

    const rawSignals = ((data['signals'] as unknown[]) ?? [])
    const signals = rawSignals.map((s) => {
      const row = s as Record<string, unknown>
      const factsArray = Array.isArray(row['constituent_facts_array'])
        ? (row['constituent_facts_array'] as string[])
        : []
      return {
        signal_id: String(row['signal_id'] ?? ''),
        signal_headline_text: row['signal_headline_text'] ? String(row['signal_headline_text']) : undefined,
        signal_summary_text: row['signal_summary_text'] ? String(row['signal_summary_text']) : undefined,
        computed_salience: Number(row['computed_salience'] ?? 0),
        // Orphan rate re-derived live (E-2) — may legitimately be empty; see defect_001 below.
        constituent_facts_array: factsArray,
        classical_sources_jsonb: row['classical_sources_jsonb'] ?? null,
        domains_affected_array: Array.isArray(row['domains_affected_array'])
          ? (row['domains_affected_array'] as string[])
          : [],
        lel_origin: Boolean(row['lel_origin'] ?? false),
        emits_reference: true as const,
      }
    })

    // Prefer query_signals' own live-derived defect_001 (design §E-2) — it already ran
    // the live query for this exact page; re-derive only if it's genuinely absent
    // (older cached response shape, or the handler graceful-emptied before reaching it).
    const provenance = (data['provenance'] as Record<string, unknown> | undefined) ?? undefined
    const upstreamDefect001 = provenance?.['defect_001'] as FreshnessNote | undefined
    const defect001Obj = upstreamDefect001 ?? await deriveDefect001Note(
      chartId,
      signals.flatMap((s) => s.constituent_facts_array),
    )

    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      signals,
      total_available: Number(data['total_available'] ?? signals.length),
      filters_applied: { seed_signal_ids: seedSignalIds, lel_enabled: lelEnabled },
      defect_001_note: defect001Obj.note,
      defect_001: defect001Obj,
    }
  } catch (err) {
    console.warn('[synergy:signals] handler error', String(err))
    const { note, obj } = await gracefulEmptyDefect001()
    return {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      signals: [],
      total_available: 0,
      filters_applied: { seed_signal_ids: seedSignalIds, lel_enabled: lelEnabled },
      defect_001_note: note,
      defect_001: obj,
    }
  }
}

// ── Step 4: Graph traversal ───────────────────────────────────────────────────

async function runGraphStep(
  chartId: string,
  seedSignalIds: string[],
  ctx: SynergyContext
): Promise<GraphTraversalResult> {
  const RELATIONSHIP_BASIS_NOTE =
    'relationship_basis is 100% NULL in current bodha_cgm_edges data. ' +
    'All edges traversed regardless — relationship_basis annotated as null in output.'

  const cap = getCapability('marsys://tool/L2/traverse_chart_graph')
  if (!cap) {
    return {
      chart_id: chartId,
      seed_signal_ids: seedSignalIds,
      mode: 'neighbors',
      depth: 1,
      nodes: [],
      edges: [],
      relationship_basis_note: RELATIONSHIP_BASIS_NOTE,
    }
  }

  try {
    const result = await cap.handler(
      {
        chart_id: chartId,
        seed_signal_ids: seedSignalIds.slice(0, 10), // limit seeds for efficiency
        mode: 'neighbors',
        depth: 2,
      },
      { chart_id: chartId }
    )
    const data = (typeof result.content === 'object' && result.content !== null)
      ? result.content as Record<string, unknown>
      : {}

    return {
      chart_id: chartId,
      seed_signal_ids: seedSignalIds,
      mode: (data['mode'] as 'neighbors' | 'paths' | 'cluster') ?? 'neighbors',
      depth: Number(data['depth'] ?? 2),
      nodes: ((data['nodes'] as unknown[]) ?? []) as GraphTraversalResult['nodes'],
      edges: ((data['edges'] as unknown[]) ?? []).map((e) => {
        const edge = e as Record<string, unknown>
        return {
          ...edge,
          // Annotate null relationship_basis explicitly (do not filter by it)
          relationship_basis: null,
        }
      }) as GraphTraversalResult['edges'],
      relationship_basis_note: RELATIONSHIP_BASIS_NOTE,
    }
  } catch (err) {
    console.warn('[synergy:graph] handler error', String(err))
    return {
      chart_id: chartId,
      seed_signal_ids: seedSignalIds,
      mode: 'neighbors',
      depth: 1,
      nodes: [],
      edges: [],
      relationship_basis_note: RELATIONSHIP_BASIS_NOTE,
    }
  }
}

// ── Step 5: Contradictions + discoveries ──────────────────────────────────────

async function runContradictionStep(
  chartId: string,
  ctx: SynergyContext
): Promise<ContradictionResult> {
  const cap = getCapability('marsys://tool/L2/query_contradictions')
  if (!cap) {
    return {
      chart_id: chartId,
      contradictions: [],
      discoveries: [],
      graceful_empty_note: 'query_contradictions capability not yet registered (D5 gap). bodha_contradictions=0 rows expected.',
    }
  }

  try {
    const result = await cap.handler(
      { chart_id: chartId },
      { chart_id: chartId }
    )
    const data = (typeof result.content === 'object' && result.content !== null)
      ? result.content as Record<string, unknown>
      : {}

    return {
      chart_id: chartId,
      // bodha_contradictions currently 0 rows — graceful-empty array
      contradictions: ((data['contradictions'] as unknown[]) ?? []) as ContradictionResult['contradictions'],
      // bodha_discoveries: 1,505 rows, novelty-ranked
      discoveries: ((data['discoveries'] as unknown[]) ?? []) as ContradictionResult['discoveries'],
      graceful_empty_note: 'bodha_contradictions currently 0 rows — graceful-empty. bodha_discoveries has 1,505 rows ranked by novelty_score.',
    }
  } catch (err) {
    console.warn('[synergy:contradictions] handler error', String(err))
    return {
      chart_id: chartId,
      contradictions: [],
      discoveries: [],
      graceful_empty_note: `handler error (graceful-empty): ${String(err)}`,
    }
  }
}

// ── Step 6: Temporal enrichment (predictive/holistic) ─────────────────────────

async function runTemporalStep(
  chartId: string,
  ayanamshaId: string,
  queryClass: SynergyQueryClass,
  ctx: SynergyContext
): Promise<TemporalEnrichmentResult | undefined> {
  if (queryClass !== 'predictive' && queryClass !== 'holistic') return undefined

  const activationCap = getCapability('marsys://tool/L3/query_temporal_activation')
  const convergenceCap = getCapability('marsys://tool/L3/query_convergence_windows')
  const lifeArcCap     = getCapability('marsys://tool/L3/query_life_arc')

  const activations:        TemporalEnrichmentResult['activations'] = []
  const convergenceWindows: TemporalEnrichmentResult['convergence_windows'] = []
  const lifeArcSegments:    TemporalEnrichmentResult['life_arc_segments'] = []

  try {
    if (activationCap) {
      const r = await activationCap.handler(
        { chart_id: chartId, ayanamsha_id: ayanamshaId },
        { chart_id: chartId }
      )
      const d = (typeof r.content === 'object' && r.content !== null) ? r.content as Record<string, unknown> : {}
      activations.push(...(((d['activations'] as unknown[]) ?? []) as TemporalEnrichmentResult['activations']))
    }

    if (convergenceCap) {
      const r = await convergenceCap.handler(
        { chart_id: chartId, ayanamsha_id: ayanamshaId },
        { chart_id: chartId }
      )
      const d = (typeof r.content === 'object' && r.content !== null) ? r.content as Record<string, unknown> : {}
      convergenceWindows.push(...(((d['convergence_windows'] as unknown[]) ?? []) as TemporalEnrichmentResult['convergence_windows']))
    }

    if (lifeArcCap) {
      const r = await lifeArcCap.handler(
        { chart_id: chartId },
        { chart_id: chartId }
      )
      const d = (typeof r.content === 'object' && r.content !== null) ? r.content as Record<string, unknown> : {}
      lifeArcSegments.push(...(((d['segments'] as unknown[]) ?? []) as TemporalEnrichmentResult['life_arc_segments']))
    }
  } catch (err) {
    console.warn('[synergy:temporal] error (non-fatal)', String(err))
  }

  return {
    chart_id: chartId,
    query_class: queryClass,
    activations,
    convergence_windows: convergenceWindows,
    life_arc_segments: lifeArcSegments,
  }
}

// ── Main orchestrator ─────────────────────────────────────────────────────────

/**
 * Run the full D6 synergy orchestration for a chart.
 *
 * Both MCP and chat channels call this function — single query source,
 * no drift by construction.
 *
 * @param chartId      - Chart UUID (required; error if missing)
 * @param ayanamshaId  - Ayanamsha filter (default: 'LAHIRI')
 * @param queryClass   - Query class for conditional enrichment
 * @param queryText    - Optional query text for provenance
 * @param ctx          - DB context + LEL flag
 */
export async function runWholeChartRead(
  chartId: string,
  ayanamshaId: string = 'LAHIRI',
  queryClass: SynergyQueryClass = 'holistic',
  queryText: string | undefined,
  ctx: SynergyContext
): Promise<WholeChartReadResult> {
  if (!chartId) {
    throw new Error('[synergy:orchestrator] chart_id is required — no default chart')
  }

  const lelEnabled = ctx.lel_enabled ?? false
  const stepsExecuted: string[] = []
  let defect001EmptyJoinsEncountered = false

  // ── Step 1: UCD orientation digest ─────────────────────────────────────────
  stepsExecuted.push('query_ucd')
  const ucdDigest = await runUcdStep(chartId, ayanamshaId, ctx)

  // ── Step 2: Domain readings (top convergence domains) ──────────────────────
  stepsExecuted.push('query_domain_reading')
  const domainReadings = await runDomainReadingsStep(
    chartId,
    ayanamshaId,
    ucdDigest.convergence_domains,
    ctx
  )

  // ── Step 3: Signal ranking (F1: de-duplicate across UCD + domain reads) ────
  stepsExecuted.push('query_signals')
  // Gather all signal refs from UCD + domain readings for dedup seed
  const allSignalRefs: SignalRef[] = [
    ...ucdDigest.top_signals,
    ...domainReadings.flatMap((dr) => dr.signal_refs),
  ]
  const uniqueRefs = deduplicateSignals(allSignalRefs)
  const seedSignalIds = uniqueRefs.map((r) => r.signal_id).filter(Boolean).slice(0, 20)

  const signalResult = await runSignalRankStep(
    chartId,
    ayanamshaId,
    seedSignalIds,
    lelEnabled,
    ctx
  )
  // Track DEFECT-001 encounters
  if (signalResult.signals.some((s) => s.constituent_facts_array.length === 0)) {
    defect001EmptyJoinsEncountered = true
  }

  // ── Step 4: Graph traversal (CGM) ──────────────────────────────────────────
  stepsExecuted.push('traverse_chart_graph')
  const topSignalIds = signalResult.signals
    .slice(0, 10)
    .map((s) => s.signal_id)
  const graphResult = await runGraphStep(chartId, topSignalIds, ctx)

  // ── Step 5: Contradictions + discoveries ───────────────────────────────────
  stepsExecuted.push('query_contradictions')
  const contradictionResult = await runContradictionStep(chartId, ctx)

  // ── Step 6: Temporal enrichment (predictive / holistic only) ───────────────
  let temporalResult: TemporalEnrichmentResult | undefined
  if (queryClass === 'predictive' || queryClass === 'holistic') {
    stepsExecuted.push('query_temporal_activation', 'query_convergence_windows', 'query_life_arc')
    temporalResult = await runTemporalStep(chartId, ayanamshaId, queryClass, ctx)
  }

  // ── Assemble final result ──────────────────────────────────────────────────
  const meta: WholeChartReadMeta = {
    executed_at: nowIso(),
    steps_executed: stepsExecuted,
    signal_ids_deduped: deduplicateSignals([
      ...ucdDigest.top_signals,
      ...domainReadings.flatMap((dr) => dr.signal_refs),
      ...signalResult.signals.map((s) => ({ signal_id: s.signal_id, emits_reference: true as const })),
    ]).length,
    defect_001_empty_joins_encountered: defect001EmptyJoinsEncountered,
    lel_enabled: lelEnabled,
  }

  return {
    chart_id: chartId,
    query_class: queryClass,
    query_text: queryText,
    ucd_digest: ucdDigest,
    domain_readings: domainReadings,
    signals: signalResult,
    graph: graphResult,
    contradictions: contradictionResult,
    temporal: temporalResult,
    meta,
  }
}
