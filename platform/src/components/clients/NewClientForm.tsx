'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useJsApiLoader } from '@react-google-maps/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { derivePreferredName, parseBirthDateDisplay } from './form_schema'
import { formatDate } from '@/lib/utils/date'
import { isGoogleMapsKeyConfigured, type PlacesResult } from './usePlacesAutocomplete'
import { cn } from '@/lib/utils'

// ─── Ayanamsha options ────────────────────────────────────────────────────────

export const AYANAMSHA_OPTIONS = [
  { id: 'lahiri',          label: 'Lahiri',      sub: 'Chitrapaksha'  },
  { id: 'true_chitra',     label: 'True Chitra', sub: 'Revati paksha' },
  { id: 'kp',              label: 'KP',          sub: 'Krishnamurti'  },
  { id: 'raman',           label: 'Raman',       sub: 'B.V. Raman'    },
  { id: 'surya_siddhanta', label: 'Surya Sidd.', sub: 'Classical drik'},
] as const

export type AyanamshaId = (typeof AYANAMSHA_OPTIONS)[number]['id']

// ─── Timezones ────────────────────────────────────────────────────────────────

export const TIMEZONES = [
  { value: 'Asia/Kolkata',        label: 'Asia/Kolkata (UTC+5:30)',      offset: 5.5  },
  { value: 'UTC',                 label: 'UTC (UTC+0)',                   offset: 0    },
  { value: 'Asia/Colombo',        label: 'Asia/Colombo (UTC+5:30)',      offset: 5.5  },
  { value: 'Asia/Kathmandu',      label: 'Asia/Kathmandu (UTC+5:45)',    offset: 5.75 },
  { value: 'Asia/Dhaka',          label: 'Asia/Dhaka (UTC+6)',           offset: 6    },
  { value: 'Asia/Dubai',          label: 'Asia/Dubai (UTC+4)',           offset: 4    },
  { value: 'Asia/Singapore',      label: 'Asia/Singapore (UTC+8)',       offset: 8    },
  { value: 'Asia/Tokyo',          label: 'Asia/Tokyo (UTC+9)',           offset: 9    },
  { value: 'America/New_York',    label: 'America/New_York (UTC-5)',     offset: -5   },
  { value: 'America/Chicago',     label: 'America/Chicago (UTC-6)',      offset: -6   },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (UTC-8)', offset: -8   },
  { value: 'Europe/London',       label: 'Europe/London (UTC+0)',        offset: 0    },
  { value: 'Europe/Berlin',       label: 'Europe/Berlin (UTC+1)',        offset: 1    },
  { value: 'Australia/Sydney',    label: 'Australia/Sydney (UTC+10)',    offset: 10   },
] as const

// ─── State types ──────────────────────────────────────────────────────────────

interface FormState {
  full_name: string
  preferred_name: string
  gender: 'M' | 'F' | 'O' | 'unknown' | ''
  birth_date: string          // YYYY-MM-DD (API wire format)
  birth_date_display: string  // dd-MMM-yyyy (user-facing)
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_id: string
  tz_offset: string
  ayanamshas: AyanamshaId[]
  places_resolved: boolean
}

interface FormErrors {
  full_name?: string
  gender?: string
  birth_date?: string
  birth_time?: string
  birth_place?: string
  latitude?: string
  longitude?: string
  tz_offset?: string
  ayanamshas?: string
  api?: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayIso(): string {
  return new Date().toISOString().split('T')[0]
}

function offsetFromTimezoneId(tzId: string): string {
  const found = TIMEZONES.find((t) => t.value === tzId)
  return found ? String(found.offset) : ''
}

function timezoneFromOffset(
  offsetMinutes: number | null,
): { timezone_id: string; tz_offset: string } {
  if (offsetMinutes == null) return { timezone_id: 'Asia/Kolkata', tz_offset: '5.5' }
  const offsetHours = offsetMinutes / 60
  const exact = TIMEZONES.find((tz) => tz.offset === offsetHours)
  if (exact) return { timezone_id: exact.value, tz_offset: String(exact.offset) }
  const nearest = TIMEZONES.reduce((a, b) =>
    Math.abs(a.offset - offsetHours) < Math.abs(b.offset - offsetHours) ? a : b,
  )
  return { timezone_id: nearest.value, tz_offset: String(offsetHours) }
}

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {}

