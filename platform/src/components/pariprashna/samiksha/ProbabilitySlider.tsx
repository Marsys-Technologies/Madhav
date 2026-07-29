'use client'

import { useId } from 'react'

/**
 * SAMĪKṢĀ probability slider — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * When confirming a `detected` candidate that stated no probability (§14.3: "Confirm elicits a
 * probability if none stated"), the caller picks a point probability here; the confirm action
 * turns it into a narrow numrange band. A native range input (keyboard-operable: arrows, Home,
 * End, Page keys) with an explicit label + live percentage readout — a11y-first, no
 * color-only signal.
 */
export function ProbabilitySlider({
  value,
  onChange,
  idPrefix,
}: {
  /** Point probability in [0,1]. */
  value: number
  onChange: (v: number) => void
  idPrefix?: string
}) {
  const autoId = useId()
  const id = `${idPrefix ?? 'prob'}-${autoId}`
  const pct = Math.round(value * 100)

  return (
    <div className="flex items-center gap-3">
      <label htmlFor={id} style={{ fontSize: '11px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))' }}>
        Probability
      </label>
      <input
        id={id}
        type="range"
        min={0}
        max={100}
        step={5}
        value={pct}
        onChange={(e) => onChange(Number(e.target.value) / 100)}
        aria-valuetext={`${pct} percent`}
        style={{ accentColor: 'var(--pp-gold, #C9A24C)', flex: 1 }}
      />
      <output
        htmlFor={id}
        style={{
          fontSize: '12px',
          fontVariantNumeric: 'tabular-nums',
          color: 'var(--pp-gold-dim, #A37F37)',
          minWidth: '3ch',
          textAlign: 'right',
        }}
      >
        {pct}%
      </output>
    </div>
  )
}
