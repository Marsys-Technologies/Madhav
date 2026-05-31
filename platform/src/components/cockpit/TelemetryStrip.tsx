'use client'

/**
 * TelemetryStrip — bottom telemetry row of the force-graph panel.
 *
 * Renders per VISUAL_CONTRACT v2: monospace labels in --text-secondary,
 * values in --gold-primary or --success depending on health.
 *
 * Metrics: QPS · WRITERS · QUEUE · SIDECAR · BUILD ID
 *
 * [C-S6]
 */

interface Props {
  qps: number
  activeWriters: number
  queueDepth: number
  sidecarHealthy: boolean
  buildId: string
}

interface MetricProps {
  label: string
  value: string | number
  valueColor?: string
}

function Metric({ label, value, valueColor }: MetricProps) {
  return (
    <span data-testid={`metric-${label.toLowerCase()}`} className="flex items-center gap-1.5">
      <span
        style={{
          fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
          fontSize: 10,
          color: 'var(--text-secondary, #888373)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        {label}
      </span>
      <span
        data-testid={`metric-${label.toLowerCase()}-value`}
        style={{
          fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
          fontSize: 11,
          color: valueColor ?? 'var(--gold-primary, #d4a648)',
          fontWeight: 500,
        }}
      >
        {value}
      </span>
    </span>
  )
}

export function TelemetryStrip({ qps, activeWriters, queueDepth, sidecarHealthy, buildId }: Props) {
  const sidecarColor = sidecarHealthy
    ? 'var(--success, #9bd49a)'
    : 'var(--danger, #e89a9a)'
  const sidecarValue = sidecarHealthy ? 'OK' : 'DOWN'

  return (
    <div
      data-testid="telemetry-strip"
      className="flex items-center gap-5 flex-wrap"
      style={{
        padding: '8px 12px',
        borderTop: '1px solid var(--obsidian-border, #1f1c17)',
        background: 'var(--obsidian-panel, #0a0908)',
      }}
    >
      <Metric label="QPS"     value={qps.toFixed(1)} />
      <Metric label="WRITERS" value={activeWriters} />
      <Metric label="QUEUE"   value={queueDepth} />
      <Metric
        label="SIDECAR"
        value={sidecarValue}
        valueColor={sidecarColor}
      />
      <Metric
        label="BUILD ID"
        value={buildId ? buildId.slice(0, 8) : '—'}
        valueColor="var(--text-secondary, #888373)"
      />
    </div>
  )
}
