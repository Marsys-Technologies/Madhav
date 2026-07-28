import type { Citation, ReadingRole } from '../../state/types'
import { proseWithCitations } from '../proseWithCitations'

const ROLE_CLASS: Record<ReadingRole, string> = {
  verdict: 'pp-prose pp-verdict',
  elaboration: 'pp-prose',
  verse: 'pp-verse',
  caveat: 'pp-caveat',
}

export function ParagraphBlock({
  turnId,
  text,
  role,
  citations,
}: {
  turnId: string
  text: string
  role?: ReadingRole
  citations: Record<number, Citation>
}) {
  return <p className={ROLE_CLASS[role ?? 'elaboration']}>{proseWithCitations(text, turnId, citations)}</p>
}
