'use client'

import { useState } from 'react'
import type { TurnState } from '../state/types'
import { WorkingBand } from './WorkingBand'
import { ActivityList } from './ActivityList'

/**
 * Mounts the instant the turn opens, at final fixed height; NEVER unmounts
 * (§5.1). Expansion is user-initiated only and grows strictly downward.
 */
export function WorkingRegion({ turn }: { turn: TurnState }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="rounded-[10px] overflow-hidden" style={{ border: '1px solid var(--pp-rule)', background: 'var(--pp-panel)' }}>
      <WorkingBand turn={turn} expanded={expanded} onToggle={() => setExpanded((v) => !v)} />
      <ActivityList activities={turn.activities} open={expanded} />
    </div>
  )
}
