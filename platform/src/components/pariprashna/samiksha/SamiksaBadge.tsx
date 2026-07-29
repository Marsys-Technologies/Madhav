import type { CSSProperties } from 'react'

/**
 * SAMĪKṢĀ dashboard badge — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * A small numeral counting `detected` + `window_closed` rows (the items awaiting a human act).
 * DESIGN RULE (§10.2 / W-2): the numeral is `--pp-gold-dim`, NEVER red — this surface is
 * explicitly non-alarming; a badge is an invitation, not a debt notice. The displayed value is
 * whatever the server computed via `countBadge` (badge.ts) — this component does no counting of
 * its own, so "badge equals SQL truth" is a property of the single production count path, and
 * the badge simply renders it.
 *
 * Renders nothing when the count is 0 (an empty review queue needs no ornament).
 */
export function SamiksaBadge({
  count,
  ariaLabel,
}: {
  count: number
  /** Accessible name; defaults to a neutral, non-shameful phrasing. */
  ariaLabel?: string
}) {
  if (count <= 0) return null

  const style: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: '18px',
    height: '18px',
    padding: '0 5px',
    borderRadius: '9px',
    fontSize: '11px',
    fontWeight: 600,
    fontVariantNumeric: 'tabular-nums',
    lineHeight: 1,
    // NEVER red — the non-alarming gold-dim token (§10.2). Foreground on a faint gold tint.
    color: 'var(--pp-gold-dim, #A37F37)',
    background: 'var(--pp-tint-2, rgba(201,162,76,0.10))',
    border: '1px solid var(--pp-rule, rgba(201,162,76,0.25))',
  }

  return (
    <span
      className="samiksa-badge"
      style={style}
      aria-label={ariaLabel ?? `${count} prediction ${count === 1 ? 'item' : 'items'} to review`}
      data-count={count}
    >
      {count}
    </span>
  )
}
