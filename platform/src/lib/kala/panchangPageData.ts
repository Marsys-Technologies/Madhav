import 'server-only'
import { mapSidecarResponse } from '@/lib/panchang/sidecar_mapper'

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

/** Kāla service adapter for SSR; admission and URL/default resolution stay with the page. */
export async function readPanchangPageData(
  date: string,
  lat: number,
  lon: number,
  tzOffsetMinutes: number,
) {
  // SSR: fetch panchang from sidecar
  let initialData = null
  try {
    const raw = await fetchPanchangSSR(date, lat, lon, tzOffsetMinutes)
    if (raw) {
      // Sidecar returns { ok: true, panchang: {...}, cache_hit: bool }
      const panchangDict = (raw['panchang'] ?? raw) as Record<string, unknown>
      panchangDict['date'] = date
      panchangDict['lat'] = lat
      panchangDict['lon'] = lon
      panchangDict['tz_offset_minutes'] = tzOffsetMinutes
      initialData = mapSidecarResponse(panchangDict)
    }
  } catch (err) {
    // SSR fetch failed — page still renders; client will retry via usePanchangDay
    console.error('[PanchangPage] SSR sidecar fetch failed:', err)
  }
  return initialData
}
