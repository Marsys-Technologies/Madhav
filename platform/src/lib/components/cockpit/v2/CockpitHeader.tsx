'use client'

import { ConnectionHealthPill } from './ConnectionHealthPill'

interface Props {
  chartId: string
  sidecarHealthy: boolean
}

export function CockpitHeader({ chartId, sidecarHealthy }: Props) {
  return (
    <div
      style={{
        background: 'var(--black-raised)',
        border: '1px solid var(--black-line)',
        borderRadius: 'var(--r-card)',
        padding: '20px 24px',
        margin: '0 0 8px 0',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* Left: chart name + coords */}
        <div>
          <h1
            style={{
              fontFamily: 'var(--display-stack)',
              color: 'var(--gold-high)',
              fontSize: '20px',
              fontVariant: 'small-caps',
              margin: 0,
            }}
          >
            Chart {chartId.slice(0, 8)}…
          </h1>
          <div
            style={{
              fontFamily: 'var(--ui-stack)',
              fontSize: '12px',
              color: 'var(--on-dark-mut)',
              marginTop: '2px',
            }}
          >
            Abhisek Mohanty · 1984-02-05 · Bhubaneswar
          </div>
        </div>
        {/* Right: sidecar status + Build CTA */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <ConnectionHealthPill healthy={sidecarHealthy} />
          <button className="marsys-btn-primary" disabled>
            Build
          </button>
        </div>
      </div>
      {/* Telemetry strip */}
      <div
        style={{
          marginTop: '12px',
          display: 'flex',
          gap: '16px',
          fontSize: '11px',
          color: 'var(--on-dark-faint)',
          fontFamily: 'var(--mono-stack)',
          flexWrap: 'wrap',
        }}
      >
        {(
          [
            ['WRITERS', '—'],
            ['QUEUE', '—'],
            ['QPS', '—'],
            ['BUILD', '—'],
            ['SIDECAR', sidecarHealthy ? 'OK' : 'DOWN'],
            ['SPEND', '—'],
          ] as [string, string][]
        ).map(([k, v]) => (
          <span key={k}>
            <span
              style={{
                color: 'var(--on-dark-faint)',
                textTransform: 'uppercase',
                fontSize: '9.5px',
                letterSpacing: '0.08em',
              }}
            >
              {k}
            </span>{' '}
            <span style={{ color: 'var(--on-dark)' }}>{v}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
