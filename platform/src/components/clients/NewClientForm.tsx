'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

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
  gender: string
  birth_date: string
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_offset: string
  ayanamshas: AyanamshaId[]
}

interface FormErrors {
  full_name?: string
  gender?: string
  birth_date?: string
  birth_time?: string
  birth_place?: string
  latitude?: string
  longitude?: string
  timezone_offset?: string
  ayanamshas?: string
  api?: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayIso(): string {
  return new Date().toISOString().split('T')[0]
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

  const tz = parseFloat(form.timezone_offset)
  if (form.timezone_offset === '') {
    errors.timezone_offset = 'Timezone offset is required.'
  } else if (isNaN(tz) || tz < -14 || tz > 14) {
    errors.timezone_offset = 'Timezone offset must be between -14 and 14.'
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
    gender: '',
    birth_date: '',
    birth_time: '',
    birth_place: '',
    latitude: '',
    longitude: '',
    timezone_offset: '',
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
      const res = await fetch('/api/clients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: form.full_name.trim(),
          gender: form.gender,
          birth_date: form.birth_date,
          birth_time: form.birth_time,
          birth_place: form.birth_place.trim(),
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          timezone_offset: parseFloat(form.timezone_offset),
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
    <div className="container mx-auto py-8 px-4 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>New Client Chart</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} noValidate className="space-y-5">

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

            {/* Gender */}
            <div className="space-y-1">
              <Label htmlFor="gender">Gender <span aria-hidden="true" className="text-destructive">*</span></Label>
              <select
                id="gender"
                value={form.gender}
                aria-required="true"
                aria-invalid={!!errors.gender}
                onChange={(e) => setField('gender', e.target.value)}
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <option value="">Select gender…</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
              {errors.gender && (
                <p role="alert" className="text-sm text-destructive">{errors.gender}</p>
              )}
            </div>

            {/* Birth Date */}
            <div className="space-y-1">
              <Label htmlFor="birth_date">Birth Date <span aria-hidden="true" className="text-destructive">*</span></Label>
              <Input
                id="birth_date"
                type="date"
                min="1900-01-01"
                max={todayIso()}
                value={form.birth_date}
                aria-required="true"
                aria-invalid={!!errors.birth_date}
                onChange={(e) => setField('birth_date', e.target.value)}
              />
              {errors.birth_date && (
                <p role="alert" className="text-sm text-destructive">{errors.birth_date}</p>
              )}
            </div>

            {/* Birth Time */}
            <div className="space-y-1">
              <Label htmlFor="birth_time">Birth Time (local, HH:MM) <span aria-hidden="true" className="text-destructive">*</span></Label>
              <Input
                id="birth_time"
                type="time"
                value={form.birth_time}
                aria-required="true"
                aria-invalid={!!errors.birth_time}
                onChange={(e) => setField('birth_time', e.target.value)}
              />
              {errors.birth_time && (
                <p role="alert" className="text-sm text-destructive">{errors.birth_time}</p>
              )}
            </div>

            {/* Birth Place */}
            <div className="space-y-1">
              <Label htmlFor="birth_place">Birth Place <span aria-hidden="true" className="text-destructive">*</span></Label>
              <Input
                id="birth_place"
                type="text"
                placeholder="e.g. Bhubaneswar, Odisha, India"
                value={form.birth_place}
                aria-required="true"
                aria-invalid={!!errors.birth_place}
                onChange={(e) => setField('birth_place', e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Enter city/region. Latitude and longitude below will be used for precise computation.
              </p>
              {errors.birth_place && (
                <p role="alert" className="text-sm text-destructive">{errors.birth_place}</p>
              )}
            </div>

            {/* Lat / Lng row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label htmlFor="latitude">Latitude <span aria-hidden="true" className="text-destructive">*</span></Label>
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
                {errors.latitude && (
                  <p role="alert" className="text-sm text-destructive">{errors.latitude}</p>
                )}
              </div>

              <div className="space-y-1">
                <Label htmlFor="longitude">Longitude <span aria-hidden="true" className="text-destructive">*</span></Label>
                <Input
                  id="longitude"
                  type="number"
                  placeholder="e.g. 85.8246"
                  step="any"
                  min={-180}
                  max={180}
                  value={form.longitude}
                  aria-required="true"
                  aria-invalid={!!errors.longitude}
                  onChange={(e) => setField('longitude', e.target.value)}
                />
                {errors.longitude && (
                  <p role="alert" className="text-sm text-destructive">{errors.longitude}</p>
                )}
              </div>
            </div>

            {/* Timezone Offset */}
            <div className="space-y-1">
              <Label htmlFor="timezone_offset">Timezone Offset (UTC±, e.g. 5.5 for IST) <span aria-hidden="true" className="text-destructive">*</span></Label>
              <Input
                id="timezone_offset"
                type="number"
                placeholder="e.g. 5.5"
                step={0.5}
                min={-14}
                max={14}
                value={form.timezone_offset}
                aria-required="true"
                aria-invalid={!!errors.timezone_offset}
                onChange={(e) => setField('timezone_offset', e.target.value)}
              />
              {errors.timezone_offset && (
                <p role="alert" className="text-sm text-destructive">{errors.timezone_offset}</p>
              )}
            </div>

            {/* Ayanamsha multi-select */}
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Ayanamsha Systems{' '}
                <span aria-hidden="true" className="text-destructive">*</span>
                <span className="font-normal text-muted-foreground ml-1">(select at least one)</span>
              </legend>
              <div className="space-y-2 pt-1">
                {AYANAMSHA_OPTIONS.map((option) => {
                  const checked = form.ayanamshas.includes(option.id)
                  return (
                    <label
                      key={option.id}
                      className="flex items-center gap-2 cursor-pointer text-sm"
                    >
                      <input
                        type="checkbox"
                        name="ayanamsha"
                        value={option.id}
                        checked={checked}
                        aria-label={option.label}
                        onChange={() => toggleAyanamsha(option.id)}
                        className="h-4 w-4 rounded border-input accent-primary"
                      />
                      {option.label}
                    </label>
                  )
                })}
              </div>
              {errors.ayanamshas && (
                <p role="alert" className="text-sm text-destructive">{errors.ayanamshas}</p>
              )}
            </fieldset>

            {/* API error */}
            {errors.api && (
              <div role="alert" className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {errors.api}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
              aria-busy={loading}
            >
              {loading ? 'Creating chart…' : 'Create Chart & Start Build'}
            </Button>

          </form>
        </CardContent>
      </Card>
    </div>
  )
}
