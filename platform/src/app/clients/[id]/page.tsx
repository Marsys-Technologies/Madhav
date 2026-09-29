import Link from 'next/link'
import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { emptyChartReadiness, getChartReadinessMap, type ChartReadiness } from '@/lib/charts/readiness'
import { getChartWorkspaceSummary } from '@/lib/charts/workspaceSummary'
import { formatDate } from '@/lib/utils/date'
import { ChartHero } from '@/components/profile/ChartHero'
import { ChartReadinessBand } from '@/components/profile/ChartReadinessBand'
import { CapabilityCard } from '@/components/profile/CapabilityCard'
import { ChartActionsMenu } from '@/components/profile/ChartActionsMenu'
import { SharingPanel } from '@/components/sharing/SharingPanel'
import '@/components/profile/jataka-workspace.css'

/**
 * Jātaka workspace — the durable home for one chart.
 *
 * D1/Rāśi hero and identity, the shared readiness band (same authority as the
 * Jātakas directory), an extensible capability deck, and only grounded
 * at-a-glance summaries. D1, daśā and yogas come from this chart's own L1 rows;
 * nothing is borrowed from another chart or invented for a missing value.
 */

function panchangReason(readiness: ChartReadiness): string {
  if (readiness.state === 'building') return 'Chart recomputation is in progress.'
  if (readiness.state === 'needs-rebuild' || readiness.state === 'failed') return 'The chart needs rebuilding first.'
  return 'Needs this chart’s Gaṇita facts.'
}

function GlanceItem({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <dt className="jw-eyebrow">{label}</dt>
      <dd className="text-sm text-[var(--jw-ink)]">{children}</dd>
    </div>
  )
}

function Unavailable({ children }: { children: React.ReactNode }) {
  return <span className="text-[var(--jw-ink-dim)]">{children}</span>
}

export default async function ClientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    timezone_id: string | null
    owner_id: string | null
    client_id: string
  }>(
    `SELECT id, name, birth_date::text AS birth_date, birth_time::text AS birth_time,
            birth_place, timezone_id, owner_id, client_id
       FROM charts WHERE id=$1`,
    [id],
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  const isSuperAdmin = access.role === 'super_admin'
  const canBuild = access.canBuild
  // Sharing follows its existing authorisation: the grant panel is super-admin only.
  const canShare = isSuperAdmin

  const [readinessMap, summary, conversationsResult] = await Promise.all([
    getChartReadinessMap([id]),
    getChartWorkspaceSummary(id),
    query<{ id: string; title: string | null; created_at: string }>(
      `SELECT id, title, created_at FROM conversations
        WHERE chart_id=$1 AND user_id=$2 AND module='consume' AND archived_at IS NULL
        ORDER BY created_at DESC, id DESC LIMIT 3`,
      [id, access.user.uid],
    ),
  ])
  const readiness = readinessMap.get(id) ?? emptyChartReadiness()
  const recentConversations = conversationsResult.rows

  const panchangAvailable =
    !['building', 'needs-rebuild', 'failed'].includes(readiness.state) &&
    readiness.layerPips.some((pip) => pip.layer === 'ganita' && pip.state === 'lit')

  return (
    <div className="jw-root min-h-full" data-permission={access.permission}>
      <ChartHero
        chart={summary.d1}
        nativeName={chart.name}
        birthDate={chart.birth_date}
        birthTime={chart.birth_time}
        birthPlace={chart.birth_place}
        timezoneId={chart.timezone_id}
        actions={
          <ChartActionsMenu
            chartId={id}
            chartName={chart.name}
            canBuild={canBuild}
            isSuperAdmin={isSuperAdmin}
            canShare={canShare}
          />
        }
      />

      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 pb-16 sm:px-6">
        <ChartReadinessBand readiness={readiness} chartId={id} canBuild={canBuild} />

        <section aria-labelledby="jw-capabilities-heading" className="flex flex-col gap-3">
          <h2 id="jw-capabilities-heading" className="jw-eyebrow">
            Capabilities
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {canBuild && (
              <CapabilityCard
                testId="build-room-card"
                name="Nirmāṇa"
                description="Construct, inspect and maintain this chart’s computed corpus."
                href={`/clients/${id}/nirmana`}
                available
                stateHint={readiness.label}
              />
            )}
            <CapabilityCard
              testId="consult-room-card"
              name="Paripraśna"
              description="Ask and explore this chart."
              href={`/clients/${id}/pariprashna`}
              available
              stateHint="Ask"
            />
            <CapabilityCard
              testId="panchang-room-card"
              name="Pañcāṅga"
              description="Personalised daily timing for this chart."
              href={`/clients/${id}/panchang`}
              available={panchangAvailable}
              stateHint="Today"
              reason={panchangAvailable ? undefined : panchangReason(readiness)}
            />
          </div>
        </section>

        <section aria-labelledby="jw-glance-heading" className="jw-panel px-5 py-5">
          <h2 id="jw-glance-heading" className="jw-eyebrow mb-4">
            At a glance
          </h2>
          <dl className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <GlanceItem label="Current daśā">
              {summary.currentDasha ? (
                <>
                  {summary.currentDasha.md} mahādaśā · {summary.currentDasha.ad} antardaśā
                  <span className="block text-xs text-[var(--jw-ink-dim)]">
                    Antardaśā until {formatDate(summary.currentDasha.adEnd)}
                  </span>
                </>
              ) : (
                <Unavailable>Not yet computed</Unavailable>
              )}
            </GlanceItem>
            <GlanceItem label="Confirmed yogas">
              {summary.confirmedYogas.length > 0 ? (
                <ul className="flex flex-wrap gap-1.5" aria-label="Confirmed yoga firings">
                  {summary.confirmedYogas.map((yoga) => (
                    <li key={yoga.id} className="rounded-full border border-[var(--jw-rule)] px-2.5 py-0.5 text-xs">
                      {yoga.name}
                    </li>
                  ))}
                </ul>
              ) : (
                <Unavailable>{summary.flags.includes('yogas_unresolved') ? 'Unavailable' : 'None confirmed yet'}</Unavailable>
              )}
            </GlanceItem>
            <GlanceItem label="Recent readings">
              {recentConversations.length > 0 ? (
                <ul className="flex flex-col gap-1">
                  {recentConversations.map((conversation) => (
                    <li key={conversation.id}>
                      <Link
                        href={`/clients/${id}/consult/${conversation.id}`}
                        className="jw-touch inline-flex min-h-11 items-center truncate text-[var(--jw-gold)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
                      >
                        {conversation.title ?? 'Untitled reading'}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <Unavailable>No readings yet</Unavailable>
              )}
            </GlanceItem>
            <GlanceItem label="Data freshness">
              {readiness.lastActivity ? (
                <>Last built {formatDate(readiness.lastActivity)}</>
              ) : (
                <Unavailable>No computed data yet</Unavailable>
              )}
            </GlanceItem>
          </dl>
        </section>

        {canShare && (
          <section id="sharing" aria-label="Sharing" className="scroll-mt-8">
            <SharingPanel chartId={id} />
          </section>
        )}
      </div>
    </div>
  )
}
