import type { Citation } from '../../state/types'
import { proseWithCitations } from '../proseWithCitations'

/** Commit-only (§5.6): classical quote + gloss line, never streamed. */
export function VerseBlock({ turnId, text, gloss, citations }: { turnId: string; text: string; gloss?: string; citations: Record<number, Citation> }) {
  return (
    <div className="my-3">
      <p className="pp-verse">{proseWithCitations(text, turnId, citations)}</p>
      {gloss && (
        <p className="mt-1" style={{ fontFamily: 'var(--pp-font-sans)', fontSize: '12.5px', color: 'var(--pp-ink-dim)', paddingLeft: '20px' }}>
          {gloss}
        </p>
      )}
    </div>
  )
}
