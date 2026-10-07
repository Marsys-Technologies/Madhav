'use client'

import { useMemo, useRef, useState } from 'react'
import type { LedgerRow, Outcome } from '@/lib/pariprashna/samiksha/schema'
import type { TurnDeepLinkTarget } from '@/lib/pariprashna/samiksha/deepLink'
import { buildTurnDeepLink } from '@/lib/pariprashna/samiksha/deepLink'
import { parseDaterange, windowLabel } from './format'
import type { ResolveAction, BatchResolveAction } from './types'

/**
 * "Resolve" (§14.4 / §14.7) — window_closed predictions get an outcome:
 * happened / didn't / partially / can't-tell. "Can't-tell" maps to `unverifiable`
 * (Brier-EXCLUDED; the DAL forces outcome_value null and the DB CHECK backstops it).
 *
 * BATCH-CAPABLE + KEYBOARD-FAST (§14.7): a caller resolving 10 lapsed windows in one sitting
 * must not need 10 mouse interactions. Each row is a roving-tabindex list item; with a row
 * focused, press H/D/P/U to assign happened/didn't/partial/unverifiable and auto-advance to the
 * next row; ArrowDown/ArrowUp (or J/K) move without assigning; then ONE "Resolve marked" button
 * (or Cmd/Ctrl+Enter) submits every marked row via a single batch action.
 *
 * NON-SHAMEFUL (W-2): no red anywhere; unresolved windows are a neutral coverage statistic, not
 * a debt. The four outcomes are peers — can't-tell is a first-class, honest answer.
 */

const OUTCOME_KEYS: Record<string, Outcome> = {
  h: 'happened',
  d: 'did_not_happen',
  p: 'partial',
  u: 'unverifiable',
}
const OUTCOME_LABEL: Record<Outcome, string> = {
  happened: 'Happened',
  did_not_happen: "Didn't happen",
  partial: 'Partially',
  unverifiable: "Can't tell",
}
const OUTCOME_ORDER: Outcome[] = ['happened', 'did_not_happen', 'partial', 'unverifiable']

