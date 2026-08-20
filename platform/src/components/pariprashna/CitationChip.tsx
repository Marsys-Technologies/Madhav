'use client'

import type { Grade } from './state/types'
import { useDockController } from './dock/DockController'

/**
 * Fixed-geometry inline chip (§6.7, M6): 20×16px box, never resizes when
 * hydrated. Click deep-links to the right dock on wide viewports, or opens
 * the mobile bottom sheet below the dock's breakpoint (§9.2) — decided
 * inside `openToCitation`, so this component doesn't need to know which.
 */
export function CitationChip({ n, grade, turnId }: { n: number; grade?: Grade; turnId: string }) {
  const { openToCitation } = useDockController()
  return (
    <button
      type="button"
      className="pp-chip"
      data-testid="pp-citation-chip"
      data-grade={grade === 'catalog' ? 'catalog' : undefined}
      onClick={(e) => {
        e.stopPropagation()
        openToCitation(turnId, n)
      }}
      aria-label={`Citation ${n}${grade === 'catalog' ? ', catalog-only, unverified' : ''} — open in grounding dock`}
    >
      {n}
    </button>
  )
}
