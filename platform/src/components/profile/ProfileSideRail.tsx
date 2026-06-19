import { FreshnessIndicator } from '@/components/build/FreshnessIndicator'
import { DashaCountdown } from './DashaCountdown'
import type { ForensicChart } from '@/lib/forensic/snapshot'

interface ProfileSideRailProps {
  chart: ForensicChart
  role: 'super_admin' | 'guest'
  freshnessAt: string | null
  audienceTier: string
  chartId: string
  generatedAt?: string
}

export function ProfileSideRail({
  chart,
  role,
  audienceTier,
  chartId,
  generatedAt,
}: ProfileSideRailProps) {
  const dasha = chart.currentDasha

  return (
    <aside
      className="flex w-full flex-col gap-6 rounded-lg border p-5 md:w-72 md:shrink-0"
      style={{
        borderColor: 'color-mix(in oklch, var(--brand-gold) 20%, transparent)',
        background: 'color-mix(in oklch, var(--brand-charcoal) 96%, var(--brand-gold) 4%)',
      }}
    >
      {/* Dasha Countdown */}
      {dasha && (
        <DashaCountdown md={dasha.md} ad={dasha.ad} adEnd={dasha.adEnd} />
      )}

      {/* Divider */}
      {dasha && <hr style={{ borderColor: 'color-mix(in oklch, var(--brand-gold) 15%, transparent)' }} />}

      {/* Top Yogas */}
      {chart.topYogas.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-xs uppercase tracking-widest opacity-70" style={{ color: 'var(--brand-gold)' }}>
            Active Yogas
          </p>
          <div className="flex flex-wrap gap-1.5">
            {chart.topYogas.map((yoga) => (
              <span
                key={yoga}
                className="rounded-full border px-2.5 py-0.5 text-xs"
                style={{
                  borderColor: 'color-mix(in oklch, var(--brand-gold) 35%, transparent)',
                  color: 'var(--brand-gold)',
                }}
              >
                {yoga}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Freshness */}
      {generatedAt && (
        <>
          <hr style={{ borderColor: 'color-mix(in oklch, var(--brand-gold) 15%, transparent)' }} />
          <FreshnessIndicator generatedAt={generatedAt} />
        </>
      )}

      {/* Audience tier badge */}
      <div className="flex items-center gap-2">
        <span className="text-xs uppercase tracking-widest opacity-70" style={{ color: 'var(--brand-gold)' }}>
          Tier
        </span>
        <span
          className="rounded border px-2 py-0.5 text-xs font-medium"
          style={{
            borderColor: 'color-mix(in oklch, var(--brand-gold) 35%, transparent)',
            color: 'var(--brand-gold-cream)',
          }}
        >
          {audienceTier}
        </span>
      </div>

      {/* Super-admin audit deep-link */}
      {role === 'super_admin' && (
        <>
          <hr style={{ borderColor: 'color-mix(in oklch, var(--brand-gold) 15%, transparent)' }} />
          <a
            href={`/cockpit/audit?chart=${chartId}`}
            className="text-xs transition-opacity hover:opacity-80"
            style={{ color: 'var(--brand-gold)', opacity: 0.85 }}
          >
            Audit log →
          </a>
        </>
      )}
    </aside>
  )
}
