'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { derivePreferredName } from './form_schema'

// ─── Ayanamsha options ────────────────────────────────────────────────────────

export const AYANAMSHA_OPTIONS = [
  { id: 'lahiri', label: 'Lahiri (Chitrapaksha)' },
  { id: 'true_chitra', label: 'True Chitra (Revati)' },
  { id: 'kp', label: 'KP (Krishnamurti Paddhati)' },
  { id: 'raman', label: 'B.V. Raman' },
  { id: 'surya_siddhanta', label: 'Surya Siddhanta' },
] as const

export type AyanamshaId = (typeof AYANAMSHA_OPTIONS)[number]['id']

// ─── Form state ───────────────────────────────────────────────────────────────

interface FormState {
  full_name: string
  preferred_name: string        // D-S1: defaults to first word of full_name
  gender: string
  birth_date: string
  birth_date_ui: string         // D-S1: DD MM YYYY alternative UI entry
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_offset: string
  timezone_id: string           // D-S1: IANA TZ e.g. "Asia/Kolkata"
  ayanamshas: AyanamshaId[]
}

interface FormErrors {
  full_name?: string
  preferred_name?: string
  gender?: string
  birth_date?: string
  birth_date_ui?: string
  birth_time?: string
  birth_place?: string
  latitude?: string
  longitude?: string
  timezone_offset?: string
  timezone_id?: string
  ayanamshas?: string
  api?: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayIso(): string {
  return new Date().toISOString().split('T')[0]
}

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

  const tz = parseFloat(form.timezone_offset)
  if (form.timezone_offset === '') {
    errors.timezone_offset = 'Timezone offset is required.'
  } else if (isNaN(tz) || tz < -14 || tz > 14) {
    errors.timezone_offset = 'Timezone offset must be between -14 and 14.'
  }

  if (!form.timezone_id || !form.timezone_id.trim()) {
    errors.timezone_id = 'Timezone is required.'
  }

  if (form.ayanamshas.length === 0) {
    errors.ayanamshas = 'At least one ayanamsha must be selected.'
  }

  return errors
}

// ─── Component ────────────────────────────────────────────────────────────────

