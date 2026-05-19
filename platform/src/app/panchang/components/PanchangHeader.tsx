'use client'

/**
 * PanchangHeader — date picker + location selector + personalise dropdown.
 *
 * State lives in URL query string: ?d=YYYY-MM-DD&loc=bhubaneswar (or &lat=&lon= for custom).
 * chart_id is persisted in both the URL (?chart_id=...) and localStorage
 * (key: panchang.personalise.chart_id) so it survives navigation.
 *
 * Phase: 4C-4-S1 (skeleton); 4C-5 (personalise wiring — Items 4)
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { format, addDays, subDays, parseISO, isValid } from 'date-fns'
import { ChevronLeft, ChevronRight, MapPin, User } from 'lucide-react'
import { useChartList } from '../hooks/useChartList'

// Preset locations (per brief §4 options list)
export const PRESET_LOCATIONS = [
  { id: 'bhubaneswar', label: 'Bhubaneswar', lat: 20.27, lon: 85.84 },
  { id: 'new_delhi',   label: 'New Delhi',   lat: 28.61, lon: 77.21 },
  { id: 'mumbai',      label: 'Mumbai',      lat: 19.08, lon: 72.88 },
  { id: 'bangalore',   label: 'Bangalore',   lat: 12.97, lon: 77.59 },
  { id: 'chennai',     label: 'Chennai',     lat: 13.08, lon: 80.27 },
  { id: 'kolkata',     label: 'Kolkata',     lat: 22.57, lon: 88.36 },
] as const

export type LocationId = (typeof PRESET_LOCATIONS)[number]['id'] | 'custom'

export interface SelectedLocation {
  id: LocationId
  label: string
  lat: number
  lon: number
}

/** Derive selected location from URL params */
export function resolveLocation(searchParams: URLSearchParams): SelectedLocation {
  const locId = searchParams.get('loc') as LocationId | null
  if (locId && locId !== 'custom') {
    const preset = PRESET_LOCATIONS.find((p) => p.id === locId)
    if (preset) return preset
  }
  if (locId === 'custom') {
    const lat = parseFloat(searchParams.get('lat') ?? '')
    const lon = parseFloat(searchParams.get('lon') ?? '')
    if (!isNaN(lat) && !isNaN(lon)) {
      return { id: 'custom', label: 'Custom', lat, lon }
    }
  }
  // Default: Bhubaneswar
  return PRESET_LOCATIONS[0]
}

/** Derive selected date from URL params, defaulting to today */
export function resolveDate(searchParams: URLSearchParams): string {
  const d = searchParams.get('d')
  if (d) {
    const parsed = parseISO(d)
    if (isValid(parsed)) return d
  }
  return format(new Date(), 'yyyy-MM-dd')
}

const PERSONALISE_LS_KEY = 'panchang.personalise.chart_id'

/** Read chart_id from URL params */
export function resolveChartId(searchParams: URLSearchParams): string | null {
  return searchParams.get('chart_id') ?? null
}

interface PanchangHeaderProps {
  /** Server-resolved date (YYYY-MM-DD) — used as initial value before client hydration */
  initialDate: string
  /** Server-resolved location */
  initialLocation: SelectedLocation
  /** Called when chart selection changes so parent can pass chartId to usePanchangDay */
  onChartIdChange?: (chartId: string | null) => void
}

