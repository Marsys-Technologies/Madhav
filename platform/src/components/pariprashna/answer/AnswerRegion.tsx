import type { TurnState } from '../state/types'
import { FrozenBlock } from './FrozenBlock'
import { VolatileTail } from './VolatileTail'
import { PassSeamLive } from './PassSeamLive'
import { LogToSamiksha } from '../samiksha/LogToSamiksha'

/**
 * A vertical list of blocks (§5.1 ②). Committed blocks are `FrozenBlock`s,
 * memoized and never re-rendered post-commit; at most one live element
 * follows them — either the volatile prose tail, or (between passes) the
 * live pass seam. Exactly one of {tail, activeSeam} is non-null at a time
 * in practice (the engine is either composing prose or between passes,
 * never both), which is what keeps "exactly zero or one volatile block"
 * true even with the seam extension.
 *
 * `chartId` (lane P2-A / G2-A · FD-4) mounts the in-stream `LogToSamiksha`
 * confirm affordance for every prediction candidate the wire has surfaced so
 * far on this turn (`turn.pendingPredictionCandidates`) — built and
 * unmounted since PB-3, live for the first time here. Optional because the
 * fixture-replay host has no real chart id; a fixture turn simply never
 * populates `pendingPredictionCandidates` (no fixture builder emits a
 * `prediction_card` event today), so the guard below is a defensive no-op on
 * that path rather than a live gap.
 */
export function AnswerRegion({ turn, chartId }: { turn: TurnState; chartId?: string }) {
  const hasPending = turn.pendingPredictionCandidates.length > 0
  if (turn.blocks.length === 0 && !turn.tail && !turn.activeSeam && !hasPending) return null
  return (
    <div className="py-1">
      {turn.blocks.map((block) => (
        <FrozenBlock key={block.id} turnId={turn.id} block={block} citations={turn.citations} />
      ))}
      {turn.activeSeam && <PassSeamLive seam={turn.activeSeam} />}
      {turn.tail && (
        <VolatileTail turnId={turn.id} tail={turn.tail} citations={turn.citations} hollowCaret={turn.reconnectHollowCaret} />
      )}
      {chartId && hasPending && (
        <div className="pp-prediction-affordances flex flex-col gap-2 mt-2">
          {turn.pendingPredictionCandidates.map((p) => (
            <LogToSamiksha
              key={p.partId}
              chartId={chartId}
              conversationId={p.conversationId}
              messagePartId={p.partId}
              candidate={p.candidate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
