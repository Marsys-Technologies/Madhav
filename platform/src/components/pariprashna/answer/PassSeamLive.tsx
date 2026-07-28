import type { ActiveSeam } from '../state/types'

/**
 * The LIVE seam (§5.8.1 ruling 8a): rendered exactly where the next prose
 * segment will continue, while the working band's ledger runs the next
 * pass's retrievals. It mutates only itself (its own spinner) and never
 * unmounts — it either settles into a `SeamBlock` (frozen) or, if the turn
 * is stopped/errored first, simply stops updating. It is intentionally NOT
 * a FrozenBlock: it is the seam's "born volatile" half, mirroring the
 * tail's own open→commit lifecycle for a different block kind.
 */
export function PassSeamLive({ seam }: { seam: ActiveSeam }) {
  return (
    <div className="flex items-center gap-2.5 my-2" style={{ fontFamily: 'var(--pp-font-sans)', fontSize: '12px', color: 'var(--pp-ink-dim)' }}>
      <span
        aria-hidden
        data-pp-spin
        className="flex-none inline-block w-[11px] h-[11px] rounded-full"
        style={{ border: '1.5px solid var(--pp-gold-tertiary)', borderTopColor: 'var(--pp-gold)' }}
      />
      <span>
        {seam.liveLabel} <i style={{ color: 'var(--pp-gold-tertiary)' }}>— the chart asked for a closer look</i>
      </span>
    </div>
  )
}
