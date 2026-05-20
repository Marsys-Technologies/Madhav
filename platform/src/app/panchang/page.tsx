/**
 * /panchang — Panchang Day View (server component)
 *
 * Fetches today's Panchang for default location (Bhubaneswar) on the server
 * by calling the Python sidecar directly (same as queryPanchanga's callSidecar
 * but without needing a full QueryPlan — the RetrievalTool is designed for
 * LLM orchestration, not SSR page entry points).
 *
 * Passes data to PanchangClientView as initialData to avoid client-side loading flash.
 * Subsequent navigation (date/location changes) handled client-side via usePanchangDay.
 *
 * Phase: 4C-4-S1 (Item 2)
 */

import { Suspense } from 'react'
import { format } from 'date-fns'
import { PanchangClientView } from './components/PanchangClientView'
import { mapSidecarResponse } from './hooks/usePanchangDay'
import type { SearchParams } from 'next/dist/server/request/search-params'

// Default location: Bhubaneswar (per brief D1 decisions + query_panchanga.ts constants)
const DEFAULT_LAT = 20.27
const DEFAULT_LON = 85.84
const DEFAULT_TZ = 330 // IST +05:30

interface PanchangPageProps {
  searchParams: Promise<SearchParams>
}

/** Call the Python sidecar directly for SSR — avoids the full QueryPlan overhead */
async function fetchPanchangSSR(
  date: string,
  lat: number,
  lon: number,
  tzOffsetMinutes: number,
): Promise<Record<string, unknown> | null> {
  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  if (!sidecarUrl) return null

  const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''
  const res = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': sidecarKey,
    },
    body: JSON.stringify({ date, lat, lon, tz_offset_minutes: tzOffsetMinutes }),
    // Next.js 16: opt out of data cache for dynamic page (re-fetch each request)
    cache: 'no-store',
  })

  if (!res.ok) return null
  return await res.json() as Record<string, unknown>
}

export default async function PanchangPage({ searchParams }: PanchangPageProps) {
  const params = await searchParams
  const today = format(new Date(), 'yyyy-MM-dd')

  // Resolve date from URL (default: today)
  const dateParam = typeof params['d'] === 'string' ? params['d'] : today
  const date = /^\d{4}-\d{2}-\d{2}$/.test(dateParam) ? dateParam : today

  // Resolve location from URL (default: Bhubaneswar)
  const latParam = typeof params['lat'] === 'string' ? parseFloat(params['lat']) : DEFAULT_LAT
  const lonParam = typeof params['lon'] === 'string' ? parseFloat(params['lon']) : DEFAULT_LON
  const resolvedLat = isNaN(latParam) ? DEFAULT_LAT : latParam
  const resolvedLon = isNaN(lonParam) ? DEFAULT_LON : lonParam

  // SSR: fetch panchang from sidecar
  let initialData = null
  try {
    const raw = await fetchPanchangSSR(date, resolvedLat, resolvedLon, DEFAULT_TZ)
    if (raw) {
      // Sidecar returns { ok: true, panchang: {...}, cache_hit: bool }
      const panchangDict = (raw['panchang'] ?? raw) as Record<string, unknown>
      panchangDict['date'] = date
      panchangDict['lat'] = resolvedLat
      panchangDict['lon'] = resolvedLon
      panchangDict['tz_offset_minutes'] = DEFAULT_TZ
      initialData = mapSidecarResponse(panchangDict)
    }
  } catch (err) {
    // SSR fetch failed — page still renders; client will retry via usePanchangDay
    console.error('[PanchangPage] SSR sidecar fetch failed:', err)
  }

  return (
    <div className="relative min-h-full overflow-hidden">
      {/* Brand background gradient — matches dashboard aesthetic */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_30%,rgba(212,175,55,0.03)_0%,transparent_60%)]" />

      <div className="relative z-10">
        <Suspense fallback={null}>
          <PanchangClientView
            initialData={initialData}
            initialDate={date}
            initialLat={resolvedLat}
            initialLon={resolvedLon}
          />
        </Suspense>
      </div>
    </div>
  )
}