export function PanchangHeader({ initialDate, initialLocation, onChartIdChange }: PanchangHeaderProps) {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Client-side resolved values (after hydration, URL is the source of truth)
  const currentDate = resolveDate(searchParams) || initialDate
  const currentLocation = resolveLocation(searchParams) || initialLocation

  const [showCustomInputs, setShowCustomInputs] = useState(currentLocation.id === 'custom')
  const [customLat, setCustomLat] = useState(String(currentLocation.id === 'custom' ? currentLocation.lat : ''))
  const [customLon, setCustomLon] = useState(String(currentLocation.id === 'custom' ? currentLocation.lon : ''))

  // Chart list for personalise dropdown
  const { charts, isLoading: chartsLoading } = useChartList()

  // Resolve initial chart_id from URL, then localStorage
  const currentChartId = useMemo(() => {
    const fromUrl = resolveChartId(searchParams)
    if (fromUrl) return fromUrl
    if (typeof window !== 'undefined') {
      return localStorage.getItem(PERSONALISE_LS_KEY) ?? null
    }
    return null
  }, [searchParams])

  // Notify parent when chart changes (so usePanchangDay cache key updates)
  useEffect(() => {
    onChartIdChange?.(currentChartId)
  }, [currentChartId, onChartIdChange])

  const parsedDate = useMemo(() => {
    const d = parseISO(currentDate)
    return isValid(d) ? d : new Date()
  }, [currentDate])

  /** Push new URL params, preserving unrelated params */
  const navigate = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString())
      for (const [key, val] of Object.entries(updates)) {
        if (val === null) {
          params.delete(key)
        } else {
          params.set(key, val)
        }
      }
      router.push(`/panchang?${params.toString()}`)
    },
    [router, searchParams],
  )

  function handlePrevDay() {
    navigate({ d: format(subDays(parsedDate, 1), 'yyyy-MM-dd') })
  }

  function handleNextDay() {
    navigate({ d: format(addDays(parsedDate, 1), 'yyyy-MM-dd') })
  }

  function handleDateInput(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value
    if (val && isValid(parseISO(val))) navigate({ d: val })
  }

  function handleLocationChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value as LocationId
    if (id === 'custom') {
      setShowCustomInputs(true)
      navigate({ loc: 'custom', lat: null, lon: null })
    } else {
      setShowCustomInputs(false)
      navigate({ loc: id, lat: null, lon: null })
    }
  }

  function handleCustomApply() {
    const lat = parseFloat(customLat)
    const lon = parseFloat(customLon)
    if (!isNaN(lat) && !isNaN(lon)) {
      navigate({ loc: 'custom', lat: String(lat), lon: String(lon) })
    }
  }

  function handlePersonaliseChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const val = e.target.value
    if (val === 'generic') {
      // Clear personalisation
      localStorage.removeItem(PERSONALISE_LS_KEY)
      navigate({ chart_id: null })
    } else {
      // Persist to localStorage + URL
      localStorage.setItem(PERSONALISE_LS_KEY, val)
      navigate({ chart_id: val })
    }
  }

  const displayDate = format(parsedDate, 'EEE, d MMM yyyy')
  const selectedPersonalise = currentChartId ?? 'generic'

  return (
    <header
      className="border-b border-[rgba(212,175,55,0.12)] bg-[rgba(28,28,26,0.70)] backdrop-blur-sm px-4 py-3"
      aria-label="Panchang controls"
    >
      <div className="mx-auto max-w-4xl flex flex-wrap items-center gap-3">

        {/* Date picker — ◀ date display ▶ */}
        <div
          className="flex items-center gap-1 rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.04)] px-1"
          role="group"
          aria-label="Date navigation"
        >
          <button
            onClick={handlePrevDay}
            aria-label="Previous day"
            className="flex h-8 w-8 items-center justify-center rounded text-[rgba(212,175,55,0.60)] transition-colors hover:bg-[rgba(212,175,55,0.10)] hover:text-[var(--brand-gold)]"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </button>

          <label className="sr-only" htmlFor="panchang-date-input">Select date</label>
          <input
            id="panchang-date-input"
            type="date"
            value={currentDate}
            onChange={handleDateInput}
            className="h-8 bg-transparent text-center text-sm font-medium cursor-pointer border-0 outline-none focus:ring-0 appearance-none"
            style={{ color: 'var(--brand-gold)', minWidth: '9rem', maxWidth: '11rem' }}
            aria-label={displayDate}
          />

          <button
            onClick={handleNextDay}
            aria-label="Next day"
            className="flex h-8 w-8 items-center justify-center rounded text-[rgba(212,175,55,0.60)] transition-colors hover:bg-[rgba(212,175,55,0.10)] hover:text-[var(--brand-gold)]"
          >
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Location selector */}
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 shrink-0" style={{ color: 'rgba(212,175,55,0.55)' }} aria-hidden="true" />
          <label htmlFor="panchang-location" className="sr-only">Location</label>
          <select
            id="panchang-location"
            value={currentLocation.id}
            onChange={handleLocationChange}
            className="h-9 rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 text-sm font-medium appearance-none cursor-pointer outline-none focus:ring-1 focus:ring-[var(--brand-gold)]"
            style={{ color: 'var(--brand-gold)' }}
          >
            {PRESET_LOCATIONS.map((loc) => (
              <option key={loc.id} value={loc.id} style={{ background: '#1c1c1a', color: '#fce29a' }}>
                {loc.label}
              </option>
            ))}
            <option value="custom" style={{ background: '#1c1c1a', color: '#fce29a' }}>
              Custom…
            </option>
          </select>

          {/* Custom lat/lon inputs — only shown when "Custom…" is selected */}
          {showCustomInputs && (
            <div className="flex items-center gap-1.5" role="group" aria-label="Custom coordinates">
              <input
                type="number"
                value={customLat}
                onChange={(e) => setCustomLat(e.target.value)}
                placeholder="Lat"
                step="0.01"
                min="-90"
                max="90"
                aria-label="Latitude"
                className="h-9 w-20 rounded border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-2 text-xs text-center outline-none focus:ring-1 focus:ring-[var(--brand-gold)]"
                style={{ color: 'var(--brand-gold)' }}
              />
              <input
                type="number"
                value={customLon}
                onChange={(e) => setCustomLon(e.target.value)}
                placeholder="Lon"
                step="0.01"
                min="-180"
                max="180"
                aria-label="Longitude"
                className="h-9 w-20 rounded border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-2 text-xs text-center outline-none focus:ring-1 focus:ring-[var(--brand-gold)]"
                style={{ color: 'var(--brand-gold)' }}
              />
              <button
                onClick={handleCustomApply}
                className="h-9 rounded-lg border border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.08)] px-3 text-xs font-medium transition-colors hover:bg-[rgba(212,175,55,0.14)]"
                style={{ color: 'var(--brand-gold)' }}
              >
                Apply
              </button>
            </div>
          )}
        </div>

        {/* Personalise dropdown — wired in 4C-5; chart_id in URL + localStorage */}
        <div className="ml-auto flex items-center gap-2">
          <User className="h-4 w-4 shrink-0" style={{ color: 'rgba(212,175,55,0.55)' }} aria-hidden="true" />
          <label htmlFor="panchang-personalise" className="sr-only">Personalise view</label>
          <select
            id="panchang-personalise"
            value={selectedPersonalise}
            aria-label="Personalise panchang view"
            disabled={chartsLoading}
            className="h-9 rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 text-sm font-medium appearance-none cursor-pointer outline-none focus:ring-1 focus:ring-[var(--brand-gold)] disabled:opacity-40 disabled:cursor-wait"
            style={{ color: 'var(--brand-gold)' }}
            onChange={handlePersonaliseChange}
          >
            <option value="generic" style={{ background: '#1c1c1a', color: '#fce29a' }}>
              Generic Panchang
            </option>
            {charts.length > 0 && (
              <option disabled style={{ background: '#1c1c1a', color: 'rgba(252,226,154,0.35)' }}>
                ── Personalise ──
              </option>
            )}
            {charts.map((chart) => (
              <option
                key={chart.id}
                value={chart.id}
                style={{ background: '#1c1c1a', color: '#fce29a' }}
              >
                {chart.name} ({chart.birth_date})
              </option>
            ))}
            {currentChartId && (
              <option disabled style={{ background: '#1c1c1a', color: 'rgba(252,226,154,0.35)' }}>
                ───────────
              </option>
            )}
            {currentChartId && (
              <option value="generic" style={{ background: '#1c1c1a', color: 'rgba(252,226,154,0.65)' }}>
                ✕ Clear personalisation
              </option>
            )}
          </select>
        </div>
      </div>
    </header>
  )
}
