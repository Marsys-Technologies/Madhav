import type { ReactNode } from 'react'
import type { Citation } from '../state/types'
import { CitationChip } from '../CitationChip'

const CITATION_TOKEN = /⟦(\d+)⟧/g

/**
 * Splits committed/tail prose text on citation sentinels (already rewritten
 * to `⟦n⟧` server-side pre-wire per §8.4.1 — the client never sees a raw
 * sentinel) and renders each as a fixed-geometry `<CitationChip>` inline
 * token, never as a later-arriving badge (M6: chips render at final
 * geometry on first paint).
 *
 * STUB SCOPE NOTE: fixture prose here is plain text, not sanitized markup —
 * a real server response (§8.4.2 prose-leak-lint + §8.4.3 role tagging)
 * would arrive as reader-safe HTML with gloss spans already marked; this
 * renderer's token-splitting approach still applies unchanged to that HTML
 * (split on text nodes only), it just has nothing further to render here
 * since our fixtures don't include markup beyond the citation tokens.
 */
export function proseWithCitations(text: string, turnId: string, citations: Record<number, Citation>): ReactNode[] {
  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null
  CITATION_TOKEN.lastIndex = 0
  let key = 0
  while ((match = CITATION_TOKEN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<span key={`t${key++}`}>{text.slice(lastIndex, match.index)}</span>)
    }
    const n = Number(match[1])
    parts.push(<CitationChip key={`c${key++}`} n={n} grade={citations[n]?.grade} turnId={turnId} />)
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    parts.push(<span key={`t${key++}`}>{text.slice(lastIndex)}</span>)
  }
  return parts
}
