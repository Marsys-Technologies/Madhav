'use client'

import Link from 'next/link'
import { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { MomentPhrase } from './MomentPhrase'
import type { ChartWithMeta, LayerPip, ChartBuildState } from '@/lib/roster/types'
import { BRAHMA_LEXICON } from '@/lib/brahma/lexicon'
import { DeleteChartDialog } from '@/components/dialogs/DeleteChartDialog'
import { formatDate } from '@/lib/utils/date'

// RasiChartMini intentionally not rendered on cards (parked — not deleted).

type OverallState = 'not-built' | 'building' | 'built' | 'attention' | 'failed'

function deriveOverallState(
  buildState: ChartBuildState | null,
  layerPips: LayerPip[],
): OverallState {
  if (buildState) {
    if (buildState.status === 'failed') return 'failed'
    if (
      buildState.status === 'queued' ||
      buildState.status === 'running' ||
      buildState.status === 'cancelling'
    )
      return 'building'
  }
  const litCount = layerPips.filter((p) => p.state === 'lit').length
  if (litCount === 0) return 'not-built'
  if (litCount === layerPips.length) return 'built'
  return 'attention'
}

interface Props {
  chart: ChartWithMeta
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function buildingLayerLabel(layerPips: LayerPip[], progressPct: number): string {
  const building = layerPips.find((p) => p.state === 'building')
  if (!building) return `${progressPct}%`
  const lex = BRAHMA_LEXICON[building.layer]
  return `${lex.sanskrit} · ${progressPct}%`
}

// ── Progress bar ─────────────────────────────────────────────────────────────

function BuildProgressBar({
  overallState,
  buildState,
  layerPips,
  pyramidPercent,
  chartName,
}: {
  overallState: OverallState
  buildState: ChartBuildState | null
  layerPips: LayerPip[]
  pyramidPercent: number
  chartName: string
}) {
  let fillPct = pyramidPercent
  let fillStyle: string
  let labelText: string
  let labelCls: string
  let animate = false

  switch (overallState) {
    case 'not-built':
      fillPct = 0
      fillStyle = 'transparent'
      labelText = 'Not built'
      labelCls = 'text-[rgba(212,175,55,0.28)]'
      break
    case 'building': {
      const progressPct = buildState?.progress_pct ?? pyramidPercent
      fillPct = Math.max(pyramidPercent, progressPct)
      fillStyle = 'linear-gradient(90deg,#a26d0e,#f4d160)'
      labelText = `Building · ${buildingLayerLabel(layerPips, progressPct)}`
      labelCls = 'text-amber-400'
      animate = true
      break
    }
    case 'built':
      fillStyle = 'linear-gradient(90deg,#a26d0e,#f4d160)'
      labelText = 'Built · all verified'
      labelCls = 'text-[#fce29a]'
      break
    case 'attention':
      fillStyle = 'linear-gradient(90deg,#a26d0e,#f4d160)'
      labelText = pyramidPercent > 0 ? `Partially built · ${pyramidPercent}%` : 'Not built'
      labelCls = 'text-[rgba(212,175,55,0.55)]'
      break
    case 'failed': {
      const failedPip = layerPips.find((p) => p.state === 'building')
      fillStyle = 'rgb(220,38,38)'
      labelText = failedPip
        ? `Failed · ${BRAHMA_LEXICON[failedPip.layer].sanskrit}`
        : 'Failed'
      labelCls = 'text-red-400'
      break
    }
  }

  return (
    <div aria-label={`${chartName}: ${labelText}`}>
      <div
        className="relative h-1.5 w-full overflow-hidden rounded-full"
        style={{
          background: 'rgba(212,175,55,0.10)',
          border: '1px solid rgba(212,175,55,0.18)',
        }}
      >
        <div
          className={cn(
            'absolute inset-y-0 left-0 transition-[width]',
            animate && 'animate-pulse motion-reduce:animate-none',
          )}
          style={{ width: `${fillPct}%`, background: fillStyle }}
        />
      </div>
      <p className={cn('mt-1 text-[10px] tracking-[0.04em]', labelCls)}>{labelText}</p>
    </div>
  )
}

// ── Button variants ──────────────────────────────────────────────────────────

const FILLED_BTN =
  'brand-cta text-xs rounded-md px-3 py-1.5 flex-1 text-center'
const GHOST_BTN =
  'border border-[rgba(212,175,55,0.22)] bg-transparent text-[rgba(212,175,55,0.55)] text-xs font-semibold uppercase tracking-[0.08em] rounded-md px-3 py-1.5 hover:text-[#fce29a] hover:border-[rgba(212,175,55,0.4)] transition-colors flex-1 text-center'

// ── Border color per state ───────────────────────────────────────────────────

const BORDER_CLASS: Record<OverallState, string> = {
  'not-built': '',
  building:    'border-amber-400/40',
  built:       '',
  attention:   'border-amber-400/25',
  failed:      'border-red-500/30',
}

// ── ⋯ Overflow menu ──────────────────────────────────────────────────────────

function OverflowMenu({
  chartId,
  chartName,
  onDelete,
}: {
  chartId: string
  chartName: string
  onDelete: () => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onOut(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onOut)
    return () => document.removeEventListener('mousedown', onOut)
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label="More actions"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="text-[rgba(212,175,55,0.4)] hover:text-[rgba(212,175,55,0.7)] transition-colors px-1 py-0.5 rounded text-base leading-none"
      >
        ⋯
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-20 min-w-[110px] rounded-md border border-[rgba(212,175,55,0.18)] bg-[#0a0804] shadow-lg py-1">
          <Link
            href={`/clients/${chartId}/edit`}
            aria-label={`Edit — ${chartName}`}
            onClick={() => setOpen(false)}
            className="block px-3 py-1.5 text-xs text-[rgba(212,175,55,0.6)] hover:text-[#fce29a] hover:bg-[rgba(212,175,55,0.06)] transition-colors"
          >
            Edit
          </Link>
          <button
            type="button"
            aria-label={`Delete — ${chartName}`}
            onClick={() => { setOpen(false); onDelete() }}
            className="block w-full text-left px-3 py-1.5 text-xs text-[rgba(192,57,43,0.65)] hover:text-[#e74c3c] hover:bg-[rgba(192,57,43,0.06)] transition-colors"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  )
}

// ── Main card ────────────────────────────────────────────────────────────────

export function ClientCard({ chart }: Props) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const overallState = deriveOverallState(chart.buildState, chart.layerPips)
  const isBuilt = overallState === 'built' || overallState === 'attention'
  const isBuilding = overallState === 'building'

  // Pariprashna (consult/analyze) is primary when built or building; Nirmāṇa (build) is primary otherwise.
  const pariprashnaPrimary = isBuilt || isBuilding

  return (
    <>
      <div
        className={cn(
          'brand-card rounded-xl p-4 flex flex-col gap-3 hover:border-[rgba(212,175,55,0.35)] transition-colors',
          BORDER_CLASS[overallState],
        )}
      >
        {/* Header: name + overflow trigger */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="bt-heading text-[#fce29a] truncate">{chart.name}</p>
            <p className="bt-label text-[rgba(212,175,55,0.42)] mt-0.5 truncate">
              {formatDate(chart.birth_date)} · {chart.birth_place}
            </p>
          </div>
          <OverflowMenu
            chartId={chart.id}
            chartName={chart.name}
            onDelete={() => setDeleteOpen(true)}
          />
        </div>

        {/* Build progress bar */}
        <BuildProgressBar
          overallState={overallState}
          buildState={chart.buildState}
          layerPips={chart.layerPips}
          pyramidPercent={chart.pyramidPercent}
          chartName={chart.name}
        />

        {/* Moment phrase */}
        <div className="text-[rgba(212,175,55,0.3)] text-xs truncate">
          <MomentPhrase
            pyramidPercent={chart.pyramidPercent}
            lastLayerActivity={chart.lastLayerActivity}
          />
        </div>

        {/* Action row: Nirmāṇa (build) · Pariprashna (consult) */}
        <div className="flex gap-2 items-center">
          {chart.canBuild ? (
            <Link
              href={`/clients/${chart.id}/nirmana`}
              aria-label={`Nirmāṇa (build) — ${chart.name}`}
              className={pariprashnaPrimary ? GHOST_BTN : FILLED_BTN}
            >
              Nirmāṇa
            </Link>
          ) : (
            <button
              type="button"
              disabled
              aria-label={`Nirmāṇa (build) — ${chart.name} — view-only`}
              title="View-only — build restricted"
              data-testid="nirmana-disabled"
              className={cn(pariprashnaPrimary ? GHOST_BTN : FILLED_BTN, 'cursor-not-allowed opacity-35')}
            >
              Nirmāṇa
            </button>
          )}
          <Link
            href={`/clients/${chart.id}/pariprashna`}
            aria-label={`Pariprashna (consult) — ${chart.name}`}
            className={pariprashnaPrimary ? FILLED_BTN : GHOST_BTN}
          >
            Pariprashna
          </Link>
        </div>
      </div>

      <DeleteChartDialog
        chartId={chart.id}
        chartName={chart.name}
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onDeleted={() => {
          setDeleteOpen(false)
          window.location.reload()
        }}
      />
    </>
  )
}
