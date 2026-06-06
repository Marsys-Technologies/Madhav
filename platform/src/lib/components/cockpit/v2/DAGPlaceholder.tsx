'use client'

/** Placeholder for the LiveDependencyGraph (Phase 10). */
export function DAGPlaceholder() {
  return (
    <div
      style={{
        border: '1px solid rgba(236,197,106,0.15)',
        borderRadius: '8px',
        background: 'rgba(236,197,106,0.03)',
        minHeight: '480px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
      }}
    >
      {/* Minimal orbit sketch */}
      <svg width="120" height="80" viewBox="0 0 120 80" fill="none">
        <ellipse cx="60" cy="40" rx="52" ry="32" stroke="rgba(236,197,106,0.18)" strokeWidth="0.8" />
        <ellipse cx="60" cy="40" rx="36" ry="22" stroke="rgba(236,197,106,0.22)" strokeWidth="0.8" />
        <ellipse cx="60" cy="40" rx="20" ry="12" stroke="rgba(236,197,106,0.28)" strokeWidth="0.8" />
        <circle cx="60" cy="40" r="5" fill="rgba(236,197,106,0.55)" />
        <circle cx="96" cy="40" r="3" fill="rgba(236,197,106,0.30)" />
        <circle cx="24" cy="40" r="3" fill="rgba(236,197,106,0.30)" />
        <circle cx="60" cy="18" r="2.5" fill="rgba(236,197,106,0.25)" />
        <circle cx="60" cy="62" r="2.5" fill="rgba(236,197,106,0.25)" />
        <circle cx="83" cy="28" r="2" fill="rgba(236,197,106,0.20)" />
        <circle cx="37" cy="52" r="2" fill="rgba(236,197,106,0.20)" />
      </svg>
      <div
        style={{
          fontFamily: 'var(--ui-stack)',
          fontSize: '12px',
          color: 'rgba(236,197,106,0.45)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
        }}
      >
        Dependency graph
      </div>
      <div
        style={{
          fontFamily: 'var(--ui-stack)',
          fontSize: '11px',
          color: 'rgba(255,255,255,0.25)',
        }}
      >
        Coming in Phase 10
      </div>
    </div>
  )
}
