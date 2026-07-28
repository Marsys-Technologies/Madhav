'use client'

import type { Citation } from '../state/types'

const GRADE_LABEL: Record<Citation['grade'], string> = {
  confirmed: 'WELL-GROUNDED',
  supported: 'SUPPORTED',
  catalog: 'CATALOG-ONLY — UNVERIFIED',
  honest_gap: 'HONEST GAP',
}

const SOURCE_CLASS_LABEL: Record<Citation['sourceClass'], string> = {
  chart_factor: 'CHART FACTOR',
  classical_source: 'CLASSICAL SOURCE',
  computed_window: 'COMPUTED WINDOW',
}

/**
 * Mobile bottom sheet (§9.2, §6.7): below the dock's breakpoint the right
 * dock is hidden entirely, so a chip tap opens this instead — same
 * citation content, sheet chrome. Desktop never uses this component; there
 * the same tap deep-links into `RightDock` (`DockController.openToCitation`
 * picks one or the other based on viewport width).
 */
export function CitationCard({ citation, onClose }: { citation: Citation; onClose: () => void }) {
  return (
    <>
      <div className="pp-sheet-scrim" onClick={onClose} />
      <div className="pp-sheet" role="dialog" aria-modal="true" aria-label="Citation detail">
        <div className="mx-auto mb-3" style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--pp-rule-strong)' }} />
        <div style={{ fontSize: 9, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'var(--pp-gold-dim)', marginBottom: 8 }}>
          {SOURCE_CLASS_LABEL[citation.sourceClass]}
        </div>
        <div className="pp-prose" style={{ fontSize: 16, marginBottom: 10 }}>
          {citation.title}
        </div>
        <p style={{ fontFamily: 'var(--pp-font-sans)', fontSize: 13, color: 'var(--pp-ink-dim)', lineHeight: 1.5, marginBottom: 10 }}>
          {citation.relevance}
        </p>
        <div className="font-mono" style={{ fontSize: 11, color: 'var(--pp-gold-dim)', marginBottom: 12 }}>
          {citation.ref}
        </div>
        <span className="pp-grade-chip">{GRADE_LABEL[citation.grade]}</span>
      </div>
    </>
  )
}
