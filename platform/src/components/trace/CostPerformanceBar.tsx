'use client'

/**
 * CostPerformanceBar — BHISMA-B3 §5.4
 *
 * Footer KPI strip showing per-stage latency decomposition + cost estimate +
 * comparison against the 10-query rolling average. Reads from trace steps;
 * defensively guards every field that BHISMA-B2 will populate (synthesis_done
 * step, citation_count, etc.).
 *
 * The cost helper is inlined here to avoid colliding with BHISMA-B1's
 * telemetry/cost.ts which is shipping in parallel. If B1 lands cost.ts with a
 * canonical estimateQueryCost(), this file can swap to it later.
 */

import { Clock, DollarSign, Activity } from 'lucide-react'
import { getModelMeta } from '@/lib/models/registry'
import type { TraceStep } from '@/lib/trace/types'

interface Props {
  steps: TraceStep[]
  /** Rolling average across the last N queries — for "vs avg" comparison. Optional. */
  comparisonAvgMs?: number | null
}

// ── Stage extraction ─────────────────────────────────────────────────────────

interface StageBreakdown {
  plan_ms: number | null
  tool_fetch_ms: number | null
  assemble_ms: number | null
  synthesis_ms: number | null
  total_ms: number | null
}

function extractStages(steps: TraceStep[]): StageBreakdown {
  const planStep = steps.find(s => s.step_name === 'plan' || s.step_name === 'classify')
  const synthStep = steps.find(s => s.step_name === 'synthesis_done' || s.step_name === 'synthesis')
  const ctxStep = steps.find(s => s.step_name === 'context_assembly')

  const toolSteps = steps.filter(s =>
    s.parallel_group === 'tool_fetch'
    || (s.step_type === 'sql' || s.step_type === 'vector' || s.step_type === 'gcs')
  )

  // tool_fetch wall-clock = max(end) - min(start) across the parallel group
  let toolFetchMs: number | null = null
  if (toolSteps.length > 0) {
    const completed = toolSteps.filter(s => s.completed_at)
    if (completed.length > 0) {
      const starts = completed.map(s => new Date(s.started_at).getTime())
      const ends = completed.map(s => new Date(s.completed_at!).getTime())
      toolFetchMs = Math.max(...ends) - Math.min(...starts)
    }
  }

  const doneSteps = steps.filter(s => s.completed_at)
  let totalMs: number | null = null
  if (doneSteps.length > 0) {
    const starts = doneSteps.map(s => new Date(s.started_at).getTime())
    const ends = doneSteps.map(s => new Date(s.completed_at!).getTime())
    totalMs = Math.max(...ends) - Math.min(...starts)
  }

  return {
    plan_ms: planStep?.latency_ms ?? null,
    tool_fetch_ms: toolFetchMs,
    assemble_ms: ctxStep?.latency_ms ?? null,
    synthesis_ms: synthStep?.latency_ms ?? null,
    total_ms: totalMs,
  }
}

// ── Cost extraction (inline, B1-compatible shape) ────────────────────────────

interface CostBreakdown {
  rows: Array<{ label: string; usd: number }>
  total_usd: number
}

