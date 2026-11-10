'use client'

import type { TraceDocument } from '@/lib/admin/trace_assembler'

interface TimingRibbonProps {
  trace: TraceDocument
  selectedStepId: string
  onSelectStep: (stepId: string) => void
}

interface GanttStep {
  id: string
  label: string
  startMs: number
  durationMs: number
  color: string
}

const STEP_COLORS: Record<string, string> = {
  classify: '#60a5fa',
  plan: '#d4af37',
  context_assembly: '#34d399',
  synthesis: '#a78bfa',
}

function getFetchColor() {
  return '#2dd4bf'
}

function formatCostCell(label: string, cost: number | null) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-[9px] text-zinc-500 uppercase tracking-wide">{label}</span>
      <span className="text-xs text-zinc-300 font-mono">
        {cost !== null ? `$${cost.toFixed(4)}` : '—'}
      </span>
    </div>
  )
}

export function TimingRibbon({ trace, onSelectStep }: TimingRibbonProps) {
  // Build gantt steps with pseudo-timing (stacked latency, since we don't have start_ms in TraceDocument)
  const steps: GanttStep[] = []
  let cursor = 0

  if (trace.classify?.latency_ms) {
    steps.push({ id: 'classify', label: 'classify', startMs: cursor, durationMs: trace.classify.latency_ms, color: STEP_COLORS.classify })
    cursor += trace.classify.latency_ms
  }

  if (trace.plan?.latency_ms) {
    steps.push({ id: 'plan', label: 'plan', startMs: cursor, durationMs: trace.plan.latency_ms, color: STEP_COLORS.plan })
    cursor += trace.plan.latency_ms
  }

  // Fetches run in parallel — all start at cursor, width = max fetch latency
  if (trace.fetches.length > 0) {
    const maxFetchMs = Math.max(...trace.fetches.map(f => f.latency_ms ?? 0))
    trace.fetches.forEach(fetch => {
      const dur = fetch.latency_ms ?? maxFetchMs
      steps.push({ id: fetch.bundle, label: fetch.bundle, startMs: cursor, durationMs: dur, color: getFetchColor() })
    })
    cursor += maxFetchMs
  }

  if (trace.synthesis?.latency_ms) {
    steps.push({ id: 'synthesis', label: 'synthesis', startMs: cursor, durationMs: trace.synthesis.latency_ms, color: STEP_COLORS.synthesis })
    cursor += trace.synthesis.latency_ms
  }

  const totalMs = cursor || 1
  const totalCost = trace.query.total_cost_usd

  return (
    <div
      className="h-[88px] border-t border-[rgba(212,175,55,0.1)] flex flex-col shrink-0"
      data-testid="timing-ribbon"
    >
      {/* Gantt row: 44px */}
      <div className="h-11 relative px-3 py-1.5">
        {steps.map((step) => (
          <div
            key={step.id}
            data-testid={`gantt-segment-${step.id}`}
            className="absolute top-1.5 h-2 rounded cursor-pointer opacity-70 hover:opacity-100 transition-opacity"
            style={{
              left: `${(step.startMs / totalMs) * 100}%`,
              width: `${Math.max(0.5, (step.durationMs / totalMs) * 100)}%`,
              backgroundColor: step.color,
            }}
            title={`${step.label}: ${step.durationMs}ms`}
            onMouseEnter={() => onSelectStep(step.id)}
          />
        ))}
      </div>

      {/* Cost row: 44px */}
      <div className="h-11 flex items-center justify-around px-4 border-t border-[rgba(212,175,55,0.05)]">
        {formatCostCell('plan', null)}
        {formatCostCell('fetch', null)}
        {formatCostCell('synthesis', null)}
        <div className="flex flex-col items-center">
          <span className="text-[9px] text-zinc-500 uppercase tracking-wide">total</span>
          <span className="text-xs text-[#d4af37] font-mono font-semibold">
            {totalCost !== null ? `$${totalCost.toFixed(4)}` : '—'}
          </span>
        </div>
      </div>
    </div>
  )
}
