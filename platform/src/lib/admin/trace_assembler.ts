import 'server-only'
import type { StorageClient } from '@/lib/storage/types'
// baseline_resolver deleted WS-0C-2 (query_baseline_stats dropped in WS-0).
// TODO(ws-2): restore once query_baseline_stats is recreated.
const resolveBaseline = async (_: unknown, __: unknown) => null
import type {
  AssembledTrace,
  AuditStepMetadata,
  CheckpointStepMetadata,
  PipelineStage,
  PlannerStepMetadata,
  RetrievalSubToolRun,
  SynthesisStepMetadata,
  TraceQueryPlan,
  TraceStep,
} from '@/lib/trace/types'
import { mapStepToStage } from '@/lib/trace/types'

/**
 * Gate II (2026-05-12) — trace_assembler now sources its primary view from
 * the new emitter's `query_trace_steps` table and returns AssembledTrace,
 * the schema defined in lib/trace/types.ts. The legacy TraceDocument shape
 * is retained as a backward-compatible projection for consumers that have
 * not yet been migrated (HealthRail, QueryHeaderStrip, TimingRibbon, etc.).
 */

// ─────────────────────────────────────────────────────────────────────────────
// Legacy TraceDocument shape — kept for backward compatibility (deprecated).
// New code should use `AssembledTrace` from `@/lib/trace/types`.
// ─────────────────────────────────────────────────────────────────────────────

/** @deprecated since Gate II (2026-05-12). Use `AssembledTrace` from `@/lib/trace/types`. */
export interface TraceDocument {
  query: {
    id: string
    text: string | null
    type: string | null
    confidence: number | null
    total_ms: number | null
    total_cost_usd: number | null
    health: 'HEALTHY' | 'DEGRADED' | 'FAILED' | 'UNKNOWN'
  }
  /**
   * Legacy classifier slot. The new pipeline has no classifier stage —
   * this field is always `null` post-Gate II but kept on the interface so
   * existing renderers (HealthRail, TimingRibbon) continue to type-check
   * while they are migrated to AssembledTrace.
   */
  classify: {
    input: unknown
    alternatives: Array<{ type: string; confidence: number; rationale: string | null }>
    decision_reasoning: string | null
    latency_ms: number | null
    tokens: { input: number; output: number }
  } | null
  plan: {
    included_bundles: Array<{ name: string; rationale: string | null; expected_recall: number | null }>
    excluded_bundles: Array<{ name: string; rationale: string | null }>
    plan_json: unknown
    latency_ms: number | null
  } | null
  fetches: Array<{
    bundle: string
    step_order: number
    raw_count: number
    kept_count: number
    dropped_items: Array<{ item_id: string; score: number | null; drop_reason: string }>
    kept_items: Array<{ item_id: string; score: number | null; contribution_tokens: number | null }>
    latency_ms: number | null
    error_class: string
  }>
  /**
   * Legacy context-assembly slot. Stage retired in Pipeline-Transform-S1
   * (2026-05-11); kept on the interface (always `null`) for the same
   * migration-period reason as `classify` above.
   */
  context_assembly: {
    items: Array<{
      rank: number
      source_bundle: string
      source_item_id: string
      layer: string
      token_cost: number
      relevance_score: number | null
      status: 'INCLUDED' | 'TRUNCATED' | 'DROPPED'
      drop_reason: string | null
      cumulative_tokens: number
      budget: number
    }>
    token_ledger: {
      total: number
      budget: number
      preamble: number
      L1: number
      L2_5: number
      dropped_count: number
      truncated_count: number
    }
  } | null
  synthesis: {
    model: string | null
    input_tokens: number | null
    output_tokens: number | null
    latency_ms: number | null
    scorecard: unknown | null
  } | null
  baselines: {
    p50_total_latency_ms: number | null
    p95_total_latency_ms: number | null
    p50_total_cost_usd: number | null
    p95_total_cost_usd: number | null
    sample_size: number
  } | null
  anomalies: Array<{
    stage: string
    severity: 'ERROR' | 'WARNING' | 'INFO'
    message: string
    step_id: string | null
  }>
  partial: boolean
}

