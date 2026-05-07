'use client'

import { useState } from 'react'
import { BookmarkPlus, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { detectPrediction } from '@/lib/consume/prediction-detection'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface Props {
  answerText: string
  queryId?: string
}

export function LogPredictionAction({ answerText, queryId }: Props) {
  const detection = detectPrediction(answerText)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [logged, setLogged] = useState(false)

  if (!detection.detected) return null

  return (
    <>
      {logged ? (
        <span className="inline-flex items-center gap-1 rounded text-[11px] text-emerald-400">
          <CheckCircle2 className="h-3 w-3" />
          Logged
        </span>
      ) : (
        <button
          type="button"
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:border-[rgba(var(--brand-gold-rgb),0.4)] hover:text-[var(--brand-gold)] transition-colors"
          title="Log this prediction to the prediction ledger"
        >
          <BookmarkPlus className="h-3 w-3" />
          Log prediction
        </button>
      )}

      <LogPredictionDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        answerText={answerText}
        prefillHorizon={detection.horizon}
        prefillConfidence={detection.confidence ?? 0.7}
        queryId={queryId}
        onLogged={id => {
          setLogged(true)
          setDialogOpen(false)
          toast.success(`Prediction logged · PRED.${id.slice(0, 8)}`)
        }}
      />
    </>
  )
}

// ── Dialog ────────────────────────────────────────────────────────────────────

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  answerText: string
  prefillHorizon?: string
  prefillConfidence: number
  queryId?: string
  onLogged: (id: string) => void
}

function LogPredictionDialog({
  open,
  onOpenChange,
  answerText,
  prefillHorizon,
  prefillConfidence,
  queryId,
  onLogged,
}: DialogProps) {
  const [horizon, setHorizon] = useState(prefillHorizon ?? '')
  const [falsifier, setFalsifier] = useState('')
  const [confidence, setConfidence] = useState(prefillConfidence)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!falsifier.trim()) {
      setError('Falsifier is required — what observation would refute this prediction?')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const today = new Date().toISOString().slice(0, 10)
      const res = await fetch('/api/lel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'append_prediction',
          payload: {
            query_id: queryId ?? 'ui-manual',
            prediction_text: answerText.slice(0, 2000),
            confidence,
            horizon_start: today,
            horizon_end: today,
            falsifier: falsifier.trim(),
          },
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error((body as { error?: string }).error ?? `HTTP ${res.status}`)
      }
      const { id } = await res.json() as { id: string }
      onLogged(id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Log prediction</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-1">
          {/* Horizon */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-foreground" htmlFor="pred-horizon">
              Horizon
            </label>
            <input
              id="pred-horizon"
              type="text"
              value={horizon}
              onChange={e => setHorizon(e.target.value)}
              placeholder="e.g. 2026, Saturn dasha, next 6 months"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Falsifier */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-foreground" htmlFor="pred-falsifier">
              Falsifier <span className="text-destructive">*</span>
            </label>
            <textarea
              id="pred-falsifier"
              value={falsifier}
              onChange={e => setFalsifier(e.target.value)}
              rows={3}
              placeholder="What observation would refute this prediction? (required by Learning Layer discipline)"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
            />
          </div>

          {/* Confidence */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-foreground" htmlFor="pred-confidence">
              Confidence: <span className="tabular-nums">{Math.round(confidence * 100)}%</span>
            </label>
            <input
              id="pred-confidence"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={confidence}
              onChange={e => setConfidence(parseFloat(e.target.value))}
              className="w-full accent-[var(--brand-gold)]"
            />
          </div>

          {error && (
            <p role="alert" className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {error}
            </p>
          )}

          <div className="flex items-center justify-end gap-2 pt-1">
            <DialogClose>
              <Button type="button" variant="ghost" size="sm">Cancel</Button>
            </DialogClose>
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? 'Logging…' : 'Log prediction'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
