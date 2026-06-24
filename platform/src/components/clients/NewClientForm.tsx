'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useJsApiLoader } from '@react-google-maps/api'
import { ChevronLeft, CalendarDays } from 'lucide-react'
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

// ─── Shared well style objects (R2.5) ─────────────────────────────────────────

const wellStyle = {
  background: 'var(--brand-charcoal-deep)',
  color: 'var(--brand-gold-cream)',
  borderColor: 'var(--brand-gold-hairline)',
}

const wellStyleError = {
  background: 'var(--brand-charcoal-deep)',
  color: 'var(--brand-gold-cream)',
}

// R4.3: read-only coord fields (always visible; muted to indicate non-editable)
const readOnlyWellStyle = {
  background: 'var(--brand-ink)',
  color: 'oklch(0.45 0.015 75)',
  borderColor: 'oklch(0.78 0.13 80 / 0.12)',
  cursor: 'not-allowed',
}

// ─── CSS for gmp-placeautocomplete theming (R3.5 / R4.4) ─────────────────────
// R4.4: surface = brand-ink (the page canvas) so the field blends with the page,
// not the card. oklch(0.04 0.005 70) is the computed value of --brand-ink.
const PLACES_WIDGET_CSS = `
gmp-placeautocomplete {
  --gmpx-color-surface: oklch(0.04 0.005 70);
  --gmpx-color-on-surface: oklch(0.92 0.075 88);
  --gmpx-color-on-surface-variant: oklch(0.58 0.025 80);
  --gmpx-color-primary: oklch(0.78 0.13 80);
  --gmpx-color-outline: oklch(0.78 0.13 80 / 0.35);
  --gmpx-font-family-base: var(--font-sans, sans-serif);
  --gmpx-font-size-base: 0.875rem;
}
`

// ─── Custom gender dropdown (R3.6) ───────────────────────────────────────────
// Native <select> option lists render in OS chrome which ignores our CSS.
// A custom listbox gives complete visual control.

const GENDER_OPTIONS: { value: 'M' | 'F' | 'O' | 'unknown' | ''; label: string }[] = [
  { value: '',        label: '— select —' },
  { value: 'unknown', label: 'Prefer not to say' },
  { value: 'M',       label: 'Male' },
  { value: 'F',       label: 'Female' },
  { value: 'O',       label: 'Other' },
]

type GenderValue = 'M' | 'F' | 'O' | 'unknown' | ''

