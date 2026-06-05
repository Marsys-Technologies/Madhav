'use client'

import Link from 'next/link'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { MomentPhrase } from './MomentPhrase'
import type { ChartWithMeta, LayerPip, ChartBuildState } from '@/lib/roster/types'
import { BRAHMA_LEXICON } from '@/lib/brahma/lexicon'
import type { BrahmaLayerId } from '@/lib/brahma/lexicon'
import { DeleteChartDialog } from '@/components/dialogs/DeleteChartDialog'

interface Props {
  chart: ChartWithMeta
}

type HealthStatus = 'green' | 'amber' | 'red'

function healthStatus(chart: ChartWithMeta): HealthStatus {
  if (chart.pyramidPercent === 0) return 'amber'
  if (!chart.lastLayerActivity) return 'amber'
  const ageMs = Date.now() - new Date(chart.lastLayerActivity).getTime()
  return ageMs / (1000 * 60 * 60 * 24) < 7 ? 'green' : 'amber'
}

const HEALTH_DOT_CLASS: Record<HealthStatus, string> = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-400',
  red: 'bg-red-500',
}

const GHOST_BTN =
  'border border-[rgba(212,175,55,0.22)] bg-transparent text-[rgba(212,175,55,0.55)] text-xs font-semibold uppercase tracking-[0.08em] rounded-md px-3 py-1.5 hover:text-[#fce29a] hover:border-[rgba(212,175,55,0.4)] transition-colors'

const DANGER_BTN =
  'border border-[rgba(192,57,43,0.35)] bg-transparent text-[rgba(192,57,43,0.65)] text-xs font-semibold uppercase tracking-[0.08em] rounded-md px-3 py-1.5 hover:text-[#e74c3c] hover:border-[rgba(192,57,43,0.55)] transition-colors'

// ── State chip ──────────────────────────────────────────────────────────────

type OverallState = 'not-built' | 'building' | 'built' | 'attention' | 'failed'

function deriveOverallState(
  buildState: ChartBuildState | null,
  layerPips: LayerPip[],
): OverallState {
  if (buildState) {
    if (buildState.status === 'failed') return 'failed'
    if (buildState.status === 'queued' || buildState.status === 'running' || buildState.status === 'cancelling')
      return 'building'
  }
  const litCount = layerPips.filter((p) => p.state === 'lit').length
  if (litCount === 0) return 'not-built'
  if (litCount === layerPips.length) return 'built'
  return 'attention'
}

function buildingLayerLabel(layerPips: LayerPip[], progressPct: number): string {
  const building = layerPips.find((p) => p.state === 'building')
  if (!building) return `${progressPct}%`
  const lex = BRAHMA_LEXICON[building.layer]
  return `${lex.sanskrit} · ${progressPct}%`
}

function StateChip({
  state,
  buildState,
  layerPips,
  chartName,
}: {
  state: OverallState
  buildState: ChartBuildState | null
  layerPips: LayerPip[]
  chartName: string
}) {
  let label: string
  let cls: string

  switch (state) {
    case 'not-built':
      label = 'Not built'
      cls = 'text-[rgba(212,175,55,0.4)] border-[rgba(212,175,55,0.15)]'
      break
    case 'building': {
      const pct = buildState?.progress_pct ?? 0
      label = `Building · ${buildingLayerLabel(layerPips, pct)}`
      cls = 'text-amber-400 border-amber-400/30 animate-pulse'
      break
    }
    case 'built':
      label = 'Built · all verified'
      cls = 'text-emerald-400 border-emerald-400/30'
      break
    case 'attention': {
      const building = layerPips.find((p) => p.state === 'building')
      label = building
        ? `Attention · ${BRAHMA_LEXICON[building.layer].sanskrit} thin`
        : 'Attention'
      cls = 'text-amber-400 border-amber-400/30'
      break
    }
    case 'failed': {
      const failedPip = layerPips.find((p) => p.state === 'building')
      label = failedPip
        ? `Failed · ${BRAHMA_LEXICON[failedPip.layer].sanskrit}`
        : 'Failed'
      cls = 'text-red-400 border-red-400/30'
      break
    }
  }

  return (
    <span
      aria-label={`${chartName}: ${label}`}
      className={cn(
        'inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[10px] font-mono tracking-[0.06em] uppercase',
        cls,
      )}
    >
      {state === 'building' && (
        <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
      )}
      {label}
    </span>
  )
}

