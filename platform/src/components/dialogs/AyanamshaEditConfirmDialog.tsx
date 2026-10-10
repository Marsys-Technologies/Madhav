'use client'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'

/**
 * Strong confirmation for changing the ayanamsha of an existing chart under the
 * `warn` edit policy (SS N-319). Plain and unsoftened: the change erases the
 * chart's built results and archives its conversations. Confirming makes the
 * form send `confirm_destructive: true`; the server enforces it regardless.
 */
interface Props {
  chartName: string
  open: boolean
  before: string
  after: string
  onConfirm: () => void
  onCancel: () => void
}

export function AyanamshaEditConfirmDialog({ chartName, open, before, after, onConfirm, onCancel }: Props) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) onCancel()
      }}
    >
      <DialogContent
        showCloseButton={false}
        role="alertdialog"
        className="max-w-lg border border-[var(--jw-danger,#d9534f)] bg-[#0a0a0a] text-[#ebe3d2] sm:max-w-lg"
      >
        <DialogHeader>
          <DialogTitle className="font-[family-name:var(--font-cormorant)] text-2xl font-medium text-[#ebe3d2]">
            Change the ayanamsha of {chartName}?
          </DialogTitle>
          <DialogDescription className="text-sm text-[rgba(235,227,210,0.85)]">
            This erases every built result for this chart and archives its conversations. It requires your confirmation.
          </DialogDescription>
        </DialogHeader>

        <p className="text-sm text-[rgba(235,227,210,0.8)]" data-testid="ayanamsha-before-after">
          <span className="line-through decoration-[rgba(235,227,210,0.35)]">{before || '—'}</span>
          {' → '}
          <span className="text-[#ebe3d2]">{after || '—'}</span>
        </p>

        <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm text-[rgba(235,227,210,0.8)]">
          <li>All built results for this chart are erased and the whole chart is rebuilt.</li>
          <li>Existing Paripraśna conversations are archived read-only.</li>
          <li>The erased results are not restored if you change your mind.</li>
        </ul>

        <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="ghost" onClick={onCancel} className="min-h-11 text-[rgba(235,227,210,0.72)]">
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            className="min-h-11 bg-[#d9534f] font-medium text-white hover:bg-[#c9302c] focus-visible:ring-2 focus-visible:ring-[#d9534f]"
          >
            Erase results and change ayanamsha
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
