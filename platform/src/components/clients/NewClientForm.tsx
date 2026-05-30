'use client'

/**
 * NewClientForm — 4-section chart creation form
 * Sections: Identity | Birth Coordinates | Compute | Relationships
 * [PHASE-C-01]
 */

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

// ─── Ayanamsha options ────────────────────────────────────────────────────────

export const AYANAMSHA_OPTIONS = [
  { id: 'lahiri',        label: 'Lahiri (Chitrapaksha)' },
  { id: 'raman',         label: 'B.V. Raman' },
  { id: 'kp',            label: 'KP (Krishnamurti Paddhati)' },
  { id: 'yukteshwar',    label: 'Yukteshwar' },
  { id: 'fagan_bradley', label: 'Fagan-Bradley' },
] as const

export type AyanamshaId = (typeof AYANAMSHA_OPTIONS)[number]['id']
const DEFAULT_AYANAMSHAS: AyanamshaId[] = AYANAMSHA_OPTIONS.map((a) => a.id)

// ─── Timezone list ────────────────────────────────────────────────────────────

const TIMEZONES = [
  { value: 'Asia/Kolkata',        label: 'Asia/Kolkata (IST, UTC+5:30)' },
  { value: 'UTC',                 label: 'UTC' },
  { value: 'America/New_York',    label: 'America/New_York (EST/EDT)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
  { value: 'America/Chicago',     label: 'America/Chicago (CST/CDT)' },
  { value: 'Europe/London',       label: 'Europe/London (GMT/BST)' },
  { value: 'Europe/Paris',        label: 'Europe/Paris (CET/CEST)' },
  { value: 'Asia/Dubai',          label: 'Asia/Dubai (GST, UTC+4)' },
  { value: 'Asia/Singapore',      label: 'Asia/Singapore (SST, UTC+8)' },
  { value: 'Australia/Sydney',    label: 'Australia/Sydney (AEST/AEDT)' },
]

// ─── Zod schema ───────────────────────────────────────────────────────────────

const formSchema = z.object({
  full_name:          z.string().min(1, 'Name is required').max(200),
  gender:             z.enum(['male', 'female', 'other', 'not-specified']),
  tier:               z.enum(['auto', 'client', 'acharya', 'super_admin']).default('auto'),
  notes:              z.string().max(2000).optional(),
  birth_date:         z.string().min(1, 'Birth date is required'),
  birth_time:         z.string().min(1, 'Birth time is required'),
  timezone:           z.string().default('Asia/Kolkata'),
  latitude:           z.string().optional(),
  longitude:          z.string().optional(),
  birthplace:         z.string().min(1, 'Birthplace is required'),
  ayanamshas:         z.array(z.string()).min(1, 'Select at least one ayanamsha'),
  year_from:          z.number().int().min(1500).max(2200).default(1950),
  year_to:            z.number().int().min(1500).max(2200).default(2100),
  verification:       z.enum(['one-pass', 'two-pass']).default('two-pass'),
  calendar:           z.enum(['gregorian', 'julian']).default('gregorian'),
  visibility:         z.enum(['private', 'shared']).default('private'),
  relationship_type:  z.enum(['self', 'client', 'research', 'other']).default('self'),
  reference_chart_id: z.string().optional(),
})

type FormValues = z.infer<typeof formSchema>
type FormErrors = Partial<Record<keyof FormValues | 'api', string>>

const DEFAULTS: FormValues = {
  full_name:          '',
  gender:             'not-specified',
  tier:               'auto',
  notes:              '',
  birth_date:         '',
  birth_time:         '',
  timezone:           'Asia/Kolkata',
  latitude:           '',
  longitude:          '',
  birthplace:         '',
  ayanamshas:         DEFAULT_AYANAMSHAS,
  year_from:          1950,
  year_to:            2100,
  verification:       'two-pass',
  calendar:           'gregorian',
  visibility:         'private',
  relationship_type:  'self',
  reference_chart_id: '',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null
  return <p role="alert" className="mt-1 text-xs text-[#9c3a2a]">{msg}</p>
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="font-serif text-base text-[#d4a648] tracking-wide uppercase">{children}</h3>
  )
}

