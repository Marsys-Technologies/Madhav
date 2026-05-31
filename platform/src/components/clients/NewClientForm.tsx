'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { derivePreferredName } from './form_schema'
import { cn } from '@/lib/utils'

// ─── Ayanamsha options ────────────────────────────────────────────────────────

export const AYANAMSHA_OPTIONS = [
  { id: 'lahiri',           label: 'Lahiri',            sub: 'Chitrapaksha' },
  { id: 'true_chitra',      label: 'True Chitra',       sub: 'Revati paksha' },
  { id: 'kp',               label: 'KP',                sub: 'Krishnamurti' },
  { id: 'raman',            label: 'Raman',             sub: 'B.V. Raman' },
  { id: 'surya_siddhanta',  label: 'Surya Siddhanta',   sub: 'Classical drik' },
] as const

export type AyanamshaId = (typeof AYANAMSHA_OPTIONS)[number]['id']

// ─── Timezones ────────────────────────────────────────────────────────────────

export const TIMEZONES = [
  { value: 'Asia/Kolkata',        label: 'Asia/Kolkata (UTC+5:30)',   offset: 5.5 },
  { value: 'UTC',                 label: 'UTC (UTC+0)',               offset: 0 },
  { value: 'Asia/Colombo',        label: 'Asia/Colombo (UTC+5:30)',   offset: 5.5 },
  { value: 'Asia/Kathmandu',      label: 'Asia/Kathmandu (UTC+5:45)', offset: 5.75 },
  { value: 'Asia/Dhaka',          label: 'Asia/Dhaka (UTC+6)',        offset: 6 },
  { value: 'Asia/Dubai',          label: 'Asia/Dubai (UTC+4)',        offset: 4 },
  { value: 'Asia/Singapore',      label: 'Asia/Singapore (UTC+8)',    offset: 8 },
  { value: 'Asia/Tokyo',          label: 'Asia/Tokyo (UTC+9)',        offset: 9 },
  { value: 'America/New_York',    label: 'America/New_York (UTC-5)',  offset: -5 },
  { value: 'America/Chicago',     label: 'America/Chicago (UTC-6)',   offset: -6 },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (UTC-8)', offset: -8 },
  { value: 'Europe/London',       label: 'Europe/London (UTC+0)',     offset: 0 },
  { value: 'Europe/Berlin',       label: 'Europe/Berlin (UTC+1)',     offset: 1 },
  { value: 'Australia/Sydney',    label: 'Australia/Sydney (UTC+10)', offset: 10 },
] as const

// ─── Single form state ────────────────────────────────────────────────────────

interface FormState {
  full_name: string
  preferred_name: string
  gender: 'M' | 'F' | 'O' | 'unknown' | ''
  birth_date: string          // YYYY-MM-DD from <input type="date">
  birth_time: string          // HH:MM from <input type="time">
  birth_place: string
  latitude: string            // string for controlled input; parseFloat on submit
  longitude: string
  timezone_id: string         // IANA, e.g. Asia/Kolkata
  tz_offset: string           // derived from timezone_id; user-editable override
  ayanamshas: AyanamshaId[]
  places_resolved: boolean    // true when Places autocomplete succeeded
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
  if (!found) return ''
  return String(found.offset)
}

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {}

  if (!form.full_name.trim()) {
    errors.full_name = 'Full name is required.'
  } else if (form.full_name.trim().length > 200) {
    errors.full_name = 'Full name must be 200 characters or fewer.'
  }

  if (!form.gender) {
    errors.gender = 'Please select a gender.'
  }

  if (!form.birth_date) {
    errors.birth_date = 'Birth date is required.'
  } else if (form.birth_date < '1900-01-01') {
    errors.birth_date = 'Birth date must be on or after 1900-01-01.'
  } else if (form.birth_date > todayIso()) {
    errors.birth_date = 'Birth date cannot be in the future.'
  }

  if (!form.birth_time) {
    errors.birth_time = 'Birth time is required.'
  }

  if (!form.birth_place.trim()) {
    errors.birth_place = 'Birth place is required.'
  }

  const lat = parseFloat(form.latitude)
  if (form.latitude === '') {
    errors.latitude = 'Latitude is required.'
  } else if (isNaN(lat) || lat < -90 || lat > 90) {
    errors.latitude = 'Latitude must be between -90 and 90.'
  }

  const lng = parseFloat(form.longitude)
  if (form.longitude === '') {
    errors.longitude = 'Longitude is required.'
  } else if (isNaN(lng) || lng < -180 || lng > 180) {
    errors.longitude = 'Longitude must be between -180 and 180.'
  }

  const tz = parseFloat(form.tz_offset)
  if (form.tz_offset === '') {
    errors.tz_offset = 'Timezone offset is required.'
  } else if (isNaN(tz) || tz < -14 || tz > 14) {
    errors.tz_offset = 'Timezone offset must be between -14 and 14.'
  }

  if (form.ayanamshas.length === 0) {
    errors.ayanamshas = 'At least one ayanamsha must be selected.'
  }

  return errors
}

