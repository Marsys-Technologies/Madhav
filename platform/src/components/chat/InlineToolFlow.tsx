'use client'

import { useCallback, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import type { TraceStep, TraceDataSummary } from '@/lib/trace/types'

const FLAG_ON = process.env.NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW === 'true'

interface StepRow {
  step_seq: number
  step_name: string
  step_type: string
  status: string
  latency_ms: number | null
  parallel_group: string | null
  data_summary: TraceDataSummary
}

function statusIcon(status: string): string {
  if (status === 'done') return '✓'
  if (status === 'error') return '✗'
  if (status === 'running') return '⏳'
  return '·'
}

function statusColor(status: string): string {
  if (status === 'done') return 'text-emerald-400'
  if (status === 'error') return 'text-red-400'
  if (status === 'running') return 'text-amber-400'
  return 'text-zinc-500'
}

function stageIcon(stepName: string, parallelGroup: string | null): string {
  if (parallelGroup === 'tool_fetch') return '🔧'
  if (stepName === 'classify' || stepName === 'compose_bundle' || stepName === 'plan_per_tool') return '🗺'
  if (stepName === 'synthesis' || stepName === 'synthesis_done' || stepName === 'context_assembly') return '✦'
  if (stepName.startsWith('checkpoint')) return '🔍'
  if (stepName === 'citation_warn' || stepName === 'citation_error') return '📎'
  return '▸'
}

interface Props {
  queryId: string | null
  isAdmin: boolean
}

export function InlineToolFlow({ queryId, isAdmin }: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cacheRef = useRef<Map<string, StepRow[]>>(new Map())

  const fetchTrace = useCallback(async (qid: string) => {
    if (cacheRef.current.has(qid)) return
    setLoading(true)
    setError(null)
    try {
      const r = await fetch(`/api/audit/${encodeURIComponent(qid)}/trace`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data = await r.json() as { steps: StepRow[] }
      cacheRef.current.set(qid, data.steps ?? [])
    } catch {
      setError('Failed to load trace.')
    } finally {
      setLoading(false)
    }
  }, [])

  if (!FLAG_ON || !isAdmin || !queryId) return null

  const steps = cacheRef.current.get(queryId) ?? null

  function handleToggle() {
    const next = !open
    setOpen(next)
    if (next && queryId && !cacheRef.current.has(queryId)) {
      fetchTrace(queryId)
    }
  }

  return (
    <div className="mt-2">
      <button
        onClick={handleToggle}
        className="flex items-center gap-1 text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors focus-visible:outline-none"
      >
        <span className={cn('transition-transform duration-150', open && 'rotate-90')}>▸</span>
        View tool flow
      </button>

      {open && (
        <div className="mt-2 rounded-md border border-zinc-800 bg-zinc-950/60 p-3 text-[11px] font-mono">
          {loading && <p className="text-zinc-500">Loading…</p>}
          {error && <p className="text-red-400">{error}</p>}
          {steps && steps.length === 0 && (
            <p className="text-zinc-600">No trace steps recorded for this query.</p>
          )}
          {steps && steps.length > 0 && (
            <ol className="space-y-1">
              {steps.map((step) => {
                const isSynthesisDone = step.step_name === 'synthesis_done'
                const ds = step.data_summary ?? {}
                return (
                  <li key={step.step_seq} className="flex items-start gap-2">
                    <span className="shrink-0 text-zinc-600 w-4 text-right">{step.step_seq}.</span>
                    <span className="shrink-0">{stageIcon(step.step_name, step.parallel_group)}</span>
                    <span className="flex-1 min-w-0">
                      <span className="text-zinc-300">{step.step_name}</span>
                      {step.parallel_group === 'tool_fetch' && ds.tool_name && (
                        <span className="text-zinc-500"> ({ds.tool_name})</span>
                      )}
                      {isSynthesisDone && ds.model && (
                        <span className="text-zinc-500"> · {ds.model}</span>
                      )}
                      {isSynthesisDone && ds.input_tokens != null && (
                        <span className="text-zinc-600"> · {ds.input_tokens}↑ {ds.output_tokens ?? 0}↓ tok</span>
                      )}
                    </span>
                    <span className="shrink-0 text-zinc-600">
                      {step.latency_ms != null ? `${step.latency_ms}ms` : '—'}
                    </span>
                    <span className={cn('shrink-0', statusColor(step.status))}>
                      {statusIcon(step.status)}
                    </span>
                  </li>
                )
              })}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