// ─────────────────────────────────────────────────────────────────────────────
// DB row types
// ─────────────────────────────────────────────────────────────────────────────

interface TraceStepRow {
  query_id: string
  conversation_id: string | null
  step_seq: number
  step_name: string
  step_type: TraceStep['step_type']
  status: TraceStep['status']
  started_at: string
  completed_at: string | null
  latency_ms: number | null
  parallel_group: string | null
  data_summary: unknown
  payload: unknown
}

// Gate II.5: aligned with production audit_events columns (migration 045 added D11 nullable cols).
interface AuditEventRow {
  audit_event_id: string      // audit_events.id aliased in SELECT
  audit_status: string        // 'ok' | 'warn' | 'block'
  audit_warnings: unknown     // jsonb array or null
  disclosure_tier: string | null
  b10_compliant: boolean | null
  b11_compliant: boolean | null
}

interface ScorecardRow {
  composite_score: number | null
  citation_density: number | null
  failures: unknown | null
}

// ─────────────────────────────────────────────────────────────────────────────
// Grouped projection — converts TraceStep[] into AssembledTrace.grouped
// ─────────────────────────────────────────────────────────────────────────────

function buildGrouped(steps: TraceStep[], audit: AuditEventRow | null): AssembledTrace['grouped'] {
  const byStage: Record<PipelineStage, TraceStep[]> = {
    planner: [], retrieval: [], synthesis: [], audit: [],
    checkpoint_4_5: [], checkpoint_5_5: [], checkpoint_8_5: [],
  }
  for (const s of steps) {
    const stage = mapStepToStage(s)
    if (stage) byStage[stage].push(s)
  }

  // Planning — classify = planner LLM call; compose_bundle = bundle hydration; plan_per_tool = per-tool refinement.
  const plannerLlm = byStage.planner.find(s => s.step_name === 'classify')
  const composeBundleStep = byStage.planner.find(s => s.step_name === 'compose_bundle')
  const planPerToolStep = byStage.planner.find(s => s.step_name === 'plan_per_tool')
  const plannerPayload = plannerLlm?.payload as
    | { query_plan?: TraceQueryPlan; tool_calls?: Array<{ tool_name: string; params: Record<string, unknown>; priority: 1 | 2 | 3; reason?: string }> }
    | undefined
  const planPerToolDs = planPerToolStep?.data_summary as
    | { tool_count?: number; planner_active?: boolean }
    | undefined
  const planner: PlannerStepMetadata | null = plannerLlm
    ? {
        step_seq: plannerLlm.step_seq,
        status: plannerLlm.status,
        latency_ms: plannerLlm.latency_ms ?? null,
        query_plan: plannerPayload?.query_plan ?? null,
        tool_calls: plannerPayload?.tool_calls ?? [],
        bundle_summary: composeBundleStep
          ? (composeBundleStep.data_summary as { result?: string })?.result ?? null
          : null,
        compose_bundle: composeBundleStep
          ? {
              latency_ms: composeBundleStep.latency_ms ?? null,
              result: (composeBundleStep.data_summary as { result?: string })?.result ?? null,
            }
          : null,
        plan_per_tool: planPerToolStep
          ? {
              step_seq: planPerToolStep.step_seq,
              latency_ms: planPerToolStep.latency_ms ?? null,
              tool_count: planPerToolDs?.tool_count ?? 0,
              planner_active: planPerToolDs?.planner_active ?? false,
            }
          : null,
      }
    : null

  // Retrieval — every parallel_group='tool_fetch' step is a sub-tool run.
  const retrieval: RetrievalSubToolRun[] = byStage.retrieval.map(s => ({
    tool_name: s.step_name,
    step_seq: s.step_seq,
    step_type: s.step_type,
    status: s.status,
    latency_ms: s.latency_ms ?? null,
    data_summary: s.data_summary,
    payload: s.payload,
  }))

  // Synthesis — discriminated by mode. Emitter has no `mode` field yet;
  // default to single_model (§I.2 in GAP_ANALYSIS).
  const synthStep = byStage.synthesis.find(s => s.step_name === 'synthesis' || s.step_name === 'synthesis_done')
  const ctxAssembly = byStage.synthesis.find(s => s.step_name === 'context_assembly')
  let synthesis: SynthesisStepMetadata | null = null
  if (synthStep) {
    const ds = synthStep.data_summary as {
      model?: string; input_tokens?: number; output_tokens?: number;
      citation_count?: number; provider?: string; reasoning_path?: boolean;
      output_shape_compliant?: boolean; temperature?: number;
    }
    const pl = synthStep.payload as { prompt_preview?: string; reasoning_trace?: string }
    const ctxDs = ctxAssembly?.data_summary as { short_circuited?: boolean; total_token_estimate?: number; threshold?: number; reason?: string } | undefined
    synthesis = {
      mode: 'single_model',
      step_seq: synthStep.step_seq,
      status: synthStep.status,
      latency_ms: synthStep.latency_ms ?? null,
      model: ds?.model ?? null,
      input_tokens: ds?.input_tokens ?? null,
      output_tokens: ds?.output_tokens ?? null,
      citation_count: ds?.citation_count ?? null,
      provider: ds?.provider ?? null,
      reasoning_path: ds?.reasoning_path ?? null,
      output_shape_compliant: ds?.output_shape_compliant ?? null,
      temperature: ds?.temperature ?? null,
      prompt_preview: pl?.prompt_preview ?? null,
      reasoning_trace: pl?.reasoning_trace ?? null,
      context_assembly_short_circuit: ctxDs
        ? {
            short_circuited: ctxDs.short_circuited === true,
            total_token_estimate: ctxDs.total_token_estimate ?? 0,
            threshold: ctxDs.threshold ?? 0,
            reason: ctxDs.reason ?? null,
          }
        : null,
    }
  }

  // Audit — citation_warn / citation_error trace steps + audit_events JOIN (Gate II.5: column names fixed).
  const citationStep = byStage.audit.find(s => s.step_name === 'citation_error' || s.step_name === 'citation_warn')

  // Map production audit_status values to the validator_verdict enum.
  function mapAuditStatus(s: string | undefined | null): AuditStepMetadata['validator_verdict'] {
    if (s === 'ok') return 'PASS'
    if (s === 'warn') return 'WARN'
    if (s === 'block') return 'ERROR'
    return 'UNKNOWN'
  }

  let auditMeta: AuditStepMetadata | null = null
  if (audit || citationStep) {
    const citationDs = citationStep?.data_summary as { result?: string; citation_count?: number } | undefined
    const rawWarnings = audit?.audit_warnings
    const auditWarnings: string[] | null = Array.isArray(rawWarnings)
      ? (rawWarnings as unknown[]).map(w => String(w))
      : null

    auditMeta = {
      audit_event_id: audit?.audit_event_id ?? null,
      audit_warnings: auditWarnings,
      disclosure_tier: audit?.disclosure_tier ?? null,
      validator_verdict: audit
        ? mapAuditStatus(audit.audit_status)
        : citationStep
          ? (citationStep.step_name === 'citation_error' ? 'ERROR' : 'WARN')
          : 'UNKNOWN',
      b10_compliant: audit?.b10_compliant ?? null,
      b11_compliant: audit?.b11_compliant ?? null,
      citation_gate: citationStep
        ? {
            result: citationStep.step_name === 'citation_error' ? 'ERROR' : 'WARN',
            reason: citationDs?.result ?? null,
            layer1_count: citationDs?.citation_count ?? null,
          }
        : null,
      placeholder_note: audit ? null : 'No audit_events row found for this query_id. Citation-gate signal (if any) is surfaced inline.',
    }
  } else {
    auditMeta = {
      audit_event_id: null,
      audit_warnings: null,
      disclosure_tier: null,
      validator_verdict: 'UNKNOWN',
      b10_compliant: null,
      b11_compliant: null,
      citation_gate: null,
      placeholder_note: 'Audit data is not on the trace stream; pipeline writes directly to audit_events. No row found for this query_id.',
    }
  }

  // Checkpoints — render dimmed when not emitted (D1).
  const cpStages: PipelineStage[] = ['checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5']
  const checkpoints: CheckpointStepMetadata[] = cpStages.map(stage => {
    const cpSteps = byStage[stage]
    const ran = cpSteps.length > 0
    const first = cpSteps[0]
    return {
      stage: stage as CheckpointStepMetadata['stage'],
      enabled: null,
      ran,
      status: first?.status ?? null,
      latency_ms: first?.latency_ms ?? null,
      verdict: ran ? 'PASS' : 'SKIPPED',
      notes: ran ? null : 'Checkpoint disabled or did not run',
    }
  })

  return { planner, retrieval, synthesis, audit: auditMeta, checkpoints }
}