// ─── Subcomponents ────────────────────────────────────────────────────────────

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3
      style={{
        fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
        fontStyle: 'italic',
        fontSize: 18,
        color: 'var(--gold-primary, #d4a648)',
        fontWeight: 500,
      }}
    >
      {children}
    </h3>
  )
}

function MicroLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-sans, Inter, sans-serif)',
        fontSize: 10,
        letterSpacing: '0.08em',
        textTransform: 'uppercase' as const,
        color: 'var(--text-tertiary, #5d5b54)',
      }}
    >
      {children}
    </span>
  )
}

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null
  return (
    <p role="alert" style={{ fontSize: 12, color: '#c0392b', marginTop: 2 }}>
      {msg}
    </p>
  )
}

function inputCls(hasError?: boolean): string {
  return cn(
    'w-full rounded-md border bg-[#08070a] px-3 py-2 text-sm text-[#f5f0e8] outline-none focus:ring-1 focus:ring-[#d4a648]',
    hasError ? 'border-red-500' : 'border-[#1f1c17]',
  )
}

function selectCls(hasError?: boolean): string {
  return cn(
    'w-full rounded-md border bg-[#08070a] px-3 py-2 text-sm text-[#f5f0e8] outline-none focus:ring-1 focus:ring-[#d4a648]',
    hasError ? 'border-red-500' : 'border-[#1f1c17]',
  )
}

// ─── Section container ────────────────────────────────────────────────────────

