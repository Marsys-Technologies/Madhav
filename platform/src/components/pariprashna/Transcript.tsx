'use client'

import { useEffect, useRef } from 'react'
import type { TurnState } from './state/types'
import { Turn } from './Turn'
import { FollowPill } from './FollowPill'
import { useFollowScroll } from './hooks/useFollowScroll'

/**
 * Owns scroll (§3.4, §5.5, §5.8.0 ruling 7): a FIXED-HEIGHT viewport. The
 * frame's geometry never changes as a response streams — the reading
 * scrolls, the page doesn't. `overflow-anchor: none` disables the
 * browser's own scroll-anchoring heuristic — the exact mechanism that
 * historically shoved carets under tables (§5.5) — in favor of our own
 * explicit follow logic.
 */
export function Transcript({ turns }: { turns: TurnState[] }) {
  const { ref, showFollowPill, notifyContentGrew, followToBottom, anchorNewTurn } = useFollowScroll<HTMLDivElement>()
  const prevTurnCount = useRef(0)
  const turnRefs = useRef(new Map<string, HTMLDivElement | null>())

  const anyStreaming = turns.some((t) => t.status === 'thinking' || t.status === 'streaming' || t.status === 'submitted')

  useEffect(() => {
    if (turns.length > prevTurnCount.current) {
      const latest = turns[turns.length - 1]
      anchorNewTurn(latest ? turnRefs.current.get(latest.id) ?? null : null)
    }
    prevTurnCount.current = turns.length
    notifyContentGrew(anyStreaming)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turns, anyStreaming])

  return (
    <div className="relative flex-1 min-h-0">
      <div
        ref={ref}
        className="h-full overflow-y-auto px-6 pt-2 pb-3"
        style={{ overflowAnchor: 'none', overscrollBehavior: 'contain' }}
      >
        {turns.map((turn) => (
          <div key={turn.id} ref={(el) => { turnRefs.current.set(turn.id, el) }}>
            <Turn turn={turn} />
          </div>
        ))}
      </div>
      <FollowPill visible={showFollowPill} onClick={followToBottom} />
    </div>
  )
}
