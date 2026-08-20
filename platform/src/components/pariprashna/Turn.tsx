import { memo } from 'react'
import type { TurnState } from './state/types'
import { UserBlock } from './UserBlock'
import { WorkingRegion } from './working/WorkingRegion'
import { AnswerRegion } from './answer/AnswerRegion'
import { GroundingRegion } from './GroundingRegion'

/**
 * One question→answer unit (§3.4): fixed vertical region order — working
 * above, prose middle, warrant (grounding) below — for every turn, forever.
 *
 * Memoization note (§8.2 "settled turns fully memoized"): the reducer's
 * `updateTurn` helper only replaces the ONE turn object a wire event
 * targets — every other turn in `ThreadState.turns` keeps its prior object
 * reference. `React.memo`'s default shallow-prop comparison therefore
 * already skips re-rendering every turn except the one actually being
 * updated, with no custom comparator needed: a 200-turn thread streaming
 * its 201st re-renders exactly one `<Turn>`, not 201.
 */
function TurnImpl({ turn, chartId }: { turn: TurnState; chartId?: string }) {
  return (
    <div className="pp-turn my-3.5 pb-7" data-testid="pp-turn" data-turn-status={turn.status}>
      <UserBlock text={turn.userText} />
      <div className="my-3.5">
        <WorkingRegion turn={turn} />
        {(turn.status === 'reconnecting' || turn.status === 'interrupted') && turn.status === 'reconnecting' && (
          <div
            className="flex items-center gap-2.5 mt-2 mb-3.5 px-3.5 py-2.5 rounded"
            style={{ border: '1px solid var(--pp-rule)', background: 'var(--pp-tint)', fontSize: 12.5, color: 'var(--pp-ink-dim)' }}
          >
            <span
              aria-hidden
              data-pp-spin
              className="flex-none inline-block w-2 h-2 rounded-full"
              style={{ border: '1.5px solid var(--pp-gold)', borderTopColor: 'transparent' }}
            />
            Connection dropped — resuming from where it left off. Nothing was lost.
          </div>
        )}
        <AnswerRegion turn={turn} chartId={chartId} />
        {turn.status === 'interrupted' && (
          <p className="pp-caveat mt-2" style={{ borderTop: '1px solid var(--pp-rule)', paddingTop: 10 }}>
            The connection was lost partway. What arrived is above; nothing was altered.
          </p>
        )}
        <GroundingRegion turn={turn} />
        {turn.status === 'settled' && <div aria-hidden className="pp-closing-rule" />}
      </div>
    </div>
  )
}

export const Turn = memo(TurnImpl)
