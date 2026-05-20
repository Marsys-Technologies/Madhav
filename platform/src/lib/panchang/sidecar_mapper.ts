/**
 * sidecar_mapper.ts — Server-safe mapper for sidecar Panchang responses.
 *
 * Extracted from usePanchangDay.ts (client module) so API routes and
 * server components can import mapSidecarResponse without pulling in
 * React hooks or 'use client' boundaries.
 *
 * Types are re-exported from usePanchangDay via type-only imports to
 * keep a single source of truth.
 *
 * Phase: 4C-7 (Item 4 — needed for ICS route)
 */

import type {
  PanchangDay,
  PanchangAngas,
  NativeContext,
} from '@/app/panchang/hooks/usePanchangDay'

export type { PanchangDay, PanchangAngas, NativeContext }

/**
 * Map a raw sidecar JSON response to a typed PanchangDay object.
 * Mirrors the identically-named function in usePanchangDay.ts; kept
 * in sync manually — if the type changes, update both files.
 */
export function mapSidecarResponse(raw: Record<string, unknown>): PanchangDay {
  const panchang = (raw['panchang'] ?? raw) as Record<string, unknown>
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
