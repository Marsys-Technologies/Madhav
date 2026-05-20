/**
 * GET /api/panchang/ics
 *
 * One-off iCal export for a single Panchang day.
 *
 * Query params:
 *   d    YYYY-MM-DD date (required)
 *   loc  Human-readable location label (optional; defaults to "Bhubaneswar, IN")
 *   lat  Latitude (optional; defaults to 20.27)
 *   lon  Longitude (optional; defaults to 85.84)
 *
 * Returns: text/calendar with Content-Disposition: attachment
 * Auth-gated: requires Firebase session.
 *
 * Phase: 4C-7 (Item 4)
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'
import { buildDayIcs } from '@/lib/panchang/ics_builder'
import { mapSidecarResponse } from '@/lib/panchang/sidecar_mapper'

const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

// Default location: Bhubaneswar
const DEFAULT_LAT = 20.27
const DEFAULT_LON = 85.84
const DEFAULT_LOC = 'Bhubaneswar, IN'
const DEFAULT_TZ = 330

export async function GET(request: NextRequest) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { searchParams } = request.nextUrl
  const date = searchParams.get('d')
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return res.badRequest('Query param "d" must be a YYYY-MM-DD date')
  }

  const locLabel = searchParams.get('loc') ?? DEFAULT_LOC
  const lat = parseFloat(searchParams.get('lat') ?? String(DEFAULT_LAT))
  const lon = parseFloat(searchParams.get('lon') ?? String(DEFAULT_LON))
  const chartId = searchParams.get('chart_id') ?? undefined

  // Fetch panchang from sidecar
  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  if (!sidecarUrl) return res.sidecarDown()

  let panchangRaw: Record<string, unknown>
  try {
    const sidecarRes = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': SIDECAR_KEY,
      },
      body: JSON.stringify({ date, lat, lon, tz_offset_minutes: DEFAULT_TZ, chart_id: chartId }),
    })
    if (!sidecarRes.ok) {
      return res.internal(`Panchang engine returned HTTP ${sidecarRes.status}`)
    }
    panchangRaw = (await sidecarRes.json()) as Record<string, unknown>
  } catch {
    return res.sidecarDown()
  }

  // Map sidecar response → PanchangDay
  let panchang
  try {
    panchang = mapSidecarResponse(panchangRaw)
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'mapping failed'
    return res.internal(`Failed to parse panchang: ${msg}`)
  }

  // Build ICS
  let icsContent: string
  try {
    icsContent = buildDayIcs(panchang, locLabel)
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'ICS build failed'
    return res.internal(`ICS generation failed: ${msg}`)
  }

  // Return as downloadable ICS file
  return new NextResponse(icsContent, {
    status: 200,
    headers: {
      'Content-Type': 'text/calendar; charset=utf-8',
      'Content-Disposition': `attachment; filename="panchang-${date}.ics"`,
      'Cache-Control': 'private, max-age=3600',
    },
  })
}
