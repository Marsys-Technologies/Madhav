'use client'

import { useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Autocomplete, useJsApiLoader } from '@react-google-maps/api'
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
  { value: 'Asia/Kolkata',        label: 'Asia/Kolkata (UTC+5:30)',     offset: 5.5  },
  { value: 'UTC',                 label: 'UTC (UTC+0)',                  offset: 0    },
  { value: 'Asia/Colombo',        label: 'Asia/Colombo (UTC+5:30)',     offset: 5.5  },
  { value: 'Asia/Kathmandu',      label: 'Asia/Kathmandu (UTC+5:45)',   offset: 5.75 },
  { value: 'Asia/Dhaka',          label: 'Asia/Dhaka (UTC+6)',          offset: 6    },
  { value: 'Asia/Dubai',          label: 'Asia/Dubai (UTC+4)',          offset: 4    },
  { value: 'Asia/Singapore',      label: 'Asia/Singapore (UTC+8)',      offset: 8    },
  { value: 'Asia/Tokyo',          label: 'Asia/Tokyo (UTC+9)',          offset: 9    },
  { value: 'America/New_York',    label: 'America/New_York (UTC-5)',    offset: -5   },
  { value: 'America/Chicago',     label: 'America/Chicago (UTC-6)',     offset: -6   },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (UTC-8)', offset: -8  },
  { value: 'Europe/London',       label: 'Europe/London (UTC+0)',       offset: 0    },
  { value: 'Europe/Berlin',       label: 'Europe/Berlin (UTC+1)',       offset: 1    },
  { value: 'Australia/Sydney',    label: 'Australia/Sydney (UTC+10)',   offset: 10   },
] as const

// ─── State types ──────────────────────────────────────────────────────────────