// ─────────────────────────────────────────────────────────────────────────────
// Anomaly detectors (legacy TraceDocument projection)
// ─────────────────────────────────────────────────────────────────────────────

function detectAnomalies(
  retrieval: RetrievalSubToolRun[],
  synthesis: SynthesisStepMetadata | null,
  scorecard: ScorecardRow | null,
  planLatencyMs: number | null,
  baselineP50LatencyMs: number | null,
): TraceDocument['anomalies'] {
  const anomalies: TraceDocument['anomalies'] = []

  if (planLatencyMs !== null && baselineP50LatencyMs !== null && baselineP50LatencyMs > 0) {
    const ratio = planLatencyMs / baselineP50LatencyMs
    if (ratio > 2) {
      anomalies.push({
        stage: 'planner',
        severity: 'WARNING',
        message: `Planner latency ${planLatencyMs}ms (${ratio.toFixed(1)}× p50)`,
        step_id: null,
      })
    }
  }

  for (const r of retrieval) {
    if (r.status === 'error') {
      anomalies.push({
        stage: 'retrieval',
        severity: 'ERROR',
        message: `${r.tool_name} fetch failed`,
        step_id: null,
      })
    }
    const ds = r.data_summary as { rows_returned?: number; chunks_returned?: number }
    const kept = ds?.rows_returned ?? ds?.chunks_returned
    if (kept === 0 && r.status === 'done') {
      anomalies.push({
        stage: 'retrieval',
        severity: 'WARNING',
        message: `${r.tool_name} returned 0 items`,
        step_id: null,
      })
    }
  }

  if (synthesis?.mode === 'single_model' && synthesis.citation_count != null && synthesis.citation_count < 3) {
    anomalies.push({
      stage: 'synthesis',
      severity: 'WARNING',
      message: `Synthesis emitted ${synthesis.citation_count} citations (< 3)`,
      step_id: null,
    })
  }

  if (scorecard?.citation_density !== null && scorecard?.citation_density !== undefined && scorecard.citation_density < 0.5) {
    anomalies.push({
      stage: 'synthesis',
      severity: 'WARNING',
      message: `Synthesis citation density low`,
      step_id: null,
    })
  }

  return anomalies
}

