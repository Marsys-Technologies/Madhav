'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Props {
  chartId: string
  chartName: string
  open: boolean
  onClose: () => void
  onDeleted: () => void
}

export function DeleteChartDialog({ chartId, chartName, open, onClose, onDeleted }: Props) {
  const [confirmInput, setConfirmInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const confirmed = confirmInput === chartName

  async function handleDelete() {
    if (!confirmed) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/charts/${chartId}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.error ?? 'Delete failed. Please try again.')
        return
      }
      onDeleted()
    } catch {
      setError('Network error — please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) {
      setConfirmInput('')
      setError(null)
      onClose()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        style={{
          background: '#08070a',
          border: '1px solid rgba(192,57,43,0.35)',
          borderRadius: 12,
          maxWidth: 440,
        }}
      >
        <DialogHeader>
          <DialogTitle
            style={{
              fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
              fontSize: 20,
              color: '#e74c3c',
              fontWeight: 500,
            }}
          >
            Delete {chartName} permanently?
          </DialogTitle>
        </DialogHeader>

        <p style={{ fontSize: 13, color: '#888373', marginTop: 4 }}>
          This immediately and irreversibly wipes the chart and all its data.
          There is no recovery.
        </p>

        <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label
            htmlFor="delete-confirm-input"
            style={{ fontSize: 12, color: '#5d5b54', letterSpacing: '0.04em' }}
          >
            Type <strong style={{ color: '#c8bfb0' }}>{chartName}</strong> to confirm
          </label>
          <Input
            id="delete-confirm-input"
            type="text"
            value={confirmInput}
            placeholder={chartName}
            aria-label={`Type ${chartName} to confirm deletion`}
            className="w-full rounded-md border bg-[#08070a] px-3 py-2 text-sm text-[#f5f0e8] outline-none focus:ring-1 focus:ring-red-500 border-[#2d1a1a]"
            onChange={(e) => {
              setConfirmInput(e.target.value)
              setError(null)
            }}
          />
        </div>

        {error && (
          <p role="alert" style={{ fontSize: 12, color: '#e74c3c', marginTop: 8 }}>
            {error}
          </p>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            style={{ color: '#888373', fontSize: 13 }}
          >
            Cancel
          </Button>
          <Button
            type="button"
            disabled={!confirmed || loading}
            onClick={handleDelete}
            style={{
              background: confirmed ? '#c0392b' : 'rgba(192,57,43,0.2)',
              color: confirmed ? '#fff' : 'rgba(255,255,255,0.3)',
              fontSize: 13,
              fontWeight: 500,
              cursor: confirmed ? 'pointer' : 'not-allowed',
              transition: 'background 0.15s, color 0.15s',
            }}
          >
            {loading ? 'Deleting…' : 'Delete permanently'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
