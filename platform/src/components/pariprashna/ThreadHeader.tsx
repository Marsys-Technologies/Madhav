export interface ChartPin {
  name: string
  bornLine: string // e.g. "05 Feb 1984 · 10:43 · Bhubaneswar"
}

/**
 * Thread header (§3.2, §5.8.0 ruling 1): the chart pin satisfies B.11's
 * frame-check for retrieval-depth turns — every turn is visibly *of a
 * chart*. Clear breathing room between the "Paripraśna" wordmark and the
 * chart-holder's name (they must never read as one string); right side
 * carries the MARSYS JIS wordmark, never a provenance/build-id stamp
 * (ruling 1 amended by ruling 8c — provenance lives only in the audit
 * drawer, nowhere ambient).
 */
export function ThreadHeader({ chartPin }: { chartPin: ChartPin }) {
  return (
    // V3-E (S2, J9 mobile pass): at 390px (the test plan's named mobile
    // viewport), an unwrapped `justify-between` row squeezed the MARSYS JIS
    // wordmark against the chart-name group until it visibly clipped —
    // `flexWrap: 'wrap'` + `minWidth: 0` on the shrinkable group lets the
    // wordmark drop to its own line instead of being cut off; nothing is
    // hidden or truncated, every string still renders in full.
    <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid var(--pp-rule)', flexWrap: 'wrap', rowGap: 6 }}>
      <div className="flex items-baseline gap-6" style={{ minWidth: 0, flexWrap: 'wrap', rowGap: 4 }}>
        <span className="pp-prose" style={{ fontSize: 19, fontWeight: 500 }}>
          Paripraśna
        </span>
        <span aria-hidden className="self-center rounded-full" style={{ width: 3, height: 3, background: 'var(--pp-gold-tertiary)' }} />
        <span style={{ minWidth: 0 }}>
          {/* V3-E-062 (S2): the Portal rendered zero h1-h6 elements anywhere,
              leaving a screen-reader user with no heading-navigation shortcut
              on any surface state. This chart-holder name is the page's own
              de facto primary content anchor, so it now carries a real <h1>
              (margin/weight explicitly reset to preserve the prior visual
              rendering exactly -- this is a semantics-only change). */}
          <h1 style={{ margin: 0, fontSize: 13, fontWeight: 400, color: 'var(--pp-ink-dim)' }}>{chartPin.name}</h1>
          <div style={{ fontSize: 8.5, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}>
            {chartPin.bornLine}
          </div>
        </span>
      </div>
      <span className="pp-prose" style={{ fontSize: 12, letterSpacing: '0.24em', fontWeight: 500, flexShrink: 0 }}>
        MARSYS <span style={{ color: 'var(--pp-gold)' }}>JIS</span>
      </span>
    </div>
  )
}