// ── Layer pip rail ──────────────────────────────────────────────────────────

const PIP_STATE_CLASS: Record<LayerPip['state'], string> = {
  dim: 'bg-[rgba(212,175,55,0.08)] border border-[rgba(212,175,55,0.12)]',
  building: 'bg-amber-400/40 border border-amber-400/60 animate-pulse',
  amber: 'bg-amber-400/25 border border-amber-400/40',
  lit: 'bg-gradient-to-r from-[#a26d0e] to-[#f4d160] border-0',
}

function LayerPipRail({ pips, chartName }: { pips: LayerPip[]; chartName: string }) {
  const litCount = pips.filter((p) => p.state === 'lit').length
  return (
    <div
      role="img"
      aria-label={`Build progress: ${litCount} of ${pips.length} layers complete`}
      className="flex gap-1"
      title={`${litCount} / ${pips.length} layers complete`}
    >
      {pips.map((pip) => {
        const lex = BRAHMA_LEXICON[pip.layer]
        return (
          <div
            key={pip.layer}
            title={`${lex.sanskrit} · ${lex.english} · ${pip.state}`}
            className={cn('h-1.5 flex-1 rounded-full', PIP_STATE_CLASS[pip.state])}
          />
        )
      })}
    </div>
  )
}

// ── Main card ───────────────────────────────────────────────────────────────

export function ClientCard({ chart }: Props) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const health = healthStatus(chart)
  const overallState = deriveOverallState(chart.buildState, chart.layerPips)
  const isBuilding = overallState === 'building'
  const hasBuilt = overallState === 'built' || overallState === 'attention'

  return (
    <>
      <div className="brand-card rounded-xl p-4 flex flex-col gap-3 hover:border-[rgba(212,175,55,0.35)] transition-colors">

        {/* Line 1: name + state chip + health dot */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="bt-heading text-[#fce29a]">{chart.name}</span>
          <div className="flex items-center gap-2">
            <StateChip
              state={overallState}
              buildState={chart.buildState}
              layerPips={chart.layerPips}
              chartName={chart.name}
            />
            <span
              aria-label={`Health: ${health}`}
              className={cn(
                'inline-block h-1.5 w-1.5 rounded-full shadow-[0_0_4px_currentColor] flex-shrink-0',
                HEALTH_DOT_CLASS[health],
              )}
            />
          </div>
        </div>

        {/* Line 2: birth metadata */}
        <div>
          <span className="bt-label" style={{ color: 'rgba(212,175,55,0.42)' }}>
            {chart.birth_date} · {chart.birth_place}
          </span>
        </div>

        {/* Line 3: layer pip rail */}
        <LayerPipRail pips={chart.layerPips} chartName={chart.name} />

        {/* Moment phrase */}
        <div className="text-[rgba(212,175,55,0.3)] text-xs truncate">
          <MomentPhrase
            pyramidPercent={chart.pyramidPercent}
            lastLayerActivity={chart.lastLayerActivity}
          />
        </div>

        {/* Action row */}
        <div className="flex gap-2 flex-wrap">
          <Link
            href={`/clients/${chart.id}/consult`}
            aria-label={`Open — ${chart.name}`}
            className="brand-cta text-xs rounded-md px-3 py-1.5 flex-1 text-center"
          >
            Open
          </Link>
          <Link
            href={`/clients/${chart.id}/build`}
            aria-label={`${isBuilding ? 'Resume' : 'Build'} — ${chart.name}`}
            className={GHOST_BTN}
          >
            {isBuilding ? 'Resume' : 'Build'}
          </Link>
          {hasBuilt && (
            <Link
              href={`/clients/${chart.id}/consult`}
              aria-label={`Consult — ${chart.name}`}
              className={GHOST_BTN}
            >
              Consult
            </Link>
          )}
          <Link
            href={`/clients/${chart.id}/edit`}
            aria-label={`Edit — ${chart.name}`}
            className={GHOST_BTN}
          >
            Edit
          </Link>
          <button
            type="button"
            aria-label={`Delete — ${chart.name}`}
            className={DANGER_BTN}
            onClick={() => setDeleteOpen(true)}
          >
            Delete
          </button>
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
