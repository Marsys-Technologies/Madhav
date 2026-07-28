'use client'

import type { LedgerRow } from '@/lib/pariprashna/samiksha/schema'
import type { TurnDeepLinkTarget } from '@/lib/pariprashna/samiksha/deepLink'
import { buildTurnDeepLink } from '@/lib/pariprashna/samiksha/deepLink'
import { parseDaterange, parseNumrange, confidencePhrase } from './format'
import { KalaRekhaTimeline } from './KalaRekhaTimeline'

/**
 * "Open" (§14.4) — a live timeline of `open` (confirmed, window not yet closed) predictions.
 * Read-only: nothing here mutates a row (the window closes via L-4's daily job, not from this
 * surface). Each entry shows the claim, its kāla-rekhā (with a REAL today-dot from `nowIso`),
 * the confidence phrase, and a read-only deep link back to the source turn.
 */
function OpenRow({
  row,
  anchor,
  nowIso,
}: {
  row: LedgerRow
  anchor: TurnDeepLinkTarget | undefined
  nowIso: string
}) {
  const win = parseDaterange(row.window)
  const conf = parseNumrange(row.confidence)
  return (
    <li
      style={{
        borderLeft: '2px solid var(--pp-gold-tertiary, #7A5A1F)',
        paddingLeft: '14px',
        marginBottom: '18px',
      }}
    >
      <div
        style={{
          fontSize: '9px',
          letterSpacing: '0.24em',
          textTransform: 'uppercase',
          color: 'var(--pp-gold-dim, #A37F37)',
          marginBottom: '4px',
        }}
      >
        Window open
      </div>
      <p
        style={{
          fontFamily: 'var(--pp-font-serif, Georgia, serif)',
          fontSize: '15px',
          lineHeight: 1.45,
          color: 'var(--pp-ink, #EBE3D2)',
          margin: '0 0 8px',
        }}
      >
        {row.claim_text}
      </p>
      <KalaRekhaTimeline window={win} nowIso={nowIso} />
      <div
        className="flex items-center"
        style={{ gap: '10px', marginTop: '6px', fontSize: '11px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))' }}
      >
        <span>{confidencePhrase(conf)}</span>
        {anchor ? (
          <a
            href={buildTurnDeepLink(anchor)}
            style={{ color: 'var(--pp-gold, #C9A24C)', textDecoration: 'underline', marginLeft: 'auto' }}
          >
            view source turn
          </a>
        ) : null}
      </div>
    </li>
  )
}

export function OpenTimeline({
  rows,
  turnAnchors,
  nowIso,
}: {
  rows: LedgerRow[]
  turnAnchors: Record<string, TurnDeepLinkTarget>
  nowIso: string
}) {
  return (
    <section aria-labelledby="samiksa-open-h">
      <h2
        id="samiksa-open-h"
        style={{ fontFamily: 'var(--pp-font-serif, Georgia, serif)', fontSize: '18px', color: 'var(--pp-gold, #C9A24C)', margin: '0 0 12px' }}
      >
        Open
      </h2>
      {rows.length === 0 ? (
        <p style={{ fontSize: '13px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))' }}>
          No open predictions. Confirmed predictions appear here while their window runs.
        </p>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {rows.map((row) => (
            <OpenRow
              key={row.id}
              row={row}
              anchor={row.message_part_id ? turnAnchors[row.message_part_id] : undefined}
              nowIso={nowIso}
            />
          ))}
        </ul>
      )}
    </section>
  )
}