  if (!form.full_name.trim()) {
    errors.full_name = 'Full name is required.'
  } else if (form.full_name.trim().length > 200) {
    errors.full_name = 'Full name must be 200 characters or fewer.'
  }

  if (!form.gender) errors.gender = 'Please select a gender.'

  if (!form.birth_date) {
    errors.birth_date = form.birth_date_display
      ? 'Enter date as DD-MMM-YYYY, e.g. 05-Feb-1984.'
      : 'Birth date is required.'
  } else if (form.birth_date < '1900-01-01') {
    errors.birth_date = 'Birth date must be on or after 1900-01-01.'
  } else if (form.birth_date > todayIso()) {
    errors.birth_date = 'Birth date cannot be in the future.'
  }

  if (!form.birth_time) errors.birth_time = 'Birth time is required.'
  if (!form.birth_place.trim()) errors.birth_place = 'Birth place is required.'

  const lat = parseFloat(form.latitude)
  if (form.latitude === '') errors.latitude = 'Latitude is required.'
  else if (isNaN(lat) || lat < -90 || lat > 90)
    errors.latitude = 'Latitude must be between -90 and 90.'

  const lng = parseFloat(form.longitude)
  if (form.longitude === '') errors.longitude = 'Longitude is required.'
  else if (isNaN(lng) || lng < -180 || lng > 180)
    errors.longitude = 'Longitude must be between -180 and 180.'

  const tz = parseFloat(form.tz_offset)
  if (form.tz_offset === '') errors.tz_offset = 'Timezone offset is required.'
  else if (isNaN(tz) || tz < -14 || tz > 14)
    errors.tz_offset = 'Timezone offset must be between -14 and 14.'

  if (form.ayanamshas.length === 0)
    errors.ayanamshas = 'At least one ayanamsha must be selected.'

  return errors
}

// ─── Shared dark-well input class ─────────────────────────────────────────────

function darkInputCls(hasError?: boolean): string {
  return cn(
    'w-full h-9 rounded-md border px-3 py-1 text-sm transition-colors duration-150',
    'focus:outline-none focus:ring-1',
    hasError
      ? 'border-destructive focus:ring-destructive'
      : 'focus:ring-brand-gold',
  )
}

// ─── Select wrapper — adds custom ▼ arrow after appearance-none ───────────────

function SelectWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative">
      {children}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-brand-gold/50 text-[10px]"
      >
        ▼
      </span>
    </div>
  )
}

// ─── PlaceAutocompleteElement (W9) ────────────────────────────────────────────
// Replaces google.maps.places.Autocomplete (dead for post-2025-03-01 keys).
// Uses importLibrary('places') to obtain PlaceAutocompleteElement, the current
// API Google directs new customers to.

