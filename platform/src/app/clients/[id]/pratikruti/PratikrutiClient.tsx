'use client'
/**
 * PratikrutiClient — BA-P7B portal learning loops (client component).
 * Fetches open windows / follow-ups / snapshots then renders all five surfaces.
 * Design system: existing Tailwind tokens only (brand-gold, card, border-border, etc.)
 */

import { useEffect, useState, useCallback } from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

interface OpenWindow {
  prediction_id: string
  domain: string
  summary: string
  window_end: string
  composite_verdict: string
}

interface PendingFollowup {
  prediction_id: string
  domain: string
  follow_up_prompt: string
  fructification_date: string
}

interface PendingSnapshot {
  snapshot_id: string
  formula_version: string
  publication_status: string
  created_at: string
  cells_jsonb: unknown
}

interface LearningData {
  open_windows: OpenWindow[]
  pending_followups: PendingFollowup[]
  pending_cosign: PendingSnapshot[]
}

type AdjOutcome = 'happened' | 'partial' | 'didnt' | 'cant_say'
type CoSignAction = 'approved' | 'revoked'

// ── Helpers ───────────────────────────────────────────────────────────────────

async function postLearning(chartId: string, body: object) {
  const res = await fetch(`/api/clients/${chartId}/learning`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── Step 1: Ask-Card ──────────────────────────────────────────────────────────

function AskCard({
  item,
  chartId,
  onDone,
}: {
  item: OpenWindow
  chartId: string
  onDone: (predictionId: string) => void
}) {
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  async function tap(outcome: AdjOutcome) {
    if (busy || done) return
    setBusy(true)
    try {
      await postLearning(chartId, { action: 'adjudicate', prediction_id: item.prediction_id, outcome })
      setDone(true)
      onDone(item.prediction_id)
    } catch {
      setBusy(false)
    }
  }

  if (done) return null

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {item.domain}
          </span>
          <p className="mt-0.5 text-sm text-foreground">{item.summary}</p>
        </div>
        <span className="shrink-0 text-xs text-muted-foreground">
          closed {item.window_end}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {([
          ['happened', 'Happened ✓'],
          ['partial', 'Partially'],
          ['didnt', "Didn't happen"],
          ['cant_say', "Can't say"],
        ] as [AdjOutcome, string][]).map(([outcome, label]) => (
          <button
            key={outcome}
            disabled={busy}
            onClick={() => tap(outcome)}
            className="rounded-md border border-border bg-muted px-3 py-1 text-xs font-medium
                       text-foreground hover:bg-accent hover:text-accent-foreground
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Step 2: LEL Intake Form ───────────────────────────────────────────────────

const MAGNITUDES = ['rupture', 'major', 'significant', 'moderate', 'minor', 'trivial'] as const
const EVENT_CLASSES = [
  'career', 'education', 'health', 'relationship', 'finance',
  'travel', 'family', 'spiritual', 'legal', 'loss', 'other',
]

function LelIntakeForm({ chartId }: { chartId: string }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [form, setForm] = useState({
    event_id: '',
    category: 'career',
    subcategory: '',
    magnitude: 'significant' as typeof MAGNITUDES[number],
    date: '',
    notes: '',
  })

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.event_id.match(/^EVT\..+/) || !form.date) return
    setBusy(true)
    try {
      await postLearning(chartId, {
        action: 'lel_entry',
        event_id: form.event_id,
        category: form.category,
        subcategory: form.subcategory || undefined,
        magnitude: form.magnitude,
        date: form.date,
        notes: form.notes || undefined,
      })
      setDone(true)
    } catch {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
        Life event appended to LEL — provenance resync triggered.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Add Life Event</h3>
        <button
          onClick={() => setOpen(!open)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {open ? 'Collapse ↑' : 'Expand ↓'}
        </button>
      </div>
      {open && (
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Event ID (EVT.XXX)</label>
              <input
                type="text"
                placeholder="EVT.2026.001"
                value={form.event_id}
                onChange={e => setForm(f => ({ ...f, event_id: e.target.value }))}
                required
                pattern="^EVT\..+"
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5
                           text-xs text-foreground placeholder:text-muted-foreground
                           focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Date</label>
              <input
                type="date"
                value={form.date}
                onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
                required
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5
                           text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Category</label>
              <select
                value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5
                           text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {EVENT_CLASSES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Magnitude</label>
              <select
                value={form.magnitude}
                onChange={e => setForm(f => ({ ...f, magnitude: e.target.value as typeof MAGNITUDES[number] }))}
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5
                           text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {MAGNITUDES.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Notes (optional)</label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full rounded-md border border-input bg-background px-2.5 py-1.5
                         text-xs text-foreground placeholder:text-muted-foreground
                         focus:outline-none focus:ring-1 focus:ring-ring resize-none overflow-y-auto"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-primary px-4 py-1.5 text-xs font-medium
                       text-primary-foreground hover:bg-primary/90
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {busy ? 'Appending…' : 'Append to LEL'}
          </button>
        </form>
      )}
    </div>
  )
}

// ── Step 3: Prashna Follow-up Card ───────────────────────────────────────────

function FollowUpCard({
  item,
  chartId,
  onDone,
}: {
  item: PendingFollowup
  chartId: string
  onDone: (predictionId: string) => void
}) {
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  async function tap(outcome: AdjOutcome) {
    if (busy || done) return
    setBusy(true)
    try {
      await postLearning(chartId, {
        action: 'adjudicate',
        prediction_id: item.prediction_id,
        outcome,
      })
      setDone(true)
      onDone(item.prediction_id)
    } catch {
      setBusy(false)
    }
  }

  if (done) return null

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50/40 dark:border-amber-900/30 dark:bg-amber-950/20 p-4 space-y-3">
      <div>
        <span className="text-xs font-medium text-amber-700 dark:text-amber-400 uppercase tracking-wide">
          Follow-up due · {item.fructification_date} · {item.domain}
        </span>
        <p className="mt-0.5 text-sm text-foreground">{item.follow_up_prompt}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {([
          ['happened', 'Happened ✓'],
          ['partial', 'Partially'],
          ['didnt', "Didn't happen"],
          ['cant_say', "Can't say"],
        ] as [AdjOutcome, string][]).map(([outcome, label]) => (
          <button
            key={outcome}
            disabled={busy}
            onClick={() => tap(outcome)}
            className="rounded-md border border-border bg-background px-3 py-1 text-xs font-medium
                       text-foreground hover:bg-accent disabled:opacity-50 transition-colors"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Step 4: Co-Sign Card ──────────────────────────────────────────────────────

function CoSignCard({
  item,
  chartId,
  onDone,
}: {
  item: PendingSnapshot
  chartId: string
  onDone: (snapshotId: string) => void
}) {
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  async function act(cosignAction: CoSignAction) {
    if (busy || done) return
    setBusy(true)
    try {
      await postLearning(chartId, { action: 'cosign', snapshot_id: item.snapshot_id, cosign_action: cosignAction })
      setDone(true)
      onDone(item.snapshot_id)
    } catch {
      setBusy(false)
    }
  }

  if (done) return null

  const cells = (item.cells_jsonb as { families?: unknown[] } | null)?.families ?? []

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div>
        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
          Proposed snapshot · {item.formula_version} · {item.created_at.slice(0, 10)}
        </span>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {Array.isArray(cells) ? cells.length : 0} signal families · Key-2 pending your sign-off
        </p>
      </div>
      <div className="flex gap-2">
        <button
          disabled={busy}
          onClick={() => act('approved')}
          className="rounded-md bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground
                     hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          Approve
        </button>
        <button
          disabled={busy}
          onClick={() => act('revoked' as CoSignAction)}
          className="rounded-md border border-destructive px-4 py-1.5 text-xs font-medium
                     text-destructive hover:bg-destructive/10 disabled:opacity-50 transition-colors"
        >
          Revoke
        </button>
      </div>
    </div>
  )
}

// ── Step 5: Resonance Feedback (QUARANTINED) ──────────────────────────────────

function ResonanceFeedback({ chartId }: { chartId: string }) {
  const [signalRef, setSignalRef] = useState('')
  const [busy, setBusy] = useState(false)

  async function tap(resonance: 'resonates' | 'doesnt_resonate' | 'neutral') {
    if (!signalRef.trim() || busy) return
    setBusy(true)
    try {
      await postLearning(chartId, {
        action: 'resonance',
        signal_ref: signalRef.trim(),
        resonance,
      })
      setSignalRef('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-border bg-muted/30 p-4 space-y-3">
      <div>
        <h3 className="text-sm font-medium text-foreground">Resonance Feedback</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Stored for presentation emphasis only — no path to predictive weights.{' '}
          <span className="font-medium text-muted-foreground">[QUARANTINED]</span>
        </p>
      </div>
      <div className="flex gap-2 items-center">
        <input
          type="text"
          placeholder="Signal ref (e.g. MSR-042)"
          value={signalRef}
          onChange={e => setSignalRef(e.target.value)}
          className="flex-1 rounded-md border border-input bg-background px-2.5 py-1.5
                     text-xs text-foreground placeholder:text-muted-foreground
                     focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <button
          disabled={busy || !signalRef.trim()}
          onClick={() => tap('resonates')}
          className="rounded-md border border-border px-3 py-1.5 text-xs text-foreground
                     hover:bg-accent disabled:opacity-40 transition-colors"
        >
          Resonates
        </button>
        <button
          disabled={busy || !signalRef.trim()}
          onClick={() => tap('doesnt_resonate')}
          className="rounded-md border border-border px-3 py-1.5 text-xs text-foreground
                     hover:bg-accent disabled:opacity-40 transition-colors"
        >
          Doesn't
        </button>
      </div>
    </div>
  )
}

// ── Root client component ─────────────────────────────────────────────────────

export function PratikrutiClient({ chartId }: { chartId: string }) {
  const [data, setData] = useState<LearningData | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    try {
      const res = await fetch(`/api/clients/${chartId}/learning`)
      if (res.ok) setData(await res.json())
    } finally {
      setLoading(false)
    }
  }, [chartId])

  useEffect(() => { void reload() }, [reload])

  const removeWindow = useCallback((predictionId: string) => {
    setData(d => d ? { ...d, open_windows: d.open_windows.filter(w => w.prediction_id !== predictionId) } : d)
  }, [])

  const removeFollowup = useCallback((predictionId: string) => {
    setData(d => d ? { ...d, pending_followups: d.pending_followups.filter(f => f.prediction_id !== predictionId) } : d)
  }, [])

  const removeSnapshot = useCallback((snapshotId: string) => {
    setData(d => d ? { ...d, pending_cosign: d.pending_cosign.filter(s => s.snapshot_id !== snapshotId) } : d)
  }, [])

  if (loading) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    )
  }

  const openWindows = data?.open_windows ?? []
  const followUps = data?.pending_followups ?? []
  const snapshots = data?.pending_cosign ?? []

  return (
    <div className="space-y-8">

      {/* Step 1: Ask-Cards */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-foreground">
          Step 1 — Adjudicate Predictions
          {openWindows.length > 0 && (
            <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
              {openWindows.length}
            </span>
          )}
        </h2>
        {openWindows.length === 0 ? (
          <p className="text-xs text-muted-foreground">No UNRESOLVED closed windows — all caught up.</p>
        ) : (
          openWindows.map(w => (
            <AskCard key={w.prediction_id} item={w} chartId={chartId} onDone={removeWindow} />
          ))
        )}
      </section>

      {/* Step 2: LEL Intake */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-foreground">Step 2 — Add Life Event</h2>
        <LelIntakeForm chartId={chartId} />
      </section>

      {/* Step 3: Prashna Follow-ups */}
      {followUps.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-foreground">
            Step 3 — Prashna Follow-ups
            <span className="ml-2 rounded-full bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-400">
              {followUps.length} due
            </span>
          </h2>
          {followUps.map(f => (
            <FollowUpCard key={f.prediction_id} item={f} chartId={chartId} onDone={removeFollowup} />
          ))}
        </section>
      )}

      {/* Step 4: Co-Sign Surface */}
      {snapshots.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-foreground">
            Step 4 — Co-Sign Snapshots
            <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
              {snapshots.length}
            </span>
          </h2>
          {snapshots.map(s => (
            <CoSignCard key={s.snapshot_id} item={s} chartId={chartId} onDone={removeSnapshot} />
          ))}
        </section>
      )}

      {/* Step 5: Resonance Capture (QUARANTINED) */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-foreground">Step 5 — Resonance</h2>
        <ResonanceFeedback chartId={chartId} />
      </section>

    </div>
  )
}
