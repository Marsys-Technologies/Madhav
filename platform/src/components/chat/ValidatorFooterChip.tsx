'use client'

/**
 * ValidatorFooterChip — γ4
 *
 * Inline amber chip rendered below the message body when the citation gate
 * emits a soft-fail (status === 'warn').
 *
 * Disclosure-tier gating:
 *   super_admin  → chip label + first issue as tooltip
 *   other tiers  → chip label only ("Validation warning")
 *
 * "Details" button opens the PerMessageDetailsDrawer (β6).
 */

interface ValidatorFooterChipProps {
  issues: string[]
  isSuperAdmin: boolean
  onOpenDetails: () => void
}

export function ValidatorFooterChip({
  issues,
  isSuperAdmin,
  onOpenDetails,
}: ValidatorFooterChipProps) {
  const firstIssue = issues[0] ?? ''

  return (
    <div
      className="mt-1 flex items-center gap-1.5"
      data-testid="v2-validator-footer-chip"
    >
      <div
        className="flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-950/30 px-2.5 py-0.5 text-[10px] text-amber-300"
        title={isSuperAdmin && firstIssue ? firstIssue : undefined}
        role="status"
        aria-label="Validation warning"
      >
        <span aria-hidden="true">⚠</span>
        <span>
          {isSuperAdmin && firstIssue ? 'Citation warning' : 'Validation warning'}
        </span>
      </div>
      <button
        type="button"
        onClick={onOpenDetails}
        className="text-[10px] text-amber-400/70 underline underline-offset-2 hover:text-amber-300 transition-colors"
        data-testid="v2-validator-chip-details-btn"
      >
        Details
      </button>
    </div>
  )
}
