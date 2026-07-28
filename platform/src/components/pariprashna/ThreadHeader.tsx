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
    <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid var(--pp-rule)' }}>
      <div className="flex items-baseline gap-6">
        <span className="pp-prose" style={{ fontSize: 19, fontWeight: 500 }}>
          Paripraśna
        </span>
        <span aria-hidden className="self-center rounded-full" style={{ width: 3, height: 3, background: 'var(--pp-gold-tertiary)' }} />
        <span>
          <div style={{ fontSize: 13, color: 'var(--pp-ink-dim)' }}>{chartPin.name}</div>
          <div style={{ fontSize: 8.5, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}>
            {chartPin.bornLine}
          </div>
        </span>
      </div>
      <span className="pp-prose" style={{ fontSize: 12, letterSpacing: '0.24em', fontWeight: 500 }}>
        MARSYS <span style={{ color: 'var(--pp-gold)' }}>JIS</span>
      </span>
    </div>
  )
}
