'use client'

import { useState } from 'react'
import type { LedgerRow } from '@/lib/pariprashna/samiksha/schema'
import type { TurnDeepLinkTarget } from '@/lib/pariprashna/samiksha/deepLink'
import { buildTurnDeepLink } from '@/lib/pariprashna/samiksha/deepLink'
import { parseNumrange, windowLabel, parseDaterange } from './format'
import { ProbabilitySlider } from './ProbabilitySlider'
import type { ConfirmAction, DismissAction, EditAction } from './types'

/**
 * "Awaiting confirmation" (§14.4) — each `detected` candidate in its original message context,
 * with one-tap confirm (probability slider) / edit / dismiss-with-reason. The STANDALONE
 * review-tab twin of the in-stream confirm affordance L-2 builds; both write the SAME L-1 row
 * via the SAME DAL — de-duplication of the shared confirm control is a documented integration
 * follow-up (L-2 is not visible to this worktree).
 */
function CandidateRow({
  row,
  anchor,
  onConfirm,
  onDismiss,
  onEdit,
}: {
  row: LedgerRow
  anchor: TurnDeepLinkTarget | undefined
  onConfirm: ConfirmAction
  onDismiss: DismissAction
  onEdit: EditAction
}) {
  const stated = parseNumrange(row.confidence)
  const [prob, setProb] = useState<number>(stated ? (stated.low + stated.high) / 2 : 0.6)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(row.claim_text)
  const win = parseDaterange(row.window)

  return (
    <li
      className="samiksa-candidate"
      style={{
        border: '1px solid var(--pp-rule, rgba(201,162,76,0.25))',
        borderRadius: '4px',
        background: 'var(--pp-panel, #0a0a0a)',
        padding: '14px 16px',
        marginBottom: '12px',
      }}
    >
      {editing ? (
        <label style={{ display: 'block' }}>
          <span className="sr-only">Edit claim text</span>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={2}
            style={{
              width: '100%',
              fontFamily: 'var(--pp-font-serif, Georgia, serif)',
              fontSize: '15px',
              background: 'var(--pp-raise, #111010)',
              color: 'var(--pp-ink, #EBE3D2)',
              border: '1px solid var(--pp-rule-strong, rgba(201,162,76,0.50))',
              borderRadius: '3px',
              padding: '6px 8px',
            }}
          />
        </label>
      ) : (
        <p
          style={{
            fontFamily: 'var(--pp-font-serif, Georgia, serif)',
            fontSize: '15px',
            lineHeight: 1.45,
            color: 'var(--pp-ink, #EBE3D2)',
            margin: '0 0 6px',
          }}
        >
          {row.claim_text}
        </p>
      )}

      <div
        style={{ fontSize: '11px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))', marginBottom: '10px' }}
      >
        {row.domain ? <span>{row.domain} · </span> : null}
        <span>{windowLabel(win)}</span>
        {anchor ? (
          <>
            {' · '}
            <a
              href={buildTurnDeepLink(anchor)}
              style={{ color: 'var(--pp-gold, #C9A24C)', textDecoration: 'underline' }}
            >
              view source turn
            </a>
          </>
        ) : null}
      </div>

      {!stated && (
        <div style={{ marginBottom: '10px' }}>
          <ProbabilitySlider value={prob} onChange={setProb} idPrefix={`prob-${row.id}`} />
        </div>
      )}

      <div className="flex items-center gap-2" style={{ flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() =>
            onConfirm({ rowId: row.id, probability: stated ? (stated.low + stated.high) / 2 : prob })
          }
          style={btnPrimary}
        >
          Log to Samīkṣā
        </button>
        {editing ? (
          <button
            type="button"
            onClick={() => {
              onEdit({ rowId: row.id, claimText: draft })
              setEditing(false)
            }}
            style={btnGhost}
          >
            Save edit
          </button>
        ) : (
          <button type="button" onClick={() => setEditing(true)} style={btnGhost}>
            Edit
          </button>
        )}
        <button
          type="button"
          onClick={() => onDismiss({ rowId: row.id, reason: 'dismissed from review tab' })}
          style={btnGhost}
        >
          Dismiss
        </button>
      </div>
    </li>
  )
}

export function AwaitingSection({
  rows,
  turnAnchors,
  onConfirm,
  onDismiss,
  onEdit,
}: {
  rows: LedgerRow[]
  turnAnchors: Record<string, TurnDeepLinkTarget>
  onConfirm: ConfirmAction
  onDismiss: DismissAction
  onEdit: EditAction
}) {
  return (
    <section aria-labelledby="samiksa-awaiting-h">
      <h2 id="samiksa-awaiting-h" style={sectionHeading}>
        Awaiting confirmation
      </h2>
      {rows.length === 0 ? (
        <p style={emptyNote}>No candidates awaiting confirmation.</p>
      ) : (
        <ul style={listReset}>
          {rows.map((row) => (
            <CandidateRow
              key={row.id}
              row={row}
              anchor={row.message_part_id ? turnAnchors[row.message_part_id] : undefined}
              onConfirm={onConfirm}
              onDismiss={onDismiss}
              onEdit={onEdit}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

const sectionHeading = {
  fontFamily: 'var(--pp-font-serif, Georgia, serif)',
  fontSize: '18px',
  color: 'var(--pp-gold, #C9A24C)',
  margin: '0 0 12px',
} as const
const emptyNote = { fontSize: '13px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))' } as const
const listReset = { listStyle: 'none', margin: 0, padding: 0 } as const
const btnPrimary = {
  fontSize: '12px',
  padding: '6px 12px',
  borderRadius: '3px',
  border: '1px solid var(--pp-gold, #C9A24C)',
  background: 'var(--pp-tint-2, rgba(201,162,76,0.10))',
  color: 'var(--pp-gold, #C9A24C)',
  cursor: 'pointer',
} as const
const btnGhost = {
  fontSize: '12px',
  padding: '6px 12px',
  borderRadius: '3px',
  border: '1px solid var(--pp-rule, rgba(201,162,76,0.25))',
  background: 'transparent',
  color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))',
  cursor: 'pointer',
} as const
