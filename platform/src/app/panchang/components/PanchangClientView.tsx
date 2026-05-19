'use client'

/**
 * PanchangClientView — client-side wrapper that reads URL params and drives
 * the PanchangHeader + PrimaryStrip with live data via usePanchangDay.
 *
 * The server component (page.tsx) renders this with SSR-fetched initialData
 * to avoid a loading flash on first load. Subsequent navigation (date/location
 * changes) is handled client-side via usePanchangDay.
 *
 * Phase: 4C-4-S1
 */

import { useSearchParams } from 'next/navigation'
import { PanchangHeader, resolveDate, resolveLocation } from './PanchangHeader'
import { PrimaryStrip } from './PrimaryStrip'
import { TimingsPanel } from './TimingsPanel'
import { PlanetaryGrid } from './PlanetaryGrid'
import { usePanchangDay, type PanchangDay } from '../hooks/usePanchangDay'
import { SpecialYogasList } from './SpecialYogasList'
import { ChoghadiyaPanel } from './ChoghadiyaPanel'
import { HoraPanel } from './HoraPanel'

interface PanchangClientViewProps {
  /** Server-rendered initial data — used as TanStack Query initialData to skip first fetch */
  initialData: PanchangDay | null
  initialDate: string
  initialLat: number
  initialLon: number
}

export function PanchangClientView({
  initialData,
  initialDate,
  initialLat,
  initialLon,
}: PanchangClientViewProps) {
  const searchParams = useSearchParams()
  const date = resolveDate(searchParams) || initialDate
  const location = resolveLocation(searchParams)

  const { data, isLoading, isError, error } = usePanchangDay({
    date,
    lat: location.lat,
    lon: location.lon,
    tzOffsetMinutes: 330,
    initialData: initialData ?? undefined,
  })

  return (
    <>
      <PanchangHeader
        initialDate={initialDate}
        initialLocation={{ id: 'bhubaneswar', label: 'Bhubaneswar', lat: initialLat, lon: initialLon }}
      />

      {isError && (
        <div className="mx-auto max-w-4xl px-4 py-6">
          <div
            className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] px-5 py-6 text-center"
          >
            <p className="font-serif text-lg" style={{ color: 'var(--brand-gold)' }}>
              ॥ Data Unavailable ॥
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'The Panchang engine could not be reached.'}
            </p>
          </div>
        </div>
      )}

      {isLoading && !data && (
        <div className="mx-auto max-w-4xl px-4 py-6">
          <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-5 py-4 border-b border-[rgba(212,175,55,0.08)] last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="h-4 w-20 rounded bg-[rgba(212,175,55,0.10)] animate-pulse" />
                  <div className="h-5 w-32 rounded bg-[rgba(212,175,55,0.14)] animate-pulse" />
                </div>
                <div className="h-4 w-16 rounded bg-[rgba(212,175,55,0.08)] animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      )}

      {data && (
        <>
          <PrimaryStrip
            angas={data.angas}
            tzOffsetMinutes={330}
            date={date}
          />

          {/* Timings + Planetary Grid — two-column on md+, stacked on mobile (§4.2) */}
          <div className="mx-auto max-w-4xl px-4 pb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TimingsPanel
                timings={data.timings}
                tzOffsetMinutes={330}
              />
              <PlanetaryGrid
                planets={data.planets as Record<string, never> | null}
              />
            </div>
          </div>

          {/* Active Special Yogas (§4.2 — below timings/planetary) */}
          <div className="mx-auto max-w-4xl px-4 pb-4">
            <SpecialYogasList
              specialYogas={data.special_yogas}
              tzOffsetMinutes={330}
            />
          </div>

          {/* Choghadiya + Hora — collapsible panels (§4.2 — collapsed by default) */}
          <div className="mx-auto max-w-4xl px-4 pb-6 flex flex-col gap-3">
            <ChoghadiyaPanel
              choghadiya={data.raw['choghadiya']}
              tzOffsetMinutes={330}
            />
            <HoraPanel
              hora={data.hora}
              tzOffsetMinutes={330}
            />
          </div>
        </>
      )}
    </>
  )
}