// Client-side computation kept as a defense — DB-backed cost_usd in
// llm_call_log is populated as of GANGA-OVERNIGHT-S1 P2, but a recent or in-
// flight trace may still surface here before the fire-and-forget DB write
// lands. Pricing for the NIM (nvidia) free tier is non-zero in the registry,
// so NIM rows here will show a notional dollar value even though NIM is
// billed separately.
function extractCost(steps: TraceStep[]): CostBreakdown {
  const llmSteps = steps.filter(s => s.step_type === 'llm' && s.status === 'done')
  const rows: Array<{ label: string; usd: number }> = []
  let total = 0

  for (const step of llmSteps) {
    const modelId = step.data_summary.model
    const inputTokens = step.data_summary.input_tokens ?? 0
    const outputTokens = step.data_summary.output_tokens ?? 0
    if (!modelId || (inputTokens === 0 && outputTokens === 0)) continue

    const meta = getModelMeta(modelId)
    if (!meta) {
      // Unknown model — show N/A row so the step is visible without crashing
      rows.push({ label: modelId, usd: NaN })
      continue
    }

    const usd =
      (inputTokens / 1_000_000) * meta.costPer1MInput +
      (outputTokens / 1_000_000) * meta.costPer1MOutput
    total += usd

    // Compact label: short model name, no provider prefix
    const shortLabel = meta.label.replace(/^(GPT|Claude|Gemini|DeepSeek)\s*/i, '')
    rows.push({ label: shortLabel || meta.label, usd })
  }

  return { rows, total_usd: total }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// I.3: fmtCost handles null (N/A) and zero ($0) distinctly.
// null = cost not available (unknown model or no tokens); zero = model is free tier.
function fmtCost(usd: number | null | undefined): string {
  if (usd == null) return 'N/A'
  if (usd === 0) return '$0'
  if (usd < 0.001) return `<$0.001`
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  if (usd < 1) return `$${usd.toFixed(3)}`
  return `$${usd.toFixed(2)}`
}

// ── Component ────────────────────────────────────────────────────────────────

export function CostPerformanceBar({ steps, comparisonAvgMs }: Props) {
  const stages = extractStages(steps)
  const cost = extractCost(steps)

  const hasAnyStage =
    stages.plan_ms != null ||
    stages.tool_fetch_ms != null ||
    stages.assemble_ms != null ||
    stages.synthesis_ms != null

  if (!hasAnyStage && cost.rows.length === 0) {
    // Don't render the bar until at least one stage has data.
    return null
  }

  // Comparison vs rolling avg
  let comparisonNode: React.ReactNode = null
  if (comparisonAvgMs != null && stages.total_ms != null && comparisonAvgMs > 0) {
    const deltaPct = ((stages.total_ms - comparisonAvgMs) / comparisonAvgMs) * 100
    const isFaster = deltaPct < 0
    comparisonNode = (
      <span className={`text-[10px] ${isFaster ? 'text-[rgba(140,210,170,0.85)]' : 'text-[rgba(240,170,100,0.85)]'}`}>
        vs avg: {isFaster ? '−' : '+'}{Math.abs(deltaPct).toFixed(0)}% {isFaster ? 'faster' : 'slower'}
      </span>
    )
  }

  return (
    <div className="border-t border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.7)] px-4 py-2 flex-shrink-0">
      {/* Top row: stage cells */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Activity size={10} className="text-[rgba(212,175,55,0.5)]" />
          <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.5)]">Performance</span>
        </div>

        <div className="flex items-center gap-px flex-1 max-w-md">
          <StageCell label="Plan"     value={stages.plan_ms} />
          <StageCell label="Fetch"    value={stages.tool_fetch_ms} />
          <StageCell label="Assemble" value={stages.assemble_ms} />
          <StageCell label="Synth"    value={stages.synthesis_ms} />
        </div>

        <div className="flex items-center gap-2 ml-auto">
          {comparisonNode}
          <span className="text-[11px] font-semibold text-[rgba(252,226,154,0.85)] tabular-nums">
            {fmtMs(stages.total_ms)}
          </span>
        </div>
      </div>

      {/* Bottom row: cost breakdown */}
      {cost.rows.length > 0 && (
        <div className="flex items-center gap-2 mt-1.5 pt-1.5 border-t border-[rgba(212,175,55,0.06)]">
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <DollarSign size={10} className="text-[rgba(212,175,55,0.5)]" />
            <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.5)]">Cost</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {cost.rows.map((row, i) => (
              <span key={`${row.label}-${i}`} className="text-[10px] text-[rgba(252,226,154,0.65)]">
                <span className="text-[rgba(212,175,55,0.5)]">{row.label}</span>
                <span className="ml-1 tabular-nums">{fmtCost(row.usd)}</span>
              </span>
            ))}
          </div>

          <span className="text-[11px] font-semibold text-[rgba(252,226,154,0.85)] tabular-nums ml-auto">
            {cost.rows.some(r => isNaN(r.usd)) ? 'N/A' : fmtCost(cost.total_usd)}
          </span>
        </div>
      )}
    </div>
  )
}

function StageCell({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex flex-col items-center px-2 py-0.5 bg-[rgba(212,175,55,0.04)] border border-[rgba(212,175,55,0.10)] flex-1 min-w-[64px]">
      <span className="text-[8px] uppercase tracking-[0.1em] text-[rgba(212,175,55,0.45)]">{label}</span>
      <span className="text-[10px] font-semibold text-[rgba(252,226,154,0.8)] tabular-nums">
        {fmtMs(value)}
      </span>
    </div>
  )
}

// ── Compact total-only summary for collapsed display ─────────────────────────

export function CostPerformanceCompactSummary({ steps }: { steps: TraceStep[] }) {
  const stages = extractStages(steps)
  const cost = extractCost(steps)
  if (stages.total_ms == null && cost.rows.length === 0) return null

  return (
    <div className="flex items-center gap-2 text-[10px] text-[rgba(212,175,55,0.55)] tabular-nums">
      <Clock size={9} />
      <span>{fmtMs(stages.total_ms)}</span>
      {cost.total_usd > 0 && (
        <>
          <span className="text-[rgba(212,175,55,0.3)]">·</span>
          <span>{fmtCost(cost.total_usd)}</span>
        </>
      )}
    </div>
  )
}
