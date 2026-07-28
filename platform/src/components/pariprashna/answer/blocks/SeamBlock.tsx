/**
 * A SETTLED pass seam: the moment prose resumes after a seam was live, it
 * settles in place into this slim hairline divider (§5.8.1 ruling 8a). This
 * is a FrozenBlock like any other — once rendered here it never changes
 * again (the live→settled transition happened in the reducer via
 * `pass.seam.settle`, before this block ever mounted as a FrozenBlock).
 */
export function SeamBlock({ summary }: { summary: string }) {
  return (
    <div className="flex items-center gap-3 my-2" style={{ fontFamily: 'var(--pp-font-sans)', fontSize: '12px', color: 'var(--pp-ink-dim)' }}>
      <span className="flex-1 h-px" style={{ background: 'rgba(201,162,76,0.18)' }} />
      <span
        className="font-mono whitespace-nowrap"
        style={{ fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}
      >
        · {summary} ·
      </span>
      <span className="flex-1 h-px" style={{ background: 'rgba(201,162,76,0.18)' }} />
    </div>
  )
}
