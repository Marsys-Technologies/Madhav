'use client'

/**
 * usePanchangDay — TanStack Query hook for client-side Panchang fetches.
 *
 * The shared cache holds only calendar data for the exact requested tuple.
 * Fetches via /api/panchang (Next.js proxy → Python sidecar). Renamed from
 * /api/panchanga in unit 0a.1.3 (panchang(a) tree merge).
 *
 * For SSR (initial page render), the server component calls queryPanchanga
 * directly and passes data as props; this hook handles subsequent client-side
 * navigation (date/location changes) without a full page reload.
 *
 * Phase: 4C-4-S1 (Item 6)
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { QueryClient, useQuery, useQueryClient } from '@tanstack/react-query'
import { AYANAMSHA_SERVE_ORDER } from '@/lib/retrieval/registry/constants'

export interface PanchangAngas {
  tithi: { name: string; number: number; ends_at_local?: string } | null
  nakshatra: { name: string; number: number; ends_at_local?: string } | null
  yoga: { name: string; number: number; ends_at_local?: string } | null
  karana_first: { name: string; number: number; ends_at_local?: string } | null
  karana_second: { name: string; number: number; ends_at_local?: string } | null
  vara: { name: string; number: number } | null
  paksha: string | null
}

export interface PanchangTimings {
  sunrise_utc: string | null
  sunset_utc: string | null
  moonrise_utc: string | null
  moonset_utc: string | null
  inauspicious: Record<string, unknown> | null
  auspicious: Record<string, unknown> | null
}

/**
 * NativeContext — optional birth-chart overlay returned by the Panchang API.
 * Populated in 4C-5; used by Tara Bala + Chandra Bala badge components.
 */
export interface NativeContext {
  chart_id: string
  native_name: string           // chart name for UI display (e.g. "Abhisek")
  birth_nakshatra_id: number    // 1..27 (Moon nakshatra at birth, sidereal)
  birth_nakshatra_name: string  // e.g. "Purva Bhadrapada"
  moon_sign_id: number          // 1..12 (1 = Aries/Mesha … 12 = Pisces/Meena)
  moon_sign_name: string        // Sanskrit sign name, e.g. "Kumbha"
  active_dasha_lord: string | null  // future dasha-aware muhurat (4C-6)
  ayanamsha_id?: string
  fact_ids?: {
    birth_nakshatra_id: string
    birth_nakshatra_name: string
    moon_sign_id: string
    moon_sign_name: string
  }
}

export interface PanchangDay {
  date: string
  lat: number
  lon: number
  tz_offset_minutes: number
  angas: PanchangAngas
  timings: PanchangTimings
  special_yogas: unknown[] | null
  planets: unknown[] | null
  choghadiya: unknown[] | null
  hora: unknown[] | null
  /** Native overlay — only present when chart_id was passed (4C-5) */
  native_context: NativeContext | null
  /** Raw sidecar panchang dict — for fields not yet modelled above */
  raw: Record<string, unknown>
}

interface UsePanchangDayOptions {
  date: string          // YYYY-MM-DD
  lat: number
  lon: number
  tzOffsetMinutes?: number
  chartId?: string | null
  /** Initial data from SSR — avoids the first client fetch */
  initialData?: PanchangDay | null
  /** Set false to skip the fetch (e.g. date out of range) */
  enabled?: boolean
}

function mapSidecarResponse(raw: Record<string, unknown>): PanchangDay {
  const panchang = (raw['panchang'] ?? raw) as Record<string, unknown>
  // native_context is at the top-level response (not inside panchang dict)
  const nativeContext = (raw['native_context'] as NativeContext | null | undefined) ?? null
  return {
    date: panchang['date'] as string,
    lat: panchang['lat'] as number,
    lon: panchang['lon'] as number,
    tz_offset_minutes: panchang['tz_offset_minutes'] as number,
    angas: {
      tithi: (panchang['tithi'] as PanchangAngas['tithi']) ?? null,
      nakshatra: (panchang['nakshatra'] as PanchangAngas['nakshatra']) ?? null,
      yoga: (panchang['yoga'] as PanchangAngas['yoga']) ?? null,
      karana_first: (panchang['karana_first'] as PanchangAngas['karana_first']) ?? null,
      karana_second: (panchang['karana_second'] as PanchangAngas['karana_second']) ?? null,
      vara: (panchang['vara'] as PanchangAngas['vara']) ?? null,
      paksha: (panchang['paksha'] as string) ?? null,
    },
    timings: {
      sunrise_utc: (panchang['sunrise_utc'] as string) ?? null,
      sunset_utc: (panchang['sunset_utc'] as string) ?? null,
      moonrise_utc: (panchang['moonrise_utc'] as string) ?? null,
      moonset_utc: (panchang['moonset_utc'] as string) ?? null,
      inauspicious: (panchang['inauspicious'] as Record<string, unknown>) ?? null,
      auspicious: (panchang['auspicious'] as Record<string, unknown>) ?? null,
    },
    special_yogas: (panchang['special_yogas'] as unknown[]) ?? null,
    planets: (panchang['planets'] as unknown[]) ?? null,
    choghadiya: (panchang['choghadiya'] as unknown[]) ?? null,
    hora: (panchang['hora'] as unknown[]) ?? null,
    native_context: nativeContext,
    raw: panchang,
  }
}

function calendarOnly(day: PanchangDay): PanchangDay {
  const { native_context: _context, native_context_error: _error, ...raw } = day.raw
  return { ...day, native_context: null, raw }
}

