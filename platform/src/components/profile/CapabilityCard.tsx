import Link from 'next/link'

/**
 * One capability in the chart workspace's extensible deck (Nirmāṇa,
 * Paripraśna, Pañcāṅga, and later additions). An available capability is a
 * single link; an unavailable one renders no link at all and says why.
 */
export interface CapabilityCardProps {
  name: string
  description: string
  href: string
  available: boolean
  stateHint: string
  reason?: string
  testId?: string
}

const BODY = 'flex min-h-11 flex-col gap-1.5 rounded-xl border p-4'

export function CapabilityCard({ name, description, href, available, stateHint, reason, testId }: CapabilityCardProps) {
  if (!available) {
    return (
      <div
        className={`${BODY} border-[var(--jw-rule)] bg-[var(--jw-panel)] opacity-80`}
        data-testid={testId}
        data-available="false"
      >
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="jw-display text-xl text-[var(--jw-ink-dim)]">{name}</h3>
          <span className="jw-eyebrow">Unavailable</span>
        </div>
        <p className="text-sm text-[var(--jw-ink-dim)]">{description}</p>
        {reason && <p className="text-xs text-[var(--jw-ink-dim)]">{reason}</p>}
      </div>
    )
  }
  return (
    <Link
      href={href}
      data-testid={testId}
      data-available="true"
      className={`${BODY} jw-capability jw-touch border-[var(--jw-rule)] bg-[var(--jw-panel)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)] focus-visible:ring-offset-2 focus-visible:ring-offset-black`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="jw-display text-xl">{name}</h3>
        <span className="jw-eyebrow">{stateHint}</span>
      </div>
      <p className="text-sm text-[var(--jw-ink-dim)]">{description}</p>
    </Link>
  )
}