function PlacesAutocompleteNew({
  hasError,
  onTextChange,
  onBlur,
  onPlaceResolved,
  onLoadError,
}: {
  hasError: boolean
  onTextChange: (v: string) => void
  onBlur: () => void
  onPlaceResolved: (r: PlacesResult) => void
  onLoadError: () => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Load core Maps JS API — no libraries needed; importLibrary handles places.
  const { isLoaded, loadError } = useJsApiLoader({
    id: 'gmaps-places',
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? '',
  })

  useEffect(() => {
    if (loadError) onLoadError()
  }, [loadError, onLoadError])

  useEffect(() => {
    const container = containerRef.current
    if (!isLoaded || !container) return
    // Guard against double-mount (strict mode / dep array changes).
    if (container.querySelector('gmp-placeautocomplete')) return

    let cancelled = false

    void (async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const lib = await (window.google.maps as any).importLibrary('places')
        if (cancelled || !container) return
        if (container.querySelector('gmp-placeautocomplete')) return

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const el: HTMLElement = new (lib as any).PlaceAutocompleteElement({
          requestedLanguage: 'en',
        })
        el.style.width = '100%'

        // CSS custom properties cascade through shadow DOM to theme the widget.
        el.style.setProperty('--gmpx-color-surface',            'oklch(0.05 0.005 70)')
        el.style.setProperty('--gmpx-color-on-surface',         'oklch(0.92 0.075 88)')
        el.style.setProperty('--gmpx-color-on-surface-variant', 'oklch(0.58 0.025 80)')
        el.style.setProperty('--gmpx-color-primary',            'oklch(0.78 0.13 80)')
        el.style.setProperty('--gmpx-color-outline',            'oklch(0.78 0.13 80 / 0.35)')
        el.style.setProperty('--gmpx-font-family-base',         'var(--font-sans, sans-serif)')
        el.style.setProperty('--gmpx-font-size-base',           '0.875rem')

        // Sync typed text back so birth_place field tracks the user's input.
        el.addEventListener('input', () => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onTextChange((el as any).value ?? '')
        })

        // On selection, fetch fields and resolve lat/lng/timezone.
        el.addEventListener('gmp-placeselect', async (event: Event) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const place = (event as any).place
          if (!place) return
          try {
            await place.fetchFields({
              fields: ['location', 'formattedAddress', 'displayName', 'utcOffsetMinutes'],
            })
            const loc = place.location
            if (!loc) { onLoadError(); return }
            onPlaceResolved({
              description: place.formattedAddress ?? place.displayName ?? '',
              lat: loc.lat(),
              lng: loc.lng(),
              utcOffsetMinutes: place.utcOffsetMinutes ?? null,
            })
          } catch {
            onLoadError()
          }
        })

        container.appendChild(el)
      } catch {
        if (!cancelled) onLoadError()
      }
    })()

    return () => { cancelled = true }
  }, [isLoaded, onPlaceResolved, onTextChange, onLoadError])

  // Stable loading placeholder — same height as real input, brand-styled.
  if (!isLoaded && !loadError) {
    return (
      <input
        disabled
        placeholder="Loading…"
        aria-label="Birth place loading"
        className={darkInputCls(hasError)}
        style={{
          background: 'var(--brand-charcoal-deep)',
          color: 'oklch(0.58 0.025 80)',
          borderColor: hasError ? undefined : 'var(--brand-gold-hairline)',
        }}
      />
    )
  }

  // React onBlur (focusout) catches events bubbling from the shadow DOM
  // so we don't need a manual addEventListener on the web component element.
  return (
    <div
      ref={containerRef}
      onBlur={onBlur}
      className={cn(
        'w-full rounded-md overflow-hidden min-h-[36px]',
        hasError
          ? 'ring-1 ring-destructive border border-destructive'
          : 'border border-[var(--brand-gold-hairline)]',
      )}
    />
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

export function NewClientForm() {
  const router = useRouter()
  const googleMapsConfigured = isGoogleMapsKeyConfigured()

  const [form, setForm] = useState<FormState>({
    full_name: '',
    preferred_name: '',
    gender: '',
    birth_date: '',
    birth_date_display: '',
    birth_time: '',
    birth_place: '',
    latitude: '',
    longitude: '',
    timezone_id: 'Asia/Kolkata',
    tz_offset: '5.5',
    ayanamshas: AYANAMSHA_OPTIONS.map((o) => o.id),
    places_resolved: false,
  })

  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState<'save' | 'build' | null>(null)
  // R2.2: collapsed by default; auto-expands when key absent or Places fails.
  const [manualOpen, setManualOpen] = useState(!googleMapsConfigured)

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  function handleTimezoneChange(tzId: string) {
    setForm((prev) => ({ ...prev, timezone_id: tzId, tz_offset: offsetFromTimezoneId(tzId) }))
    setErrors((prev) => ({ ...prev, tz_offset: undefined }))
  }

  function toggleAyanamsha(id: AyanamshaId) {
    setForm((prev) => {
      const next = prev.ayanamshas.includes(id)
        ? prev.ayanamshas.filter((a) => a !== id)
        : [...prev.ayanamshas, id]
      return { ...prev, ayanamshas: next }
    })
    setErrors((prev) => ({ ...prev, ayanamshas: undefined }))
  }

  // Stable callbacks for PlacesAutocompleteNew (useEffect deps must be stable).

  const handleBirthPlaceBlur = useCallback(() => {
    // Functional update reads current state without stale closure.
    setForm((prev) => {
      if (prev.birth_place.trim() && !prev.places_resolved) setManualOpen(true)
      return prev
    })
  }, [])

  const handleBirthPlaceTextChange = useCallback((v: string) => {
    setForm((prev) => ({
      ...prev,
      birth_place: v,
      places_resolved: v.trim() ? prev.places_resolved : false,
    }))
    setErrors((prev) => ({ ...prev, birth_place: undefined }))
  }, [])

  const handlePlaceResolved = useCallback((result: PlacesResult) => {
    const tz = timezoneFromOffset(result.utcOffsetMinutes)
    setForm((prev) => ({
      ...prev,
      birth_place: result.description,
      latitude: String(result.lat),
      longitude: String(result.lng),
      timezone_id: tz.timezone_id,
      tz_offset: tz.tz_offset,
      places_resolved: true,
    }))
    setManualOpen(false)
    setErrors((prev) => ({
      ...prev,
      birth_place: undefined,
      latitude: undefined,
      longitude: undefined,
    }))
  }, [])

  const handlePlacesLoadError = useCallback(() => {
    setManualOpen(true)
  }, [])

  function handleDateDisplayChange(raw: string) {
    const parsed = parseBirthDateDisplay(raw)
    setForm((prev) => ({ ...prev, birth_date_display: raw, birth_date: parsed ?? '' }))
    if (parsed) setErrors((prev) => ({ ...prev, birth_date: undefined }))
  }

  function handleDateBlur() {
    if (form.birth_date_display && !form.birth_date) {
      setErrors((prev) => ({
        ...prev,
        birth_date: 'Enter date as DD-MMM-YYYY, e.g. 05-Feb-1984.',
      }))
    } else if (form.birth_date) {
      setForm((prev) => ({ ...prev, birth_date_display: formatDate(prev.birth_date) }))
    }
  }

  // ── Submit ───────────────────────────────────────────────────────────────

  async function submit(action: 'save' | 'build') {
    const validationErrors = validate(form)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    setSubmitting(action)
    setErrors({})

    try {
      const res = await fetch('/api/clients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.full_name.trim(),
          preferred_name: derivePreferredName(form.full_name, form.preferred_name),
          gender: form.gender,
          birth_date: form.birth_date,
          birth_time: form.birth_time,
          birth_place: form.birth_place.trim(),
          lat: parseFloat(form.latitude),
          lon: parseFloat(form.longitude),
          tz_offset: parseFloat(form.tz_offset),
          timezone_id: form.timezone_id || undefined,
          ayanamshas: form.ayanamshas,
        }),
      })

      const data = await res.json()

      if (res.status === 422) {
        const fieldMap: Record<string, keyof FormErrors> = {
          lat: 'latitude', lon: 'longitude', tz_offset: 'tz_offset',
          name: 'full_name', birth_date: 'birth_date', birth_time: 'birth_time',
          birth_place: 'birth_place', gender: 'gender', ayanamshas: 'ayanamshas',
        }
        const newErrors: FormErrors = {}
        for (const err of (data.errors ?? []) as { field: string; message: string }[]) {
          const key = (fieldMap[err.field] ?? 'api') as keyof FormErrors
          newErrors[key] = err.message
        }
        setErrors(newErrors)
        return
      }

      if (res.status === 429) {
        const mins = data.retry_after ? Math.ceil(data.retry_after / 60) : '?'
        setErrors({ api: `Rate limit hit — try again in ${mins} minute(s).` })
        return
      }

      if (!res.ok) {
        setErrors({ api: data?.error ?? 'Failed to create chart.' })
        return
      }

      if (action === 'build') {
        router.push(data.redirect_url ?? `/clients/${data.chart_id}/build`)
      } else {
        router.push(`/dashboard?chart_created=${data.chart_id}`)
      }
    } catch {
      setErrors({ api: 'Network error — please check your connection and try again.' })
    } finally {
      setSubmitting(null)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  const isInFlight = submitting !== null
  const nodeCount = form.ayanamshas.length * 28

  // Dark-well style shared across inputs and selects (R2.5).
  const wellStyle = {
    background: 'var(--brand-charcoal-deep)',
    color: 'var(--brand-gold-cream)',
    borderColor: 'var(--brand-gold-hairline)',
  }
  const wellStyleError = {
    background: 'var(--brand-charcoal-deep)',
    color: 'var(--brand-gold-cream)',
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4 py-6"
      style={{
        // R2.5: page canvas = near-black brand-ink
        background: 'var(--brand-ink)',
        // Re-point muted-foreground to a warm readable grey on near-black.
        '--muted-foreground': 'oklch(0.58 0.025 80)',
      } as React.CSSProperties}
    >
      {/* ── Back link ──────────────────────────────────────────────────── */}
      <div className="w-full max-w-[540px] mb-2">
        <Link
          href="/dashboard"
          aria-label="Back to dashboard"
          className="bt-body text-muted-foreground hover:underline"
        >
          ← Back to dashboard
        </Link>
      </div>

      {/* ── Title ──────────────────────────────────────────────────────── */}
      <div data-testid="form-title" className="text-center mb-4">
        <h1 className="bt-display text-brand-gold-cream">
          <span className="opacity-55 text-brand-gold font-serif mr-1" aria-hidden="true">॥</span>
          Nava Jātaka
          <span className="opacity-55 text-brand-gold font-serif ml-1" aria-hidden="true">॥</span>
        </h1>
        <p className="bt-body text-muted-foreground mt-0.5">New Chart</p>
      </div>

      {/* ── Centered card (R2.1) ───────────────────────────────────────── */}
      <div
        className="w-full max-w-[540px] rounded-xl flex flex-col gap-4 p-6"
        style={{
          // R2.5: card = brand-charcoal, gold-hairline border
          background: 'var(--brand-charcoal)',
          border: '1px solid var(--brand-gold-hairline)',
        }}
      >

        {/* Full name ─────────────────────────────────────────────────── */}
        <div className="flex flex-col gap-1">
          <Label htmlFor="full_name" className="bt-label bt-label-upper text-brand-gold/70">
            Full name *
          </Label>
          <Input
            id="full_name"
            type="text"
            placeholder="e.g. Abhisek Mohanty"
            value={form.full_name}
            maxLength={200}
            aria-required="true"
            aria-label="Full name"
            aria-invalid={!!errors.full_name}
            className={cn(darkInputCls(!!errors.full_name), 'placeholder:text-brand-gold/25')}
            style={errors.full_name ? wellStyleError : wellStyle}
            onChange={(e) => setField('full_name', e.target.value)}
          />
          {errors.full_name && (
            <p role="alert" className="bt-label text-destructive">{errors.full_name}</p>
          )}
        </div>

        {/* Preferred name + Gender ────────────────────────────────────── */}
        <div className="grid gap-3" style={{ gridTemplateColumns: '1fr 148px' }}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="preferred_name" className="bt-label bt-label-upper text-brand-gold/70">
              Preferred name
            </Label>
            <Input
              id="preferred_name"
              type="text"
              placeholder="First word of full name"
              value={form.preferred_name}
              maxLength={100}
              className="placeholder:text-brand-gold/25"
              style={wellStyle}
              onChange={(e) => setField('preferred_name', e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="gender" className="bt-label bt-label-upper text-brand-gold/70">
              Gender *
            </Label>
            {/* R2.4: brand-styled select with dark well + custom arrow */}
            <SelectWrapper>
              <select
                id="gender"
                value={form.gender}
                aria-invalid={!!errors.gender}
                className={cn(darkInputCls(!!errors.gender), 'appearance-none pr-7 cursor-pointer')}
                style={
                  errors.gender
                    ? wellStyleError
                    : { ...wellStyle, color: form.gender ? 'var(--brand-gold-cream)' : 'oklch(0.58 0.025 80)' }
                }
                onChange={(e) => setField('gender', e.target.value as FormState['gender'])}
              >
                <option value="" style={{ background: 'var(--brand-charcoal)' }}>— select —</option>
                <option value="unknown" style={{ background: 'var(--brand-charcoal)' }}>Prefer not to say</option>
                <option value="M" style={{ background: 'var(--brand-charcoal)' }}>Male</option>
                <option value="F" style={{ background: 'var(--brand-charcoal)' }}>Female</option>
                <option value="O" style={{ background: 'var(--brand-charcoal)' }}>Other</option>
              </select>
            </SelectWrapper>
            {errors.gender && (
              <p role="alert" className="bt-label text-destructive">{errors.gender}</p>
            )}
          </div>
        </div>

        {/* Birth place ────────────────────────────────────────────────── */}
        <div className="flex flex-col gap-1">
          <Label htmlFor="birth_place" className="bt-label bt-label-upper text-brand-gold/70">
            Birth place *
          </Label>
          {googleMapsConfigured ? (
            <PlacesAutocompleteNew
              hasError={!!errors.birth_place}
              onTextChange={handleBirthPlaceTextChange}
              onBlur={handleBirthPlaceBlur}
              onPlaceResolved={handlePlaceResolved}
              onLoadError={handlePlacesLoadError}
            />
          ) : (
            <Input
              id="birth_place"
              type="text"
              placeholder="e.g. Bhubaneswar, Odisha, India"
              value={form.birth_place}
              aria-required="true"
              aria-invalid={!!errors.birth_place}
              className={cn(darkInputCls(!!errors.birth_place), 'placeholder:text-brand-gold/25')}
              style={errors.birth_place ? wellStyleError : wellStyle}
              onChange={(e) => {
                setField('birth_place', e.target.value)
                if (!e.target.value.trim()) setForm((prev) => ({ ...prev, places_resolved: false }))
              }}
              onBlur={() => {
                if (form.birth_place.trim() && !form.places_resolved) setManualOpen(true)
              }}
            />
          )}
          {errors.birth_place && (
            <p role="alert" className="bt-label text-destructive">{errors.birth_place}</p>
          )}

          {/* R2.2 — resolved place chip: compact green badge, replaces raw coords */}
          {form.places_resolved && (
            <div
              data-testid="places-resolved-indicator"
              className="bt-label flex items-center gap-1.5 px-2 py-1 rounded-md mt-0.5"
              style={{
                color: 'var(--status-success)',
                background: 'rgba(46,167,94,0.08)',
                border: '1px solid rgba(46,167,94,0.25)',
              }}
            >
              <span aria-hidden="true">✓</span>
              <span>
                {parseFloat(form.latitude).toFixed(4)}, {parseFloat(form.longitude).toFixed(4)}
                {' · '}{form.timezone_id}
                {' · UTC'}{parseFloat(form.tz_offset) >= 0 ? '+' : ''}{form.tz_offset}
              </span>
            </div>
          )}
        </div>

        {/* Date + Time ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <Label htmlFor="birth_date" className="bt-label bt-label-upper text-brand-gold/70">
              Date *
            </Label>
            <Input
              id="birth_date"
              type="text"
              placeholder="05-Feb-1984"
              value={form.birth_date_display}
              aria-required="true"
              aria-label="Birth date in DD-MMM-YYYY format"
              aria-invalid={!!errors.birth_date}
              className={cn(darkInputCls(!!errors.birth_date), 'placeholder:text-brand-gold/25')}
              style={errors.birth_date ? wellStyleError : wellStyle}
              onChange={(e) => handleDateDisplayChange(e.target.value)}
              onBlur={handleDateBlur}
            />
            {errors.birth_date && (
              <p role="alert" className="bt-label text-destructive">{errors.birth_date}</p>
            )}
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="birth_time" className="bt-label bt-label-upper text-brand-gold/70">
              Time (24 h) *
            </Label>
            <input
              id="birth_time"
              type="time"
              value={form.birth_time}
              aria-required="true"
              aria-invalid={!!errors.birth_time}
              className={darkInputCls(!!errors.birth_time)}
              style={{
                ...(errors.birth_time ? wellStyleError : wellStyle),
                colorScheme: 'dark',
                color: form.birth_time ? 'var(--brand-gold-cream)' : 'oklch(0.58 0.025 80)',
              }}
              onChange={(e) => setField('birth_time', e.target.value)}
            />
            {errors.birth_time && (
              <p role="alert" className="bt-label text-destructive">{errors.birth_time}</p>
            )}
          </div>
        </div>

        {/* Manual coordinates (R2.2 — collapsed by default) ─────────── */}
        <div data-testid="manual-override-accordion">
          <button
            type="button"
            onClick={() => setManualOpen((v) => !v)}
            className="bt-label text-muted-foreground hover:text-brand-gold/70 transition-colors flex items-center gap-1.5"
          >
            <span aria-hidden="true" className="text-[9px]">{manualOpen ? '▲' : '▼'}</span>
            {form.places_resolved ? 'Override coordinates' : 'Enter coordinates manually'}
          </button>

          {manualOpen && (
            <div className="mt-3 flex flex-col gap-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-0.5">
                  <Label htmlFor="latitude" className="bt-label bt-label-upper text-brand-gold/70">
                    Latitude *
                  </Label>
                  <input
                    id="latitude"
                    type="number"
                    step="0.0001"
                    min={-90}
                    max={90}
                    placeholder="20.2961"
                    value={form.latitude}
                    aria-required="true"
                    aria-invalid={!!errors.latitude}
                    className={darkInputCls(!!errors.latitude)}
                    style={errors.latitude ? wellStyleError : wellStyle}
                    onChange={(e) => setField('latitude', e.target.value)}
                  />
                  {errors.latitude && (
                    <p role="alert" className="bt-label text-destructive">{errors.latitude}</p>
                  )}
                </div>
                <div className="flex flex-col gap-0.5">
                  <Label htmlFor="longitude" className="bt-label bt-label-upper text-brand-gold/70">
                    Longitude *
                  </Label>
                  <input
                    id="longitude"
                    type="number"
                    step="0.0001"
                    min={-180}
                    max={180}
                    placeholder="85.8245"
                    value={form.longitude}
                    aria-required="true"
                    aria-invalid={!!errors.longitude}
                    className={darkInputCls(!!errors.longitude)}
                    style={errors.longitude ? wellStyleError : wellStyle}
                    onChange={(e) => setField('longitude', e.target.value)}
                  />
                  {errors.longitude && (
                    <p role="alert" className="bt-label text-destructive">{errors.longitude}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-0.5">
                  <Label htmlFor="timezone_id" className="bt-label bt-label-upper text-brand-gold/70">
                    Timezone
                  </Label>
                  <SelectWrapper>
                    <select
                      id="timezone_id"
                      value={form.timezone_id}
                      className={cn(darkInputCls(), 'appearance-none pr-7 cursor-pointer')}
                      style={wellStyle}
                      onChange={(e) => handleTimezoneChange(e.target.value)}
                    >
                      {TIMEZONES.map((tz) => (
                        <option key={tz.value} value={tz.value}
                          style={{ background: 'var(--brand-charcoal)' }}>
                          {tz.label}
                        </option>
                      ))}
                    </select>
                  </SelectWrapper>
                </div>
                <div className="flex flex-col gap-0.5">
                  <Label htmlFor="tz_offset" className="bt-label bt-label-upper text-brand-gold/70">
                    UTC offset *
                  </Label>
                  <input
                    id="tz_offset"
                    type="number"
                    step="0.25"
                    min={-14}
                    max={14}
                    placeholder="5.5"
                    value={form.tz_offset}
                    aria-required="true"
                    aria-invalid={!!errors.tz_offset}
                    className={darkInputCls(!!errors.tz_offset)}
                    style={errors.tz_offset ? wellStyleError : wellStyle}
                    onChange={(e) => setField('tz_offset', e.target.value)}
                  />
                  {errors.tz_offset && (
                    <p role="alert" className="bt-label text-destructive">{errors.tz_offset}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Ayanamsha chips (R2.4 — dot indicator, unambiguous toggle) ── */}
        <div className="flex flex-col gap-2" data-testid="section-compute">
          <span className="bt-label bt-label-upper text-brand-gold/70">Ayanamsha systems</span>
          <div className="flex flex-wrap gap-2">
            {AYANAMSHA_OPTIONS.map((opt) => {
              const checked = form.ayanamshas.includes(opt.id)
              return (
                <label
                  key={opt.id}
                  className={cn(
                    'flex items-center gap-2 cursor-pointer rounded-lg border px-2.5 py-2 min-w-[100px]',
                    'transition-all duration-150',
                  )}
                  style={{
                    background: checked ? 'oklch(0.78 0.13 80 / 0.12)' : 'transparent',
                    borderColor: checked ? 'var(--brand-gold)' : 'var(--brand-gold-hairline)',
                  }}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={checked}
                    aria-label={opt.label}
                    onChange={() => toggleAyanamsha(opt.id)}
                  />
                  {/* Filled dot = selected; hollow ring = unselected */}
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0 transition-colors duration-150"
                    style={{
                      background: checked ? 'var(--brand-gold)' : 'transparent',
                      border: checked ? 'none' : '1px solid oklch(0.50 0.020 75)',
                    }}
                  />
                  <span className="flex flex-col gap-0.5">
                    <span
                      className="text-sm font-medium leading-none"
                      style={{ color: checked ? 'var(--brand-gold)' : 'oklch(0.72 0.025 80)' }}
                    >
                      {opt.label}
                    </span>
                    <span
                      className="bt-label leading-none"
                      style={{
                        color: checked
                          ? 'oklch(0.78 0.13 80 / 0.60)'
                          : 'oklch(0.50 0.015 75)',
                      }}
                    >
                      {opt.sub}
                    </span>
                  </span>
                </label>
              )
            })}
          </div>
          {errors.ayanamshas && (
            <p role="alert" className="bt-label text-destructive">{errors.ayanamshas}</p>
          )}
        </div>

        {/* API error ──────────────────────────────────────────────────── */}
        {errors.api && (
          <div
            role="alert"
            className="rounded-lg border px-4 py-2.5 bt-body"
            style={{
              borderColor: 'rgba(184,56,18,0.40)',
              background: 'var(--status-halt-bg)',
              color: 'var(--status-halt)',
            }}
          >
            {errors.api}
          </div>
        )}

        {/* Footer: microcopy + Cancel / Save / Build (R2.1) ──────────── */}
        <div
          data-testid="form-footer"
          className="flex items-center justify-between gap-3 pt-3"
          style={{ borderTop: '1px solid var(--brand-gold-hairline)' }}
        >
          {/* AC16: microcopy is never clipped — shrink-0 + min-w-0 ensure it wraps */}
          <span
            data-testid="footer-microcopy"
            className="bt-mono bt-label text-muted-foreground shrink min-w-0"
          >
            {form.ayanamshas.length} ayanamshas × 28 assets = {nodeCount} nodes
          </span>

          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Cancel */}
            <button
              type="button"
              disabled={isInFlight}
              onClick={() => router.push('/dashboard')}
              className="bt-body text-muted-foreground hover:text-brand-gold-cream px-3 h-8 rounded-md transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            {/* Save chart — gold hairline outline */}
            <button
              type="button"
              disabled={isInFlight}
              onClick={() => submit('save')}
              aria-busy={submitting === 'save'}
              className={cn(
                'bt-body h-8 rounded-md border px-3 transition-colors',
                isInFlight && submitting !== 'save' && 'opacity-40 cursor-not-allowed',
                submitting === 'save' && 'opacity-70',
              )}
              style={{
                borderColor: 'var(--brand-gold)',
                color: 'var(--brand-gold)',
                background: 'transparent',
              }}
            >
              {submitting === 'save' ? 'Saving…' : 'Save chart'}
            </button>

            {/* Build chart — primary brand-cta */}
            <button
              type="button"
              disabled={isInFlight}
              onClick={() => submit('build')}
              aria-busy={submitting === 'build'}
              className={cn(
                'brand-cta h-8 rounded-lg px-4 text-sm',
                isInFlight && submitting !== 'build' && 'opacity-40 cursor-not-allowed',
                submitting === 'build' && 'opacity-70',
              )}
            >
              {submitting === 'build' ? 'Building…' : 'Build chart'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
