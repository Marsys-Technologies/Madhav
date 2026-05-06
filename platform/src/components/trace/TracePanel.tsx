'use client'

/**
 * MARSYS-JIS Query Trace Panel
 *
 * v2.0 (BHISMA-B3, 2026-05-01):
 *  - Full warm-gold re-skin per §5.1 (no cold slate palette anywhere)
 *  - QueryDNAPanel above the timeline (§5.2)
 *  - CostPerformanceBar in the footer (§5.4) above the wall-clock TimelineBar
 *  - RetrievalScorecard mounted in ContextInspector when a tool step is selected (§5.3)
 *  - Inline SynthesisQualityIndicators below the context summary (§5.5)
 *  - History tab gains an Analytics sub-tab (§5.7)
 *  - Single-click chunk expand (§5.8 GAP.T.10), inline error message display (§5.8)
 *
 * Right-side drawer (65vw) showing real-time pipeline execution for any query.
 * Opens from the ⚡ TRACE button in the ConsumeChat input area.
 */

import { useState, useMemo } from 'react'
import { X, ChevronRight, ChevronDown, Clock, Layers, Database, Zap, AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { useTraceStream } from '@/hooks/useTraceStream'
import type { TraceStep, TraceChunkItem, TraceHistoryRow } from '@/lib/trace/types'
import { getModelMeta } from '@/lib/models/registry'
import { QueryDNAPanel } from './QueryDNAPanel'
import { CostPerformanceBar } from './CostPerformanceBar'
import { RetrievalScorecard, RetrievalEfficiency } from './RetrievalScorecard'
import { AnalyticsTab } from './AnalyticsTab'
import { PipelineLifecycleView } from './PipelineLifecycleView'
import { ToolCoverageMatrix } from './ToolCoverageMatrix'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Props {
  queryId: string | null
  isSuperAdmin: boolean
  onClose: () => void
}

// TODO(J.1): TracePanel and QueryDNAPanel use hardcoded rgba() colour values.
// Once the R7 portal design system publishes CSS variables (e.g. --color-gold,
// --color-violet, --color-error) or Tailwind tokens, replace the inline rgba()
// strings below with those tokens. Track missing tokens as design-system-owner
// requests. Current palette reference: §5.1 warm-gold scheme (BHISMA-B3).
// TODO(J.2): TracePanel has no React context dependencies beyond useTraceStream
// (which is self-contained). No missing providers identified for R7 shell
// integration. If a ThemeProvider or AuthContext is added to the R7 shell,
// verify TracePanel doesn't duplicate its own provider.

// ── Step type display config (warm tonal palette per BHISMA §5.1) ─────────────

const STEP_TYPE_CONFIG = {
  deterministic: {
    label: 'DET',
    color: 'bg-[rgba(180,140,20,0.15)] text-[rgba(212,175,55,0.75)] border-[rgba(212,175,55,0.25)]',
  },
  llm: {
    label: 'LLM',
    color: 'bg-[rgba(140,90,200,0.15)] text-[rgba(180,140,240,0.85)] border-[rgba(160,110,220,0.25)]',
  },
  sql: {
    label: 'SQL',
    color: 'bg-[rgba(20,100,180,0.15)] text-[rgba(100,160,240,0.85)] border-[rgba(60,130,210,0.25)]',
  },
  vector: {
    label: 'VEC',
    color: 'bg-[rgba(20,160,100,0.15)] text-[rgba(80,200,140,0.85)] border-[rgba(40,180,120,0.25)]',
  },
  gcs: {
    label: 'GCS',
    color: 'bg-[rgba(200,80,40,0.15)] text-[rgba(240,130,100,0.85)] border-[rgba(220,100,60,0.25)]',
  },
} as const

const TIMELINE_BAR_COLOR = {
  deterministic: 'bg-[rgba(212,175,55,0.6)]',
  llm:           'bg-[rgba(160,110,220,0.7)]',
  sql:           'bg-[rgba(60,130,210,0.7)]',
  vector:        'bg-[rgba(40,180,120,0.7)]',
  gcs:           'bg-[rgba(220,100,60,0.7)]',
} as const

const LAYER_COLOR = {
  L1:      { dot: 'bg-[rgba(244,209,96,0.85)]', bar: 'bg-[rgba(244,209,96,0.85)]', text: 'text-[rgba(244,209,96,0.9)]' },
  'L2.5':  { dot: 'bg-[rgba(190,150,240,0.85)]', bar: 'bg-[rgba(190,150,240,0.85)]', text: 'text-[rgba(190,150,240,0.9)]' },
  system:  { dot: 'bg-[rgba(212,175,55,0.4)]', bar: 'bg-[rgba(212,175,55,0.4)]', text: 'text-[rgba(212,175,55,0.6)]' },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtMs(ms: number | undefined): string {
  if (ms == null) return '…'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function fmtTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function stepSummaryLine(step: TraceStep): string {
  const s = step.data_summary
  if (step.step_type === 'vector' && s.chunks_returned != null)
    return `${s.chunks_returned} chunks · score ${s.top_score?.toFixed(2) ?? '?'}`
  if (step.step_type === 'sql' && s.rows_returned != null)
    return `${s.rows_returned} rows · ~${fmtTokens(s.token_estimate ?? 0)} tok`
  if (step.step_type === 'gcs' && s.token_estimate != null)
    return `~${fmtTokens(s.token_estimate)} tok`
  if (step.step_type === 'llm' && s.model)
    return `${s.model.replace(/^claude-|^gpt-|^gemini-|^deepseek-/, '')} · in:${s.input_tokens ?? '?'} out:${s.output_tokens ?? '?'}`
  if (s.result) return s.result
  return ''
}

// ── Sub-component: Step row ───────────────────────────────────────────────────

function StepRow({
  step,
  isSelected,
  onClick,
}: {
  step: TraceStep
  isSelected: boolean
  onClick: () => void
}) {
  const cfg = STEP_TYPE_CONFIG[step.step_type]
  const isDone = step.status === 'done'
  const isRunning = step.status === 'running'
  const isError = step.status === 'error'

  const seqBg = isDone
    ? 'bg-[rgba(212,175,55,0.08)] border-[rgba(212,175,55,0.35)] text-[rgba(244,209,96,0.9)]'
    : isRunning
    ? 'bg-[rgba(100,80,20,0.3)] border-[rgba(212,175,55,0.45)] text-[rgba(252,226,154,0.95)] animate-pulse'
    : isError
    ? 'bg-[rgba(220,90,60,0.15)] border-[rgba(230,110,80,0.5)] text-[rgba(240,150,120,0.95)]'
    : 'bg-[rgba(5,3,1,0.8)] border-[rgba(212,175,55,0.15)] text-[rgba(212,175,55,0.4)]'

  const summaryLine = stepSummaryLine(step)
  const errorMessage = isError
    ? (step.payload.error_message ?? step.data_summary.error_reason ?? 'unknown error')
    : null
  const latencyPct = step.latency_ms ? Math.min(100, (step.latency_ms / 2000) * 100) : 0

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left flex items-start gap-2.5 px-3 py-2 transition-colors border-l-2 hover:bg-[rgba(212,175,55,0.04)] ${
        isSelected ? 'bg-[rgba(212,175,55,0.06)] border-l-[#d4af37]' : 'border-l-transparent'
      }`}
    >
      {/* Sequence number */}
      <div
        className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full border text-[10px] font-bold flex items-center justify-center ${seqBg}`}
      >
        {step.step_seq}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-[11px] font-semibold text-[rgba(252,226,154,0.9)] truncate">
            {step.step_name.replace(/_/g, ' ')}
          </span>
          <span className={`text-[9px] font-bold px-1 py-px rounded border ${cfg.color}`}>
            {cfg.label}
          </span>
          {step.latency_ms != null && (
            <span className="text-[10px] text-[rgba(212,175,55,0.5)] ml-auto">{fmtMs(step.latency_ms)}</span>
          )}
          {step.parallel_group && (
            <span className="text-[9px] text-[rgba(212,175,55,0.4)]">⇉</span>
          )}
        </div>

        {summaryLine && !isError && (
          <div className="text-[10px] text-[rgba(212,175,55,0.6)] truncate">{summaryLine}</div>
        )}

        {/* Inline error message — §5.8 */}
        {isError && errorMessage && (
          <div className="text-[10px] text-[rgba(240,150,120,0.85)] line-clamp-2 mt-0.5">
            <AlertCircle size={9} className="inline mr-1 -translate-y-px" />
            {errorMessage}
          </div>
        )}

        {/* Latency bar */}
        {isDone && step.latency_ms != null && (
          <div className="mt-1 h-[2px] bg-[rgba(212,175,55,0.06)] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${TIMELINE_BAR_COLOR[step.step_type]}`}
              style={{ width: `${latencyPct}%` }}
            />
          </div>
        )}
        {isRunning && (
          <div className="mt-1 h-[2px] bg-[rgba(212,175,55,0.06)] rounded-full overflow-hidden">
            <div className="h-full w-1/3 rounded-full bg-[rgba(212,175,55,0.6)] animate-[slide_1.2s_ease-in-out_infinite]" />
          </div>
        )}
      </div>
    </button>
  )
}

// ── Sub-component: Parallel group block ───────────────────────────────────────

function ParallelGroup({
  groupSteps,
  selectedSeq,
  onSelect,
}: {
  groupSteps: TraceStep[]
  selectedSeq: number | null
  onSelect: (s: TraceStep) => void
}) {
  return (
    <div className="border border-[rgba(212,175,55,0.10)] rounded mx-2 my-1 overflow-hidden">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-[rgba(212,175,55,0.04)] border-b border-[rgba(212,175,55,0.08)]">
        <span className="text-[9px] font-bold text-[rgba(212,175,55,0.5)] tracking-wider">⇉ PARALLEL</span>
        <span className="text-[9px] text-[rgba(212,175,55,0.35)]">{groupSteps.length} concurrent</span>
      </div>
      {groupSteps.map(step => (
        <StepRow
          key={step.step_seq}
          step={step}
          isSelected={selectedSeq === step.step_seq}
          onClick={() => onSelect(step)}
        />
      ))}
    </div>
  )
}

// ── Sub-component: Synthesis quality indicators (§5.5) ────────────────────────

function getOutputShapeCompliance(plan: TraceStep | undefined, synthStep: TraceStep | undefined, previewText?: string): boolean | null {
  if (!plan || !synthStep) return null
  const shape = plan.payload.query_plan?.expected_output_shape
  if (!shape || !previewText) return null
  if (shape === 'time_indexed_prediction') {
    // heuristic: presence of a year token (e.g., 2026) or a date-like phrase
    return /\b(19|20)\d{2}\b/.test(previewText)
  }
  if (shape === 'three_interpretation') {
    return (previewText.match(/^#{1,3}\s/gm) ?? []).length >= 3
  }
  if (shape === 'structured_data') {
    return /[{}\[\]]/.test(previewText)
  }
  // single_answer — always pass (no negative heuristic)
  return true
}

function getCitationThreshold(queryClass?: string): number {
  switch ((queryClass ?? '').toLowerCase()) {
    case 'holistic': return 5
    case 'cross_domain': return 4
    case 'interpretive': return 3
    case 'discovery': return 3
    case 'predictive': return 2
    case 'cross_native': return 2
    case 'remedial': return 1
    case 'factual': return 0
    default: return 1
  }
}

function SynthesisQualityIndicators({ steps }: { steps: TraceStep[] }) {
  const synthStep = steps.find(s => s.step_name === 'synthesis_done' || s.step_name === 'synthesis')
  if (!synthStep || synthStep.status !== 'done') return null

  const planStep = steps.find(s => s.step_name === 'plan' || s.step_name === 'classify')
  const queryClass = planStep?.payload.query_plan?.query_class ?? planStep?.data_summary.query_class
  const citationCount = synthStep.data_summary.citation_count
  const threshold = getCitationThreshold(queryClass)
  const lowCitation = typeof citationCount === 'number' && citationCount < threshold
  const compliance = getOutputShapeCompliance(planStep, synthStep, synthStep.payload.prompt_preview)

  // Nothing to show if neither field is populated
  if (citationCount == null && compliance == null) return null

  return (
    <div className="border-b border-[rgba(212,175,55,0.10)] flex-shrink-0">
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-[rgba(212,175,55,0.08)]">
        <CheckCircle2 size={11} className="text-[rgba(212,175,55,0.55)]" />
        <span className="text-[10px] font-bold text-[rgba(212,175,55,0.6)] uppercase tracking-[0.16em]">
          Synthesis quality
        </span>
      </div>
      <div className="px-3 py-2 flex items-center flex-wrap gap-2">
        {citationCount != null && (
          <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border ${
            lowCitation
              ? 'bg-[rgba(220,140,60,0.10)] text-[rgba(240,170,100,0.95)] border-[rgba(220,140,60,0.35)]'
              : 'bg-[rgba(212,175,55,0.06)] text-[rgba(252,226,154,0.85)] border-[rgba(212,175,55,0.25)]'
          }`}>
            {lowCitation && <AlertTriangle size={10} />}
            <span className="text-[10px]">
              {citationCount} signals cited
              {lowCitation && (
                <span className="opacity-70 ml-1">(expected ≥{threshold} for {queryClass})</span>
              )}
            </span>
          </div>
        )}
        {compliance != null && (
          <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[10px] ${
            compliance
              ? 'bg-[rgba(140,210,170,0.08)] text-[rgba(140,210,170,0.9)] border-[rgba(120,190,150,0.3)]'
              : 'bg-[rgba(220,140,60,0.10)] text-[rgba(240,170,100,0.95)] border-[rgba(220,140,60,0.35)]'
          }`}>
            output shape: {compliance ? 'matches' : 'deviation'}
          </div>
        )}
        {synthStep.data_summary.input_tokens != null && synthStep.data_summary.output_tokens != null && (
          <div className="text-[10px] text-[rgba(212,175,55,0.55)] tabular-nums ml-auto">
            in {fmtTokens(synthStep.data_summary.input_tokens)} · out {fmtTokens(synthStep.data_summary.output_tokens)}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Sub-component: Context Inspector ─────────────────────────────────────────

function ContextInspector({
  steps,
  selectedStep,
}: {
  steps: TraceStep[]
  selectedStep: TraceStep | null
}) {
  const [expandedLayer, setExpandedLayer] = useState<'L1' | 'L2.5' | null>(null)
  const [drilldownItem, setDrilldownItem] = useState<TraceChunkItem | null>(null)

  const ctxStep = steps.find(s => s.step_name === 'context_assembly')
  const payload = ctxStep?.payload

  const l1Tok = payload?.l1_tokens ?? 0
  const l2Tok = payload?.l2_tokens ?? 0
  const sysTok = payload?.system_tokens ?? 0
  const total = payload?.total_tokens ?? (l1Tok + l2Tok + sysTok)

  const l1Pct = total > 0 ? Math.round((l1Tok / total) * 100) : 0
  const l2Pct = total > 0 ? Math.round((l2Tok / total) * 100) : 0
  const sysPct = total > 0 ? Math.round((sysTok / total) * 100) : 0

  if (drilldownItem) {
    return (
      <div className="flex flex-col h-full">
        {/* Drilldown header */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-[rgba(212,175,55,0.10)] flex-shrink-0">
          <button
            type="button"
            onClick={() => setDrilldownItem(null)}
            className="text-[10px] text-[#d4af37] hover:text-[rgba(244,209,96,0.95)] flex items-center gap-1"
          >
            ← Back
          </button>
          <span className="text-[10px] text-[rgba(212,175,55,0.5)] font-mono truncate">{drilldownItem.id}</span>
          <span className={`text-[9px] font-bold ml-auto ${LAYER_COLOR[drilldownItem.layer]?.text ?? ''}`}>
            {drilldownItem.layer}
          </span>
        </div>
        {/* Chunk meta */}
        <div className="flex items-center gap-3 px-3 py-1.5 border-b border-[rgba(212,175,55,0.08)] flex-shrink-0">
          <span className="text-[10px] text-[rgba(212,175,55,0.5)]">source: <span className="text-[rgba(252,226,154,0.85)]">{drilldownItem.source}</span></span>
          <span className="text-[10px] text-[rgba(212,175,55,0.5)]">~{drilldownItem.token_estimate} tok</span>
          {drilldownItem.score != null && (
            <span className="text-[10px] text-[rgba(212,175,55,0.5)]">score: <span className="text-[rgba(252,226,154,0.85)]">{drilldownItem.score.toFixed(3)}</span></span>
          )}
          {drilldownItem.doc_type && (
            <span className="text-[10px] text-[rgba(212,175,55,0.5)]">type: <span className="text-[rgba(252,226,154,0.85)]">{drilldownItem.doc_type}</span></span>
          )}
        </div>
        {/* Chunk text */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          <pre className="text-[11px] text-[rgba(252,226,154,0.85)] whitespace-pre-wrap leading-relaxed font-mono">
            {drilldownItem.text}
          </pre>
        </div>
      </div>
    )
  }

  // ── Selected step detail ───────────────────────────────────────────────────
  const showSelectedStep = selectedStep && selectedStep.step_name !== 'context_assembly'
  const isToolStep = selectedStep && (selectedStep.step_type === 'sql' || selectedStep.step_type === 'vector' || selectedStep.step_type === 'gcs')

  return (
    <div className="flex flex-col h-full gap-0 overflow-y-auto">

      {/* Synthesis quality (§5.5) — at top, when synthesis is done */}
      <SynthesisQualityIndicators steps={steps} />

      {/* Context summary card */}
      <div className="border-b border-[rgba(212,175,55,0.10)] flex-shrink-0">
        <div className="flex items-center justify-between px-3 py-2 border-b border-[rgba(212,175,55,0.08)]">
          <div className="flex items-center gap-1.5">
            <Layers size={11} className="text-[rgba(212,175,55,0.55)]" />
            <span className="text-[10px] font-bold text-[rgba(212,175,55,0.6)] uppercase tracking-[0.16em]">Context</span>
          </div>
          {total > 0 && (
            <span className="text-[10px] text-[rgba(252,226,154,0.85)] font-semibold">{fmtTokens(total)} tokens</span>
          )}
        </div>

        {total > 0 ? (
          <div className="px-3 py-2">
            {/* Multi-colored bar */}
            <div className="h-2 rounded-full overflow-hidden flex gap-px mb-3">
              <div className="bg-[rgba(244,209,96,0.85)] h-full rounded-l-full" style={{ width: `${l1Pct}%` }} />
              <div className="bg-[rgba(190,150,240,0.85)] h-full" style={{ width: `${l2Pct}%` }} />
              <div className="bg-[rgba(212,175,55,0.4)] h-full rounded-r-full" style={{ width: `${sysPct}%` }} />
            </div>

            {/* L1 row */}
            <LayerRow
              layer="L1"
              label="L1 — Raw Facts"
              sublabel={`${(payload?.l1_items ?? []).length} items · bundle_load + vector_search`}
              tokens={l1Tok}
              pct={l1Pct}
              expanded={expandedLayer === 'L1'}
              onToggle={() => setExpandedLayer(e => e === 'L1' ? null : 'L1')}
              items={payload?.l1_items ?? []}
              onDrilldown={setDrilldownItem}
            />
            {/* L2.5 row */}
            <LayerRow
              layer="L2.5"
              label="L2.5 — Holistic Synthesis"
              sublabel={`${(payload?.l2_items ?? []).length} items · msr_sql + vector_search`}
              tokens={l2Tok}
              pct={l2Pct}
              expanded={expandedLayer === 'L2.5'}
              onToggle={() => setExpandedLayer(e => e === 'L2.5' ? null : 'L2.5')}
              items={payload?.l2_items ?? []}
              onDrilldown={setDrilldownItem}
            />
            {/* System row */}
            <div className="flex items-center gap-2 py-1.5 px-1">
              <div className="w-2 h-2 rounded-sm bg-[rgba(212,175,55,0.4)] flex-shrink-0" />
              <div className="flex-1">
                <div className="text-[11px] font-medium text-[rgba(252,226,154,0.85)]">System Preamble</div>
                <div className="text-[10px] text-[rgba(212,175,55,0.5)]">static · prompt registry</div>
              </div>
              <div className="text-right">
                <div className="text-[12px] font-bold text-[rgba(252,226,154,0.85)]">{fmtTokens(sysTok)}</div>
                <div className="text-[9px] text-[rgba(212,175,55,0.5)]">{sysPct}%</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="px-3 py-3 text-[11px] text-[rgba(212,175,55,0.4)] italic">
            {steps.length === 0 ? 'Waiting for query…' : 'Context assembling…'}
          </div>
        )}

        {/* Cross-tool retrieval efficiency (§5.3 footer) */}
        <RetrievalEfficiency steps={steps} />
      </div>

      {/* Selected step detail */}
      {showSelectedStep && (
        <div className="flex-shrink-0">
          <div className="flex items-center gap-1.5 px-3 py-2 border-b border-[rgba(212,175,55,0.08)]">
            <Database size={11} className="text-[rgba(212,175,55,0.55)]" />
            <span className="text-[10px] font-bold text-[rgba(212,175,55,0.6)] uppercase tracking-[0.16em]">
              Step {selectedStep.step_seq} — {selectedStep.step_name.replace(/_/g, ' ')}
            </span>
            <span className="text-[10px] text-[rgba(212,175,55,0.4)] ml-auto">{fmtMs(selectedStep.latency_ms)}</span>
          </div>

          <div className="px-3 py-2 grid grid-cols-[110px_1fr] gap-y-1 gap-x-2 text-[11px]">
            <span className="text-[rgba(212,175,55,0.55)]">Status</span>
            <span className={
              selectedStep.status === 'done' ? 'text-[rgba(244,209,96,0.9)]'
              : selectedStep.status === 'running' ? 'text-[rgba(252,226,154,0.95)]'
              : 'text-[rgba(240,150,120,0.95)]'
            }>
              {selectedStep.status}
            </span>
            <span className="text-[rgba(212,175,55,0.55)]">Type</span>
            <span className="text-[rgba(252,226,154,0.85)]">{selectedStep.step_type}</span>
            {selectedStep.data_summary.model && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">Model</span>
                <span className="text-[rgba(252,226,154,0.85)]">{selectedStep.data_summary.model}</span>
              </>
            )}
            {/* G.2: LLM step additional fields — stack/provider, tokens, estimated cost */}
            {selectedStep.step_type === 'llm' && selectedStep.data_summary.model && (() => {
              const meta = getModelMeta(selectedStep.data_summary.model)
              const inTok = selectedStep.data_summary.input_tokens ?? 0
              const outTok = selectedStep.data_summary.output_tokens ?? 0
              const costUsd = meta && (inTok + outTok) > 0
                ? (inTok / 1_000_000) * meta.costPer1MInput + (outTok / 1_000_000) * meta.costPer1MOutput
                : null
              return (
                <>
                  {meta?.provider && (
                    <>
                      <span className="text-[rgba(212,175,55,0.55)]">Stack</span>
                      <span className="text-[rgba(252,226,154,0.75)]">{meta.provider}</span>
                    </>
                  )}
                  {inTok > 0 && (
                    <>
                      <span className="text-[rgba(212,175,55,0.55)]">Prompt tok</span>
                      <span className="text-[rgba(252,226,154,0.75)] tabular-nums">{fmtTokens(inTok)}</span>
                    </>
                  )}
                  {outTok > 0 && (
                    <>
                      <span className="text-[rgba(212,175,55,0.55)]">Completion tok</span>
                      <span className="text-[rgba(252,226,154,0.75)] tabular-nums">{fmtTokens(outTok)}</span>
                    </>
                  )}
                  <span className="text-[rgba(212,175,55,0.55)]">Est. cost</span>
                  <span className="text-[rgba(252,226,154,0.75)] tabular-nums">
                    {costUsd == null ? 'N/A' : costUsd < 0.001 ? '<$0.001' : `$${costUsd.toFixed(4)}`}
                  </span>
                  {/* TODO(G.2): cost_usd is computed client-side from model registry pricing.
                      Replace with DB-backed value from GET /api/audit/[query_id] once
                      llm_call_log.cost_usd is populated (currently null in monitoring-write). */}
                </>
              )
            })()}
            {selectedStep.data_summary.chunks_returned != null && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">Chunks</span>
                <span className="text-[rgba(140,210,170,0.9)]">{selectedStep.data_summary.chunks_returned} returned</span>
                {selectedStep.data_summary.top_score != null && (
                  <>
                    <span className="text-[rgba(212,175,55,0.55)]">Top score</span>
                    <span className="text-[rgba(140,210,170,0.9)]">{selectedStep.data_summary.top_score.toFixed(3)}</span>
                  </>
                )}
              </>
            )}
            {selectedStep.data_summary.rows_returned != null && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">Rows</span>
                <span className="text-[rgba(100,160,240,0.9)]">{selectedStep.data_summary.rows_returned} returned</span>
              </>
            )}
            {selectedStep.data_summary.token_estimate != null && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">~Tokens</span>
                <span className="text-[rgba(252,226,154,0.85)]">{fmtTokens(selectedStep.data_summary.token_estimate)}</span>
              </>
            )}
            {selectedStep.parallel_group && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">Group</span>
                <span className="text-[rgba(212,175,55,0.6)]">⇉ {selectedStep.parallel_group}</span>
              </>
            )}
            {selectedStep.status === 'error' && (
              <>
                <span className="text-[rgba(212,175,55,0.55)]">Error</span>
                <span className="text-[rgba(240,150,120,0.95)]">
                  {selectedStep.payload.error_message ?? selectedStep.data_summary.error_reason ?? 'unknown'}
                </span>
                {selectedStep.data_summary.error_stage && (
                  <>
                    <span className="text-[rgba(212,175,55,0.55)]">Stage</span>
                    <span className="text-[rgba(240,150,120,0.85)]">{selectedStep.data_summary.error_stage}</span>
                  </>
                )}
              </>
            )}
          </div>

          {/* Retrieval scorecard for tool steps (§5.3) */}
          {isToolStep && (
            <RetrievalScorecard step={selectedStep} />
          )}

          {/* Chunk preview for tool steps — single-click expand (§5.8 GAP.T.10) */}
          {selectedStep.payload.items && selectedStep.payload.items.length > 0 && (
            <div className="px-3 pb-2">
              <div className="text-[9px] font-bold text-[rgba(212,175,55,0.45)] uppercase tracking-[0.12em] mb-1">
                Retrieved items — click to expand
              </div>
              <div className="space-y-1">
                {selectedStep.payload.items.slice(0, 4).map((item, i) => (
                  <button
                    key={`${item.id}-${i}`}
                    type="button"
                    onClick={() => setDrilldownItem(item)}
                    className="group w-full text-left bg-[rgba(5,3,1,0.6)] border border-[rgba(212,175,55,0.10)] rounded p-2 hover:border-[rgba(212,175,55,0.25)] hover:bg-[rgba(5,3,1,0.8)] transition-colors"
                  >
                    <div className="flex items-center justify-between mb-0.5 gap-2">
                      <span className="text-[9px] font-mono text-[rgba(212,175,55,0.5)] truncate flex-1">{item.id}</span>
                      <span className={`text-[9px] font-bold ${LAYER_COLOR[item.layer]?.text ?? ''}`}>{item.layer}</span>
                      <span className="text-[10px] text-[rgba(212,175,55,0.4)] group-hover:text-[rgba(212,175,55,0.7)]">↗</span>
                    </div>
                    <div className="text-[10px] text-[rgba(252,226,154,0.7)] line-clamp-2">{item.text.slice(0, 120)}</div>
                  </button>
                ))}
                {selectedStep.payload.items.length > 4 && (
                  <div className="text-[9px] text-[rgba(212,175,55,0.4)] px-1">
                    +{selectedStep.payload.items.length - 4} more items
                  </div>
                )}
              </div>
            </div>
          )}

          {/* LLM prompt preview */}
          {selectedStep.payload.prompt_preview && (
            <div className="px-3 pb-2">
              <div className="text-[9px] font-bold text-[rgba(212,175,55,0.45)] uppercase tracking-[0.12em] mb-1">
                Output preview (first 500 chars)
              </div>
              <div className="bg-[rgba(5,3,1,0.6)] border border-[rgba(212,175,55,0.10)] rounded p-2">
                <p className="text-[10px] text-[rgba(252,226,154,0.7)] leading-relaxed">
                  {selectedStep.payload.prompt_preview}
                </p>
              </div>
            </div>
          )}

          {/* DeepSeek R1 reasoning trace (when present) */}
          {selectedStep.payload.reasoning_trace && (
            <details className="px-3 pb-2">
              <summary className="text-[9px] font-bold text-[rgba(212,175,55,0.45)] uppercase tracking-[0.12em] cursor-pointer">
                Reasoning trace ({selectedStep.payload.reasoning_trace.length} chars)
              </summary>
              <div className="bg-[rgba(5,3,1,0.6)] border border-[rgba(212,175,55,0.10)] rounded p-2 mt-1">
                <pre className="text-[10px] text-[rgba(252,226,154,0.65)] leading-relaxed font-mono whitespace-pre-wrap">
                  {selectedStep.payload.reasoning_trace.slice(0, 2000)}
                  {selectedStep.payload.reasoning_trace.length > 2000 && '…'}
                </pre>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

// ── Sub-component: Layer row with drill-down ───────────────────────────────────

function LayerRow({
  layer,
  label,
  sublabel,
  tokens,
  pct,
  expanded,
  onToggle,
  items,
  onDrilldown,
}: {
  layer: 'L1' | 'L2.5'
  label: string
  sublabel: string
  tokens: number
  pct: number
  expanded: boolean
  onToggle: () => void
  items: TraceChunkItem[]
  onDrilldown: (item: TraceChunkItem) => void
}) {
  const cfg = LAYER_COLOR[layer]

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-2 py-1.5 px-1 hover:bg-[rgba(212,175,55,0.04)] rounded transition-colors"
      >
        <div className={`w-2 h-2 rounded-sm ${cfg.dot} flex-shrink-0`} />
        <div className="flex-1 text-left min-w-0">
          <div className="text-[11px] font-medium text-[rgba(252,226,154,0.85)]">{label}</div>
          <div className="text-[10px] text-[rgba(212,175,55,0.5)] truncate">{sublabel}</div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-[12px] font-bold text-[rgba(252,226,154,0.85)]">{fmtTokens(tokens)}</div>
          <div className="text-[9px] text-[rgba(212,175,55,0.5)]">{pct}%</div>
        </div>
        {expanded ? (
          <ChevronDown size={11} className="text-[rgba(212,175,55,0.5)] flex-shrink-0" />
        ) : (
          <ChevronRight size={11} className="text-[rgba(212,175,55,0.5)] flex-shrink-0" />
        )}
      </button>

      {expanded && items.length > 0 && (
        <div className="ml-4 mb-1 space-y-1">
          {items.map((item, i) => (
            <button
              key={`${item.id}-${i}`}
              type="button"
              onClick={() => onDrilldown(item)}
              className="group w-full text-left bg-[rgba(5,3,1,0.6)] border border-[rgba(212,175,55,0.08)] rounded p-1.5 hover:border-[rgba(212,175,55,0.22)] transition-colors"
            >
              <div className="flex items-center justify-between mb-0.5 gap-2">
                <span className="text-[9px] font-mono text-[rgba(212,175,55,0.45)] truncate flex-1">{item.id}</span>
                <span className="text-[9px] text-[rgba(212,175,55,0.45)]">{fmtTokens(item.token_estimate)} tok</span>
                <span className="text-[10px] text-[rgba(212,175,55,0.35)] group-hover:text-[rgba(212,175,55,0.7)]">↗</span>
              </div>
              <p className="text-[10px] text-[rgba(252,226,154,0.65)] leading-relaxed line-clamp-2">{item.text.slice(0, 100)}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Sub-component: Wall-clock timeline bar ────────────────────────────────────

function TimelineBar({ steps }: { steps: TraceStep[] }) {
  const doneSteps = steps.filter(s => s.completed_at)
  if (doneSteps.length === 0) return null

  const starts = doneSteps.map(s => new Date(s.started_at).getTime())
  const ends = doneSteps.map(s => new Date(s.completed_at!).getTime())
  const minStart = Math.min(...starts)
  const maxEnd = Math.max(...ends)
  const totalMs = maxEnd - minStart
  if (totalMs <= 0) return null

  // Group parallel steps
  const parallelGroups: Record<string, TraceStep[]> = {}
  for (const step of doneSteps) {
    if (step.parallel_group) {
      parallelGroups[step.parallel_group] = parallelGroups[step.parallel_group] ?? []
      parallelGroups[step.parallel_group].push(step)
    }
  }

  const renderItems: Array<{ type: 'seq'; step: TraceStep } | { type: 'par'; group: string; steps: TraceStep[] }> = []
  const seenGroups = new Set<string>()
  for (const step of doneSteps) {
    if (step.parallel_group) {
      if (!seenGroups.has(step.parallel_group)) {
        seenGroups.add(step.parallel_group)
        renderItems.push({ type: 'par', group: step.parallel_group, steps: parallelGroups[step.parallel_group] })
      }
    } else {
      renderItems.push({ type: 'seq', step })
    }
  }

  const pct = (ms: number) => `${((ms - minStart) / totalMs) * 100}%`
  const width = (start: number, end: number) => `${Math.max(0.5, ((end - start) / totalMs) * 100)}%`

  return (
    <div className="border-t border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.7)] px-3 py-2 flex-shrink-0">
      <div className="flex items-center gap-2 mb-1">
        <Clock size={10} className="text-[rgba(212,175,55,0.4)]" />
        <span className="text-[9px] text-[rgba(212,175,55,0.4)] uppercase tracking-[0.16em]">Wall-clock</span>
        <span className="text-[10px] text-[rgba(252,226,154,0.85)] font-semibold ml-auto">{fmtMs(totalMs)} total</span>
      </div>

      {/* Track area */}
      <div className="relative" style={{ height: `${Math.max(20, renderItems.filter(r => r.type === 'par').length > 0 ? 44 : 20)}px` }}>
        {renderItems.map((item) => {
          if (item.type === 'seq') {
            const s = item.step
            const start = new Date(s.started_at).getTime()
            const end = new Date(s.completed_at!).getTime()
            return (
              <div
                key={`seq-${s.step_seq}`}
                className={`absolute top-0 h-4 rounded-sm text-[8px] flex items-center justify-center overflow-hidden text-[rgba(8,5,2,0.85)] font-bold ${TIMELINE_BAR_COLOR[s.step_type]}`}
                style={{ left: pct(start), width: width(start, end) }}
                title={`${s.step_name}: ${fmtMs(s.latency_ms)}`}
              >
                <span className="px-0.5 truncate">{s.step_seq}</span>
              </div>
            )
          }

          // Parallel group — stacked lanes
          return item.steps.map((ps, laneIdx) => {
            const start = new Date(ps.started_at).getTime()
            const end = new Date(ps.completed_at!).getTime()
            return (
              <div
                key={`par-${ps.step_seq}`}
                className={`absolute h-3 rounded-sm text-[7px] flex items-center justify-center overflow-hidden text-[rgba(8,5,2,0.85)] font-bold opacity-90 ${TIMELINE_BAR_COLOR[ps.step_type]}`}
                style={{
                  left: pct(start),
                  width: width(start, end),
                  top: `${laneIdx * 14}px`,
                }}
                title={`${ps.step_name}: ${fmtMs(ps.latency_ms)}`}
              >
                <span className="px-0.5 truncate">{ps.step_seq}</span>
              </div>
            )
          })
        })}
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-0.5">
        <span className="text-[8px] text-[rgba(212,175,55,0.3)]">0ms</span>
        <span className="text-[8px] text-[rgba(212,175,55,0.3)]">{fmtMs(totalMs / 2)}</span>
        <span className="text-[8px] text-[rgba(212,175,55,0.3)]">{fmtMs(totalMs)}</span>
      </div>
    </div>
  )
}

// ── Sub-component: Timeline (left column) ────────────────────────────────────

function TraceTimeline({
  steps,
  selectedSeq,
  onSelect,
}: {
  steps: TraceStep[]
  selectedSeq: number | null
  onSelect: (s: TraceStep) => void
}) {
  // Build render list grouping parallel steps
  const renderItems = useMemo(() => {
    const items: Array<{ type: 'seq'; step: TraceStep } | { type: 'par'; group: string; steps: TraceStep[] }> = []
    const seenGroups = new Set<string>()
    const groupMap: Record<string, TraceStep[]> = {}
    for (const step of steps) {
      if (step.parallel_group) {
        groupMap[step.parallel_group] = groupMap[step.parallel_group] ?? []
        groupMap[step.parallel_group].push(step)
      }
    }
    for (const step of steps) {
      if (step.parallel_group) {
        if (!seenGroups.has(step.parallel_group)) {
          seenGroups.add(step.parallel_group)
          items.push({ type: 'par', group: step.parallel_group, steps: groupMap[step.parallel_group] })
        }
      } else {
        items.push({ type: 'seq', step })
      }
    }
    return items
  }, [steps])

  return (
    <div className="flex flex-col overflow-y-auto border-r border-[rgba(212,175,55,0.10)] py-2">
      <div className="px-3 pb-1.5 text-[9px] font-bold text-[rgba(212,175,55,0.45)] uppercase tracking-[0.12em]">
        Pipeline · {steps.length} steps
      </div>
      {renderItems.map((item, idx) =>
        item.type === 'seq' ? (
          <div key={`s-${item.step.step_seq}`}>
            {idx > 0 && <div className="mx-4 h-3 w-px bg-[rgba(212,175,55,0.12)]" />}
            <StepRow
              step={item.step}
              isSelected={selectedSeq === item.step.step_seq}
              onClick={() => onSelect(item.step)}
            />
          </div>
        ) : (
          <div key={`pg-${item.group}`}>
            {idx > 0 && <div className="mx-4 h-3 w-px bg-[rgba(212,175,55,0.12)]" />}
            <ParallelGroup
              groupSteps={item.steps}
              selectedSeq={selectedSeq}
              onSelect={onSelect}
            />
          </div>
        )
      )}
    </div>
  )
}

// ── TracePanelContent — shared render body used by TraceDrawer + TracePanel ────

interface ContentProps {
  queryId: string | null
  steps?: TraceStep[]
  done?: boolean
  error?: string | null
  planningActive?: boolean
  planningModel?: string | null
  toolsSelected?: string[] | null
  queryIntentSummary?: string | null
}

type HistorySubTab = 'list' | 'analytics'

export function TracePanelContent({
  queryId,
  steps: stepsProp,
  done: doneProp,
  error: errorProp,
  planningActive: planningActiveProp,
  planningModel: planningModelProp,
}: ContentProps) {
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live')
  const [viewTab, setViewTab] = useState<'steps' | 'pipeline' | 'lifecycle'>('lifecycle')
  const [historySubTab, setHistorySubTab] = useState<HistorySubTab>('list')
  const [historyQueryId, setHistoryQueryId] = useState<string | null>(null)
  const [historyList, setHistoryList] = useState<TraceHistoryRow[]>([])
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [selectedStep, setSelectedStep] = useState<TraceStep | null>(null)

  const isControlled = stepsProp !== undefined
  const effectiveQueryId = activeTab === 'live' ? queryId : historyQueryId
  const isHistorical = activeTab === 'history'
  const streamQueryId = isControlled && activeTab === 'live' ? null : effectiveQueryId

  const {
    steps: streamSteps,
    done: streamDone,
    error: streamError,
    planningActive: streamPlanningActive,
    planningModel: streamPlanningModel,
  } = useTraceStream(streamQueryId, isHistorical)

  const isLiveControlled = isControlled && activeTab === 'live'
  const steps = isLiveControlled ? (stepsProp ?? []) : streamSteps
  const done = isLiveControlled ? (doneProp ?? false) : streamDone
  const error = isLiveControlled ? (errorProp ?? null) : streamError
  const planningActive = isLiveControlled ? (planningActiveProp ?? false) : streamPlanningActive
  const planningModel = isLiveControlled ? (planningModelProp ?? null) : streamPlanningModel

  // Compute 10-query rolling-avg total latency for the cost/perf comparison
  const comparisonAvgMs = useMemo(() => {
    const completed = historyList
      .filter(r => r.total_latency_ms != null && r.query_id !== effectiveQueryId)
      .slice(0, 10)
    if (completed.length === 0) return null
    const sum = completed.reduce((s, r) => s + (r.total_latency_ms ?? 0), 0)
    return sum / completed.length
  }, [historyList, effectiveQueryId])

  const loadHistory = () => {
    if (historyLoaded) return
    fetch('/api/trace/history')
      .then(r => r.json())
      .then(data => {
        setHistoryList(Array.isArray(data) ? data : [])
        setHistoryLoaded(true)
      })
      .catch(err => console.error('[TracePanelContent] history load failed', err))
  }

  const liveBadgeLabel = done ? 'DONE' : steps.length > 0 ? 'LIVE' : 'READY'
  const liveBadgeColor = done
    ? 'bg-[rgba(212,175,55,0.06)] text-[rgba(212,175,55,0.6)] border-[rgba(212,175,55,0.2)]'
    : steps.length > 0
    ? 'bg-[rgba(212,175,55,0.10)] text-[rgba(244,209,96,0.95)] border-[rgba(212,175,55,0.4)]'
    : 'bg-[rgba(5,3,1,0.6)] text-[rgba(212,175,55,0.4)] border-[rgba(212,175,55,0.15)]'

  return (
    <div className="flex flex-col h-full">
      {/* Sub-header: query pill + live badge + tabs */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.7)] flex-shrink-0">
        <div className="flex items-center gap-2">
          <Zap size={12} className="text-[#d4af37]" />
          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${liveBadgeColor}`}>
            {liveBadgeLabel}
          </span>
        </div>

        {effectiveQueryId && (
          <div className="flex-1 min-w-0 px-2 py-0.5 bg-[rgba(5,3,1,0.6)] border border-[rgba(212,175,55,0.12)] rounded text-[10px] text-[rgba(212,175,55,0.5)] font-mono truncate">
            {effectiveQueryId}
          </div>
        )}

        <div className="flex gap-px bg-[rgba(5,3,1,0.6)] rounded p-0.5">
          <button
            type="button"
            onClick={() => setActiveTab('live')}
            className={`px-3 py-1 rounded text-[11px] font-medium transition-colors ${
              activeTab === 'live'
                ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                : 'text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.85)]'
            }`}
          >
            Live
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('history'); loadHistory() }}
            className={`px-3 py-1 rounded text-[11px] font-medium transition-colors ${
              activeTab === 'history'
                ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                : 'text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.85)]'
            }`}
          >
            History
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-4 py-2 bg-[rgba(220,90,60,0.10)] border-b border-[rgba(220,90,60,0.30)] text-[11px] text-[rgba(240,150,120,0.95)] flex-shrink-0">
          {error}
        </div>
      )}

      {/* History list view */}
      {activeTab === 'history' && !historyQueryId ? (
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">
          {/* History sub-tabs */}
          <div className="flex items-center gap-2 px-4 py-1.5 border-b border-[rgba(212,175,55,0.08)] bg-[rgba(13,10,5,0.4)] flex-shrink-0">
            <button
              type="button"
              onClick={() => setHistorySubTab('list')}
              className={`text-[10px] font-semibold uppercase tracking-[0.16em] px-2 py-0.5 rounded ${
                historySubTab === 'list'
                  ? 'text-[rgba(252,226,154,0.95)] bg-[rgba(212,175,55,0.08)]'
                  : 'text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.85)]'
              }`}
            >
              List
            </button>
            <button
              type="button"
              onClick={() => setHistorySubTab('analytics')}
              className={`text-[10px] font-semibold uppercase tracking-[0.16em] px-2 py-0.5 rounded ${
                historySubTab === 'analytics'
                  ? 'text-[rgba(252,226,154,0.95)] bg-[rgba(212,175,55,0.08)]'
                  : 'text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.85)]'
              }`}
            >
              Analytics
            </button>
          </div>

          {/* History sub-tab body */}
          {historySubTab === 'list' ? (
            <div className="flex-1 overflow-y-auto py-2">
              {!historyLoaded ? (
                <div className="px-4 py-3 text-[11px] text-[rgba(212,175,55,0.5)]">Loading history…</div>
              ) : historyList.length === 0 ? (
                <div className="px-4 py-3 text-[11px] text-[rgba(212,175,55,0.5)]">No trace history yet. Run a query first.</div>
              ) : (
                historyList.map(entry => (
                  <button
                    key={entry.query_id}
                    type="button"
                    onClick={() => setHistoryQueryId(entry.query_id)}
                    className="w-full text-left px-4 py-2.5 hover:bg-[rgba(212,175,55,0.04)] border-b border-[rgba(212,175,55,0.06)] transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[11px] text-[rgba(252,226,154,0.85)] truncate flex-1">
                        {entry.query_text ?? '(no text)'}
                      </span>
                      <span className="text-[9px] text-[rgba(212,175,55,0.4)] flex-shrink-0">{entry.step_count} steps</span>
                      {entry.total_latency_ms != null && (
                        <span className="text-[9px] text-[rgba(212,175,55,0.4)] flex-shrink-0">{fmtMs(entry.total_latency_ms)}</span>
                      )}
                    </div>
                    <div className="text-[9px] text-[rgba(212,175,55,0.4)]">
                      {new Date(entry.created_at).toLocaleString()}
                    </div>
                  </button>
                ))
              )}
            </div>
          ) : (
            <div className="flex-1 overflow-hidden">
              <AnalyticsTab visible={historySubTab === 'analytics'} />
            </div>
          )}
        </div>
      ) : (
        /* Live / single-query view */
        <>
          <QueryDNAPanel steps={steps} />
          {/* Inner tab bar: Pipeline Flow (default) vs Steps */}
          <div className="flex items-center px-3 py-1.5 border-b border-[rgba(212,175,55,0.08)] bg-[rgba(13,10,5,0.4)] flex-shrink-0">
            <div className="flex gap-px bg-[rgba(5,3,1,0.6)] rounded p-0.5">
              <button
                type="button"
                onClick={() => setViewTab('lifecycle')}
                className={`px-2.5 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  viewTab === 'lifecycle'
                    ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                    : 'text-[rgba(212,175,55,0.45)] hover:text-[rgba(252,226,154,0.85)]'
                }`}
              >
                Lifecycle
              </button>
              <button
                type="button"
                onClick={() => setViewTab('pipeline')}
                className={`px-2.5 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  viewTab === 'pipeline'
                    ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                    : 'text-[rgba(212,175,55,0.45)] hover:text-[rgba(252,226,154,0.85)]'
                }`}
              >
                Pipeline Flow
              </button>
              <button
                type="button"
                onClick={() => setViewTab('steps')}
                className={`px-2.5 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  viewTab === 'steps'
                    ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                    : 'text-[rgba(212,175,55,0.45)] hover:text-[rgba(252,226,154,0.85)]'
                }`}
              >
                Steps
              </button>
            </div>
          </div>
          {viewTab === 'lifecycle' ? (
            <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-3">
              <PipelineLifecycleView steps={steps} manifestTools={ALL_RETRIEVAL_TOOLS as unknown as string[]} />
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                  Tool coverage
                </div>
                <ToolCoverageMatrix
                  manifestTools={ALL_RETRIEVAL_TOOLS as unknown as string[]}
                  planned={
                    (steps.find(s => s.step_name === 'plan')?.payload as { query_plan?: { tools_authorized?: string[] } } | undefined)
                      ?.query_plan?.tools_authorized ?? []
                  }
                  executed={steps
                    .filter(s => (s.step_type === 'sql' || s.step_type === 'vector' || s.step_type === 'gcs') && s.status === 'done')
                    .map(s => s.step_name)}
                  results={Object.fromEntries(
                    steps
                      .filter(s => s.step_type === 'sql' || s.step_type === 'vector' || s.step_type === 'gcs')
                      .map(s => {
                        const ds = s.data_summary as { rows_returned?: number; chunks_returned?: number }
                        const rows = ds?.rows_returned ?? ds?.chunks_returned ?? 0
                        return [s.step_name, { rows, empty: rows === 0 }]
                      }),
                  )}
                />
              </div>
            </div>
          ) : viewTab === 'steps' ? (
            <div className="flex-1 flex overflow-hidden min-h-0">
              <div className="w-[300px] flex-shrink-0 overflow-hidden flex flex-col">
                <TraceTimeline
                  steps={steps}
                  selectedSeq={selectedStep?.step_seq ?? null}
                  onSelect={s => setSelectedStep(s)}
                />
              </div>
              <div className="flex-1 overflow-hidden flex flex-col">
                <ContextInspector steps={steps} selectedStep={selectedStep} />
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto min-h-0">
              <PipelineFlowView
                steps={steps}
                planningActive={planningActive}
                planningModel={planningModel}
              />
            </div>
          )}
        </>
      )}

      {/* Footer: cost/perf bar (§5.4) + wall-clock timeline */}
      {(activeTab === 'live' || historyQueryId) && (
        <>
          <CostPerformanceBar steps={steps} comparisonAvgMs={comparisonAvgMs} />
          <TimelineBar steps={steps} />
        </>
      )}
    </div>
  )
}

// ── PipelineFlowView — structured pipeline command centre ─────────────────────

const ALL_RETRIEVAL_TOOLS = [
  'msr_sql', 'pattern_register', 'resonance_register', 'cluster_atlas',
  'contradiction_register', 'temporal', 'query_msr_aggregate', 'cgm_graph_walk',
  'manifest_query', 'vector_search', 'kp_query', 'saham_query',
  'divisional_query', 'chart_facts_query', 'domain_report_query',
  'remedial_codex_query', 'timeline_query', 'query_signal_state',
  'query_kp_ruling_planets', 'query_varshaphala',
] as const

function PfRow({
  icon, name, dim, meta, pulse,
}: {
  icon: string; name: string; dim?: boolean; meta?: string; pulse?: boolean
}) {
  return (
    <div className={`flex items-center gap-2 px-2 py-1.5 rounded ${pulse ? 'animate-pulse bg-[rgba(212,175,55,0.04)]' : ''}`}>
      <span className="w-4 flex-shrink-0 text-[11px]">{icon}</span>
      <span className={`flex-1 text-[11px] font-medium truncate ${dim ? 'text-[rgba(212,175,55,0.35)]' : 'text-[rgba(252,226,154,0.85)]'}`}>{name}</span>
      {meta && <span className={`text-[10px] font-mono flex-shrink-0 ${dim ? 'text-[rgba(212,175,55,0.3)]' : 'text-[rgba(212,175,55,0.55)]'}`}>{meta}</span>}
    </div>
  )
}

function PfStepRow({ step, label }: { step: TraceStep; label: string }) {
  const isDone = step.status === 'done'
  const isRunning = step.status === 'running'
  const isError = step.status === 'error'
  const icon = isDone ? '✅' : isRunning ? '🔄' : isError ? '❌' : '⬜'
  const model = step.data_summary.model
    ?.replace(/^claude-haiku-/, 'haiku-')
    .replace(/^claude-sonnet-/, 'sonnet-')
    .replace(/^claude-opus-/, 'opus-')
    .replace(/nvidia\//i, '')
    .replace(/@.*$/, '') ?? ''
  const count = step.data_summary.rows_returned != null
    ? `${step.data_summary.rows_returned}r`
    : step.data_summary.chunks_returned != null
    ? `${step.data_summary.chunks_returned}c`
    : ''
  const errMsg = isError
    ? (step.payload.error_message ?? step.data_summary.error_reason ?? 'error')
    : null
  return (
    <div className={`flex items-center gap-2 px-2 py-1.5 rounded ${isRunning ? 'animate-pulse bg-[rgba(212,175,55,0.04)]' : ''}`}>
      <span className="w-4 flex-shrink-0 text-[11px]">{icon}</span>
      <span className="flex-1 text-[11px] font-medium text-[rgba(252,226,154,0.85)] truncate">
        {label.replace(/_/g, ' ')}
      </span>
      {count && <span className="text-[10px] font-mono text-[rgba(212,175,55,0.5)] flex-shrink-0">{count}</span>}
      {model && <span className="text-[10px] font-mono text-[rgba(180,140,240,0.7)] flex-shrink-0">{model}</span>}
      {isDone && step.latency_ms != null && (
        <span className="text-[10px] font-mono text-[rgba(212,175,55,0.55)] flex-shrink-0">{fmtMs(step.latency_ms)}</span>
      )}
      {errMsg && (
        <span className="text-[10px] text-[rgba(240,150,120,0.8)] truncate max-w-[120px]">{errMsg}</span>
      )}
    </div>
  )
}

function PfToolRow({
  toolName, step, priority, notSelected,
}: {
  toolName: string
  step: TraceStep | undefined
  priority: 1 | 2 | 3 | undefined
  notSelected?: boolean
}) {
  const isDone = step?.status === 'done'
  const isRunning = step?.status === 'running'
  const isError = step?.status === 'error'
  const icon = notSelected ? '⬜' : isDone ? '✅' : isRunning ? '🔄' : isError ? '❌' : '⬜'
  const priColor = priority === 1
    ? 'text-[rgba(244,209,96,0.9)]'
    : priority === 2
    ? 'text-[rgba(200,200,200,0.75)]'
    : 'text-[rgba(140,140,140,0.65)]'
  const count = step?.data_summary.rows_returned != null
    ? `${step.data_summary.rows_returned}r`
    : step?.data_summary.chunks_returned != null
    ? `${step.data_summary.chunks_returned}c`
    : ''
  return (
    <div className={`flex items-center gap-2 px-3 py-1 ${notSelected ? 'opacity-40' : ''} ${isRunning ? 'animate-pulse' : ''}`}>
      <span className="w-3.5 flex-shrink-0 text-[10px]">{icon}</span>
      <span className={`flex-1 text-[10px] font-mono truncate ${notSelected ? 'text-[rgba(212,175,55,0.5)]' : 'text-[rgba(252,226,154,0.75)]'}`}>
        {toolName}
      </span>
      {priority && !notSelected && <span className={`text-[9px] font-bold flex-shrink-0 ${priColor}`}>P{priority}</span>}
      {count && <span className="text-[10px] font-mono text-[rgba(212,175,55,0.45)] flex-shrink-0">{count}</span>}
      {step?.latency_ms != null && (
        <span className="text-[10px] font-mono text-[rgba(212,175,55,0.45)] flex-shrink-0">{fmtMs(step.latency_ms)}</span>
      )}
      {notSelected && <span className="text-[9px] text-[rgba(212,175,55,0.3)] flex-shrink-0">not selected</span>}
    </div>
  )
}

function PipelineFlowView({
  steps,
  planningActive,
  planningModel,
}: {
  steps: TraceStep[]
  planningActive: boolean
  planningModel: string | null
}) {
  const [notSelectedOpen, setNotSelectedOpen] = useState(false)

  const plannerStep  = steps.find(s => s.step_name === 'llm_planner')
  const classifyStep = steps.find(s => s.step_name === 'classify')
  const composeStep  = steps.find(s => s.step_name === 'compose_bundle' || s.step_name === 'compose')
  const ctxStep      = steps.find(s => s.step_name === 'context_assembly')
  const synthStep    = steps.find(s => s.step_name === 'synthesis_done' || s.step_name === 'synthesis')
  const citationStep = steps.find(s => s.step_name.startsWith('citation'))
  const validatorSteps = steps.filter(s => s.step_name.startsWith('validate_'))

  const toolSteps = steps.filter(s => (ALL_RETRIEVAL_TOOLS as readonly string[]).includes(s.step_name))

  const toolsAuthorized: string[] =
    plannerStep?.payload.query_plan?.tools_authorized ??
    classifyStep?.payload.query_plan?.tools_authorized ??
    toolSteps.map(s => s.step_name)

  const priorityMap: Record<string, 1 | 2 | 3> = {}
  const toolCallsList = plannerStep?.payload.tool_calls ?? classifyStep?.payload.tool_calls
  if (toolCallsList) {
    for (const tc of toolCallsList) priorityMap[tc.tool_name] = tc.priority
  }

  const notSelectedTools = (ALL_RETRIEVAL_TOOLS as readonly string[]).filter(
    t => !toolsAuthorized.includes(t),
  )

  const showPlannerThinking = planningActive && !plannerStep
  const hasAnyContent = steps.length > 0 || planningActive

  return (
    <div className="px-3 py-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] font-bold text-[rgba(212,175,55,0.55)] tracking-[0.14em] uppercase">Pipeline Flow</span>
        {toolSteps.length > 0 && (
          <span className="text-[9px] px-1.5 py-0.5 rounded border bg-[rgba(212,175,55,0.04)] text-[rgba(212,175,55,0.5)] border-[rgba(212,175,55,0.15)]">
            {toolSteps.length} tools ran
          </span>
        )}
      </div>

      {!hasAnyContent && (
        <div className="text-[11px] text-[rgba(212,175,55,0.35)] text-center py-6">
          No pipeline data yet. Run a query to see the flow.
        </div>
      )}

      {/* LLM Planner */}
      {showPlannerThinking && (
        <PfRow
          icon="⏳"
          name={`LLM Planner thinking…${planningModel ? ` (${planningModel.replace(/^claude-/, '')})` : ''}`}
          pulse
        />
      )}
      {plannerStep && (
        <PfStepRow step={plannerStep} label="LLM Planner" />
      )}

      {/* Classify */}
      {classifyStep && <PfStepRow step={classifyStep} label="Classify" />}

      {/* Compose Bundle */}
      {composeStep && <PfStepRow step={composeStep} label="Compose Bundle" />}

      {/* Tool Fetch section */}
      {(toolsAuthorized.length > 0 || toolSteps.length > 0) && (
        <div className="border border-[rgba(212,175,55,0.10)] rounded my-2">
          <div className="flex items-center gap-1.5 px-2 py-1 bg-[rgba(212,175,55,0.04)] border-b border-[rgba(212,175,55,0.08)]">
            <span className="text-[9px] font-bold text-[rgba(212,175,55,0.45)] tracking-wider">⇉ TOOL FETCH — PARALLEL</span>
            <span className="text-[9px] text-[rgba(212,175,55,0.3)] ml-auto">{toolsAuthorized.length} selected</span>
          </div>
          {toolsAuthorized.map(toolName => (
            <PfToolRow
              key={toolName}
              toolName={toolName}
              step={toolSteps.find(s => s.step_name === toolName)}
              priority={priorityMap[toolName] as 1 | 2 | 3 | undefined}
            />
          ))}
          {notSelectedTools.length > 0 && (
            <div className="border-t border-[rgba(212,175,55,0.06)]">
              <button
                type="button"
                onClick={() => setNotSelectedOpen(v => !v)}
                className="w-full flex items-center gap-1 px-3 py-1.5 text-left hover:bg-[rgba(212,175,55,0.02)] transition-colors"
              >
                <span className="text-[9px] text-[rgba(212,175,55,0.35)] font-semibold uppercase tracking-wider">
                  {notSelectedOpen ? '▾' : '›'} {notSelectedTools.length} tools not selected
                </span>
              </button>
              {notSelectedOpen && notSelectedTools.map(toolName => (
                <PfToolRow key={toolName} toolName={toolName} step={undefined} priority={undefined} notSelected />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Context Assembly */}
      {ctxStep ? (
        <PfStepRow step={ctxStep} label="Context Assembly" />
      ) : hasAnyContent ? (
        <PfRow icon="⏭" name="Context Assembly" dim meta="skipped (NIM stack)" />
      ) : null}

      {/* Synthesis */}
      {synthStep && <PfStepRow step={synthStep} label="Synthesis" />}

      {/* Citation Gate */}
      {citationStep && <PfStepRow step={citationStep} label="Citation Gate" />}

      {/* Validators */}
      {validatorSteps.map(step => (
        <PfStepRow
          key={step.step_seq}
          step={step}
          label={step.step_name.replace(/^validate_/, 'Validator: ').replace(/_/g, ' ')}
        />
      ))}
    </div>
  )
}

// ── Main TracePanel — backward-compatible always-on drawer wrapper ─────────────

export function TracePanel({ queryId, isSuperAdmin, onClose }: Props) {
  if (!isSuperAdmin) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="fixed inset-y-0 right-0 z-50 flex flex-col w-[65vw] min-w-[700px] max-w-[1100px] bg-[rgba(8,5,2,0.97)] border-l border-[rgba(212,175,55,0.15)] shadow-2xl">
        <div className="flex items-center gap-3 px-4 py-2.5 border-b border-[rgba(212,175,55,0.12)] bg-[rgba(13,10,5,0.7)] flex-shrink-0">
          <Zap size={13} className="text-[#d4af37]" />
          <span className="text-[13px] font-bold text-[rgba(252,226,154,0.95)]">Query Trace</span>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.95)] transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <TracePanelContent queryId={queryId} />
        </div>
      </div>
    </>
  )
}
