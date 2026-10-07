/**
 * LogToSamiksha — in-stream one-tap "Log to Samīkṣā" affordance — PB-3 lane L-2.
 *
 * Design authority: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14.4 (§14.4.2) +
 * BRIEF_PB-3 §F1 L-2.
 *
 * §14.4.2: "one-tap 'log this' at the moment of utterance, because confirmation
 * propensity decays fast." So the primary action is a SINGLE tap on the settled
 * turn — immediate, frictionless. Tapping opens a compact confirm panel:
 *   - the detected claim (read-only, or editable via "Edit"),
 *   - a ConfidenceSlider → numrange band (pre-seeded from any stated point),
 *   - Confirm  → POST { action:'confirm' } → an L-1 `confirmed` ledger row,
 *   - Dismiss  → POST { action:'dismiss', reason } → dismissal reason persisted.
 *
 * No auto-promotion (§14.3 / W-1): the ledger row is written ONLY on the human's
 * explicit Confirm tap. This is a CLIENT component; it calls the L-2 seam route
 * (/api/pariprashna/samiksha/confirm), which copies the D-16 stamp + calls L-1.
 */

'use client'

import { useState } from 'react'
import { ConfidenceSlider, bandFromStatedPoint } from './ConfidenceSlider'
import type { StructuredPredictionCandidate } from '@/lib/pariprashna/samiksha/detector'
import type { ConfidenceBand } from '@/lib/pariprashna/samiksha/schema'

export interface LogToSamikshaProps {
  chartId: string
  conversationId: string
  messagePartId?: string | null
  candidate: StructuredPredictionCandidate
  /** Injectable poster (defaults to fetch) — lets a test drive without a network. */
  post?: (body: unknown) => Promise<{ ok: boolean; ledger_row?: unknown; error?: string }>
  onLogged?: (ledgerRow: unknown) => void
  onDismissed?: (ledgerRow: unknown) => void
}

type Mode = 'idle' | 'confirm' | 'dismiss' | 'done' | 'dismissed' | 'error'

async function defaultPost(body: unknown) {
  const r = await fetch('/api/pariprashna/samiksha/confirm', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  const json = (await r.json()) as { ok?: boolean; ledger_row?: unknown; error?: string }
  return { ok: r.ok && !!json.ok, ledger_row: json.ledger_row, error: json.error }
}

export function LogToSamiksha(props: LogToSamikshaProps) {
  const post = props.post ?? defaultPost
  const [mode, setMode] = useState<Mode>('idle')
  const [claim, setClaim] = useState(props.candidate.claim_text)
  const [editing, setEditing] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [band, setBand] = useState<ConfidenceBand>(
    props.candidate.confidence_stated !== undefined
      ? bandFromStatedPoint(props.candidate.confidence_stated)
      : { low: 0.4, high: 0.6 },
  )

  async function confirm() {
    setError(null)
    const res = await post({
      action: 'confirm',
      chartId: props.chartId,
      conversationId: props.conversationId,
      messagePartId: props.messagePartId ?? null,
      candidate: props.candidate,
      confidence: band,
      ...(editing && claim !== props.candidate.claim_text ? { edits: { claim_text: claim } } : {}),
    })
    if (res.ok) {
      setMode('done')
      props.onLogged?.(res.ledger_row)
    } else {
      setError(res.error ?? 'Could not log the prediction.')
      setMode('error')
    }
  }

  async function dismiss() {
    setError(null)
    if (!reason.trim()) {
      setError('A dismissal reason is required (it tunes detector precision).')
      return
    }
    const res = await post({
      action: 'dismiss',
      chartId: props.chartId,
      conversationId: props.conversationId,
      messagePartId: props.messagePartId ?? null,
      candidate: props.candidate,
      reason: reason.trim(),
    })
    if (res.ok) {
      setMode('dismissed')
      props.onDismissed?.(res.ledger_row)
    } else {
      setError(res.error ?? 'Could not dismiss.')
      setMode('error')
    }
  }

  if (mode === 'done') {
    return (
      <div className="pp-log-samiksha pp-log-samiksha--done" data-testid="log-samiksha-done">
        Logged to Samīkṣā
      </div>
    )
  }
  if (mode === 'dismissed') {
    return (
      <div className="pp-log-samiksha pp-log-samiksha--dismissed" data-testid="log-samiksha-dismissed">
        Dismissed
      </div>
    )
  }

  if (mode === 'idle') {
    // The one-tap primary affordance (§14.4.2).
    return (
      <button
        type="button"
        className="pp-log-samiksha__tap"
        data-testid="log-samiksha-tap"
        onClick={() => setMode('confirm')}
      >
        Log to Samīkṣā
      </button>
    )
  }

  return (
    <div className="pp-log-samiksha__panel" data-testid="log-samiksha-panel">
      {editing ? (
        <textarea
          className="pp-log-samiksha__claim-edit"
          data-testid="log-samiksha-claim-edit"
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
        />
      ) : (
        <div className="pp-log-samiksha__claim">{claim}</div>
      )}

      {mode === 'confirm' ? (
        <>
          <ConfidenceSlider statedPoint={props.candidate.confidence_stated} value={band} onChange={setBand} />
          <div className="pp-log-samiksha__actions">
            <button type="button" data-testid="log-samiksha-confirm" className="pp-log-samiksha__btn pp-log-samiksha__btn--primary" onClick={confirm}>
              Confirm
            </button>
            <button type="button" data-testid="log-samiksha-edit" className="pp-log-samiksha__btn" onClick={() => setEditing((v) => !v)}>
              {editing ? 'Done editing' : 'Edit'}
            </button>
            <button type="button" data-testid="log-samiksha-to-dismiss" className="pp-log-samiksha__btn" onClick={() => setMode('dismiss')}>
              Dismiss
            </button>
          </div>
        </>
      ) : null}

      {mode === 'dismiss' ? (
        <>
          <label className="pp-log-samiksha__reason-lbl">Why dismiss? (tunes detector precision)</label>
          <input
            type="text"
            data-testid="log-samiksha-reason"
            className="pp-log-samiksha__reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. not a prediction — historical reference"
          />
          <div className="pp-log-samiksha__actions">
            <button type="button" data-testid="log-samiksha-dismiss-confirm" className="pp-log-samiksha__btn" onClick={dismiss}>
              Dismiss with reason
            </button>
            <button type="button" className="pp-log-samiksha__btn" onClick={() => setMode('confirm')}>
              Back
            </button>
          </div>
        </>
      ) : null}

      {error ? (
        <div className="pp-log-samiksha__error" data-testid="log-samiksha-error" role="alert">
          {error}
        </div>
      ) : null}
    </div>
  )
}
