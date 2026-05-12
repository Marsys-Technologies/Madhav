'use client'

// Realigned for new pipeline 2026-05-12 (Gate II W6).
// HealthRail still consumes the legacy `TraceDocument` shape produced by
// `trace_assembler.assembleTrace`. Post-Gate II that document is a backward-
// compatible projection over the new pipeline; `trace.classify` and
// `trace.context_assembly` are always `null`, and the related guards below
// skip cleanly. Follow-up gates can migrate this component to
// `AssembledTrace` directly; the displayed information is unchanged.

import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { TraceDocument } from '@/lib/admin/trace_assembler'
import { type Anomaly, buildHealthSummary } from '@/lib/admin/anomaly_detector'

// ── Card 1: Overall health verdict ─────────────────────────────────────────

const HEALTH_CONFIG = {
  HEALTHY: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/30',
    icon: '✓',
  },
  DEGRADED: {
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/30',
    icon: '⚠',
  },
  FAILED: {
    color: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/30',
    icon: '✗',
  },
  UNKNOWN: {
    color: 'text-zinc-400',
    bg: 'bg-zinc-400/10',
    border: 'border-zinc-400/30',
    icon: '?',
  },
} as const

function HealthVerdictCard({
  health,
  summary,
}: {
  health: TraceDocument['query']['health']
  summary: string
}) {
  const cfg = HEALTH_CONFIG[health] ?? HEALTH_CONFIG.UNKNOWN
  return (
    <div
      data-testid="health-verdict-card"
      className={`rounded-lg border ${cfg.border} ${cfg.bg} p-4 text-center`}
    >
      <div className={`text-3xl font-mono ${cfg.color} mb-1`} aria-hidden="true">
        {cfg.icon}
      </div>
      <div className={`text-sm font-bold ${cfg.color}`}>{health}</div>
      <div className="mt-2 text-xs text-zinc-400 leading-relaxed">{summary}</div>
    </div>
  )
}

// ── Card 2: Per-stage health strip ─────────────────────────────────────────