function GenderSelect({
  value,
  hasError,
  onChange,
}: {
  value: GenderValue
  hasError: boolean
  onChange: (v: GenderValue) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const selected = GENDER_OPTIONS.find((o) => o.value === value)

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Gender"
        id="gender"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'w-full h-9 rounded-md border px-3 py-1 text-sm text-left flex items-center justify-between',
          'transition-colors duration-150 focus:outline-none focus:ring-1',
          hasError ? 'border-destructive focus:ring-destructive' : 'focus:ring-brand-gold',
        )}
        style={{
          ...wellStyle,
          borderColor: hasError ? undefined : 'var(--brand-gold-hairline)',
          color: value ? 'var(--brand-gold-cream)' : 'oklch(0.58 0.025 80)',
        }}
      >
        <span>{selected?.label ?? '— select —'}</span>
        <span aria-hidden="true" className="text-[9px] ml-1" style={{ color: 'oklch(0.50 0.015 75)' }}>▼</span>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label="Gender options"
          className="absolute z-50 w-full mt-0.5 rounded-md border py-0.5 shadow-lg"
          style={{
            background: 'var(--brand-charcoal)',
            borderColor: 'var(--brand-gold-hairline)',
          }}
        >
          {GENDER_OPTIONS.map((opt) => (
            <li
              key={opt.value || '__empty'}
              role="option"
              aria-selected={value === opt.value}
              className="px-3 py-1.5 text-sm cursor-pointer transition-colors duration-100"
              style={{
                color: value === opt.value ? 'var(--brand-gold)' : 'var(--brand-gold-cream)',
                background: value === opt.value ? 'oklch(0.78 0.13 80 / 0.10)' : 'transparent',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = 'oklch(0.78 0.13 80 / 0.08)'
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLElement
                el.style.background = value === opt.value ? 'oklch(0.78 0.13 80 / 0.10)' : 'transparent'
              }}
              onMouseDown={(e) => {
                e.preventDefault()
                onChange(opt.value as GenderValue)
                setOpen(false)
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ─── PlaceAutocompleteElement (W9 + R3.4 + R3.5) ─────────────────────────────
// R3.4: overflow-hidden MUST NOT be on the container — the shadow-DOM prediction
// popup would be clipped. The container uses position:relative with no overflow
// constraint so the popup can escape.

function PlacesAutocompleteNew({
  hasError,
  onTextChange,
  onPlaceResolved,
  onLoadError,
}: {
  hasError: boolean
  onTextChange: (v: string) => void
  onPlaceResolved: (r: PlacesResult) => void
  onLoadError: () => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)

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

        // Theme tokens (R3.5 / R4.4) — cascade into shadow DOM via inline custom properties
        // R4.4: surface = brand-ink so field blends with the page canvas.
        el.style.setProperty('--gmpx-color-surface',            'oklch(0.04 0.005 70)')
        el.style.setProperty('--gmpx-color-on-surface',         'oklch(0.92 0.075 88)')
        el.style.setProperty('--gmpx-color-on-surface-variant', 'oklch(0.58 0.025 80)')
        el.style.setProperty('--gmpx-color-primary',            'oklch(0.78 0.13 80)')
        el.style.setProperty('--gmpx-color-outline',            'oklch(0.78 0.13 80 / 0.35)')
        el.style.setProperty('--gmpx-font-family-base',         'var(--font-sans, sans-serif)')
        el.style.setProperty('--gmpx-font-size-base',           '0.875rem')

        el.addEventListener('input', () => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onTextChange((el as any).value ?? '')
        })

        // R5.1: PlaceAutocompleteElement fires 'gmp-select' with event.placePrediction
        // (a PlacePrediction object). Call .toPlace() then .fetchFields() — this is the
        // call that issues the Place Details network request and populates location.
        // R5.2: After getting lat/lng, derive timezone via Google Time Zone API (falls back
        // to timezoneFromOffset on 403 or any error, so submit is never blocked).
        const handlePlaceSelect = async (event: Event) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const pp = (event as any).placePrediction
          if (!pp) return
          try {
            const place = pp.toPlace()
            await place.fetchFields({ fields: ['location', 'displayName', 'formattedAddress'] })
            const loc = place.location
            if (!loc) { onLoadError(); return }
            const lat = loc.lat()
            const lng = loc.lng()

            // R5.2: Google Time Zone API — derive IANA tz + offset; fall back on any error
            let timezone_id = 'Asia/Kolkata'
            let tz_offset = '5.5'
            try {
              const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
              const ts = Math.floor(Date.now() / 1000)
              const tzRes = await fetch(
                `https://maps.googleapis.com/maps/api/timezone/json?location=${lat},${lng}&timestamp=${ts}&key=${apiKey}`,
              )
              const tzData = await tzRes.json()
              if (tzData.status === 'OK') {
                const offsetHours = (tzData.rawOffset + tzData.dstOffset) / 3600
                timezone_id = tzData.timeZoneId
                tz_offset = String(offsetHours)
              }
            } catch {
              // TZ API unavailable (not enabled or 403) — keep defaults
            }

            onPlaceResolved({
              description: place.formattedAddress ?? place.displayName ?? '',
              lat,
              lng,
              utcOffsetMinutes: null,
              timezone_id,
              tz_offset,
            })
          } catch {
            onLoadError()
          }
        }

        el.addEventListener('gmp-select', handlePlaceSelect)

        container.appendChild(el)
      } catch {
        if (!cancelled) onLoadError()
      }
    })()

    return () => { cancelled = true }
  }, [isLoaded, onPlaceResolved, onTextChange, onLoadError])

  if (!isLoaded && !loadError) {
    return (
      <input
        disabled
        placeholder="Loading…"
        aria-label="Birth place loading"
        className={darkInputCls(hasError)}
        style={{
          ...wellStyle,
          color: 'oklch(0.58 0.025 80)',
          borderColor: hasError ? undefined : 'var(--brand-gold-hairline)',
        }}
      />
    )
  }

  // R3.4: No overflow-hidden — popup must not be clipped.
  // R5.3: No onBlur — the shadow-DOM popup closing fires blur, which was incorrectly
  // toggling manualOpen. Override scopes to its checkbox only.
  return (
    <div
      ref={containerRef}
      className={cn(
        'w-full rounded-md min-h-[36px]',
        hasError
          ? 'ring-1 ring-destructive border border-destructive'
          : 'border border-[var(--brand-gold-hairline)]',
      )}
      style={{ position: 'relative' }}
    />
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

export function NewClientForm() {
  const router = useRouter()
  const googleMapsConfigured = isGoogleMapsKeyConfigured()
  const hiddenDateRef = useRef<HTMLInputElement>(null)

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
  const [manualOpen, setManualOpen] = useState(!googleMapsConfigured)

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
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

  const handleBirthPlaceTextChange = useCallback((v: string) => {
    setForm((prev) => ({
      ...prev,
      birth_place: v,
      places_resolved: v.trim() ? prev.places_resolved : false,
    }))
    setErrors((prev) => ({ ...prev, birth_place: undefined }))
  }, [])

  const handlePlaceResolved = useCallback((result: PlacesResult) => {
    // Use Time Zone API result if available (R5.2); otherwise fall back to offset-based lookup
    const tz = (result.timezone_id && result.tz_offset)
      ? { timezone_id: result.timezone_id, tz_offset: result.tz_offset }
      : timezoneFromOffset(result.utcOffsetMinutes)
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

  // R3.7: hidden native date input → calendar popup → reformats to dd-MMM-yyyy
  function handleHiddenDateChange(e: React.ChangeEvent<HTMLInputElement>) {
    const iso = e.target.value
    if (!iso) return
    setForm((prev) => ({ ...prev, birth_date: iso, birth_date_display: formatDate(iso) }))
    setErrors((prev) => ({ ...prev, birth_date: undefined }))
  }

  function openCalendar(e: React.MouseEvent) {
    e.preventDefault()
    try {
      hiddenDateRef.current?.showPicker()
    } catch {
      hiddenDateRef.current?.click()
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
        router.push(data.redirect_url ?? `/clients/${data.chart_id}/nirmana`)
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

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4 py-6"
      style={{
        background: 'var(--brand-ink)',
        '--muted-foreground': 'oklch(0.58 0.025 80)',
      } as React.CSSProperties}
    >
      {/* R3.5: global style for gmp-placeautocomplete theming */}
      {/* eslint-disable-next-line react/no-danger */}
      <style dangerouslySetInnerHTML={{ __html: PLACES_WIDGET_CSS }} />

      {/* ── R3.1: Icon-only back link on the same line as the title ─────── */}
      {/* position:relative container lets the icon be absolute-left while
          the title stays centered in the full row width.                   */}
      <div
        data-testid="form-title"
        className="relative flex items-center justify-center w-full max-w-[720px] mb-5"
      >
        <Link
          href="/dashboard"
          aria-label="Back to dashboard"
          className="absolute left-0 flex items-center justify-center w-8 h-8 rounded-full transition-colors duration-150"
          style={{ color: 'oklch(0.58 0.025 80)' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--brand-gold)' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = 'oklch(0.58 0.025 80)' }}
        >
          <ChevronLeft size={20} strokeWidth={1.5} />
        </Link>

        {/* Subtitle removed per R3.1 — title alone carries it */}
        <h1 className="bt-display text-brand-gold-cream">
          <span className="opacity-55 text-brand-gold font-serif mr-1" aria-hidden="true">॥</span>
          Nava Jātaka
          <span className="opacity-55 text-brand-gold font-serif ml-1" aria-hidden="true">॥</span>
        </h1>
      </div>

      {/* ── Card — wider at 680px for single-line ayanamshas (R3.2) ─────── */}
      <div
        className="w-full max-w-[680px] rounded-xl flex flex-col gap-4 p-6"
        style={{
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
          {/* R3.6: fully themed custom listbox — no OS chrome */}
          <div className="flex flex-col gap-1">
            <span className="bt-label bt-label-upper text-brand-gold/70">
              Gender *
            </span>
            <GenderSelect
              value={form.gender}
              hasError={!!errors.gender}
              onChange={(v) => setField('gender', v)}
            />
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
            />
          )}
          {errors.birth_place && (
            <p role="alert" className="bt-label text-destructive">{errors.birth_place}</p>
          )}

          {/* R4.3: resolved state is visible in the always-shown coord fields below */}
        </div>

        {/* Date + Time ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          {/* R3.7: dd-MMM-yyyy text field + calendar icon → hidden date picker */}
          <div className="flex flex-col gap-1">
            <Label htmlFor="birth_date" className="bt-label bt-label-upper text-brand-gold/70">
              Date *
            </Label>
            <div className="relative flex items-center">
              <Input
                id="birth_date"
                type="text"
                placeholder="05-Feb-1984"
                value={form.birth_date_display}
                aria-required="true"
                aria-label="Birth date in DD-MMM-YYYY format"
                aria-invalid={!!errors.birth_date}
                className={cn(
                  darkInputCls(!!errors.birth_date),
                  'pr-8 placeholder:text-brand-gold/25',
                )}
                style={errors.birth_date ? wellStyleError : wellStyle}
                onChange={(e) => handleDateDisplayChange(e.target.value)}
                onBlur={handleDateBlur}
              />
              <button
                type="button"
                aria-label="Open date picker"
                onClick={openCalendar}
                className="absolute right-2 flex items-center justify-center transition-colors duration-150"
                style={{ color: 'oklch(0.58 0.025 80)' }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--brand-gold)' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = 'oklch(0.58 0.025 80)' }}
              >
                <CalendarDays size={14} strokeWidth={1.5} />
              </button>
              {/* Hidden date input: triggers the browser's native calendar (R3.7) */}
              <input
                ref={hiddenDateRef}
                type="date"
                tabIndex={-1}
                aria-hidden="true"
                value={form.birth_date}
                min="1900-01-01"
                max={todayIso()}
                onChange={handleHiddenDateChange}
                style={{
                  position: 'absolute',
                  opacity: 0,
                  width: 0,
                  height: 0,
                  pointerEvents: 'none',
                  colorScheme: 'dark',
                }}
              />
            </div>
            {errors.birth_date && (
              <p role="alert" className="bt-label text-destructive">{errors.birth_date}</p>
            )}
          </div>

          {/* R3.8: Time — dark well + colorScheme:dark for native chrome */}
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

        {/* R4.3: Coordinates — always visible; read-only until "Manual override" ── */}
        <div data-testid="manual-override-accordion">
          {/* Manual override checkbox */}
          <label className="flex items-center gap-2 cursor-pointer group w-fit">
            <input
              type="checkbox"
              className="sr-only"
              checked={manualOpen}
              aria-label="Manual coordinate override"
              onChange={(e) => setManualOpen(e.target.checked)}
            />
            <span
              aria-hidden="true"
              className="w-3.5 h-3.5 rounded border flex items-center justify-center flex-shrink-0 transition-all duration-150"
              style={{
                background: manualOpen ? 'oklch(0.78 0.13 80 / 0.14)' : 'transparent',
                borderColor: manualOpen ? 'var(--brand-gold)' : 'oklch(0.50 0.020 75)',
              }}
            >
              {manualOpen && (
                <span style={{ color: 'var(--brand-gold)', fontSize: '9px', lineHeight: 1, fontWeight: 700 }}>✓</span>
              )}
            </span>
            <span className="bt-label text-muted-foreground group-hover:text-brand-gold/70 transition-colors">
              Manual override
            </span>
          </label>

          {/* Coord fields — always rendered; editable only when override is checked */}
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
                  readOnly={!manualOpen}
                  tabIndex={manualOpen ? 0 : -1}
                  aria-required="true"
                  aria-readonly={!manualOpen}
                  aria-invalid={!!errors.latitude}
                  className={cn(darkInputCls(!!errors.latitude), !manualOpen && 'cursor-not-allowed')}
                  style={errors.latitude ? wellStyleError : manualOpen ? wellStyle : readOnlyWellStyle}
                  onChange={manualOpen ? (e) => setField('latitude', e.target.value) : undefined}
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
                  readOnly={!manualOpen}
                  tabIndex={manualOpen ? 0 : -1}
                  aria-required="true"
                  aria-readonly={!manualOpen}
                  aria-invalid={!!errors.longitude}
                  className={cn(darkInputCls(!!errors.longitude), !manualOpen && 'cursor-not-allowed')}
                  style={errors.longitude ? wellStyleError : manualOpen ? wellStyle : readOnlyWellStyle}
                  onChange={manualOpen ? (e) => setField('longitude', e.target.value) : undefined}
                />
                {errors.longitude && (
                  <p role="alert" className="bt-label text-destructive">{errors.longitude}</p>
                )}
              </div>
            </div>

          </div>
        </div>

        {/* R3.2: Ayanamsha checkboxes — single flex-nowrap row ─────────── */}
        <div className="flex flex-col gap-2" data-testid="section-compute">
          <span className="bt-label bt-label-upper text-brand-gold/70">Ayanamsha systems</span>
          <div className="flex flex-nowrap gap-2">
            {AYANAMSHA_OPTIONS.map((opt) => {
              const checked = form.ayanamshas.includes(opt.id)
              return (
                <label
                  key={opt.id}
                  className={cn(
                    'flex items-center gap-2 cursor-pointer rounded-lg border px-2.5 py-2 flex-1',
                    'transition-all duration-150 min-w-0',
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
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0 transition-colors duration-150"
                    style={{
                      background: checked ? 'var(--brand-gold)' : 'transparent',
                      border: checked ? 'none' : '1px solid oklch(0.50 0.020 75)',
                    }}
                  />
                  <span className="flex flex-col gap-0.5 min-w-0">
                    <span
                      className="font-medium leading-none truncate"
                      style={{
                        fontSize: '11px',
                        color: checked ? 'var(--brand-gold)' : 'oklch(0.72 0.025 80)',
                      }}
                    >
                      {opt.label}
                    </span>
                    <span
                      className="leading-none truncate"
                      style={{
                        fontSize: '9px',
                        color: checked ? 'oklch(0.78 0.13 80 / 0.60)' : 'oklch(0.50 0.015 75)',
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

        {/* R3.3: Footer — 3 buttons only; microcopy removed ──────────── */}
        <div
          data-testid="form-footer"
          className="flex items-center justify-end gap-2 pt-3"
          style={{ borderTop: '1px solid var(--brand-gold-hairline)' }}
        >
          <button
            type="button"
            disabled={isInFlight}
            onClick={() => router.push('/dashboard')}
            className="bt-body text-muted-foreground hover:text-brand-gold-cream px-3 h-8 rounded-md transition-colors disabled:opacity-50"
          >
            Cancel
          </button>

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
  )
}
