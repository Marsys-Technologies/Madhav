'use client'

/**
 * usePanchangDay — TanStack Query hook for client-side Panchang fetches.
 *
 * Cache key: ['panchang', date, lat, lon, chartId]
 * Fetches via /api/panchanga (Next.js proxy → Python sidecar).
 *
 * For SSR (initial page render), the server component calls queryPanchanga
 * directly and passes data as props; this hook handles subsequent client-side
 * navigation (date/location changes) without a full page reload.
 *
 * Phase: 4C-4-S1 (Item 6)
 */

import { useQuery } from '@tanstack/react-query'

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
}

function mapSidecarResponse(raw: Record<string, unknown>): PanchangDay {
  const panchang = (raw['panchang'] ?? raw) as Record<string, unknown>
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
    raw: panchang,
  }
}

async function fetchPanchangDay(
  date: string,
  lat: number,
  lon: number,
  tzOffsetMinutes: number,
  chartId?: string | null,
): Promise<PanchangDay> {
  const body: Record<string, unknown> = { date, lat, lon, tz_offset_minutes: tzOffsetMinutes }
  if (chartId) body['chart_id'] = chartId

  const response = await fetch('/api/panchanga', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`Panchang fetch failed: HTTP ${response.status}`)
  }

  const raw = await response.json() as Record<string, unknown>
  return mapSidecarResponse(raw)
}

export function usePanchangDay({
  date,
  lat,
  lon,
  tzOffsetMinutes = 330, // IST +05:30
  chartId = null,
  initialData,
}: UsePanchangDayOptions) {
  return useQuery<PanchangDay>({
    queryKey: ['panchang', date, lat, lon, chartId],
    queryFn: () => fetchPanchangDay(date, lat, lon, tzOffsetMinutes, chartId),
    initialData: initialData ?? undefined,
    staleTime: 5 * 60 * 1000,      // 5 min — panchang values don't change mid-day
    refetchOnWindowFocus: false,    // brief spec: "refetch on focus disabled"
    retry: 1,
  })
}

export { mapSidecarResponse }
