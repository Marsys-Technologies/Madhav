'use client'

interface Props {
  healthy: boolean | null
}

export function ConnectionHealthPill({ healthy }: Props) {
  const color =
    healthy === null
      ? 'var(--marsys-warning)'
      : healthy
        ? 'var(--marsys-success)'
        : 'var(--marsys-error)'

  const bg =
    healthy === null
      ? 'rgba(168,124,42,0.2)'
      : healthy
        ? 'rgba(62,124,75,0.2)'
        : 'rgba(181,71,76,0.2)'

  const label =
    healthy === null ? 'SIDECAR …' : healthy ? 'SIDECAR OK' : 'SIDECAR DOWN'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontSize: '10px',
        fontFamily: 'var(--mono-stack)',
        padding: '3px 8px',
        borderRadius: '12px',
        background: bg,
        color,
        border: `1px solid ${color}`,
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          background: color,
          display: 'inline-block',
        }}
      />
      {label}
    </span>
  )
}