export function ResolveSection({
  rows,
  turnAnchors,
  coverage,
  onResolve,
  onBatchResolve,
}: {
  rows: LedgerRow[]
  turnAnchors: Record<string, TurnDeepLinkTarget>
  coverage: { resolvedCount: number; unverifiableCount: number; lapsedCount: number; coverageFraction: number | null }
  onResolve: ResolveAction
  onBatchResolve: BatchResolveAction
}) {
  const [pending, setPending] = useState<Record<string, Outcome>>({})
  const rowRefs = useRef<(HTMLLIElement | null)[]>([])

  const markedCount = useMemo(() => Object.keys(pending).length, [pending])

  function setOutcome(rowId: string, outcome: Outcome) {
    setPending((p) => ({ ...p, [rowId]: outcome }))
  }
  function focusRow(index: number) {
    const clamped = Math.max(0, Math.min(rows.length - 1, index))
    rowRefs.current[clamped]?.focus()
  }

  function onRowKeyDown(e: React.KeyboardEvent<HTMLLIElement>, index: number, rowId: string) {
    const k = e.key.toLowerCase()
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      submitBatch()
      return
    }
    if (k === 'arrowdown' || k === 'j') {
      e.preventDefault()
      focusRow(index + 1)
    } else if (k === 'arrowup' || k === 'k') {
      e.preventDefault()
      focusRow(index - 1)
    } else if (k in OUTCOME_KEYS) {
      e.preventDefault()
      setOutcome(rowId, OUTCOME_KEYS[k])
      focusRow(index + 1)
    } else if (e.key === 'Enter') {
      // Enter on a marked row resolves just that row immediately.
      const outcome = pending[rowId]
      if (outcome) {
        e.preventDefault()
        onResolve({ rowId, outcome })
      }
    }
  }

  function submitBatch() {
    const items = Object.entries(pending).map(([rowId, outcome]) => ({ rowId, outcome }))
    if (items.length > 0) onBatchResolve(items)
  }

  return (
    <section aria-labelledby="samiksa-resolve-h">
      <h2
        id="samiksa-resolve-h"
        style={{ fontFamily: 'var(--pp-font-serif, Georgia, serif)', fontSize: '18px', color: 'var(--pp-gold, #C9A24C)', margin: '0 0 6px' }}
      >
        Resolve
      </h2>

      {/* Non-shameful coverage statistic (W-2) — neutral phrasing, never a red counter. */}
      <p style={{ fontSize: '11px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))', margin: '0 0 4px' }}>
        {coverage.resolvedCount} resolved · {coverage.unverifiableCount} can&apos;t-tell ·{' '}
        {coverage.lapsedCount} not yet reviewed
        {coverage.coverageFraction != null
          ? ` · ${Math.round(coverage.coverageFraction * 100)}% of closed windows attended`
          : ''}
      </p>

      <p style={{ fontSize: '11px', color: 'var(--pp-gold-tertiary, #7A5A1F)', margin: '0 0 12px' }}>
        Keyboard: focus a prediction, then H happened · D didn&apos;t · P partially · U can&apos;t-tell (auto-advances).
        ↑/↓ to move. Then Resolve marked.
      </p>

      {rows.length === 0 ? (
        <p style={{ fontSize: '13px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))' }}>
          No predictions with a closed window awaiting resolution.
        </p>
      ) : (
        <>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Predictions awaiting resolution">
            {rows.map((row, index) => {
              const win = parseDaterange(row.window)
              const anchor = row.message_part_id ? turnAnchors[row.message_part_id] : undefined
              const marked = pending[row.id]
              return (
                <li
                  key={row.id}
                  ref={(el) => {
                    rowRefs.current[index] = el
                  }}
                  tabIndex={0}
                  onKeyDown={(e) => onRowKeyDown(e, index, row.id)}
                  aria-label={`Prediction: ${row.claim_text}. ${marked ? `Marked ${OUTCOME_LABEL[marked]}.` : 'Not yet marked.'}`}
                  style={{
                    border: '1px solid var(--pp-rule, rgba(201,162,76,0.25))',
                    borderRadius: '4px',
                    background: marked ? 'var(--pp-tint, rgba(201,162,76,0.06))' : 'var(--pp-panel, #0a0a0a)',
                    padding: '12px 14px',
                    marginBottom: '10px',
                    outlineOffset: '2px',
                  }}
                >
                  <p
                    style={{
                      fontFamily: 'var(--pp-font-serif, Georgia, serif)',
                      fontSize: '14.5px',
                      lineHeight: 1.4,
                      color: 'var(--pp-ink, #EBE3D2)',
                      margin: '0 0 4px',
                    }}
                  >
                    {row.claim_text}
                  </p>
                  <div style={{ fontSize: '11px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))', marginBottom: '8px' }}>
                    <span>{windowLabel(win)}</span>
                    {anchor ? (
                      <>
                        {' · '}
                        <a href={buildTurnDeepLink(anchor)} style={{ color: 'var(--pp-gold, #C9A24C)', textDecoration: 'underline' }}>
                          view source turn
                        </a>
                      </>
                    ) : null}
                  </div>
                  <div role="radiogroup" aria-label="Outcome" className="flex items-center" style={{ gap: '6px', flexWrap: 'wrap' }}>
                    {OUTCOME_ORDER.map((outcome) => {
                      const isSel = marked === outcome
                      return (
                        <button
                          key={outcome}
                          type="button"
                          role="radio"
                          aria-checked={isSel}
                          onClick={() => setOutcome(row.id, outcome)}
                          style={{
                            fontSize: '12px',
                            padding: '4px 10px',
                            borderRadius: '3px',
                            border: `1px solid ${isSel ? 'var(--pp-gold, #C9A24C)' : 'var(--pp-rule, rgba(201,162,76,0.25))'}`,
                            background: isSel ? 'var(--pp-tint-2, rgba(201,162,76,0.10))' : 'transparent',
                            color: isSel ? 'var(--pp-gold, #C9A24C)' : 'var(--pp-ink-dim, rgba(235,227,210,0.64))',
                            cursor: 'pointer',
                          }}
                        >
                          {OUTCOME_LABEL[outcome]}
                        </button>
                      )
                    })}
                  </div>
                </li>
              )
            })}
          </ul>

          <div className="flex items-center" style={{ gap: '12px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={submitBatch}
              disabled={markedCount === 0}
              style={{
                fontSize: '13px',
                padding: '8px 16px',
                borderRadius: '3px',
                border: '1px solid var(--pp-gold, #C9A24C)',
                background: markedCount === 0 ? 'transparent' : 'var(--pp-tint-2, rgba(201,162,76,0.10))',
                color: markedCount === 0 ? 'var(--pp-ink-dim, rgba(235,227,210,0.64))' : 'var(--pp-gold, #C9A24C)',
                cursor: markedCount === 0 ? 'default' : 'pointer',
              }}
            >
              Resolve marked ({markedCount})
            </button>
            <span style={{ fontSize: '11px', color: 'var(--pp-gold-tertiary, #7A5A1F)' }}>Cmd/Ctrl+Enter</span>
          </div>
        </>
      )}
    </section>
  )
}
