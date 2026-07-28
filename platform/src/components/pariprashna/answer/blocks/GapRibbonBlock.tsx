/**
 * Honest-gap ribbon (§6.8, J7): its own block, unmissable by structure (the
 * only bordered/tinted block a reading can contain), calm by chrome (same
 * golds as everything else — no warning iconography, no red).
 */
export function GapRibbonBlock({ text }: { text: string }) {
  return (
    <div className="pp-gap-ribbon my-3">
      <div
        style={{ fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--pp-gold-dim)', marginBottom: '8px' }}
      >
        The chart is silent here
      </div>
      <p className="pp-verse" style={{ borderLeft: 'none', paddingLeft: 0, color: 'var(--pp-ink-dim)' }}>
        {text}
      </p>
    </div>
  )
}