function storedContext(context: NativeContext | null, chartId: string): NativeContext | null {
  if (typeof context?.chart_id !== 'string' || context.chart_id.toLowerCase() !== chartId.toLowerCase()
    || !AYANAMSHA_SERVE_ORDER.some((frame) => frame === context.ayanamsha_id)) return null

  const facts = context.fact_ids
  const ids = [facts?.birth_nakshatra_id, facts?.birth_nakshatra_name, facts?.moon_sign_id, facts?.moon_sign_name]
  return ids.every((id) => typeof id === 'string' && id.trim().length > 0) && new Set(ids).size === ids.length
    ? context
    : null
}

async function fetchPanchangDay(
  [date, lat, lon, tzOffsetMinutes]: readonly [string, number, number, number],
  signal: AbortSignal,
  chartId?: string,
): Promise<PanchangDay | null> {
  const body = { date, lat, lon, tz_offset_minutes: tzOffsetMinutes, ...(chartId && { chart_id: chartId }) }
  const response = await fetch('/api/panchang', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  // Older servers deny the whole combined request. The caller can still load the public day.
  if (chartId && response.status === 403) return null
  if (!response.ok) throw new Error(`Panchang fetch failed: HTTP ${response.status}`)

  return mapSidecarResponse(await response.json() as Record<string, unknown>)
}

function useOverlaySession() {
  const [session, setSession] = useState({ revision: 0, signedOut: false })

  useEffect(() => {
    let disposed = false
    let unsubscribe: (() => void) | undefined
    let previousUid: string | null | undefined
    // The SDK observes account changes. The server cookie still governs every overlay request.
    void Promise.all([import('firebase/auth'), import('@/lib/firebase/client')]).then(([sdk, { auth }]) => {
      if (disposed) return
      unsubscribe = sdk.onAuthStateChanged(auth, (user) => {
        const uid = user?.uid ?? null
        if (!disposed && previousUid !== undefined && uid !== previousUid) {
          setSession(({ revision }) => ({ revision: revision + 1, signedOut: uid === null }))
        }
        previousUid = uid
      })
    }).catch(() => { /* An unavailable SDK supplies no discard hint. */ })
    return () => {
      disposed = true
      unsubscribe?.()
    }
  }, [])

  return session
}

const queryBehavior = {
  staleTime: 5 * 60 * 1000,
  refetchOnWindowFocus: false,
  retry: 1,
} as const

export function usePanchangDay({
  date,
  lat,
  lon,
  tzOffsetMinutes = 330, // IST +05:30
  chartId = null,
  initialData,
  enabled = true,
}: UsePanchangDayOptions) {
  const sharedClient = useQueryClient()
  const [overlayClient] = useState(() => new QueryClient())
  const [retryGeneration, setRetryGeneration] = useState(0)
  const session = useOverlaySession()
  useEffect(() => {
    overlayClient.mount()
    return () => overlayClient.unmount()
  }, [overlayClient])

  const tuple = useMemo(() => [date, lat, lon, tzOffsetMinutes] as const, [date, lat, lon, tzOffsetMinutes])
  const calendarKey = ['panchang', ...tuple] as const
  const activeChart = enabled && !session.signedOut ? chartId : null
  const scope = useMemo(() => ({ tuple, activeChart, revision: session.revision, retryGeneration }),
    [tuple, activeChart, session.revision, retryGeneration])

  // This observer is private to the mounted view. The shared QueryClient only sees calendarOnly().
  const overlay = useQuery({
    ...queryBehavior,
    queryKey: ['panchang-overlay', ...tuple, activeChart, scope.revision, scope.retryGeneration],
    queryFn: async ({ signal }) => {
      if (!activeChart) return { scope, fallback: false, context: null }
      const result = await fetchPanchangDay(tuple, signal, activeChart)
      if (!result) return { scope, fallback: true, context: null }
      if (!signal.aborted) sharedClient.setQueryData(calendarKey, calendarOnly(result))
      return { scope, fallback: false, context: storedContext(result.native_context, activeChart) }
    },
    enabled: activeChart !== null,
    gcTime: 0,
    structuralSharing: false,
  }, overlayClient)

  const overlayResult = overlay.data?.scope === scope ? overlay.data : undefined
  const calendar = useQuery({
    ...queryBehavior,
    queryKey: calendarKey,
    queryFn: async ({ signal }) => {
      const result = await fetchPanchangDay(tuple, signal)
      if (!result) throw new Error('Panchang calendar unavailable')
      return calendarOnly(result)
    },
    initialData: initialData && initialData.native_context === null && initialData.raw['native_context'] == null
      && initialData.date === date && initialData.lat === lat && initialData.lon === lon
      && initialData.tz_offset_minutes === tzOffsetMinutes
      ? calendarOnly(initialData)
      : undefined,
    enabled: enabled && (!activeChart || overlayResult?.fallback === true),
  })

  const usePersonalRequest = !!activeChart && !overlayResult?.fallback
  const current = usePersonalRequest ? overlay : calendar
  const refetchCalendar = calendar.refetch
  const refetch = useCallback(() => {
    // Explicit revalidation starts with an empty overlay in the next render.
    if (usePersonalRequest) setRetryGeneration((generation) => generation + 1)
    else void refetchCalendar()
  }, [refetchCalendar, usePersonalRequest])
  const nativeContext = activeChart && overlay.fetchStatus === 'idle' && overlay.isSuccess
    ? overlayResult?.context ?? null
    : null

  return {
    data: calendar.data,
    nativeContext,
    isLoading: current.isLoading,
    isError: current.isError,
    error: current.error,
    refetch,
  }
}

export { mapSidecarResponse }