function Section({
  testId,
  title,
  children,
}: {
  testId: string
  title: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div
      data-testid={testId}
      style={{
        background: 'var(--obsidian-panel, #0a0908)',
        border: '1px solid var(--obsidian-border, #1f1c17)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ marginBottom: 16 }}>{title}</div>
      <div style={{ display: 'grid', gap: 16 }}>{children}</div>
    </div>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

export function NewClientForm() {
  const router = useRouter()

  const [form, setForm] = useState<FormState>({
    full_name: '',
    preferred_name: '',
    gender: '',
    birth_date: '',
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
  const [loading, setLoading] = useState(false)
  const [manualOpen, setManualOpen] = useState(true)

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  function handleTimezoneChange(tzId: string) {
    const offset = offsetFromTimezoneId(tzId)
    setForm((prev) => ({ ...prev, timezone_id: tzId, tz_offset: offset }))
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

  function handleBirthPlaceBlur() {
    if (form.birth_place.trim() && !form.places_resolved) {
      setManualOpen(true)
    }
  }

  // ── Submit ───────────────────────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const validationErrors = validate(form)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setLoading(true)
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

      if (res.status === 409 || (res.ok && data.idempotent)) {
        router.push(data.redirect_url ?? `/clients/${data.chart_id}/build`)
        return
      }

      if (res.status === 422) {
        const fieldMap: Record<string, keyof FormErrors> = {
          lat: 'latitude',
          lon: 'longitude',
          tz_offset: 'tz_offset',
          name: 'full_name',
          birth_date: 'birth_date',
          birth_time: 'birth_time',
          birth_place: 'birth_place',
          gender: 'gender',
          ayanamshas: 'ayanamshas',
        }
        const newErrors: FormErrors = {}
        for (const err of data.errors ?? []) {
          const uiKey = fieldMap[err.field] ?? ('api' as keyof FormErrors)
          newErrors[uiKey] = err.message
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

      router.push(data.redirect_url ?? `/clients/${data.chart_id}/build`)
    } catch {
      setErrors({ api: 'Network error — please check your connection and try again.' })
    } finally {
      setLoading(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  const nodeCount = form.ayanamshas.length * 28

  return (
    <div
      className="min-h-screen px-4 py-10"
      style={{ background: 'var(--obsidian-bg, #08070a)', color: 'var(--text-primary, #e8e6df)' }}
    >
      <div className="mx-auto max-w-2xl">

        {/* ── Header bar ──────────────────────────────────────────── */}
        <div data-testid="form-header" className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              style={{
                fontFamily: 'var(--font-serif, serif)',
                fontSize: 22,
                color: 'var(--gold-primary, #d4a648)',
                lineHeight: 1,
              }}
            >
              ॥
            </span>
            <span
              style={{
                fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
                fontSize: 18,
                color: 'var(--gold-primary, #d4a648)',
                fontWeight: 500,
                letterSpacing: '0.04em',
              }}
            >
              MARSYS
            </span>
            <MicroLabel>Jyotish Instrument</MicroLabel>
          </div>
          <div className="flex items-center gap-3">
            <span
              style={{
                fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                fontSize: 10,
                color: 'var(--text-tertiary, #5d5b54)',
                letterSpacing: '0.08em',
              }}
            >
              Charts · New
            </span>
          </div>
        </div>

        {/* ── Hero ──────────────────────────────────────────────────── */}
        <div className="mb-8">
          <h1
            data-testid="form-title"
            style={{
              fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
              fontStyle: 'italic',
              fontSize: 36,
              color: 'var(--gold-primary, #d4a648)',
              lineHeight: 1.15,
              marginBottom: 8,
            }}
          >
            Naya Yantra
          </h1>
          <p
            style={{
              fontFamily: 'var(--font-sans, Inter, sans-serif)',
              fontSize: 13,
              color: 'var(--text-secondary, #888373)',
            }}
          >
            Enter the birth details below to instantiate a new Jyotish instrument. Fields marked * are required.
          </p>
        </div>

        {/* ── Form ─────────────────────────────────────────────────── */}
        <form onSubmit={handleSubmit} noValidate style={{ display: 'grid', gap: 16 }}>

          {/* ══ Section 1: Vyakti · Identity ════════════════════════ */}
          <Section
            testId="section-identity"
            title={<SectionTitle>Vyakti · Identity</SectionTitle>}
          >
            {/* Row 1: Full name */}
            <div className="flex flex-col gap-1">
              <Label htmlFor="full_name" className="text-[#c8bfb0] text-sm">
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
                className={inputCls(!!errors.full_name)}
                onChange={(e) => setField('full_name', e.target.value)}
              />
              <FieldError msg={errors.full_name} />
            </div>

            {/* Row 2: Preferred name + Gender */}
            <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 200px' }}>
              <div className="flex flex-col gap-1">
                <Label htmlFor="preferred_name" className="text-[#c8bfb0] text-sm">
                  Preferred name
                </Label>
                <Input
                  id="preferred_name"
                  type="text"
                  placeholder="Defaults to first word of full name"
                  value={form.preferred_name}
                  maxLength={100}
                  className={inputCls()}
                  onChange={(e) => setField('preferred_name', e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-1">
                <Label htmlFor="gender" className="text-[#c8bfb0] text-sm">
                  Gender *
                </Label>
                <select
                  id="gender"
                  value={form.gender}
                  aria-invalid={!!errors.gender}
                  className={selectCls(!!errors.gender)}
                  onChange={(e) => setField('gender', e.target.value as FormState['gender'])}
                >
                  <option value="">— select —</option>
                  <option value="unknown">Prefer not to say</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
                <FieldError msg={errors.gender} />
              </div>
            </div>
          </Section>

          {/* ══ Section 2: Janma Sthana · Birth coordinates ══════════ */}
          <Section
            testId="section-birth"
            title={<SectionTitle>Janma Sthana · Birth coordinates</SectionTitle>}
          >
            {/* Row 1: Date + Time */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_date" className="text-[#c8bfb0] text-sm">
                  Date *
                </Label>
                <input
                  id="birth_date"
                  type="date"
                  value={form.birth_date}
                  min="1900-01-01"
                  max={todayIso()}
                  aria-required="true"
                  aria-invalid={!!errors.birth_date}
                  className={inputCls(!!errors.birth_date)}
                  onChange={(e) => setField('birth_date', e.target.value)}
                />
                <FieldError msg={errors.birth_date} />
              </div>

              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_time" className="text-[#c8bfb0] text-sm">
                  Time (24 h) *
                </Label>
                <input
                  id="birth_time"
                  type="time"
                  value={form.birth_time}
                  aria-required="true"
                  aria-invalid={!!errors.birth_time}
                  className={inputCls(!!errors.birth_time)}
                  onChange={(e) => setField('birth_time', e.target.value)}
                />
                <FieldError msg={errors.birth_time} />
              </div>
            </div>

            {/* Row 2: Birth place */}
            <div className="flex flex-col gap-1">
              <Label htmlFor="birth_place" className="text-[#c8bfb0] text-sm">
                Birth place *
              </Label>
              <Input
                id="birth_place"
                type="text"
                placeholder="e.g. Bhubaneswar, Odisha, India"
                value={form.birth_place}
                aria-required="true"
                aria-invalid={!!errors.birth_place}
                className={inputCls(!!errors.birth_place)}
                onChange={(e) => {
                  setField('birth_place', e.target.value)
                  if (!e.target.value.trim()) {
                    setForm((prev) => ({ ...prev, places_resolved: false }))
                  }
                }}
                onBlur={handleBirthPlaceBlur}
              />
              <FieldError msg={errors.birth_place} />
            </div>

            {/* Row 3: Resolved indicator */}
            {form.places_resolved && (
              <div
                data-testid="places-resolved-indicator"
                style={{ fontSize: 12, color: '#27ae60', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span>✓</span>
                <span>
                  {form.latitude}, {form.longitude} · {form.timezone_id} · UTC
                  {parseFloat(form.tz_offset) >= 0 ? '+' : ''}{form.tz_offset}
                </span>
              </div>
            )}

            {/* Row 4: Manual override accordion */}
            <div
              data-testid="manual-override-accordion"
              style={{ borderRadius: 8, border: '1px solid #1f1c17', overflow: 'hidden' }}
            >
              <button
                type="button"
                onClick={() => setManualOpen((v) => !v)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 16px',
                  fontSize: 12,
                  color: '#8a8070',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <span>Manual override · latitude / longitude / timezone</span>
                <span style={{ fontSize: 10 }}>{manualOpen ? '▲' : '▼'}</span>
              </button>

              {manualOpen && (
                <div style={{ padding: '0 16px 16px', display: 'grid', gap: 12 }}>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1">
                      <Label htmlFor="latitude" className="text-[#c8bfb0] text-sm">
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
                        className={inputCls(!!errors.latitude)}
                        onChange={(e) => setField('latitude', e.target.value)}
                      />
                      <FieldError msg={errors.latitude} />
                    </div>

                    <div className="flex flex-col gap-1">
                      <Label htmlFor="longitude" className="text-[#c8bfb0] text-sm">
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
                        className={inputCls(!!errors.longitude)}
                        onChange={(e) => setField('longitude', e.target.value)}
                      />
                      <FieldError msg={errors.longitude} />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <Label htmlFor="timezone_id" className="text-[#c8bfb0] text-sm">
                      Timezone
                    </Label>
                    <select
                      id="timezone_id"
                      value={form.timezone_id}
                      className={selectCls()}
                      onChange={(e) => handleTimezoneChange(e.target.value)}
                    >
                      {TIMEZONES.map((tz) => (
                        <option key={tz.value} value={tz.value}>
                          {tz.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex flex-col gap-1">
                    <Label htmlFor="tz_offset" className="text-[#c8bfb0] text-sm">
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
                      className={inputCls(!!errors.tz_offset)}
                      onChange={(e) => setField('tz_offset', e.target.value)}
                    />
                    <FieldError msg={errors.tz_offset} />
                  </div>
                </div>
              )}
            </div>
          </Section>

          {/* ══ Section 3: Ganana · Compute ══════════════════════════ */}
          <Section
            testId="section-compute"
            title={<SectionTitle>Ganana · Compute</SectionTitle>}
          >
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {AYANAMSHA_OPTIONS.map((opt) => {
                const checked = form.ayanamshas.includes(opt.id)
                return (
                  <label
                    key={opt.id}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 2,
                      cursor: 'pointer',
                      borderRadius: 8,
                      border: `1px solid ${checked ? '#d4a648' : '#1f1c17'}`,
                      padding: '10px 14px',
                      background: checked ? 'rgba(212,166,72,0.06)' : 'transparent',
                      minWidth: 120,
                      transition: 'border-color 0.15s',
                    }}
                  >
                    <input
                      type="checkbox"
                      style={{ display: 'none' }}
                      checked={checked}
                      aria-label={opt.label}
                      onChange={() => toggleAyanamsha(opt.id)}
                    />
                    <span
                      style={{
                        fontSize: 13,
                        fontWeight: 500,
                        color: checked ? '#d4a648' : '#c8bfb0',
                      }}
                    >
                      {opt.label}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        color: checked ? 'rgba(212,166,72,0.6)' : '#5d5b54',
                        fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                        letterSpacing: '0.04em',
                      }}
                    >
                      {opt.sub}
                    </span>
                  </label>
                )
              })}
            </div>
            <FieldError msg={errors.ayanamshas} />
          </Section>

          {/* ── API error ─────────────────────────────────────────── */}
          {errors.api && (
            <div
              role="alert"
              style={{
                borderRadius: 8,
                border: '1px solid rgba(156,58,42,0.4)',
                background: 'rgba(156,58,42,0.1)',
                padding: '12px 16px',
                fontSize: 13,
                color: '#c0392b',
              }}
            >
              {errors.api}
            </div>
          )}

          {/* ── Footer ───────────────────────────────────────────── */}
          <div
            data-testid="form-footer"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 16 }}
          >
            <span
              data-testid="footer-microcopy"
              style={{
                fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                fontSize: 11,
                color: 'var(--text-tertiary, #5d5b54)',
              }}
            >
              {form.ayanamshas.length} ayanamshas × 28 assets = {nodeCount} nodes will be built
            </span>
            <div style={{ display: 'flex', gap: 12 }}>
              <Button
                type="button"
                variant="ghost"
                onClick={() => router.back()}
                style={{
                  color: 'var(--text-secondary, #888373)',
                  fontFamily: 'var(--font-sans, Inter, sans-serif)',
                  fontSize: 13,
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading}
                style={{
                  background: 'var(--gold-primary, #d4a648)',
                  color: 'var(--obsidian-bg, #08070a)',
                  fontFamily: 'var(--font-sans, Inter, sans-serif)',
                  fontSize: 13,
                  fontWeight: 500,
                  padding: '0 24px',
                  opacity: loading ? 0.5 : 1,
                }}
              >
                {loading ? 'Computing…' : 'Compute chart'}
              </Button>
            </div>
          </div>

        </form>
      </div>
    </div>
  )
}
