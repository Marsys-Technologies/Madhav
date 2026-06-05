'use client'

interface Props {
  healthy: boolean
}

export function ConnectionHealthPill({ healthy }: Props) {
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
        background: healthy ? 'rgba(62,124,75,0.2)' : 'rgba(181,71,76,0.2)',
        color: healthy ? 'var(--marsys-success)' : 'var(--marsys-error)',
        border: `1px solid ${healthy ? 'var(--marsys-success)' : 'var(--marsys-error)'}`,
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          background: healthy ? 'var(--marsys-success)' : 'var(--marsys-error)',
          display: 'inline-block',
        }}
      />
      {healthy ? 'SIDECAR OK' : 'SIDECAR DOWN'}
    </span>
  )
}
