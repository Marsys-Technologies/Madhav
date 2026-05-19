'use client'

/**
 * MuhuratFinderModal — full Muhurat Finder UI surface.
 *
 * Triggered by ActionBar's "Find Muhurat" button.
 * Form fields:
 *   - Event dropdown (6 MVP events, Sanskrit + English label)
 *   - Date range: date_from (default: today) + date_to (default: today + 90 days)
 *   - Location (auto-filled from page; editable)
 *   - Personalise checkbox (auto-checked if chartId present)
 *
 * Submits to /api/compute/muhurat via useMuhuratFinder hook.
 * Renders MuhuratResultsList inside a scrollable results panel.
 *
 * Phase: 4C-6-S3 (Items 1, 5, 6)
 */

import { useState, useCallback } from 'react'
import { X, Search } from 'lucide-react'
import { useMuhuratFinder } from '../hooks/useMuhuratFinder'
import { MuhuratResultsList } from './MuhuratResultsList'

// ── MVP event set ─────────────────────────────────────────────────────────────

export const MVP_EVENTS = [
  { key: 'vivah',              label: 'Vivah (Marriage)' },
  { key: 'griha_pravesh',      label: 'Griha Pravesh (Housewarming)' },
  { key: 'vyapara',            label: 'Vyapara (Business Start)' },
  { key: 'yatra',              label: 'Yatra (Travel)' },
  { key: 'property_purchase',  label: 'Property / Vehicle Purchase' },
  { key: 'mantra_initiation',  label: 'Mantra Initiation / Puja' },
] as const

// ── Helpers ───────────────────────────────────────────────────────────────────

