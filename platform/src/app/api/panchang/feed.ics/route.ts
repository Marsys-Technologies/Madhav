/**
 * GET /api/panchang/feed.ics
 *
 * Subscribable rolling iCal feed (today → today+90 days).
 * Auth: HMAC-signed token in ?token= query param (no Firebase session required).
 * Content-Type: text/calendar; charset=utf-8
 *
 * Calendar apps (Google, Apple) subscribe to this URL and poll on their
 * own schedule (typically every 12–24 hours). The feed regenerates on
 * each request — it's stateless except for the revocation check.
 *
 * Token is verified via sign_url.verifyFeedToken; revocation is checked
 * via feed_revocations.isTokenRevoked. Both must pass.
 *
 * Phase: 4C-7 (Item 5)
 */

import { NextRequest, NextResponse } from 'next/server'
import ical, { ICalCalendarMethod } from 'ical-generator'
import { verifyFeedToken } from '@/lib/security/sign_url'
import { isTokenRevoked } from '@/lib/panchang/feed_revocations'
import { mapSidecarResponse } from '@/lib/panchang/sidecar_mapper'

const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

// Location coordinates per location slug (expand as needed)
const LOCATION_COORDS: Record<string, { lat: number; lon: number; label: string }> = {
  bhubaneswar: { lat: 20.27, lon: 85.84, label: 'Bhubaneswar, IN' },
  // Add more as 4C-8 expands location support
}

const DEFAULT_LOCATION = { lat: 20.27, lon: 85.84, label: 'Bhubaneswar, IN' }
const DEFAULT_TZ = 330

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

async function fetchPanchangFromSidecar(
  date: string,
  lat: number,
  lon: number,
): Promise<Record<string, unknown> | null> {
  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  if (!sidecarUrl) return null
  try {
    const r = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': SIDECAR_KEY },
      body: JSON.stringify({ date, lat, lon, tz_offset_minutes: DEFAULT_TZ }),
    })
    if (!r.ok) return null
    return (await r.json()) as Record<string, unknown>
  } catch {
    return null
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const token = searchParams.get('token')

  if (!token) {
    return new NextResponse('Missing token', { status: 401 })
  }

  // 1. Verify HMAC + expiry
  const verifyResult = verifyFeedToken(token)
  if (!verifyResult.ok) {
    const msg =
      verifyResult.reason === 'expired'
        ? 'Feed token has expired. Please generate a new subscription URL.'
        : verifyResult.reason === 'tampered'
          ? 'Invalid token signature.'
          : 'Invalid feed token.'
    return new NextResponse(msg, { status: 401 })
  }

  const { payload } = verifyResult

  // 2. Check revocation list by jti (no PII in token — jti is random)
  const revoked = await isTokenRevoked(payload.jti)
  if (revoked) {
    return new NextResponse('Feed token has been revoked.', { status: 401 })
  }

  // 3. Resolve location
  const locationSlug = payload.location.toLowerCase()
  const locationInfo = LOCATION_COORDS[locationSlug] ?? DEFAULT_LOCATION

  // 4. Build rolling 90-day feed
  const today = todayIso()
  const FEED_DAYS = 90

  // Fetch up to 90 days of panchang — but we're smart about it:
  // For a subscribable feed, we generate ALL 90 days' inauspicious windows
  // (lightweight data) rather than full panchang to keep the response fast.
  // Each day's ICS string is merged into a single calendar.

  // We use a single ical-generator calendar and append events from each day.
  // For performance, we only fetch every day in parallel (sidecar is fast —
  // 4C-6-S1 baseline showed 0.68s for 90-day muhurat range).
  const dateRange: string[] = Array.from({ length: FEED_DAYS }, (_, i) => addDays(today, i))

  const cal = ical({
    prodId: '-//MARSYS-JIS//Panchang Feed//EN',
    name: `MARSYS Panchang Feed — ${locationInfo.label}`,
    method: ICalCalendarMethod.PUBLISH,
    description: `Rolling 90-day Panchang feed for ${locationInfo.label}. Refreshed daily.`,
    // ttl: 86400 seconds = 24 hours (calendar apps respect this for refresh)
    ttl: 86400,
  })

  // Fetch up to 14 days concurrently (to avoid hammering sidecar with 90 calls)
  // and generate inauspicious + special yoga events for each day.
  const BATCH_SIZE = 14

  for (let batchStart = 0; batchStart < dateRange.length; batchStart += BATCH_SIZE) {
    const batch = dateRange.slice(batchStart, batchStart + BATCH_SIZE)
    const results = await Promise.allSettled(
      batch.map((date) => fetchPanchangFromSidecar(date, locationInfo.lat, locationInfo.lon)),
    )

    for (const result of results) {
      if (result.status === 'rejected' || !result.value) continue
      try {
        const panchang = mapSidecarResponse(result.value)
        // Extract inauspicious windows
        if (panchang.timings.inauspicious) {
          const inaus = panchang.timings.inauspicious as Record<
            string,
            { start: string | null; end: string | null } | null
          >
          const inauspKeys = ['rahu_kalam', 'yamagandam', 'gulika_kalam', 'bhadra']
          const labels: Record<string, string> = {
            rahu_kalam: 'Rahu Kalam',
            yamagandam: 'Yamagandam',
            gulika_kalam: 'Gulika Kalam',
            bhadra: 'Bhadra',
          }
          for (const key of inauspKeys) {
            const w = inaus[key]
            if (!w?.start) continue
            const start = new Date(w.start)
            const end = w.end ? new Date(w.end) : new Date(start.getTime() + 90 * 60 * 1000)
            if (isNaN(start.getTime())) continue
            cal.createEvent({
              start,
              end,
              summary: `⚠️ ${labels[key] ?? key} — Avoid`,
              description: `${labels[key] ?? key} inauspicious period.`,
              location: locationInfo.label,
              categories: [{ name: 'MARSYS-Panchang/avoid' }],
            })
          }
        }
        // Extract special yogas
        if (Array.isArray(panchang.special_yogas)) {
          const sunrise = panchang.timings.sunrise_utc ? new Date(panchang.timings.sunrise_utc) : null
          const sunset = panchang.timings.sunset_utc ? new Date(panchang.timings.sunset_utc) : null
          for (const yoga of panchang.special_yogas) {
            const y = yoga as { name?: string; score?: number; start?: string | null; end?: string | null }
            if (!y.name) continue
            const start = y.start ? new Date(y.start) : sunrise
            if (!start || isNaN(start.getTime())) continue
            const end = y.end ? new Date(y.end) : sunset ?? new Date(start.getTime() + 90 * 60 * 1000)
            const stars = '★'.repeat(Math.round(Math.max(1, Math.min(5, y.score ?? 3))))
            cal.createEvent({
              start,
              end,
              summary: `✨ ${y.name} ${stars}`,
              description: `${y.name} — auspicious yoga.`,
              location: locationInfo.label,
              categories: [{ name: 'MARSYS-Panchang/auspicious' }],
            })
          }
        }
      } catch {
        // Skip days where mapping fails — don't abort the whole feed
      }
    }
  }

  const icsContent = cal.toString()

  return new NextResponse(icsContent, {
    status: 200,
    headers: {
      'Content-Type': 'text/calendar; charset=utf-8',
      'Cache-Control': 'public, max-age=43200', // 12 hours
    },
  })
}
