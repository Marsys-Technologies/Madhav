'use client'

import { useState, useEffect } from 'react'
import { ConnectionHealthPill } from './ConnectionHealthPill'

interface Props {
  chartId: string
  chartName?: string | null
  birthDate?: string | null
  birthPlace?: string | null
}

export function CockpitHeader({ chartId, chartName, birthDate, birthPlace }: Props) {
  const [sidecarHealthy, setSidecarHealthy] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/api/sidecar/health', {
          credentials: 'include',
          cache: 'no-store',
        })
        const body = await r.json()
        setSidecarHealthy(!!body.healthy)
      } catch {
        setSidecarHealthy(false)
      }
    }
    check()
    const t = setInterval(check, 30_000)
    return () => clearInterval(t)
  }, [])

  const sidecarLabel =
    sidecarHealthy === null ? '…' : sidecarHealthy ? 'OK' : 'DOWN'

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
            {chartName ?? 'Loading chart…'}
          </h1>
          <div
            style={{
              fontFamily: 'var(--ui-stack)',
              fontSize: '12px',
              color: 'var(--on-dark-mut)',
              marginTop: '2px',
            }}
          >
            {birthDate ?? '—'} · {birthPlace ?? '—'}{' '}
            <span
              style={{
                fontFamily: 'var(--mono-stack)',
                fontSize: '11px',
                color: 'var(--on-dark-faint)',
              }}
            >
              {chartId.slice(0, 8)}…
            </span>
          </div>
        </div>
        {/* Right: sidecar status + Pro view pill + Build CTA */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <ConnectionHealthPill healthy={sidecarHealthy} />
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 10px',
              borderRadius: '12px',
              background: 'rgba(168,124,42,0.15)',
              border: '1px solid var(--gold-engrave)',
              color: 'var(--gold-bright)',
              fontSize: '10px',
              fontFamily: 'var(--ui-stack)',
              fontWeight: 600,
              letterSpacing: '0.05em',
            }}
          >
            ◆ Pro view
          </span>
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
            ['SIDECAR', sidecarLabel],
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
