import { useMemo } from 'react'
import type { ActivityRow as ActivityRowT } from '../state/types'
import { ActivityRow } from './ActivityRow'

/**
 * User-expanded, fixed-height internally-scrolling well (~5 rows visible,
 * §5.8.0 ruling 6). Expansion never grows the turn unboundedly — all
 * history is retained and reachable inside the well's own scroll, never
 * ambient. Rows group by pass under a `PASS N` eyebrow (§5.8.1 ruling 8a).
 */
export function ActivityList({ activities, open }: { activities: ActivityRowT[]; open: boolean }) {
  const passes = useMemo(() => {
    const byPass = new Map<number, ActivityRowT[]>()
    for (const row of activities) {
      const list = byPass.get(row.passIndex) ?? []
      list.push(row)
      byPass.set(row.passIndex, list)
    }
    return [...byPass.entries()].sort(([a], [b]) => a - b)
  }, [activities])

  return (
    <div className="pp-activity-well" data-open={open}>
      <div>
        <div className="pp-activity-scroll px-4 pb-3 pt-0.5">
          {passes.map(([passIndex, rows]) => (
            <div key={passIndex}>
              <div
                className="mt-2 mb-0.5"
                style={{ fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}
              >
                Pass {passIndex + 1}
              </div>
              {rows.map((row) => (
                <ActivityRow key={row.id} row={row} />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
