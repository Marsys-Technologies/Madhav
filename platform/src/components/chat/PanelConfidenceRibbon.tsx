'use client'

/**
 * PanelConfidenceRibbon — γ1
 *
 * Thin ribbon rendered at the top of a panel-synthesized assistant message.
 * Shows whether panel members agreed (aligned) or diverged.
 * The "Show panel dissent" toggle is managed by the parent; this ribbon just
 * renders the badge + wires the toggle callback.
 */

interface PanelConfidenceRibbonProps {
  memberCount: number
  hasDivergence: boolean
  showDissent: boolean
  onToggleDissent: () => void
  /** Whether the viewing user is super_admin (controls label verbosity). */
  isSuperAdmin: boolean
  'data-testid'?: string
}

export function PanelConfidenceRibbon({
  memberCount,
  hasDivergence,
  showDissent,
  onToggleDissent,
  isSuperAdmin,
  'data-testid': testId,
}: PanelConfidenceRibbonProps) {
  const alignedColor = hasDivergence
    ? 'border-amber-500/40 bg-amber-950/30 text-amber-300'
    : 'border-emerald-500/40 bg-emerald-950/30 text-emerald-300'

  const statusLabel = hasDivergence ? 'Divergent panel' : 'Aligned panel'
  const memberLabel = `${memberCount} member${memberCount !== 1 ? 's' : ''}`

  return (
    <div
      className={`flex items-center justify-between rounded-md border px-3 py-1.5 text-xs ${alignedColor}`}
      data-testid={testId ?? 'panel-confidence-ribbon'}
      role="region"
      aria-label={`${statusLabel}, ${memberLabel}`}
    >
      <div className="flex items-center gap-2">
        {/* Dot indicator */}
        <span
          className={`h-1.5 w-1.5 rounded-full ${hasDivergence ? 'bg-amber-400' : 'bg-emerald-400'}`}
          aria-hidden="true"
        />
        <span className="font-medium">{statusLabel}</span>
        <span className="text-[10px] opacity-70">{memberLabel} synthesized</span>
      </div>

      {/* Toggle button — only show if user is super_admin or divergence exists (lower tiers still know it exists) */}
      {(isSuperAdmin || hasDivergence) && (
        <button
          type="button"
          onClick={onToggleDissent}
          className="ml-4 flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium opacity-80 hover:opacity-100 transition-opacity focus:outline-none focus-visible:ring-1 focus-visible:ring-current"
          aria-expanded={showDissent}
          aria-controls="panel-dissent-tabs"
          data-testid="panel-dissent-toggle"
        >
          {showDissent ? 'Hide' : 'Show'} panel dissent
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className={`h-2.5 w-2.5 transition-transform ${showDissent ? 'rotate-180' : ''}`}
            aria-hidden="true"
          >
            <path d="M2 4l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
    </div>
  )
}
