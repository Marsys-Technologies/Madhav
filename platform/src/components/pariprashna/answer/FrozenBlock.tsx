import { memo } from 'react'
import type { CommittedBlock, Citation } from '../state/types'
import { ParagraphBlock } from './blocks/ParagraphBlock'
import { TableBlock } from './blocks/TableBlock'
import { VerseBlock } from './blocks/VerseBlock'
import { GapRibbonBlock } from './blocks/GapRibbonBlock'
import { SeamBlock } from './blocks/SeamBlock'

export interface FrozenBlockProps {
  turnId: string
  block: CommittedBlock
  citations: Record<number, Citation>
}

function renderBlockContent({ turnId, block, citations }: FrozenBlockProps) {
  switch (block.kind) {
    case 'paragraph':
    case 'list':
      return <ParagraphBlock turnId={turnId} text={block.html} role={block.role} citations={citations} />
    case 'heading':
      return (
        <h3 style={{ fontFamily: 'var(--pp-font-serif)', fontSize: '24px', lineHeight: 1.25, fontWeight: 600, margin: '20px 0 8px' }}>
          {block.html}
        </h3>
      )
    case 'table':
      return block.table ? <TableBlock table={block.table} /> : null
    case 'verse':
      return <VerseBlock turnId={turnId} text={block.html} citations={citations} />
    case 'gap_ribbon':
      return <GapRibbonBlock text={block.gapText ?? block.html} />
    case 'seam':
      return <SeamBlock summary={block.seamSummary ?? ''} />
    case 'prediction_card':
      // Rendered in the right dock, not inline (native ruling 2026-07-27,
      // §5.8.0 ruling 2 / §3.2). The block still exists in `turn.blocks` so
      // the dock can discover it by scanning committed blocks — nothing
      // renders here.
      return null
    default:
      return null
  }
}

function FrozenBlockImpl(props: FrozenBlockProps) {
  const content = renderBlockContent(props)
  if (content === null) return null
  // `data-committed="true"` (§9.3 structural test hook): the aria-live
  // discipline gate asserts no committed block is a descendant of the
  // streaming tail's `[aria-live="polite"]` region — a committed block
  // staying inside the live region would cause a screen reader to
  // re-announce settled prose forever. Tagging every committed block here
  // (rather than per-block-kind) means the assertion holds regardless of
  // which block type settles.
  return (
    <div data-committed="true" data-block-kind={props.block.kind}>
      {content}
    </div>
  )
}

/**
 * `React.memo` with an ALWAYS-EQUAL comparator (§8.2, P1 in code): props
 * are set exactly once at commit; content mutation post-commit is
 * impossible by construction. This is the mechanism the dev harness's
 * React Profiler check asserts against — see this build's final report for
 * how to verify it (no committed FrozenBlock may ever re-render).
 */
export const FrozenBlock = memo(FrozenBlockImpl, () => true)
FrozenBlock.displayName = 'FrozenBlock'
