'use client'

import { useState } from 'react'
import type { BuildAction, BuildScope } from '@/lib/build/plan'
import { PlanModal } from './PlanModal'
import { PauseStopGroup } from './PauseStopGroup'

interface ScopeStats {
  total: number
  dormant: number
  stale: number
  active_run_id?: string | null
  is_paused?: boolean
}

interface Props {
  chartId: string
  scope: BuildScope
  scopeTarget?: string | null
  stats: ScopeStats
  size?: 'sm' | 'md'
  onRunStarted?: (runId: string) => void
  onRunStateChange?: () => void
  /** When provided and action === 'rebuild', called instead of opening PlanModal */
  onRebuildOverride?: () => void
}

function deriveAction(stats: ScopeStats): { label: string; action: BuildAction } {
  if (stats.dormant === stats.total) return { label: 'Build', action: 'build' }
  if (stats.stale > 0) return { label: 'Update', action: 'update' }
  return { label: 'Rebuild', action: 'rebuild' }
}

export function BuildActionButton({
  chartId,
  scope,
  scopeTarget = null,
  stats,
  size = 'md',
  onRunStarted,
  onRunStateChange,
  onRebuildOverride,
}: Props) {
  const [showModal, setShowModal] = useState(false)

  if (stats.active_run_id) {
    return (
      <PauseStopGroup
        runId={stats.active_run_id}
        chartId={chartId}
        isPaused={!!stats.is_paused}
        onStateChange={onRunStateChange}
      />
    )
  }

  const { label, action } = deriveAction(stats)

  const btnStyle: React.CSSProperties =
    size === 'sm'
      ? {
          padding: '3px 8px',
          fontSize: '10px',
          borderRadius: '4px',
        }
      : {}

  const handleClick = () => {
    if (action === 'rebuild' && onRebuildOverride) {
      onRebuildOverride()
    } else {
      setShowModal(true)
    }
  }

  return (
    <>
      <button
        className="marsys-btn-primary"
        style={btnStyle}
        onClick={handleClick}
      >
        {label}
      </button>

      {showModal && (
        <PlanModal
          chartId={chartId}
          scope={scope}
          scopeTarget={scopeTarget}
          action={action}
          label={label}
          onClose={() => setShowModal(false)}
          onRunStarted={(runId) => {
            setShowModal(false)
            onRunStarted?.(runId)
          }}
        />
      )}
    </>
  )
}
