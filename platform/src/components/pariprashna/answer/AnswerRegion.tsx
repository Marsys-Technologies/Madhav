import type { TurnState } from '../state/types'
import { FrozenBlock } from './FrozenBlock'
import { VolatileTail } from './VolatileTail'
import { PassSeamLive } from './PassSeamLive'

/**
 * A vertical list of blocks (§5.1 ②). Committed blocks are `FrozenBlock`s,
 * memoized and never re-rendered post-commit; at most one live element
 * follows them — either the volatile prose tail, or (between passes) the
 * live pass seam. Exactly one of {tail, activeSeam} is non-null at a time
 * in practice (the engine is either composing prose or between passes,
 * never both), which is what keeps "exactly zero or one volatile block"
 * true even with the seam extension.
 */
export function AnswerRegion({ turn }: { turn: TurnState }) {
  if (turn.blocks.length === 0 && !turn.tail && !turn.activeSeam) return null
  return (
    <div className="py-1">
      {turn.blocks.map((block) => (
        <FrozenBlock key={block.id} turnId={turn.id} block={block} citations={turn.citations} />
      ))}
      {turn.activeSeam && <PassSeamLive seam={turn.activeSeam} />}
      {turn.tail && (
        <VolatileTail turnId={turn.id} tail={turn.tail} citations={turn.citations} hollowCaret={turn.reconnectHollowCaret} />
      )}
    </div>
  )
}
