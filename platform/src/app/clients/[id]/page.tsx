import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { ChartHero } from '@/components/profile/ChartHero'
import { RoomCard } from '@/components/profile/RoomCard'
import { ProfileSideRail } from '@/components/profile/ProfileSideRail'
import { JourneyStrip } from '@/components/build/JourneyStrip'
import { getForensicSnapshot } from '@/lib/forensic/snapshot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import type { MacroPhaseEntry } from '@/lib/build/types'

export default async function ClientPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
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
    client_id: string
  }>('SELECT id, name, birth_date, birth_time, birth_place, client_id FROM charts WHERE id=$1', [id])

  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  const role = access.role === 'super_admin' ? 'super_admin' : 'client'
  const canBuild = access.canBuild

  const [forensicChart, conversationsResult, layersResult, buildManifestResult] = await Promise.all([
    getForensicSnapshot(id),
    query<{ id: string; title: string | null; created_at: string }>(
      `SELECT id, title, created_at FROM conversations
       WHERE chart_id=$1 AND module='consume'
       ORDER BY created_at DESC LIMIT 3`,
      [id],
    ),
    canBuild
      ? query<{ layer: string; sublayer: string; status: string }>(
          'SELECT layer, sublayer, status FROM pyramid_layers WHERE chart_id=$1 ORDER BY layer, sublayer',
          [id],
        )
      : Promise.resolve({ rows: [] }),
    canBuild
      ? query<{ promoted_at: string | null; build_id: string }>(
          `SELECT build_id, promoted_at FROM build_manifests
           WHERE status='live'
           ORDER BY promoted_at DESC NULLS LAST LIMIT 1`,
          [],
        )
      : Promise.resolve({ rows: [] }),
  ])

  const recentConversations = conversationsResult.rows
  const pyramidLayers = layersResult.rows
  const lastBuild = buildManifestResult.rows[0] ?? null

  const pyramidTotal = pyramidLayers.length
  const pyramidDone = pyramidLayers.filter((l) => l.status === 'complete').length
  const pyramidPercent = pyramidTotal > 0 ? Math.round((pyramidDone / pyramidTotal) * 100) : 0

  const buildArc: MacroPhaseEntry[] = pyramidLayers.slice(0, 5).map((l) => ({
    id: l.sublayer,
    title: l.sublayer,
    status: l.status === 'complete' ? 'completed' : l.status === 'in_progress' ? 'active' : 'pending',
    milestones: [],
  }))
  const activeBuildId = buildArc.find((e) => e.status === 'active')?.id ?? ''

  const generatedAt = lastBuild?.promoted_at ?? null

  return (
    <ZoneRoot zone="ink" className="min-h-full" data-permission={access.permission}>
      <ChartHero
        chart={forensicChart}
        nativeName={chart.name}
        birthDate={chart.birth_date}
        birthTime={chart.birth_time}
        birthPlace={chart.birth_place}
      />

      <div className="mx-auto flex max-w-7xl flex-col gap-6 p-6 md:flex-row md:items-start md:p-8">
        <div className="flex flex-1 flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {canBuild && (
              <div data-testid="build-room-card">
              <RoomCard
                title="Build Room"
                description="Chart corpus construction"
                cta={{ label: 'Continue building', href: `/clients/${id}/build` }}
              >
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between text-xs" style={{ color: 'var(--brand-gold)', opacity: 0.65 }}>
                    <span>Pyramid</span>
                    <span>{pyramidPercent}%</span>
                  </div>
                  <div
                    className="h-1 w-full overflow-hidden rounded-full"
                    style={{ background: 'color-mix(in oklch, var(--brand-gold) 20%, transparent)' }}
                  >
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${pyramidPercent}%`, background: 'var(--brand-gold)' }}
                    />
                  </div>
                  {buildArc.length > 0 && (
                    <div className="overflow-x-hidden">
                      <JourneyStrip arc={buildArc} activeId={activeBuildId} />
                    </div>
                  )}
                  {generatedAt && (
                    <p className="text-xs opacity-50" style={{ color: 'var(--brand-gold)' }}>
                      Last build · {new Date(generatedAt).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </RoomCard>
              </div>
            )}

            <div data-testid="consult-room-card">
            <RoomCard
              title="Consult Room"
              description="Query the chart"
              cta={{ label: 'Ask anything', href: `/clients/${id}/consult` }}
            >
              {recentConversations.length > 0 ? (
                <ul className="flex flex-col gap-2">
                  {recentConversations.map((conv) => (
                    <li key={conv.id}>
                      <a
                        href={`/clients/${id}/consume/${conv.id}`}
                        className="block truncate text-xs transition-opacity hover:opacity-80"
                        style={{ color: 'var(--brand-gold)', opacity: 0.75 }}
                      >
                        {conv.title ?? 'Untitled conversation'}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs opacity-40" style={{ color: 'var(--brand-gold)' }}>
                  No conversations yet
                </p>
              )}
            </RoomCard>
            </div>

            <div data-testid="panchang-room-card">
            <RoomCard
              title="Panchang"
              description="Personalized daily timing"
              cta={{ label: 'Open Panchang', href: `/clients/${id}/panchang` }}
            >
              <p className="text-xs opacity-50" style={{ color: 'var(--brand-gold)' }}>
                Tithi · vara · nakshatra · yoga · karana — aligned to this chart.
              </p>
            </RoomCard>
            </div>

            {/* Timeline Room — intentionally disabled until R5 */}
            <RoomCard
              title="Timeline Room"
              description="Life events · predictions"
              cta={{
                label: 'Open timeline (coming in R5)',
                href: '#',
                disabled: true,
                tooltip: 'Timeline view lands in Portal Redesign R5',
              }}
            >
              <p className="text-xs opacity-40" style={{ color: 'var(--brand-gold)' }}>
                Event log and prospective predictions — available after R5.
              </p>
            </RoomCard>
          </div>
        </div>

        <ProfileSideRail
          chart={forensicChart}
          role={role}
          freshnessAt={generatedAt}
          audienceTier="Acharya"
          chartId={id}
          generatedAt={generatedAt ?? undefined}
        />
      </div>

      {role === 'super_admin' && (
        <footer
          className="mx-auto max-w-7xl border-t px-8 py-4 text-xs opacity-40"
          style={{
            borderColor: 'color-mix(in oklch, var(--brand-gold) 15%, transparent)',
            color: 'var(--brand-gold)',
          }}
        >
          Mirror pairs: active · Last governance close: 2026-04-24 (Step 15)
        </footer>
      )}
    </ZoneRoot>
  )
}