export function NewClientForm() {
  const router = useRouter()

  const [form, setForm] = useState<FormState>({
    full_name: '',
    preferred_name: '',
    gender: '',
    birth_date: '',
    birth_date_ui: '',
    birth_time: '',
    birth_place: '',
    latitude: '',
    longitude: '',
    timezone_offset: '',
    timezone_id: 'Asia/Kolkata',
    ayanamshas: AYANAMSHA_OPTIONS.map((o) => o.id),
  })

  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(false)

  // ── Field helpers ────────────────────────────────────────────────────────

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    // Clear the individual field error on change
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
      const preferred_name = derivePreferredName(form.full_name, form.preferred_name)
      const res = await fetch('/api/clients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: form.full_name.trim(),
          preferred_name,
          gender: form.gender,
          birth_date: form.birth_date,
          birth_time: form.birth_time,
          birth_place: form.birth_place.trim(),
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          timezone_offset: parseFloat(form.timezone_offset),
          timezone_id: form.timezone_id,
          ayanamshas: form.ayanamshas,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setErrors({ api: data?.error ?? 'Failed to create client. Please try again.' })
        return
      }

      router.push(data.redirect_url ?? `/clients/${data.id}/build`)
    } catch {
      setErrors({ api: 'Network error — please check your connection and try again.' })
    } finally {
      setLoading(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div
      className="min-h-screen px-4 py-10"
      style={{ background: 'var(--obsidian-bg, #08070a)', color: 'var(--text-primary, #e8e6df)' }}
    >
      <div className="mx-auto max-w-2xl">
        {/* ── Header bar ─────────────────────────────────────────── */}
        <div
          data-testid="form-header"
          className="flex items-center justify-between mb-6"
        >
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
            <span
              data-testid="step-pill"
              style={{
                fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                fontSize: 10,
                color: 'var(--gold-primary, #d4a648)',
                background: 'rgba(212,166,72,0.12)',
                border: '1px solid rgba(212,166,72,0.3)',
                borderRadius: 999,
                padding: '2px 10px',
              }}
            >
              Step 1 of 2
            </span>
          </div>
        </div>

        {/* ── Hero ────────────────────────────────────────────────── */}
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

            {/* Full Name */}
            <div className="space-y-1">
              <Label htmlFor="full_name">Full Name <span aria-hidden="true" className="text-destructive">*</span></Label>
              <Input
                id="full_name"
                type="text"
                placeholder="e.g. Abhisek Mohanty"
                value={form.full_name}
                maxLength={200}
                aria-required="true"
                aria-invalid={!!errors.full_name}
                onChange={(e) => setField('full_name', e.target.value)}
              />
              {errors.full_name && (
                <p role="alert" className="text-sm text-destructive">{errors.full_name}</p>
              )}
            </div>

          {/* ── Section 1: Vyakti · Identity ─────────────────────── */}
          <Card
            data-testid="section-identity"
            style={{ background: 'var(--obsidian-panel, #0a0908)', border: '1px solid var(--obsidian-border, #1f1c17)', borderRadius: 12, padding: 20 }}
            className="shadow-none ring-0"
          >
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>Vyakti · Identity</SectionTitle></CardTitle>
            </CardHeader>
            <CardContent className="p-0 grid gap-4">
              <div className="flex flex-col gap-1">
                <Label className="text-[#c8bfb0] text-sm">Full name *</Label>
                <Input
                  id="latitude"
                  type="number"
                  placeholder="e.g. 20.2960"
                  step="any"
                  min={-90}
                  max={90}
                  value={form.latitude}
                  aria-required="true"
                  aria-invalid={!!errors.latitude}
                  onChange={(e) => setField('latitude', e.target.value)}
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

          {/* ── Section 2: Janma Sthana · Birth coordinates ────── */}
          <Card
            data-testid="section-birth"
            style={{ background: 'var(--obsidian-panel, #0a0908)', border: '1px solid var(--obsidian-border, #1f1c17)', borderRadius: 12, padding: 20 }}
            className="shadow-none ring-0"
          >
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>Janma Sthana · Birth coordinates</SectionTitle></CardTitle>
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

          {/* ── Section 3: Ganana · Compute ─────────────────────── */}
          <Card
            data-testid="section-compute"
            style={{ background: 'var(--obsidian-panel, #0a0908)', border: '1px solid var(--obsidian-border, #1f1c17)', borderRadius: 12, padding: 20 }}
            className="shadow-none ring-0"
          >
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>Ganana · Compute</SectionTitle></CardTitle>
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

          {/* ── Section 4: Sambandha · Relationships ─────────────── */}
          <Card
            style={{ background: 'var(--obsidian-panel, #0a0908)', border: '1px solid var(--obsidian-border, #1f1c17)', borderRadius: 12, padding: 20 }}
            className="shadow-none ring-0"
          >
            <CardHeader className="p-0 pb-4">
              <CardTitle><SectionTitle>Sambandha · Relationships</SectionTitle></CardTitle>
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

          <div
            data-testid="form-footer"
            className="flex items-center justify-between pb-4"
          >
            <span
              data-testid="footer-microcopy"
              style={{
                fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                fontSize: 11,
                color: 'var(--text-tertiary, #5d5b54)',
              }}
            >
              5 ayanamshas × 28 assets = 140 nodes
            </span>
            <div className="flex gap-3">
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
                disabled={submitting}
                style={{
                  background: 'var(--gold-primary, #d4a648)',
                  color: 'var(--obsidian-bg, #08070a)',
                  fontFamily: 'var(--font-sans, Inter, sans-serif)',
                  fontSize: 13,
                  fontWeight: 500,
                  padding: '0 24px',
                  opacity: submitting ? 0.5 : 1,
                }}
              >
                {submitting ? 'Computing…' : 'Compute chart'}
              </Button>
            </div>
          </div>

          </form>
        </CardContent>
      </Card>
    </div>
  )
}