function deriveHealth(
  retrieval: RetrievalSubToolRun[],
  scorecard: ScorecardRow | null,
): TraceDocument['query']['health'] {
  if (retrieval.some(r => r.status === 'error')) return 'FAILED'
  if (scorecard?.composite_score !== null && scorecard?.composite_score !== undefined
      && scorecard.composite_score < 0.5) return 'DEGRADED'
  if (retrieval.length === 0) return 'UNKNOWN'
  return 'HEALTHY'
}

// ─────────────────────────────────────────────────────────────────────────────
// Legacy TraceDocument projection — kept until consumers migrate.
// ─────────────────────────────────────────────────────────────────────────────

function projectLegacy(
  queryId: string,
  assembled: AssembledTrace,
  scorecard: ScorecardRow | null,
  baselines: TraceDocument['baselines'],
): TraceDocument {
  const { grouped, query_text, total_latency_ms } = assembled
  const planLatency = grouped.planner?.latency_ms ?? null
  const totalCost = 0 // no cost projection in the new model; left at 0 to avoid fabrication
  const anomalies = detectAnomalies(
    grouped.retrieval,
    grouped.synthesis,
    scorecard,
    planLatency,
    baselines?.p50_total_latency_ms ?? null,
  )

  const includedBundles = (grouped.planner?.tool_calls ?? []).map(tc => ({
    name: tc.tool_name,
    rationale: tc.reason ?? null,
    expected_recall: null,
  }))

  return {
    query: {
      id: queryId,
      text: query_text,
      type: grouped.planner?.query_plan?.query_class ?? null,
      confidence: grouped.planner?.query_plan?.router_confidence ?? null,
      total_ms: total_latency_ms,
      total_cost_usd: totalCost > 0 ? totalCost : null,
      health: deriveHealth(grouped.retrieval, scorecard),
    },
    classify: null,
    plan: grouped.planner
      ? {
          included_bundles: includedBundles,
          excluded_bundles: [],
          plan_json: grouped.planner.query_plan,
          latency_ms: grouped.planner.latency_ms,
        }
      : null,
    fetches: grouped.retrieval.map((r, idx) => {
      const ds = r.data_summary as { rows_returned?: number; chunks_returned?: number }
      const kept = ds?.rows_returned ?? ds?.chunks_returned ?? 0
      return {
        bundle: r.tool_name,
        step_order: idx,
        raw_count: kept,
        kept_count: kept,
        dropped_items: [],
        kept_items: [],
        latency_ms: r.latency_ms,
        error_class: r.status === 'error' ? 'ERROR' : 'OK',
      }
    }),
    context_assembly: null,
    synthesis: grouped.synthesis?.mode === 'single_model'
      ? {
          model: grouped.synthesis.model,
          input_tokens: grouped.synthesis.input_tokens,
          output_tokens: grouped.synthesis.output_tokens,
          latency_ms: grouped.synthesis.latency_ms,
          scorecard: scorecard,
        }
      : grouped.synthesis?.mode === 'panel'
        ? {
            model: grouped.synthesis.aggregator?.model ?? null,
            input_tokens: grouped.synthesis.aggregator?.input_tokens ?? null,
            output_tokens: grouped.synthesis.aggregator?.output_tokens ?? null,
            latency_ms: grouped.synthesis.latency_ms,
            scorecard: scorecard,
          }
        : null,
    baselines,
    anomalies,
    partial: assembled.partial,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

async function loadTraceSteps(queryId: string, db: StorageClient): Promise<TraceStep[]> {
  const r = await db.query<TraceStepRow>(
    `SELECT query_id, conversation_id, step_seq, step_name, step_type, status,
            started_at, completed_at, latency_ms, parallel_group, data_summary, payload
     FROM query_trace_steps
     WHERE query_id = $1::uuid
     ORDER BY step_seq ASC`,
    [queryId],
  ).catch(() => ({ rows: [] as TraceStepRow[] }))
  return r.rows.map(row => ({
    query_id: row.query_id,
    conversation_id: row.conversation_id ?? undefined,
    step_seq: row.step_seq,
    step_name: row.step_name,
    step_type: row.step_type,
    status: row.status,
    started_at: row.started_at,
    completed_at: row.completed_at ?? undefined,
    latency_ms: row.latency_ms ?? undefined,
    parallel_group: row.parallel_group ?? undefined,
    data_summary: (row.data_summary ?? {}) as TraceStep['data_summary'],
    payload: (row.payload ?? {}) as TraceStep['payload'],
  }))
}

async function loadAuditRow(queryId: string, db: StorageClient): Promise<AuditEventRow | null> {
  // Gate II.5: SELECT uses actual production column names (audit_events.id → audit_event_id alias).
  // disclosure_tier, b10_compliant, b11_compliant added via migration 045 (nullable; null until
  // audit writer populates — see POST_GATE_II_FOLLOWUPS FU.2).
  const r = await db.query<AuditEventRow>(
    `SELECT id AS audit_event_id,
            audit_status,
            audit_warnings,
            disclosure_tier,
            b10_compliant,
            b11_compliant
     FROM audit_events
     WHERE query_id = $1::uuid
     LIMIT 1`,
    [queryId],
  ).catch((err: unknown) => {
    console.warn('[trace_assembler] loadAuditRow failed:', err)
    return { rows: [] as AuditEventRow[] }
  })
  return r.rows[0] ?? null
}

async function loadScorecard(queryId: string, db: StorageClient): Promise<ScorecardRow | null> {
  const r = await db.query<ScorecardRow>(
    `SELECT composite_score, citation_density, failures
     FROM synthesis_quality_scorecard
     WHERE query_id = $1::uuid
     LIMIT 1`,
    [queryId],
  ).catch(() => ({ rows: [] as ScorecardRow[] }))
  return r.rows[0] ?? null
}

async function loadQueryText(queryId: string, db: StorageClient): Promise<string | null> {
  const r = await db.query<{ query_text: string | null }>(
    `SELECT query_text FROM query_plan_log WHERE query_id = $1::uuid LIMIT 1`,
    [queryId],
  ).catch(() => ({ rows: [] as Array<{ query_text: string | null }> }))
  return r.rows[0]?.query_text ?? null
}

/**
 * Assemble the full trace document for a query_id. Returns the new AssembledTrace
 * shape (from `@/lib/trace/types`), the legacy TraceDocument projection, and the
 * raw step list — all in one call so consumers can pick.
 */
export async function assembleTraceFull(
  queryId: string,
  db: StorageClient,
): Promise<{ assembled: AssembledTrace; legacy: TraceDocument; steps: TraceStep[] }> {
  const [steps, auditRow, scorecard, queryText, baselines] = await Promise.all([
    loadTraceSteps(queryId, db),
    loadAuditRow(queryId, db),
    loadScorecard(queryId, db),
    loadQueryText(queryId, db),
    resolveBaseline(null, db),
  ])

  const grouped = buildGrouped(steps, auditRow)
  const totalLatency = steps.reduce((sum, s) => sum + (s.latency_ms ?? 0), 0)

  // `satisfies AssembledTrace` — any drift in the AssembledTrace shape will
  // become a compile-time error here (added Gate II 2026-05-12 per W7).
  const assembled = {
    query_id: queryId,
    query_text: queryText,
    total_latency_ms: totalLatency > 0 ? totalLatency : null,
    query_plan: grouped.planner?.query_plan ?? null,
    steps,
    grouped,
    partial: steps.length === 0,
  } satisfies AssembledTrace

  const legacy = projectLegacy(queryId, assembled, scorecard, baselines)
  return { assembled, legacy, steps }
}

/**
 * Returns the legacy TraceDocument shape, projected from the new pipeline data.
 * @deprecated since Gate II. Prefer `assembleTraceFull` and read `.assembled` (AssembledTrace).
 */
export async function assembleTrace(
  queryId: string,
  db: StorageClient,
): Promise<TraceDocument> {
  const { legacy } = await assembleTraceFull(queryId, db)
  return legacy
}
