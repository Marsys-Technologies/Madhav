import type { Citation, ReadingRole, TailBlock } from '../state/types'
import { proseWithCitations } from './proseWithCitations'
import { Caret } from './Caret'

const ROLE_CLASS: Record<ReadingRole, string> = {
  verdict: 'pp-prose pp-verdict',
  elaboration: 'pp-prose',
  verse: 'pp-verse',
  caveat: 'pp-caveat',
}

/**
 * The ONLY volatile region in the answer column (§5.1, §8.2): receives
 * deltas via the reducer's `tail` slot, rendered fresh each time (React is
 * free to re-render this — it is the one place re-rendering is expected
 * and cheap, O(tail) not O(transcript)). The caret is the tail's own last
 * child, after the last text node — never positioned by layout guesswork.
 */
export function VolatileTail({
  turnId,
  tail,
  citations,
  hollowCaret,
}: {
  turnId: string
  tail: TailBlock
  citations: Record<number, Citation>
  hollowCaret: boolean
}) {
  return (
    <p className={ROLE_CLASS[tail.role ?? 'elaboration']} aria-live="polite" data-testid="pp-tail" data-pp-tail-live="true">
      {proseWithCitations(tail.text, turnId, citations)}
      <Caret hollow={hollowCaret} />
    </p>
  )
}
