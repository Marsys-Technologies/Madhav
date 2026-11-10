'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { EVENT_CLASSES } from '@/lib/event_classes'

interface LogEventDialogProps {
  chartId: string
  onSuccess: () => void
}

export function LogEventDialog({ chartId, onSuccess }: LogEventDialogProps) {
  const [open, setOpen] = useState(false)
  const [date, setDate] = useState('')
  const [eventClass, setEventClass] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const response = await fetch('/api/lel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'append_event', chartId, payload: { date, eventClass, description } }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        setError(body?.error?.detail ?? 'Could not save the event. Try again.')
        return
      }
      setOpen(false)
      onSuccess()
    } catch {
      setError('Could not save the event. Try again.')
    } finally {
      setSubmitting(false)
    }
  }

  function changeOpen(next: boolean) {
    if (submitting) return
    if (next) {
      setDate('')
      setEventClass('')
      setDescription('')
      setError(null)
    }
    setOpen(next)
  }

  return (
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogTrigger className="rounded-md border border-border px-3 py-1.5 text-sm">Log event</DialogTrigger>
      <DialogContent showCloseButton={false}>
        <DialogTitle>Log new event</DialogTitle>
        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="block text-sm">
            Event date
            <input
              required
              maxLength={10}
              className="mt-1 block w-full rounded-md border border-border bg-input px-3 py-1.5 text-base"
              placeholder="YYYY-MM-DD, YYYY-MM-XX, or YYYY"
              value={date}
              onChange={e => setDate(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            Event type
            <select
              required
              className="mt-1 block w-full rounded-md border border-border bg-input px-3 py-1.5 text-base"
              value={eventClass}
              onChange={e => setEventClass(e.target.value)}
            >
              <option value="">Choose an event type</option>
              {EVENT_CLASSES.map(event => (
                <option key={event.event_class_id} value={event.event_class_id}>{event.name_en}</option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Description
            <textarea
              required
              rows={3}
              maxLength={4000}
              className="mt-1 block w-full rounded-md border border-border bg-input px-3 py-1.5 text-base"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </label>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" disabled={submitting} onClick={() => changeOpen(false)} className="rounded-md border border-border px-4 py-1.5 text-sm">Cancel</button>
            <button type="submit" disabled={submitting} className="rounded-md bg-amber-500 px-4 py-1.5 text-sm font-medium text-black disabled:opacity-50">
              {submitting ? 'Saving…' : 'Save event'}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
