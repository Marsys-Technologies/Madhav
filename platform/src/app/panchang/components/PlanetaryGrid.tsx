'use client'

/**
 * PlanetaryGrid — 9-graha planetary positions grid.
 *
 * Renders Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
 * each with: Sanskrit + English name, sign (Sanskrit + glyph), longitude
 * in DMS within sign, retrograde (R) and combust (C) markers.
 *
 * Layout: 3-column grid on desktop, single-column on mobile.
 * Legend strip below grid: "R = retrograde · C = combust"
 *
 * Planet data from sidecar: dict keyed by lowercase English planet name.
 * Shape: {name, longitude_sidereal, sign_id, sign_name, nakshatra_name,
 *          nakshatra_pada, retrograde, combust}
 *
 * Phase: 4C-4-S2 (Item 2)
 */

import { lonWithinSign, formatDMSShort } from '@/lib/format/dms'
import { getZodiacGlyph } from '@/components/ui/icons/zodiac'

// ── Graha catalog ─────────────────────────────────────────────────────────────

interface GrahaSpec {
  key: string        // key in the planets dict (lowercase English, from sidecar)
  sanskrit: string   // Sanskrit name
  english: string    // English name
}

const GRAHA_ORDER: GrahaSpec[] = [
  { key: 'sun',     sanskrit: 'सूर्य',  english: 'Sun' },
  { key: 'moon',    sanskrit: 'चन्द्र', english: 'Moon' },
  { key: 'mars',    sanskrit: 'मंगल',  english: 'Mars' },
  { key: 'mercury', sanskrit: 'बुध',   english: 'Mercury' },
  { key: 'jupiter', sanskrit: 'गुरु',  english: 'Jupiter' },
  { key: 'venus',   sanskrit: 'शुक्र', english: 'Venus' },
  { key: 'saturn',  sanskrit: 'शनि',   english: 'Saturn' },
  { key: 'rahu',    sanskrit: 'राहु',  english: 'Rahu' },
  { key: 'ketu',    sanskrit: 'केतु',  english: 'Ketu' },
]

// ── Planet state type (from sidecar serialization) ────────────────────────────

interface PlanetStateDict {
  name: string
  longitude_sidereal: number
  sign_id: number
  sign_name: string
  nakshatra_id: number
  nakshatra_name: string
  nakshatra_pada: number
  retrograde: boolean
  combust: boolean
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface PlanetaryGridProps {
  /**
   * planets from PanchangDay — the sidecar serializes this as a dict
   * keyed by lowercase planet name: { sun: PlanetStateDict, ... }
   * The hook maps it as unknown[] | null (permissive); we accept both shapes.
   */
  planets: Record<string, PlanetStateDict> | unknown[] | null | undefined
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function normalizePlanets(
  raw: Record<string, PlanetStateDict> | unknown[] | null | undefined,
): Record<string, PlanetStateDict> {
  if (!raw) return {}
  // Dict shape (from sidecar): {sun: {...}, moon: {...}, ...}
  if (!Array.isArray(raw)) return raw as Record<string, PlanetStateDict>
  // Array shape (fallback — shouldn't happen with current sidecar, but be defensive):
  // [{name: "Sun", ...}, ...]
  const out: Record<string, PlanetStateDict> = {}
  for (const entry of raw) {
    if (entry && typeof entry === 'object' && 'name' in (entry as object)) {
      const ps = entry as PlanetStateDict
      out[ps.name.toLowerCase()] = ps
    }
  }
  return out
}

// ── Sub-components ────────────────────────────────────────────────────────────

function GrahaCard({
  spec,
  ps,
}: {
  spec: GrahaSpec
  ps: PlanetStateDict | undefined
}) {
  const glyph = ps ? getZodiacGlyph(ps.sign_name) : ''
  const withinSign = ps ? lonWithinSign(ps.longitude_sidereal) : null
  const dms = withinSign !== null ? formatDMSShort(withinSign) : null

  return (
    <div
      className="flex flex-col gap-1 rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(28,28,26,0.35)] px-4 py-3"
      role="row"
      aria-label={`${spec.english}${ps ? `: ${ps.sign_name} ${dms}` : ''}`}
    >
      {/* Header row: Sanskrit + English + flags */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="font-serif text-xs shrink-0"
            style={{ color: 'rgba(212,175,55,0.40)' }}
            aria-hidden="true"
          >
            {spec.sanskrit}
          </span>
          <span
            className="text-xs font-semibold uppercase tracking-widest truncate"
            style={{ color: 'rgba(212,175,55,0.65)' }}
          >
            {spec.english}
          </span>
        </div>

        {/* Retrograde + Combust badges */}
        <div className="flex items-center gap-1 shrink-0 ml-2">
          {ps?.retrograde && (
            <span
              className="rounded px-1.5 py-0.5 text-[10px] font-bold"
              style={{ background: 'rgba(220,140,60,0.15)', color: 'rgba(220,140,60,0.90)' }}
              title="Retrograde"
              aria-label="Retrograde"
            >
              R
            </span>
          )}
          {ps?.combust && (
            <span
              className="rounded px-1.5 py-0.5 text-[10px] font-bold"
              style={{ background: 'rgba(220,80,60,0.15)', color: 'rgba(220,80,60,0.90)' }}
              title="Combust"
              aria-label="Combust"
            >
              C
            </span>
          )}
        </div>
      </div>

      {/* Sign + longitude row */}
      {ps ? (
        <div className="flex items-center gap-1.5">
          {glyph && (
            <span
              className="text-base leading-none"
              style={{ color: 'rgba(212,175,55,0.55)' }}
              aria-hidden="true"
            >
              {glyph}
            </span>
          )}
          <span
            className="font-serif text-sm font-medium"
            style={{ color: 'var(--brand-gold-cream, #fce29a)' }}
          >
            {ps.sign_name}
          </span>
          {dms && (
            <span
              className="font-mono text-xs tabular-nums"
              style={{ color: 'rgba(212,175,55,0.55)' }}
            >
              {dms}
            </span>
          )}
        </div>
      ) : (
        <span className="text-xs italic opacity-30">—</span>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function PlanetaryGrid({ planets }: PlanetaryGridProps) {
  const planetMap = normalizePlanets(planets)
  const hasAnyData = Object.keys(planetMap).length > 0

  return (
    <section aria-label="Planetary Positions — 9 Grahas">
      <div
        className="mb-2 px-1"
        style={{ color: 'rgba(212,175,55,0.35)' }}
      >
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em]">
          Planetary Positions
        </span>
      </div>

      {/* 3-column grid on md+, single column on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        {GRAHA_ORDER.map((spec) => (
          <GrahaCard
            key={spec.key}
            spec={spec}
            ps={planetMap[spec.key]}
          />
        ))}
      </div>

      {/* Legend */}
      {hasAnyData && (
        <p
          className="mt-2 text-right text-[10px] opacity-40 pr-1"
          aria-label="Legend: R equals retrograde, C equals combust"
        >
          R = retrograde · C = combust
        </p>
      )}
    </section>
  )
}
