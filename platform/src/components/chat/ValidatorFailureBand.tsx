'use client'

/**
 * ValidatorFailureBand — γ4
 *
 * Inline red band rendered above a message body when the citation gate
 * emits a hard-fail (status === 'fail').
 *
 * Disclosure-tier gating:
 *   super_admin  → shows issue list inline
 *   other tiers  → shows generic "Validation failed" summary only
 *
 * "Details" button opens the PerMessageDetailsDrawer (β6) where the
 * validator output is already rendered.
 */

interface ValidatorFailureBandProps {
  issues: string[]
  isSuperAdmin: boolean
  onOpenDetails: () => void
}

export function ValidatorFailureBand({
  issues,
  isSuperAdmin,
  onOpenDetails,
}: ValidatorFailureBandProps) {
  return (
    <div
      className="mb-2 rounded-md border border-red-500/40 bg-red-950/40 px-3 py-2 text-xs"
      role="alert"
      data-testid="v2-validator-failure-band"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 min-w-0">
          <span
            className="mt-0.5 shrink-0 text-red-400"
            aria-hidden="true"
          >
            ✕
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-red-300">Citation validation failed</p>
            {isSuperAdmin && issues.length > 0 ? (
              <ul className="mt-1 space-y-0.5 text-red-400/80">
                {issues.map((issue, i) => (
                  <li key={i} className="truncate" title={issue}>
                    {issue}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-0.5 text-red-400/70">
                One or more citations could not be verified.
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onOpenDetails}
          className="shrink-0 rounded px-2 py-0.5 text-[10px] font-medium text-red-300 hover:bg-red-900/60 transition-colors"
          data-testid="v2-validator-failure-details-btn"
        >
          Details
        </button>
      </div>
    </div>
  )
}
