'use client'

/**
 * PanchangClientView — client-side wrapper that reads URL params and drives
 * the PanchangHeader + PrimaryStrip with live data via usePanchangDay.
 *
 * The server component (page.tsx) renders this with SSR-fetched initialData
 * to avoid a loading flash on first load. Subsequent navigation (date/location
 * changes) is handled client-side via usePanchangDay.
 *
 * Phase: 4C-4-S1 / 4C-4-S4 (edge-state polish); 4C-5 (chartId state + native_context)
 */

import { useCallback, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { parseISO, isAfter, addYears } from 'date-fns'
import { PanchangHeader, resolveDate, resolveLocation, resolveChartId } from './PanchangHeader'
import { PrimaryStrip } from './PrimaryStrip'
import { TimingsPanel } from './TimingsPanel'
import { PlanetaryGrid } from './PlanetaryGrid'
import { usePanchangDay, type PanchangDay } from '../hooks/usePanchangDay'
import { SpecialYogasList } from './SpecialYogasList'
import { ChoghadiyaPanel } from './ChoghadiyaPanel'
import { HoraPanel } from './HoraPanel'
import { ActionBar } from './ActionBar'

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

  // chartId state — initialised from URL (handles server-rendered deep links),
  // then updated by PanchangHeader.onChartIdChange when user changes selection.
  const [chartId, setChartId] = useState<string | null>(() => resolveChartId(searchParams))

  // Ephemeris range: Swiss Ephemeris supports ~5400 BCE – 5400 CE.
  // For practical purposes, flag dates beyond +100 years as "beyond range".
  const EPHEMERIS_CEILING = addYears(new Date(), 100)
  const isBeyondEphemeris = (() => {
    try { return isAfter(parseISO(date), EPHEMERIS_CEILING) } catch { return false }
  })()

  // Polar latitude: abs(lat) >= 66.5° — sun may not rise/set.
  const isPolarLat = Math.abs(location.lat) >= 66.5

  const { data, isLoading, isError, error, refetch } = usePanchangDay({
    date,
    lat: location.lat,
    lon: location.lon,
    tzOffsetMinutes: 330,
    chartId,
    initialData: initialData ?? undefined,
    // Skip fetching if we know the request can't succeed
    enabled: !isBeyondEphemeris,
  })

  const handleRetry = useCallback(() => { void refetch() }, [refetch])

  return (
    <div className="flex min-h-full flex-col">
      <PanchangHeader
        initialDate={initialDate}
        initialLocation={{ id: 'bhubaneswar', label: 'Bhubaneswar', lat: initialLat, lon: initialLon }}
        onChartIdChange={setChartId}
      />

      {/* Edge: date beyond ephemeris range */}
      {isBeyondEphemeris && (
        <div className="mx-auto max-w-4xl px-4 py-6 w-full">
          <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] px-5 py-6 text-center">
            <p className="font-serif text-lg" style={{ color: 'var(--brand-gold)' }}>
              ॥ Beyond Ephemeris Range ॥
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              This date is beyond the supported ephemeris range. Please select a date within the next 100 years.
            </p>
          </div>
        </div>
      )}

      {/* Edge: polar latitude — sunrise N/A */}
      {isPolarLat && !isBeyondEphemeris && (
        <div className="mx-auto max-w-4xl px-4 pt-4 w-full">
          <div className="rounded-lg border border-[rgba(212,175,55,0.12)] bg-[rgba(212,175,55,0.04)] px-4 py-3 flex items-start gap-3">
            <span style={{ color: 'rgba(212,175,55,0.70)' }} aria-hidden="true">⚠</span>
            <p className="text-sm" style={{ color: 'rgba(212,175,55,0.80)' }}>
              <strong>Sunrise N/A</strong> — this location is currently in polar twilight. Timings that
              depend on sunrise (Rahu Kalam, Choghadiya, etc.) may be unavailable or approximate.
            </p>
          </div>
        </div>
      )}

      {/* Error: sidecar 500 or network failure */}
      {isError && !isBeyondEphemeris && (
        <div className="mx-auto max-w-4xl px-4 py-6 w-full">
          <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] px-5 py-6 text-center">
            <p className="font-serif text-lg" style={{ color: 'var(--brand-gold)' }}>
              ॥ Data Unavailable ॥
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'The Panchang engine could not be reached.'}
            </p>
            <button
              onClick={handleRetry}
              className="mt-4 rounded-lg border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.08)] px-4 py-2 text-sm font-medium transition-colors hover:bg-[rgba(212,175,55,0.14)]"
              style={{ color: 'var(--brand-gold)' }}
            >
              Retry
            </button>
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
            nativeContext={data.native_context}
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
                nativeContext={data.native_context}
              />
            </div>
          </div>

          {/* Active Special Yogas (§4.2 — below timings/planetary) */}
          <div className="mx-auto max-w-4xl px-4 pb-4">
            <SpecialYogasList
              specialYogas={data.special_yogas}
              tzOffsetMinutes={330}
              nativeContext={data.native_context}
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

      {/* Action Bar — sticky bottom on mobile, inline on desktop (§4.2) */}
      <div className="mt-auto">
        <ActionBar date={date} />
      </div>
    </div>
  )
}
