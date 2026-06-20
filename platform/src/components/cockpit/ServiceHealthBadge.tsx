'use client'

/**
 * ServiceHealthBadge — compact health badge for service-kind assets.
 *
 * Renders a colored pill showing the current health state of a service asset.
 * Maps the DB-level health values to human-readable labels + theme colors.
 *
 * Used in AssetTable rows and LiveDependencyGraph tooltips for service nodes.
 *
 * [L3-K0 service-asset-type infrastructure]
 */

type ServiceHealth = 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | null

interface Props {
  health: ServiceHealth
  /** When true renders a smaller inline variant (default false) */
  compact?: boolean
  /** Optional ISO timestamp of last invocation for tooltip / label */
  lastInvokedAt?: string | null
}

const HEALTH_LABEL: Record<string, string> = {
  healthy:   'Healthy',
  degraded:  'Degraded',
  unhealthy: 'Unhealthy',
  unknown:   'Unknown',
}

const HEALTH_COLOR: Record<string, { border: string; bg: string; text: string; dot: string }> = {
  healthy:   { border: '#3a5c3a', bg: '#0f2010', text: '#9bd49a', dot: '#9bd49a' },
  degraded:  { border: '#5a4a1f', bg: '#1e1608', text: '#d4a648', dot: '#d4a648' },
  unhealthy: { border: '#5c3a3a', bg: '#201010', text: '#e89a9a', dot: '#e89a9a' },
  unknown:   { border: '#3a3328', bg: '#12100c', text: '#888373', dot: '#5d5b54' },
}

function formatLastInvoked(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function ServiceHealthBadge({ health, compact = false, lastInvokedAt }: Props) {
  const key = health ?? 'unknown'
  const label = HEALTH_LABEL[key] ?? 'Unknown'
  const colors = HEALTH_COLOR[key] ?? HEALTH_COLOR['unknown']
  const lastStr = formatLastInvoked(lastInvokedAt)

  return (
    <span
      data-testid={`service-health-badge-${key}`}
      title={lastStr ? `Last invoked: ${lastStr}` : `Service health: ${label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: compact ? 3 : 4,
        padding: compact ? '1px 6px' : '2px 8px',
        borderRadius: 999,
        border: `1px solid ${colors.border}`,
        background: colors.bg,
        fontFamily: 'var(--font-sans, Inter, sans-serif)',
        fontSize: compact ? 10 : 11,
        color: colors.text,
        whiteSpace: 'nowrap',
        cursor: lastStr ? 'help' : 'default',
      }}
    >
      {/* Status dot */}
      <span
        aria-hidden="true"
        style={{
          display: 'inline-block',
          width: compact ? 5 : 6,
          height: compact ? 5 : 6,
          borderRadius: '50%',
          background: colors.dot,
          flexShrink: 0,
          // Pulse animation for healthy state — shows live service
          animation: key === 'healthy' ? 'service-pulse 2s ease-in-out infinite' : 'none',
        }}
      />
      {label}
    </span>
  )
}

/**
 * ServiceLastInvokedLabel — small secondary line showing last invocation time.
 * Renders nothing if lastInvokedAt is null/undefined.
 */
export function ServiceLastInvokedLabel({
  lastInvokedAt,
}: {
  lastInvokedAt: string | null | undefined
}) {
  if (!lastInvokedAt) return null
  const label = formatLastInvoked(lastInvokedAt)
  return (
    <span
      data-testid="service-last-invoked"
      style={{
        fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
        fontSize: 9,
        color: 'var(--text-tertiary, #5d5b54)',
      }}
    >
      last: {label}
    </span>
  )
}
