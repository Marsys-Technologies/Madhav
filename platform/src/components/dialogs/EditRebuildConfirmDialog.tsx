'use client'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Props {
  chartName: string
  open: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function EditRebuildConfirmDialog({ chartName, open, onConfirm, onCancel }: Props) {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onCancel() }}>
      <DialogContent
        style={{
          background: '#08070a',
          border: '1px solid rgba(212,175,55,0.25)',
          borderRadius: 12,
          maxWidth: 440,
        }}
      >
        <DialogHeader>
          <DialogTitle
            style={{
              fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
              fontSize: 20,
              color: '#d4a648',
              fontWeight: 500,
            }}
          >
            Rebuild {chartName}?
          </DialogTitle>
        </DialogHeader>

        <p style={{ fontSize: 13, color: '#888373', marginTop: 4 }}>
          Editing birth details rebuilds the entire chart from scratch (Gaṇita → Mīmāṃsā).
          Current results will be replaced.
        </p>

        <div
          style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}
        >
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            style={{ color: '#888373', fontSize: 13 }}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            style={{
              background: 'var(--gold-primary, #d4a648)',
              color: 'var(--obsidian-bg, #08070a)',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            Rebuild
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
