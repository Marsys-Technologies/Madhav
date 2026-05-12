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
    'retrieval',
    ...env.assembled.grouped.retrieval.map(r => `retrieval:${r.tool_name}`),
    'synthesis',
    'audit',
  ]
}

function extractStepData(env: TraceEnvelope, stepId: string): unknown {
  if (stepId === 'planner') return env.assembled.grouped.planner
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
  const [error, setError] = useState<string | null>(null)
  const [selectedStepId, setSelectedStepId] = useState<string>('synthesis')
  const [showSearch, setShowSearch] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [showHelp, setShowHelp] = useState(false)

  const trace: TraceDocument | null = envelope?.legacy ?? null

  useEffect(() => {
    fetchTraceEnvelope(queryId)
      .then(env => { setEnvelope(env); setSelectedStepId('synthesis') })
      .catch(e => setError(String(e)))
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
      <div className="w-[92vw] h-[92vh] rounded-xl border border-[rgba(212,175,55,0.4)] bg-[oklch(0.10_0.012_70)] flex items-center justify-center">
        <p className="text-red-400 text-sm" data-testid="trace-error">Failed to load trace: {error}</p>
      </div>
    )
  }

  if (!trace || !envelope) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Query Trace"
      data-testid="trace-modal"
      className="w-[92vw] h-[92vh] rounded-xl border border-[rgba(212,175,55,0.4)] bg-[oklch(0.10_0.012_70)] flex flex-col overflow-hidden"
    >
      {/* Shortcut help overlay */}
      {showHelp && <ShortcutHelpOverlay onClose={() => setShowHelp(false)} />}

      {/* Row 1: Header strip */}
      <QueryHeaderStrip trace={trace} />

      {/* Row 2: Three-zone work area */}
      <div className="flex-1 min-h-0 grid" style={{ gridTemplateColumns: '380px 1fr 320px' }}>
        {/* Left: Lifecycle graph */}
        <div className="border-r border-[rgba(212,175,55,0.1)] overflow-y-auto flex flex-col">
          {showSearch && (
            <SearchFilter
              value={searchValue}
              onChange={setSearchValue}
              onClose={() => { setShowSearch(false); setSearchValue('') }}
            />
          )}
          <div className="flex-1 overflow-y-auto">
            <LifecycleGraph
              steps={envelope.steps}
              selectedStepId={selectedStepId}
              onSelectStep={setSelectedStepId}
              searchFilter={showSearch ? searchValue : ''}
            />
          </div>
        </div>

        {/* Center: Step detail */}
        <div className="overflow-y-auto">
          <StepDetail trace={trace} selectedStepId={selectedStepId} />
        </div>

        {/* Right: Health rail */}
        <div className="border-l border-[rgba(212,175,55,0.1)] overflow-y-auto">
          <HealthRail
            trace={trace}
            anomalies={anomalies}
            onFocusStep={setSelectedStepId}
          />
        </div>
      </div>

      {/* Row 3: Timing + cost ribbon */}
      <TimingRibbon trace={trace} selectedStepId={selectedStepId} onSelectStep={setSelectedStepId} />
    </div>
  )
}
