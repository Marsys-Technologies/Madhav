'use client'

import * as React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { runJudge } from '@/lib/performance/api_client'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  window: { start: string; end: string }
  onCompleted: () => void
}

export function JudgeRunModal({ open, onOpenChange, window, onCompleted }: Props) {
  const [limit, setLimit] = React.useState(100)
  const [busy, setBusy] = React.useState(false)
  const [result, setResult] = React.useState<string | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const submit = async () => {
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const r = await runJudge({ window_start: window.start, window_end: window.end, limit })
      setResult(`Judged ${r.judged_count} (✓ ${r.breakdown.correct} / ✗ ${r.breakdown.wrong} / ? ${r.breakdown.ambiguous})`)
      onCompleted()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Run plan-accuracy judge</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <div className="text-xs text-muted-foreground">
            Window: {new Date(window.start).toLocaleDateString()} →{' '}
            {new Date(window.end).toLocaleDateString()}
          </div>
          <label className="block">
            Limit (max 200):
            <input
              type="range"
              min={10}
              max={200}
              step={10}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="ml-2 align-middle"
            />
            <span className="ml-2 font-mono">{limit}</span>
          </label>
          <button
            onClick={submit}
            disabled={busy}
            className="rounded bg-foreground px-3 py-1.5 text-sm text-background disabled:opacity-60"
          >
            {busy ? 'Judging…' : 'Run judge'}
          </button>
          {result && <div className="rounded bg-emerald-500/10 px-2 py-1 text-xs">{result}</div>}
          {error && <div className="rounded bg-rose-500/10 px-2 py-1 text-xs text-rose-500">{error}</div>}
        </div>
      </DialogContent>
    </Dialog>
  )
}
