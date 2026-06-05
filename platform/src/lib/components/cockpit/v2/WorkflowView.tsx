'use client'

export function WorkflowView() {
  return (
    <div
      style={{
        padding: '32px 24px',
        color: 'var(--on-dark-mut)',
        fontFamily: 'var(--ui-stack)',
      }}
    >
      <p style={{ fontSize: '14px' }}>Workflow timeline — coming in M6</p>
      <p
        style={{
          fontSize: '12px',
          marginTop: '8px',
          color: 'var(--on-dark-faint)',
        }}
      >
        39 known assets · This view will derive build estimates from measured
        throughput once the first build runs.
      </p>
    </div>
  )
}
