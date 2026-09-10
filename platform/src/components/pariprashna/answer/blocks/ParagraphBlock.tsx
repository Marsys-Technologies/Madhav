import type { ReactNode } from 'react'
import type { Citation, ReadingRole, TableSpan } from '../../state/types'
import { proseWithCitations } from '../proseWithCitations'
import { TableBlock } from './TableBlock'

const ROLE_CLASS: Record<ReadingRole, string> = {
  verdict: 'pp-prose pp-verdict',
  elaboration: 'pp-prose',
  verse: 'pp-verse',
  caveat: 'pp-caveat',
}

/**
 * DD-22, approach (c) — "annotate rather than split": a table embedded
 * inside a larger prose block never changes `committedBlocks`' cardinality
 * server-side (still one block per role-shift). This is the render-time
 * half of that approach — the ONLY place `tableSpans` is consumed. It slices
 * `text` at the server-computed offsets and interleaves real `<TableBlock>`s
 * between the surrounding prose `<p>`s, rather than rendering the table's
 * raw markdown pipe-syntax as flat, illegible text inside one `<p>`.
 *
 * Byte-exact by construction: `text.slice(cursor, span.start)` +
 * `text.slice(span.start, span.end)` for every span, then the trailing
 * `text.slice(cursor)`, walks `text` start to end with no gaps or overlaps —
 * verified in `block_classifier.test.ts` against the offsets this renders.
 */
function renderWithTableSpans(
  text: string,
  role: ReadingRole | undefined,
  turnId: string,
  citations: Record<number, Citation>,
  tableSpans: TableSpan[],
): ReactNode {
  const segments: ReactNode[] = []
  let cursor = 0
  const proseClassName = ROLE_CLASS[role ?? 'elaboration']
  tableSpans.forEach((span, i) => {
    const proseText = text.slice(cursor, span.start)
    if (proseText.trim().length > 0) {
      segments.push(
        <p key={`prose-${i}`} className={proseClassName}>
          {proseWithCitations(proseText, turnId, citations)}
        </p>,
      )
    }
    segments.push(<TableBlock key={`table-${i}`} table={span.table} />)
    cursor = span.end
  })
  const trailingProse = text.slice(cursor)
  if (trailingProse.trim().length > 0) {
    segments.push(
      <p key="prose-trailing" className={proseClassName}>
        {proseWithCitations(trailingProse, turnId, citations)}
      </p>,
    )
  }
  return <>{segments}</>
}

export function ParagraphBlock({
  turnId,
  text,
  role,
  citations,
  tableSpans,
}: {
  turnId: string
  text: string
  role?: ReadingRole
  citations: Record<number, Citation>
  tableSpans?: TableSpan[]
}) {
  if (tableSpans && tableSpans.length > 0) {
    return renderWithTableSpans(text, role, turnId, citations, tableSpans)
  }
  return <p className={ROLE_CLASS[role ?? 'elaboration']}>{proseWithCitations(text, turnId, citations)}</p>
}