function StageHealthRow({
  stage,
  latencyRatio,
  completeness,
  qualityOk,
}: {
  stage: string
  latencyRatio: number | null
  completeness: number | null
  qualityOk: boolean | null
}) {
  const latencyColor =
    latencyRatio == null
      ? 'bg-zinc-600'
      : latencyRatio <= 1.2
        ? 'bg-emerald-400'
        : latencyRatio <= 2.0
          ? 'bg-amber-400'
          : 'bg-red-400'

  const barWidth = latencyRatio == null ? 0 : Math.min(100, (latencyRatio / 3) * 100)

  const completenessColor =
    completeness == null
      ? 'bg-zinc-600'
      : completeness >= 0.9
        ? 'bg-emerald-400'
        : completeness >= 0.7
          ? 'bg-amber-400'
          : 'bg-red-400'

  const qualityColor =
    qualityOk == null ? 'bg-zinc-600' : qualityOk ? 'bg-emerald-400' : 'bg-amber-400'

  const latencyLabel =
    latencyRatio == null ? '—' : `${latencyRatio.toFixed(1)}× p50`
  const completenessLabel =
    completeness == null ? '—' : `${(completeness * 100).toFixed(0)}%`
  const qualityLabel = qualityOk == null ? '—' : qualityOk ? 'ok' : 'degraded'

  return (
    <div className="flex items-center gap-2 py-1.5" data-testid={`stage-health-row-${stage}`}>
      <span className="text-xs text-zinc-400 w-16 shrink-0">{stage}</span>
      <div
        className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden"
        title={`latency ${latencyLabel}`}
        aria-label={`${stage} latency ${latencyLabel}`}
      >
        <div
          className={`h-full rounded-full transition-all ${latencyColor}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>
      <div
        className={`w-2 h-2 rounded-full shrink-0 ${completenessColor}`}
        title={`completeness ${completenessLabel}`}
        aria-label={`${stage} completeness ${completenessLabel}`}
      />
      <div
        className={`w-2 h-2 rounded-full shrink-0 ${qualityColor}`}
        title={`quality ${qualityLabel}`}
        aria-label={`${stage} quality ${qualityLabel}`}
      />
    </div>
  )
}

// ── Card 4: Anomaly callouts ────────────────────────────────────────────────

function AnomalyCallouts({
  anomalies,
  onFocus,
}: {
  anomalies: Anomaly[]
  onFocus: (stepId: string) => void
}) {
  const [filter, setFilter] = useState<'all' | 'errors' | 'warnings'>('all')

  const filtered = anomalies.filter(a =>
    filter === 'all'
      ? true
      : filter === 'errors'
        ? a.severity === 'ERROR'
        : a.severity === 'WARNING',
  )

  return (
    <div data-testid="anomaly-callouts">
      <div className="flex gap-1 mb-2" role="tablist" aria-label="Anomaly filter">
        {(['all', 'errors', 'warnings'] as const).map(f => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            onClick={() => setFilter(f)}
            className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
              filter === f
                ? 'border-[rgba(212,175,55,0.4)] text-[#d4af37]'
                : 'border-zinc-700 text-zinc-500 hover:border-zinc-500'
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <p className="text-xs text-zinc-600">No anomalies detected.</p>
      ) : (
        <div className="space-y-1.5">
          {filtered.map((a, i) => (
            <div
              key={i}
              role="button"
              tabIndex={0}
              aria-label={`${a.severity}: ${a.message}`}
              onClick={() => a.step_id && onFocus(a.step_id)}
              onKeyDown={e => {
                if ((e.key === 'Enter' || e.key === ' ') && a.step_id) onFocus(a.step_id)
              }}
              className={`rounded px-2 py-1.5 text-xs cursor-pointer border transition-opacity hover:opacity-80 ${
                a.severity === 'ERROR'
                  ? 'border-red-400/30 bg-red-400/5 text-red-300'
                  : a.severity === 'WARNING'
                    ? 'border-amber-400/30 bg-amber-400/5 text-amber-300'
                    : 'border-zinc-600 bg-zinc-900 text-zinc-400'
              }`}
            >
              <span className="font-semibold mr-1">
                {a.severity === 'ERROR' ? 'ERROR' : a.severity === 'WARNING' ? 'WARN' : 'INFO'}
              </span>
              {a.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Card 5: Cost & token ledger ─────────────────────────────────────────────

function CostTokenLedger({ trace }: { trace: TraceDocument }) {
  type LedgerRow = { label: string; input: number | null; output: number | null; cost: number | null }
  const rows: LedgerRow[] = []

  const scorecard = trace.synthesis?.scorecard as Record<string, unknown> | null | undefined

  if (trace.classify) {
    rows.push({
      label: 'Classify',
      input: trace.classify.tokens.input,
      output: trace.classify.tokens.output,
      cost: null,
    })
  }
  if (trace.plan) {
    rows.push({ label: 'Plan', input: null, output: null, cost: null })
  }
  if (trace.synthesis) {
    rows.push({
      label: 'Synthesis',
      input: trace.synthesis.input_tokens,
      output: trace.synthesis.output_tokens,
      cost: trace.query.total_cost_usd,
    })
  }

  const totalInput = rows.reduce((s, r) => s + (r.input ?? 0), 0)
  const totalOutput = rows.reduce((s, r) => s + (r.output ?? 0), 0)

  void scorecard

  return (
    <div data-testid="cost-token-ledger">
      <table className="w-full text-[10px]">
        <thead>
          <tr className="text-zinc-500 border-b border-zinc-800">
            <th className="py-1 text-left font-normal">Call</th>
            <th className="py-1 text-right font-normal">In</th>
            <th className="py-1 text-right font-normal">Out</th>
            <th className="py-1 text-right font-normal">Cost</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.label} className="border-b border-zinc-800/40">
              <td className="py-1 text-zinc-400">{r.label}</td>
              <td className="py-1 text-zinc-300 text-right font-mono">
                {r.input != null ? r.input.toLocaleString() : '—'}
              </td>
              <td className="py-1 text-zinc-300 text-right font-mono">
                {r.output != null ? r.output.toLocaleString() : '—'}
              </td>
              <td className="py-1 text-zinc-300 text-right font-mono">
                {r.cost != null ? `$${r.cost.toFixed(4)}` : '—'}
              </td>
            </tr>
          ))}
          <tr className="font-semibold">
            <td className="py-1 text-zinc-300">Total</td>
            <td className="py-1 text-zinc-200 text-right font-mono">
              {totalInput > 0 ? totalInput.toLocaleString() : '—'}
            </td>
            <td className="py-1 text-zinc-200 text-right font-mono">
              {totalOutput > 0 ? totalOutput.toLocaleString() : '—'}
            </td>
            <td className="py-1 text-[#d4af37] text-right font-mono">
              {trace.query.total_cost_usd != null
                ? `$${trace.query.total_cost_usd.toFixed(4)}`
                : '—'}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

// ── HealthRail: main export ─────────────────────────────────────────────────

interface HealthRailProps {
  trace: TraceDocument
  anomalies: Anomaly[]
  onFocusStep: (stepId: string) => void
}

function SectionHeader({ title }: { title: string }) {
  return (
    <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
      {title}
    </p>
  )
}

export function HealthRail({ trace, anomalies, onFocusStep }: HealthRailProps) {
  const summary = buildHealthSummary(trace.query.health, anomalies)
  const baselines = trace.baselines
  const scorecard = trace.synthesis?.scorecard as
    | { citation_density?: number; composite_score?: number }
    | null
    | undefined

  // Per-stage completeness calculations
  const planCompleteness =
    trace.plan != null
      ? trace.plan.included_bundles.length /
        Math.max(
          trace.plan.included_bundles.length + trace.plan.excluded_bundles.length,
          1,
        )
      : null

  const emptyFetchCount = trace.fetches.filter(
    f => f.error_class === 'OK' && f.raw_count === 0,
  ).length
  const fetchCompleteness =
    trace.fetches.length > 0
      ? 1 - emptyFetchCount / trace.fetches.length
      : null

  const assembleCompleteness =
    trace.context_assembly != null
      ? 1 -
        trace.context_assembly.token_ledger.dropped_count /
          Math.max(trace.context_assembly.items.length, 1)
      : null

  // Per-stage latency ratios vs p50 total (proxy)
  const p50 = baselines?.p50_total_latency_ms ?? null
  const classifyRatio =
    trace.classify?.latency_ms != null && p50 != null && p50 > 0
      ? trace.classify.latency_ms / p50
      : null
  const planRatio =
    trace.plan?.latency_ms != null && p50 != null && p50 > 0
      ? trace.plan.latency_ms / p50
      : null
  const avgFetchLatency =
    trace.fetches.length > 0
      ? trace.fetches.reduce((s, f) => s + (f.latency_ms ?? 0), 0) / trace.fetches.length
      : null
  const fetchRatio =
    avgFetchLatency != null && p50 != null && p50 > 0 ? avgFetchLatency / p50 : null
  const synthRatio =
    trace.synthesis?.latency_ms != null && p50 != null && p50 > 0
      ? trace.synthesis.latency_ms / p50
      : null

  // Baseline chart data
  const baselineData = [
    {
      name: 'Plan (s)',
      actual: (trace.plan?.latency_ms ?? 0) / 1000,
      p50: (baselines?.p50_total_latency_ms ?? 0) / 1000,
    },
    {
      name: 'Synth (s)',
      actual: (trace.synthesis?.latency_ms ?? 0) / 1000,
      p50: (baselines?.p50_total_latency_ms ?? 0) / 1000,
    },
    {
      name: 'Cost ($)',
      actual: trace.query.total_cost_usd ?? 0,
      p50: baselines?.p50_total_cost_usd ?? 0,
    },
  ]

  const lowSampleSize = (baselines?.sample_size ?? 0) < 30

  return (
    <div
      data-testid="health-rail"
      className="p-4 space-y-5 text-xs"
      aria-label="Health and performance rail"
    >
      {/* Card 1: Overall verdict */}
      <div>
        <SectionHeader title="Overall Health" />
        <HealthVerdictCard health={trace.query.health} summary={summary} />
      </div>

      {/* Card 2: Per-stage health strip */}
      <div data-testid="stage-health-strip">
        <SectionHeader title="Stage Health" />
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[9px] text-zinc-600 w-16 shrink-0" />
          <span className="flex-1 text-[9px] text-zinc-600 text-center">latency vs p50</span>
          <span className="text-[9px] text-zinc-600 w-2 text-center" title="completeness">C</span>
          <span className="text-[9px] text-zinc-600 w-2 text-center" title="quality">Q</span>
        </div>
        <StageHealthRow
          stage="classify"
          latencyRatio={classifyRatio}
          completeness={trace.query.confidence ?? null}
          qualityOk={trace.classify != null}
        />
        <StageHealthRow
          stage="plan"
          latencyRatio={planRatio}
          completeness={planCompleteness}
          qualityOk={trace.plan != null}
        />
        <StageHealthRow
          stage="fetch"
          latencyRatio={fetchRatio}
          completeness={fetchCompleteness}
          qualityOk={fetchCompleteness == null ? null : fetchCompleteness >= 0.8}
        />
        <StageHealthRow
          stage="assemble"
          latencyRatio={null}
          completeness={assembleCompleteness}
          qualityOk={
            assembleCompleteness == null ? null : assembleCompleteness >= 0.7
          }
        />
        <StageHealthRow
          stage="synthesize"
          latencyRatio={synthRatio}
          completeness={scorecard?.composite_score ?? null}
          qualityOk={
            scorecard?.composite_score != null
              ? scorecard.composite_score >= 0.6
              : null
          }
        />
      </div>

      {/* Card 3: Baseline comparison */}
      <div data-testid="baseline-comparison">
        <SectionHeader title="vs Baseline" />
        {lowSampleSize && (
          <p
            data-testid="baseline-unreliable-warning"
            className="text-[10px] text-amber-400 mb-2 px-2 py-1 bg-amber-400/10 border border-amber-400/30 rounded"
          >
            ⚠ Baselines unreliable (n={baselines?.sample_size ?? 0} &lt; 30)
          </p>
        )}
        {baselines && (
          <p className="text-[10px] text-zinc-500 mb-2">
            n={baselines.sample_size} queries
          </p>
        )}
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={baselineData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#71717a' }} />
              <YAxis tick={{ fontSize: 9, fill: '#71717a' }} />
              <Tooltip
                contentStyle={{
                  background: 'oklch(0.10 0.012 70)',
                  border: '1px solid rgba(212,175,55,0.2)',
                  fontSize: 10,
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: 9, color: '#71717a' }}
                iconSize={8}
              />
              <Bar dataKey="actual" name="This query" fill="#d4af37" radius={[2, 2, 0, 0]} />
              <Bar dataKey="p50" name="p50" fill="#52525b" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Card 4: Anomaly callouts */}
      <div>
        <SectionHeader title={`Anomalies (${anomalies.length})`} />
        <AnomalyCallouts anomalies={anomalies} onFocus={onFocusStep} />
      </div>

      {/* Card 5: Cost & token ledger */}
      <div>
        <SectionHeader title="Cost & Tokens" />
        <CostTokenLedger trace={trace} />
      </div>
    </div>
  )
}
