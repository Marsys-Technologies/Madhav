'use client'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'

/**
 * Confirmation for a computation-affecting chart correction.
 *
 * Specific and informational: the exact before/after of every changed field,
 * that previous computed results will be replaced, that existing Paripraśna
 * conversations are archived read-only, and that progress stays visible. It
 * never asks the user to delete or recreate the chart. Focus is trapped by the
 * dialog primitive; the caller returns focus to its trigger on cancel.
 */
export interface ChangedField {
  key: string
  label: string
  before: string
  after: string
}

interface Props {
  chartName: string
  open: boolean
  changes: ChangedField[]
  onConfirm: () => void
  onCancel: () => void
}

export function EditRebuildConfirmDialog({ chartName, open, changes, onConfirm, onCancel }: Props) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) onCancel()
      }}
    >
      <DialogContent
        showCloseButton={false}
        className="max-w-lg border border-[rgba(201,162,76,0.5)] bg-[#0a0a0a] text-[#ebe3d2] sm:max-w-lg"
      >
        <DialogHeader>
          <DialogTitle className="font-[family-name:var(--font-cormorant)] text-2xl font-medium text-[#ebe3d2]">
            Recompute {chartName}?
          </DialogTitle>
          <DialogDescription className="text-sm text-[rgba(235,227,210,0.72)]">
            These corrected details change the chart itself, so the whole chart is computed again.
          </DialogDescription>
        </DialogHeader>

        <table className="w-full text-left text-sm">
          <caption className="sr-only">Changed chart details</caption>
          <thead>
            <tr className="text-[11px] uppercase tracking-[0.2em] text-[#a37f37]">
              <th scope="col" className="py-1.5 pr-3 font-normal">Field</th>
              <th scope="col" className="py-1.5 pr-3 font-normal">Before</th>
              <th scope="col" className="py-1.5 font-normal">After</th>
            </tr>
          </thead>
          <tbody>
            {changes.map((change) => (
              <tr key={change.key} data-testid={`change-${change.key}`} className="border-t border-[rgba(201,162,76,0.25)]">
                <th scope="row" className="py-2 pr-3 font-normal text-[rgba(235,227,210,0.72)]">{change.label}</th>
                <td className="py-2 pr-3 text-[rgba(235,227,210,0.72)] line-through decoration-[rgba(235,227,210,0.35)]">
                  {change.before || '—'}
                </td>
                <td className="py-2 text-[#ebe3d2]">{change.after || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm text-[rgba(235,227,210,0.8)]">
          <li>Previous computed results will be replaced; they are never shown for the corrected details.</li>
          <li>Existing Paripraśna conversations will be archived read-only under the earlier chart details.</li>
          <li>Recomputation takes time. Progress stays visible on the chart workspace.</li>
        </ul>

        <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="ghost" onClick={onCancel} className="min-h-11 text-[rgba(235,227,210,0.72)]">
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            className="min-h-11 bg-[#c9a24c] font-medium text-black hover:bg-[#d8b25e] focus-visible:ring-2 focus-visible:ring-[#c9a24c]"
          >
            Save and recompute
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
