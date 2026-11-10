'use client'

import { useEffect, useMemo, useState } from 'react'
import { fetchTraceEnvelope, type TraceEnvelope } from '@/lib/admin/trace_client'
import type { TraceDocument } from '@/lib/admin/trace_assembler'
import { detectAnomalies } from '@/lib/admin/anomaly_detector'
import { QueryHeaderStrip } from './QueryHeaderStrip'
import { LifecycleGraph } from './LifecycleGraph'
import { StepDetail } from './StepDetail'
import { TimingRibbon } from './TimingRibbon'
import { HealthRail } from './HealthRail'
import { SearchFilter } from './SearchFilter'
import { ShortcutHelpOverlay } from './ShortcutHelpOverlay'

interface TraceModalProps {
  queryId: string
}

function buildStepOrder(env: TraceEnvelope): string[] {
  return [
    'planner',
    'planner:classify',
    'planner:compose_bundle',
    'planner:plan_per_tool',
    'retrieval',
    ...env.assembled.grouped.retrieval.map(r => `retrieval:${r.tool_name}`),
    'synthesis',
    'audit',
  ]
}

function extractStepData(env: TraceEnvelope, stepId: string): unknown {
  if (stepId === 'planner') return env.assembled.grouped.planner
  if (stepId === 'planner:classify') return env.assembled.grouped.planner
  if (stepId === 'planner:compose_bundle') return env.assembled.grouped.planner?.compose_bundle ?? null
  if (stepId === 'planner:plan_per_tool') return env.assembled.grouped.planner?.plan_per_tool ?? null
  if (stepId === 'retrieval') return env.assembled.grouped.retrieval
  if (stepId === 'synthesis') return env.assembled.grouped.synthesis
  if (stepId === 'audit') return env.assembled.grouped.audit
  if (stepId.startsWith('retrieval:')) {
    const name = stepId.slice('retrieval:'.length)
    return env.assembled.grouped.retrieval.find(r => r.tool_name === name) ?? null
  }
  if (stepId.startsWith('checkpoint_')) {
    return env.assembled.grouped.checkpoints.find(c => c.stage === stepId) ?? null
  }
  return null
}

export function TraceModal({ queryId }: TraceModalProps) {
  const [envelope, setEnvelope] = useState<TraceEnvelope | null>(null)
  const [error, setError] = useState(false)
  const [selectedStepId, setSelectedStepId] = useState<string>('synthesis')
  const [showSearch, setShowSearch] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [showHelp, setShowHelp] = useState(false)

  const trace: TraceDocument | null = envelope?.legacy ?? null

  useEffect(() => {
    let current = true
    fetchTraceEnvelope(queryId)
      .then(env => { if (current) setEnvelope(env) })
      .catch(() => { if (current) setError(true) })
    return () => { current = false }
  }, [queryId])

  const anomalies = useMemo(
    () => (trace ? detectAnomalies(trace) : []),
    [trace],
  )

  // Keyboard navigation
  useEffect(() => {
    if (!envelope) return
    const stepOrder = buildStepOrder(envelope)

    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isInput = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement

      if (e.key === '?' && !isInput) {
        e.preventDefault()
        setShowHelp(h => !h)
        return
      }

      if (e.key === 'Escape') {
        if (showHelp) { setShowHelp(false); return }
        if (showSearch) { setShowSearch(false); setSearchValue(''); return }
      }

      if (e.key === '/' && !isInput) {
        e.preventDefault()
        setShowSearch(true)
        return
      }

      if (isInput) return

      if (e.key === 'j') {
        setSelectedStepId(prev => {
          const idx = stepOrder.indexOf(prev)
          return idx < stepOrder.length - 1 ? stepOrder[idx + 1] : prev
        })
      }
      if (e.key === 'k') {
        setSelectedStepId(prev => {
          const idx = stepOrder.indexOf(prev)
          return idx > 0 ? stepOrder[idx - 1] : prev
        })
      }
      if (e.key === 'c') {
        setSelectedStepId(prev => {
          const stepData = extractStepData(envelope, prev)
          void navigator.clipboard.writeText(JSON.stringify(stepData, null, 2))
          return prev
        })
      }
      const num = parseInt(e.key, 10)
      if (!isNaN(num) && num >= 1 && num <= stepOrder.length) {
        setSelectedStepId(stepOrder[num - 1])
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [envelope, showHelp, showSearch])

  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-[var(--folio-panel)] p-4 text-[var(--folio-error)]" data-testid="trace-error">
        Trace could not be loaded. Reload to try again or return to query sessions.
      </p>
    )
  }

  if (!trace || !envelope) return <p role="status">Loading trace…</p>

  return (
    <section
      aria-label="Query trace details"
      data-testid="trace-modal"
      className="relative min-w-0 rounded-xl border border-[rgba(212,175,55,0.4)] bg-[oklch(0.10_0.012_70)] text-zinc-100"
    >
      {/* Shortcut help overlay */}
      {showHelp && <ShortcutHelpOverlay onClose={() => setShowHelp(false)} />}

      {/* Row 1: Header strip */}
      <QueryHeaderStrip trace={trace} />

      {/* Row 2: Three-zone work area */}
      <div className="grid min-w-0 grid-cols-1 divide-y divide-zinc-800 xl:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1fr)] xl:divide-x xl:divide-y-0">
        {/* Left: Lifecycle graph */}
        <div className="flex min-w-0 flex-col xl:max-h-[70dvh] xl:overflow-y-auto">
          {showSearch && (
            <SearchFilter
              value={searchValue}
              onChange={setSearchValue}
              onClose={() => { setShowSearch(false); setSearchValue('') }}
            />
          )}
          <div className="min-w-0 flex-1 overflow-auto">
            <LifecycleGraph
              steps={envelope.steps}
              assembled={envelope.assembled}
              selectedStepId={selectedStepId}
              onSelectStep={setSelectedStepId}
              searchFilter={showSearch ? searchValue : ''}
            />
          </div>
        </div>

        {/* Center: Step detail */}
        <div className="min-w-0 overflow-auto xl:max-h-[70dvh]">
          <StepDetail assembled={envelope.assembled} selectedStepId={selectedStepId} />
        </div>

        {/* Right: Health rail */}
        <div className="min-w-0 overflow-auto xl:max-h-[70dvh]">
          <HealthRail
            trace={trace}
            anomalies={anomalies}
            onFocusStep={setSelectedStepId}
          />
        </div>
      </div>

      {/* Row 3: Timing + cost ribbon */}
      <div className="overflow-x-auto" role="region" aria-label="Trace timing and cost" tabIndex={0}>
        <TimingRibbon trace={trace} selectedStepId={selectedStepId} onSelectStep={setSelectedStepId} />
      </div>
    </section>
  )
}