interface FormState {
  full_name: string
  preferred_name: string
  gender: 'M' | 'F' | 'O' | 'unknown' | ''
  birth_date: string         // YYYY-MM-DD (API wire format)
  birth_date_display: string // dd-MMM-yyyy (user-facing)
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

// ─── Shared native-input class ────────────────────────────────────────────────

function nativeInputCls(hasError?: boolean): string {
  return cn(
    'w-full h-9 rounded-md border bg-background px-3 py-1 text-sm',
    'focus:outline-none focus:ring-1 focus:ring-ring',
    hasError ? 'border-destructive' : 'border-input',
  )
}

// ─── Places autocomplete wrapper ──────────────────────────────────────────────

const GMAPS_LIBS: 'places'[] = ['places']

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
  onTextChange,
  onPlaceResolved,
}: {
  value: string
  hasError: boolean
  onTextChange: (v: string) => void
  onPlaceResolved: (r: PlacesResult) => void
}) {
  const { isLoaded } = useJsApiLoader({
    id: 'gmaps-places',
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? '',
    libraries: GMAPS_LIBS,
  })
  const acRef = useRef<google.maps.places.Autocomplete | null>(null)

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

  if (!isLoaded) return inputEl

  return (
    <Autocomplete
      onLoad={(ac) => { acRef.current = ac }}
      onPlaceChanged={onPlaceChanged}
      options={{ fields: ['geometry', 'formatted_address', 'name', 'utc_offset_minutes'] }}
    >
      {inputEl}
    </Autocomplete>
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

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-background text-foreground">

      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <div className="shrink-0 flex items-center justify-between px-6 h-10 border-b border-border">
        <Link
          href="/dashboard"
          aria-label="Back to dashboard"
          className="bt-body text-muted-foreground hover:underline"
        >
          ← Back to dashboard
        </Link>
        <span className="bt-label bt-label-upper text-muted-foreground">Charts · New</span>
      </div>

      {/* ── Title ──────────────────────────────────────────────────────── */}
      <div data-testid="form-title" className="shrink-0 text-center py-3">
        <h1 className="bt-display text-[#fce29a]">
          <span className="opacity-55 text-[#d4af37] font-serif mr-1" aria-hidden="true">॥</span>
          Nava Jātaka
          <span className="opacity-55 text-[#d4af37] font-serif ml-1" aria-hidden="true">॥</span>
        </h1>
        <p className="bt-body text-muted-foreground mt-0.5">New Chart</p>
      </div>

      {/* ── Two-column form ─────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 px-6 flex flex-col gap-2 overflow-hidden">
        <div className="grid grid-cols-2 gap-3 flex-1 min-h-0">

          {/* Left: Identity + Compute ────────────────────────────────── */}
          <div className="flex flex-col gap-3 min-h-0">

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

              <div className="flex flex-col gap-1">
                <Label htmlFor="full_name" className="bt-label bt-label-upper">Full name *</Label>
                <Input
                  id="full_name"
                  type="text"
                  placeholder="e.g. Abhisek Mohanty"
                  value={form.full_name}
                  maxLength={200}
                  aria-required="true"
                  aria-label="Full name"
                  aria-invalid={!!errors.full_name}
                  className={cn(errors.full_name && 'border-destructive')}
                  onChange={(e) => setField('full_name', e.target.value)}
                />
                {errors.full_name && (
                  <p role="alert" className="bt-label text-destructive">{errors.full_name}</p>
                )}
              </div>

              <div className="grid gap-2.5" style={{ gridTemplateColumns: '1fr 152px' }}>
                <div className="flex flex-col gap-1">
                  <Label htmlFor="preferred_name" className="bt-label bt-label-upper">
                    Preferred name
                  </Label>
                  <Input
                    id="preferred_name"
                    type="text"
                    placeholder="First word of full name"
                    value={form.preferred_name}
                    maxLength={100}
                    onChange={(e) => setField('preferred_name', e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <Label htmlFor="gender" className="bt-label bt-label-upper">Gender *</Label>
                  <select
                    id="gender"
                    value={form.gender}
                    aria-invalid={!!errors.gender}
                    className={nativeInputCls(!!errors.gender)}
                    onChange={(e) =>
                      setField('gender', e.target.value as FormState['gender'])
                    }
                  >
                    <option value="">— select —</option>
                    <option value="unknown">Prefer not to say</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                  {errors.gender && (
                    <p role="alert" className="bt-label text-destructive">{errors.gender}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Gaṇana · Compute */}
            <div
              data-testid="section-compute"
              className="bg-card rounded-xl border border-border p-3 flex flex-col gap-2"
            >
              <h3 className="bt-heading text-brand-gold-cream">Gaṇana · Compute</h3>
              <div className="flex flex-wrap gap-1.5">
                {AYANAMSHA_OPTIONS.map((opt) => {
                  const checked = form.ayanamshas.includes(opt.id)
                  return (
                    <label
                      key={opt.id}
                      className={cn(
                        'flex flex-col gap-0.5 cursor-pointer rounded-lg border px-2.5 py-2 min-w-[96px]',
                        'transition-colors duration-150',
                        checked
                          ? 'border-brand-gold bg-brand-gold/[0.06]'
                          : 'border-border hover:border-brand-gold/40',
                      )}
                    >
                      <input
                        type="checkbox"
                        className="sr-only"
                        checked={checked}
                        aria-label={opt.label}
                        onChange={() => toggleAyanamsha(opt.id)}
                      />
                      <span
                        className={cn(
                          'text-sm font-medium',
                          checked ? 'text-brand-gold' : 'text-foreground/80',
                        )}
                      >
                        {opt.label}
                      </span>
                      <span className={cn('bt-label', checked ? 'text-brand-gold/60' : '')}>
                        {opt.sub}
                      </span>
                    </label>
                  )
                })}
              </div>
              {errors.ayanamshas && (
                <p role="alert" className="bt-label text-destructive">{errors.ayanamshas}</p>
              )}
            </div>
          </div>

          {/* Right: Birth ────────────────────────────────────────────── */}
          <div
            data-testid="section-birth"
            className="bg-card rounded-xl border border-border p-3 flex flex-col gap-2.5"
          >
            <h3 className="bt-heading text-brand-gold-cream">Janma Sthāna · Birth</h3>

            {/* Birth place */}
            <div className="flex flex-col gap-1">
              <Label htmlFor="birth_place" className="bt-label bt-label-upper">
                Birth place *
              </Label>
              {googleMapsConfigured ? (
                <PlacesAutocompleteInput
                  value={form.birth_place}
                  hasError={!!errors.birth_place}
                  onTextChange={(v) => {
                    setField('birth_place', v)
                    if (!v.trim()) setForm((prev) => ({ ...prev, places_resolved: false }))
                  }}
                  onBlur={handleBirthPlaceBlur}
                  onPlaceResolved={(result) => {
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
                  }}
                />
              ) : (
                <Input
                  id="birth_place"
                  type="text"
                  placeholder="e.g. Bhubaneswar, Odisha, India"
                  value={form.birth_place}
                  aria-required="true"
                  aria-invalid={!!errors.birth_place}
                  className={cn(errors.birth_place && 'border-destructive')}
                  onChange={(e) => {
                    setField('birth_place', e.target.value)
                    if (!e.target.value.trim())
                      setForm((prev) => ({ ...prev, places_resolved: false }))
                  }}
                  onBlur={handleBirthPlaceBlur}
                />
              )}
              {errors.birth_place && (
                <p role="alert" className="bt-label text-destructive">{errors.birth_place}</p>
              )}
              {form.places_resolved && (
                <div
                  data-testid="places-resolved-indicator"
                  className="bt-label flex items-center gap-1.5"
                  style={{ color: 'var(--status-success)' }}
                >
                  <span>✓</span>
                  <span>
                    {form.latitude}, {form.longitude} · {form.timezone_id} · UTC
                    {parseFloat(form.tz_offset) >= 0 ? '+' : ''}{form.tz_offset}
                  </span>
                </div>
              )}
            </div>

            {/* Date + Time */}
            <div className="grid grid-cols-2 gap-2.5">
              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_date" className="bt-label bt-label-upper">Date *</Label>
                <Input
                  id="birth_date"
                  type="text"
                  placeholder="05-Feb-1984"
                  value={form.birth_date_display}
                  aria-required="true"
                  aria-label="Birth date in DD-MMM-YYYY format"
                  aria-invalid={!!errors.birth_date}
                  className={cn(errors.birth_date && 'border-destructive')}
                  onChange={(e) => handleDateDisplayChange(e.target.value)}
                  onBlur={handleDateBlur}
                />
                {errors.birth_date && (
                  <p role="alert" className="bt-label text-destructive">{errors.birth_date}</p>
                )}
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_time" className="bt-label bt-label-upper">
                  Time (24 h) *
                </Label>
                <input
                  id="birth_time"
                  type="time"
                  value={form.birth_time}
                  aria-required="true"
                  aria-invalid={!!errors.birth_time}
                  className={nativeInputCls(!!errors.birth_time)}
                  onChange={(e) => setField('birth_time', e.target.value)}
                />
                {errors.birth_time && (
                  <p role="alert" className="bt-label text-destructive">{errors.birth_time}</p>
                )}
              </div>
            </div>

            {/* Manual coords accordion */}
            <div
              data-testid="manual-override-accordion"
              className="rounded-lg border border-border overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setManualOpen((v) => !v)}
                className="w-full flex items-center justify-between px-3 py-2 bt-label text-muted-foreground hover:text-foreground transition-colors"
              >
                <span>
                  {form.places_resolved
                    ? 'Override coordinates'
                    : 'Manual coordinates · lat / lng / timezone'}
                </span>
                <span className="text-[10px]">{manualOpen ? '▲' : '▼'}</span>
              </button>

              {manualOpen && (
                <div className="px-3 pb-3 flex flex-col gap-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-0.5">
                      <Label htmlFor="latitude" className="bt-label bt-label-upper">
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
                        className={nativeInputCls(!!errors.latitude)}
                        onChange={(e) => setField('latitude', e.target.value)}
                      />
                      {errors.latitude && (
                        <p role="alert" className="bt-label text-destructive">{errors.latitude}</p>
                      )}
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <Label htmlFor="longitude" className="bt-label bt-label-upper">
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
                        className={nativeInputCls(!!errors.longitude)}
                        onChange={(e) => setField('longitude', e.target.value)}
                      />
                      {errors.longitude && (
                        <p role="alert" className="bt-label text-destructive">{errors.longitude}</p>
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
        </div>

        {/* ── API error ──────────────────────────────────────────────────── */}
        {errors.api && (
          <div
            role="alert"
            className="shrink-0 rounded-lg border px-4 py-2.5 bt-body"
            style={{
              borderColor: 'color-mix(in oklch, var(--status-halt) 40%, transparent)',
              background: 'var(--status-halt-bg)',
              color: 'var(--status-halt)',
            }}
          >
            {errors.api}
          </div>
        )}
      </div>

      {/* ── Footer: microcopy + 3 buttons ──────────────────────────────── */}
      <div
        data-testid="form-footer"
        className="shrink-0 border-t border-border px-6 h-14 flex items-center justify-between"
      >
        <span data-testid="footer-microcopy" className="bt-mono bt-label text-muted-foreground">
          {form.ayanamshas.length} ayanamshas × 28 assets = {nodeCount} nodes
        </span>

        <div className="flex items-center gap-2">
          {/* Cancel */}
          <button
            type="button"
            disabled={isInFlight}
            onClick={() => router.push('/dashboard')}
            className="bt-body text-muted-foreground hover:text-foreground px-4 h-9 rounded-md transition-colors disabled:opacity-50"
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
              'bt-body h-9 rounded-md border px-4 transition-colors',
              isInFlight && submitting !== 'save'
                ? 'opacity-40 cursor-not-allowed border-border text-muted-foreground'
                : 'border-brand-gold/50 text-brand-gold hover:bg-brand-gold/[0.05]',
              submitting === 'save' && 'opacity-70',
            )}
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
              'brand-cta h-9 rounded-lg px-5 text-sm',
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