/** ISO date for today (YYYY-MM-DD) in local time */
function todayISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Add N days to an ISO date string */
function addDaysISO(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00`)
  d.setDate(d.getDate() + days)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface MuhuratFinderModalProps {
  onClose: () => void
  /** Current page location — pre-filled into the modal */
  lat: number
  lon: number
  tzOffsetMinutes?: number
  /** If present, personalise checkbox defaults to checked */
  chartId?: string | null
}

// ── Component ─────────────────────────────────────────────────────────────────

export function MuhuratFinderModal({
  onClose,
  lat,
  lon,
  tzOffsetMinutes = 330,
  chartId,
}: MuhuratFinderModalProps) {
  const today = todayISO()

  // Form state
  const [event, setEvent] = useState<string>(MVP_EVENTS[0].key)
  const [dateFrom, setDateFrom] = useState(today)
  const [dateTo, setDateTo] = useState(addDaysISO(today, 90))
  const [customLat, setCustomLat] = useState(String(lat))
  const [customLon, setCustomLon] = useState(String(lon))
  const [personalise, setPersonalise] = useState(Boolean(chartId))
  const [hasSubmitted, setHasSubmitted] = useState(false)

  const { windows, isLoading, error, search } = useMuhuratFinder()

  // Derived validation
  const latNum = parseFloat(customLat)
  const lonNum = parseFloat(customLon)
  const latValid = !isNaN(latNum) && latNum >= -90 && latNum <= 90
  const lonValid = !isNaN(lonNum) && lonNum >= -180 && lonNum <= 180
  const dateValid = dateFrom <= dateTo
  const daysDiff = Math.round(
    (new Date(dateTo).getTime() - new Date(dateFrom).getTime()) / 86_400_000
  )
  const rangeValid = daysDiff >= 0 && daysDiff <= 89
  const canSubmit = latValid && lonValid && dateValid && rangeValid && !isLoading

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (!canSubmit) return
      setHasSubmitted(true)
      await search({
        event,
        date_from: dateFrom,
        date_to: dateTo,
        lat: latNum,
        lon: lonNum,
        tz_offset_minutes: tzOffsetMinutes,
        chart_id: personalise && chartId ? chartId : null,
        top_n: 10,
      })
    },
    [canSubmit, search, event, dateFrom, dateTo, latNum, lonNum, tzOffsetMinutes, personalise, chartId]
  )

  // Trap focus: close on backdrop click
  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  const eventLabel = MVP_EVENTS.find((ev) => ev.key === event)?.label ?? event

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Muhurat Finder"
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto py-8 px-4"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/65 backdrop-blur-sm" aria-hidden="true" />

      {/* Panel */}
      <div
        className="relative z-10 w-full max-w-lg rounded-2xl border border-[rgba(212,175,55,0.20)] bg-[rgba(18,18,16,0.97)] shadow-2xl"
        style={{ boxShadow: '0 0 60px rgba(212,175,55,0.08)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[rgba(212,175,55,0.12)] px-5 py-4">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 shrink-0" style={{ color: 'var(--brand-gold)' }} aria-hidden="true" />
            <h2 className="font-serif text-lg" style={{ color: 'var(--brand-gold)' }}>
              Muhurat Finder
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Muhurat Finder"
            className="flex h-7 w-7 items-center justify-center rounded-full transition-colors hover:bg-[rgba(212,175,55,0.10)]"
            style={{ color: 'rgba(212,175,55,0.45)' }}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 pt-4 pb-5 flex flex-col gap-4">
          {/* Event selector */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="muhurat-event" className="text-xs font-medium text-muted-foreground">
              Event
            </label>
            <select
              id="muhurat-event"
              value={event}
              onChange={(e) => setEvent(e.target.value)}
              disabled={isLoading}
              className="w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 py-2 text-sm outline-none focus:border-[rgba(212,175,55,0.50)] focus:ring-1 focus:ring-[rgba(212,175,55,0.30)] disabled:opacity-50"
              style={{ color: 'var(--brand-gold)' }}
            >
              {MVP_EVENTS.map((ev) => (
                <option key={ev.key} value={ev.key}>
                  {ev.label}
                </option>
              ))}
            </select>
          </div>

          {/* Date range */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="muhurat-date-from" className="text-xs font-medium text-muted-foreground">
                From
              </label>
              <input
                id="muhurat-date-from"
                type="date"
                value={dateFrom}
                min={today}
                onChange={(e) => {
                  setDateFrom(e.target.value)
                  // Push dateTo if it's now before dateFrom
                  if (e.target.value > dateTo) {
                    setDateTo(addDaysISO(e.target.value, 30))
                  }
                }}
                disabled={isLoading}
                className="w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 py-2 text-sm outline-none focus:border-[rgba(212,175,55,0.50)] focus:ring-1 focus:ring-[rgba(212,175,55,0.30)] disabled:opacity-50"
                style={{ color: 'rgba(212,175,55,0.80)' }}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="muhurat-date-to" className="text-xs font-medium text-muted-foreground">
                To
              </label>
              <input
                id="muhurat-date-to"
                type="date"
                value={dateTo}
                min={dateFrom}
                onChange={(e) => setDateTo(e.target.value)}
                disabled={isLoading}
                className="w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 py-2 text-sm outline-none focus:border-[rgba(212,175,55,0.50)] focus:ring-1 focus:ring-[rgba(212,175,55,0.30)] disabled:opacity-50"
                style={{ color: 'rgba(212,175,55,0.80)' }}
              />
            </div>
          </div>

          {/* Date range validation hint */}
          {!rangeValid && dateFrom <= dateTo && (
            <p className="text-xs" style={{ color: 'rgba(220,80,60,0.85)' }}>
              Range exceeds 90 days — please shorten it.
            </p>
          )}

          {/* Location */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="muhurat-lat" className="text-xs font-medium text-muted-foreground">
                Latitude
              </label>
              <input
                id="muhurat-lat"
                type="number"
                step="0.01"
                min="-90"
                max="90"
                value={customLat}
                onChange={(e) => setCustomLat(e.target.value)}
                disabled={isLoading}
                placeholder="20.27"
                className="w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 py-2 text-sm outline-none focus:border-[rgba(212,175,55,0.50)] focus:ring-1 focus:ring-[rgba(212,175,55,0.30)] disabled:opacity-50"
                style={{ color: 'rgba(212,175,55,0.80)' }}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="muhurat-lon" className="text-xs font-medium text-muted-foreground">
                Longitude
              </label>
              <input
                id="muhurat-lon"
                type="number"
                step="0.01"
                min="-180"
                max="180"
                value={customLon}
                onChange={(e) => setCustomLon(e.target.value)}
                disabled={isLoading}
                placeholder="85.84"
                className="w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.80)] px-3 py-2 text-sm outline-none focus:border-[rgba(212,175,55,0.50)] focus:ring-1 focus:ring-[rgba(212,175,55,0.30)] disabled:opacity-50"
                style={{ color: 'rgba(212,175,55,0.80)' }}
              />
            </div>
          </div>

          {/* Personalise checkbox */}
          <label className="flex items-start gap-3 cursor-pointer">
            <div className="relative mt-0.5">
              <input
                type="checkbox"
                id="muhurat-personalise"
                checked={personalise}
                onChange={(e) => setPersonalise(e.target.checked)}
                disabled={isLoading || !chartId}
                className="sr-only"
              />
              <div
                className="h-4 w-4 rounded border flex items-center justify-center transition-colors"
                style={{
                  borderColor: personalise && chartId
                    ? 'rgba(212,175,55,0.70)'
                    : 'rgba(212,175,55,0.25)',
                  background: personalise && chartId
                    ? 'rgba(212,175,55,0.15)'
                    : 'rgba(28,28,26,0.80)',
                }}
                onClick={() => {
                  if (!isLoading && chartId) setPersonalise((v) => !v)
                }}
                role="checkbox"
                aria-checked={personalise}
                aria-labelledby="muhurat-personalise-label"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === ' ' && !isLoading && chartId) {
                    e.preventDefault()
                    setPersonalise((v) => !v)
                  }
                }}
              >
                {personalise && chartId && (
                  <span style={{ color: 'var(--brand-gold)', fontSize: '10px', lineHeight: 1 }}>✓</span>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-0.5">
              <span
                id="muhurat-personalise-label"
                className="text-sm font-medium"
                style={{ color: chartId ? 'rgba(212,175,55,0.80)' : 'rgba(212,175,55,0.35)' }}
              >
                Personalise for my chart
              </span>
              <span className="text-xs text-muted-foreground">
                {chartId
                  ? 'Applies Tara Bala + Chandra Bala overlay from your birth chart'
                  : 'Select a chart on the Panchang page to enable personalisation'}
              </span>
            </div>
          </label>

          {/* Submit */}
          <button
            type="submit"
            disabled={!canSubmit}
            className="mt-1 w-full rounded-xl border py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed"
            style={{
              color: canSubmit ? 'var(--brand-gold)' : 'rgba(212,175,55,0.30)',
              borderColor: canSubmit ? 'rgba(212,175,55,0.40)' : 'rgba(212,175,55,0.12)',
              background: canSubmit ? 'rgba(212,175,55,0.10)' : 'rgba(212,175,55,0.03)',
            }}
          >
            {isLoading ? 'Searching…' : 'Find Muhurat'}
          </button>
        </form>

        {/* Results panel — shown after first submit */}
        {hasSubmitted && (
          <div className="border-t border-[rgba(212,175,55,0.10)] px-5 pb-6 pt-4 max-h-[60vh] overflow-y-auto">
            <p className="mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Results for {eventLabel}
            </p>
            <MuhuratResultsList
              windows={windows}
              isLoading={isLoading}
              error={error}
              event={event}
              tzOffsetMinutes={tzOffsetMinutes}
            />
          </div>
        )}
      </div>
    </div>
  )
}