function selectCls(hasError?: boolean) {
  return cn(
    'h-8 w-full rounded-lg border bg-[#08070a] px-2.5 text-sm text-[#f5f0e8] outline-none focus:ring-1 focus:ring-[#d4a648]',
    hasError ? 'border-[#9c3a2a]' : 'border-[#1a1820]',
  )
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
  const [values, setValues] = useState<FormValues>(DEFAULTS)
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [manualCoords, setManualCoords] = useState(false)
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function set<K extends keyof FormValues>(key: K, val: FormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: val }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const handleBirthplaceChange = useCallback((val: string) => {
    setValues((prev) => ({ ...prev, birthplace: val }))
    if (errors.birthplace) setErrors((prev) => ({ ...prev, birthplace: undefined }))
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    if (val.trim().length > 2) {
      searchTimeoutRef.current = setTimeout(() => {
        // Places API hook point — open manual override when no result after 800 ms
        setManualCoords(true)
      }, 800)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function toggleAyanamsha(id: AyanamshaId) {
    const next = values.ayanamshas.includes(id)
      ? values.ayanamshas.filter((a) => a !== id)
      : [...values.ayanamshas, id]
    set('ayanamshas', next)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const result = formSchema.safeParse(values)
    if (!result.success) {
      const fieldErrors: FormErrors = {}
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof FormValues
        if (!fieldErrors[key]) fieldErrors[key] = issue.message
      }
      setErrors(fieldErrors)
      return
    }

    setSubmitting(true)
    setErrors({})

    try {
      const d = result.data
      const body = {
        name:                d.full_name,
        gender:              d.gender,
        ...(d.tier !== 'auto' ? { tier: d.tier } : {}),
        ...(d.notes ? { notes: d.notes } : {}),
        birth_date:          d.birth_date,
        birth_time:          d.birth_time,
        timezone:            d.timezone,
        ...(d.latitude  ? { birth_lat: parseFloat(d.latitude)  } : {}),
        ...(d.longitude ? { birth_lng: parseFloat(d.longitude) } : {}),
        birth_place:         d.birthplace,
        ayanamshas:          d.ayanamshas,
        year_from:           d.year_from,
        year_to:             d.year_to,
        verification_passes: d.verification,
        calendar_system:     d.calendar,
        visibility:          d.visibility,
        relationship_type:   d.relationship_type,
        ...(d.reference_chart_id ? { reference_chart_id: d.reference_chart_id } : {}),
      }

      const res = await fetch('/api/clients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setErrors({ api: data?.error ?? `Server error (${res.status})` })
        return
      }

      const chartId = data.chart_id ?? data.id
      if (!chartId) { setErrors({ api: 'Server returned no chart ID.' }); return }
      router.push(`/clients/${chartId}/cockpit`)
    } catch (err) {
      setErrors({ api: err instanceof Error ? err.message : 'Network error.' })
    } finally {
      setSubmitting(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  const isInFlight = submitting !== null

  return (
    <div className="min-h-screen bg-[#08070a] text-[#f5f0e8] px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <h1 className="font-serif text-2xl text-[#d4a648]">New Chart</h1>
          <p className="mt-1 text-sm text-[#8a8070]">Fields marked * are required.</p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-6">

          {/* ── Section 1: Identity ──────────────────────────────── */}
          <Card className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-5 shadow-none ring-0">
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>1 · Identity</SectionTitle></CardTitle>
            </CardHeader>
            <CardContent className="p-0 grid gap-4">
              <div className="flex flex-col gap-1">
                <Label className="text-[#c8bfb0] text-sm">Full name *</Label>
                <Input
                  value={values.full_name}
                  onChange={(e) => set('full_name', e.target.value)}
                  placeholder="e.g. Abhisek Mohanty"
                  className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8] placeholder:text-[#5a5550]"
                />
                <FieldError msg={errors.full_name} />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Gender *</Label>
                  <select
                    value={values.gender}
                    onChange={(e) => set('gender', e.target.value as FormValues['gender'])}
                    className={selectCls(!!errors.gender)}
                  >
                    <option value="not-specified">Not specified</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                  <FieldError msg={errors.gender} />
                </div>
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Tier</Label>
                  <select
                    value={values.tier}
                    onChange={(e) => set('tier', e.target.value as FormValues['tier'])}
                    className={selectCls()}
                  >
                    <option value="auto">Auto-assigned</option>
                    <option value="client">Client</option>
                    <option value="acharya">Acharya</option>
                    <option value="super_admin">Super Admin</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-[#c8bfb0] text-sm">Notes</Label>
                <textarea
                  value={values.notes}
                  onChange={(e) => set('notes', e.target.value)}
                  rows={3}
                  placeholder="Optional notes about this native…"
                  className="w-full resize-none rounded-lg border border-[#1a1820] bg-[#08070a] px-3 py-2 text-sm text-[#f5f0e8] placeholder:text-[#5a5550] outline-none focus:ring-1 focus:ring-[#d4a648]"
                />
              </div>
            </CardContent>
          </Card>

          {/* ── Section 2: Birth Coordinates ─────────────────────── */}
          <Card className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-5 shadow-none ring-0">
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>2 · Birth Coordinates</SectionTitle></CardTitle>
            </CardHeader>
            <CardContent className="p-0 grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Date *</Label>
                  <Input
                    type="date"
                    value={values.birth_date}
                    onChange={(e) => set('birth_date', e.target.value)}
                    className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8]"
                  />
                  <FieldError msg={errors.birth_date} />
                </div>
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Time (24 h) *</Label>
                  <Input
                    type="time"
                    value={values.birth_time}
                    onChange={(e) => set('birth_time', e.target.value)}
                    className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8]"
                  />
                  <FieldError msg={errors.birth_time} />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-[#c8bfb0] text-sm">Timezone</Label>
                <select
                  value={values.timezone}
                  onChange={(e) => set('timezone', e.target.value)}
                  className={selectCls()}
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz.value} value={tz.value}>{tz.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-[#c8bfb0] text-sm">Birthplace *</Label>
                <Input
                  value={values.birthplace}
                  onChange={(e) => handleBirthplaceChange(e.target.value)}
                  placeholder="e.g. Bhubaneswar, Odisha, India"
                  className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8] placeholder:text-[#5a5550]"
                />
                <FieldError msg={errors.birthplace} />
              </div>

              {/* Manual coords accordion */}
              <div className="rounded-lg border border-[#1a1820] overflow-hidden">
                <button
                  type="button"
                  onClick={() => setManualCoords((v) => !v)}
                  className="flex w-full items-center justify-between px-4 py-2.5 text-sm text-[#8a8070] hover:text-[#c8bfb0] transition-colors"
                >
                  <span>Manual lat/lng override</span>
                  <span className="text-xs">{manualCoords ? '▲' : '▼'}</span>
                </button>
                {manualCoords && (
                  <div className="grid grid-cols-2 gap-4 px-4 pb-4 pt-1">
                    <div className="flex flex-col gap-1">
                      <Label className="text-[#c8bfb0] text-sm">Latitude</Label>
                      <Input
                        type="number"
                        step="0.0001"
                        value={values.latitude}
                        onChange={(e) => set('latitude', e.target.value)}
                        placeholder="20.2961"
                        className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8] placeholder:text-[#5a5550]"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label className="text-[#c8bfb0] text-sm">Longitude</Label>
                      <Input
                        type="number"
                        step="0.0001"
                        value={values.longitude}
                        onChange={(e) => set('longitude', e.target.value)}
                        placeholder="85.8245"
                        className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8] placeholder:text-[#5a5550]"
                      />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* ── Section 3: Compute ───────────────────────────────── */}
          <Card className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-5 shadow-none ring-0">
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>3 · Compute</SectionTitle></CardTitle>
            </CardHeader>
            <CardContent className="p-0 grid gap-4">
              <div className="flex flex-col gap-2">
                <Label className="text-[#c8bfb0] text-sm">Ayanamshas *</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {AYANAMSHA_OPTIONS.map((opt) => {
                    const checked = values.ayanamshas.includes(opt.id)
                    return (
                      <label
                        key={opt.id}
                        className={cn(
                          'flex items-center gap-2 cursor-pointer rounded-md border px-3 py-1.5 text-sm transition-colors',
                          checked
                            ? 'border-[#d4a648] text-[#d4a648] bg-[#d4a648]/5'
                            : 'border-[#1a1820] text-[#8a8070] hover:border-[#5a5550]',
                        )}
                      >
                        <input
                          type="checkbox"
                          className="sr-only"
                          checked={checked}
                          onChange={() => toggleAyanamsha(opt.id as AyanamshaId)}
                        />
                        {opt.label}
                      </label>
                    )
                  })}
                </div>
                <FieldError msg={errors.ayanamshas} />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Year from</Label>
                  <Input
                    type="number"
                    value={values.year_from}
                    onChange={(e) => set('year_from', parseInt(e.target.value) || 1950)}
                    className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8]"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Year to</Label>
                  <Input
                    type="number"
                    value={values.year_to}
                    onChange={(e) => set('year_to', parseInt(e.target.value) || 2100)}
                    className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-[#c8bfb0] text-sm">Verification passes</Label>
                  <div className="flex gap-4 mt-1">
                    {(['one-pass', 'two-pass'] as const).map((v) => (
                      <label key={v} className="flex items-center gap-2 cursor-pointer text-sm text-[#c8bfb0]">
                        <input
                          type="radio"
                          name="verification"
                          value={v}
                          checked={values.verification === v}
                          onChange={() => set('verification', v)}
                          className="accent-[#d4a648]"
                        />
                        {v === 'one-pass' ? 'One-pass' : 'Two-pass (default)'}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <Label className="text-[#c8bfb0] text-sm">Calendar system</Label>
                  <div className="flex gap-4 mt-1">
                    {(['gregorian', 'julian'] as const).map((v) => (
                      <label key={v} className="flex items-center gap-2 cursor-pointer text-sm text-[#c8bfb0]">
                        <input
                          type="radio"
                          name="calendar"
                          value={v}
                          checked={values.calendar === v}
                          onChange={() => set('calendar', v)}
                          className="accent-[#d4a648]"
                        />
                        {v.charAt(0).toUpperCase() + v.slice(1)}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <Label className="text-[#c8bfb0] text-sm">Visibility</Label>
                <div className="flex gap-4 mt-1">
                  {(['private', 'shared'] as const).map((v) => (
                    <label key={v} className="flex items-center gap-2 cursor-pointer text-sm text-[#c8bfb0]">
                      <input
                        type="radio"
                        name="visibility"
                        value={v}
                        checked={values.visibility === v}
                        onChange={() => set('visibility', v)}
                        className="accent-[#d4a648]"
                      />
                      {v.charAt(0).toUpperCase() + v.slice(1)}
                    </label>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── Section 4: Relationships ─────────────────────────── */}
          <Card className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-5 shadow-none ring-0">
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>4 · Relationships</SectionTitle></CardTitle>
            </CardHeader>
            <CardContent className="p-0 grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Relationship type</Label>
                  <select
                    value={values.relationship_type}
                    onChange={(e) => set('relationship_type', e.target.value as FormValues['relationship_type'])}
                    className={selectCls()}
                  >
                    <option value="self">Self</option>
                    <option value="client">Client</option>
                    <option value="research">Research</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <Label className="text-[#c8bfb0] text-sm">Reference chart ID</Label>
                  <Input
                    value={values.reference_chart_id}
                    onChange={(e) => set('reference_chart_id', e.target.value)}
                    placeholder="Optional"
                    className="bg-[#08070a] border-[#1a1820] text-[#f5f0e8] placeholder:text-[#5a5550]"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {errors.api && (
            <div role="alert" className="rounded-lg border border-[#9c3a2a]/40 bg-[#9c3a2a]/10 px-4 py-3 text-sm text-[#9c3a2a]">
              {errors.api}
            </div>
          )}

          <div className="flex justify-end gap-3 pb-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => router.back()}
              className="text-[#8a8070] hover:text-[#c8bfb0]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-[#d4a648] text-[#08070a] hover:bg-[#e8c878] font-medium px-6 disabled:opacity-50"
            >
              {submitting ? 'Creating chart…' : 'Create Chart'}
            </Button>
          </div>

        </form>
      </div>
    </div>
  )
}
