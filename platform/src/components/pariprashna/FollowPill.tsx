/**
 * "↓ Reading continues" (§3.2, §5.5): bottom-center hairline pill, appears
 * only while streaming and the reader has scrolled away from the tail.
 * Tapping re-pins follow mode.
 */
export function FollowPill({ visible, onClick }: { visible: boolean; onClick: () => void }) {
  if (!visible) return null
  return (
    <button
      type="button"
      onClick={onClick}
      className="absolute left-1/2 z-[6] inline-flex items-center gap-1.5 rounded-full"
      style={{
        transform: 'translateX(-50%)',
        bottom: 12,
        fontSize: 11.5,
        color: 'var(--pp-gold)',
        background: 'var(--pp-raise)',
        border: '1px solid var(--pp-rule-strong)',
        padding: '7px 15px',
        boxShadow: '0 10px 30px -8px rgba(0,0,0,0.9)',
      }}
    >
      <span className="font-mono" aria-hidden>↓</span>
      the reading continues
    </button>
  )
}
