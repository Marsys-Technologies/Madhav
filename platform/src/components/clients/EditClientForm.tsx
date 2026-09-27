'use client'

import Link from 'next/link'
import { useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { EditRebuildConfirmDialog, type ChangedField } from '@/components/dialogs/EditRebuildConfirmDialog'
import { resolveTimezoneOffsetMinutes } from '@/lib/charts/updateChart'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils/date'
import { AYANAMSHA_OPTIONS, PlacesAutocompleteNew, TIMEZONES, type AyanamshaId } from './NewClientForm'
import { isGoogleMapsKeyConfigured, type PlacesResult } from './usePlacesAutocomplete'

/**
 * Chart-details correction form (Jātaka chart workspace, Task 7).
 *
 * Four groups — Identity, Birth coordinates, Time standard, Computation frame.
 * The computation hint here only chooses the button copy and whether to
 * confirm; `PATCH /api/charts/[id]` classifies authoritatively. The effective
 * offset shown is computed with the same resolver the server verifies against.
 */

export interface EditableChart {
  id: string
  name: string
  preferred_name: string | null
  subject_name: string | null
  birth_date: string
  /** HH:MM:SS as stored. */
  birth_time: string
  birth_place: string
  birth_lat: number | null
  birth_lng: number | null
  timezone_id: string | null
  /** Effective offset at the stored birth instant; null when the timezone is missing or invalid. */
  tz_offset_hours: number | null
  ayanamshas: string[]
}

interface FormState {
  full_name: string
  preferred_name: string
  subject_name: string
  birth_date: string
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_id: string
  ayanamshas: AyanamshaId[]
}

type FieldKey = keyof FormState
type FormErrors = Partial<Record<FieldKey, string>> & { api?: string }

const SERVER_FIELD_TO_FORM: Record<string, FieldKey> = {
  name: 'full_name',
  preferred_name: 'preferred_name',
  subject_name: 'subject_name',
  birth_date: 'birth_date',
  birth_time: 'birth_time',
  birth_place: 'birth_place',
  lat: 'latitude',
  lon: 'longitude',
  timezone_id: 'timezone_id',
  tz_offset: 'timezone_id',
  ayanamshas: 'ayanamshas',
}

const FIELD_LABELS: Record<FieldKey, string> = {
  full_name: 'Full name',
  preferred_name: 'Preferred name',
  subject_name: 'Subject label',
  birth_date: 'Date of birth',
  birth_time: 'Time of birth',
  birth_place: 'Birth place',
  latitude: 'Latitude',
  longitude: 'Longitude',
  timezone_id: 'Timezone',
  ayanamshas: 'Ayanāṃśas',
}

const DISPLAY_KEYS: FieldKey[] = ['full_name', 'preferred_name', 'subject_name']
const COMPUTATION_KEYS: FieldKey[] = ['birth_date', 'birth_time', 'birth_place', 'latitude', 'longitude', 'timezone_id', 'ayanamshas']

function initialTime(stored: string): string {
  const hhmmss = stored.slice(0, 8)
  return hhmmss.endsWith(':00') ? hhmmss.slice(0, 5) : hhmmss
}

function comparable(key: FieldKey, value: FormState[FieldKey]): string {
  if (Array.isArray(value)) return [...value].sort().join(',')
  const text = String(value).trim().replace(/\s+/g, ' ')
  if (key === 'birth_time') return text.length === 5 ? `${text}:00` : text
  if (key === 'latitude' || key === 'longitude') return text === '' ? '' : Number(text).toFixed(6)
  return text
}

function describe(key: FieldKey, value: FormState[FieldKey]): string {
  if (Array.isArray(value)) {
    return value.map((id) => AYANAMSHA_OPTIONS.find((o) => o.id === id)?.label ?? id).join(', ')
  }
  return String(value).trim()
}

function formatOffset(minutes: number): string {
  const sign = minutes < 0 ? '−' : '+'
  const abs = Math.abs(minutes)
  return `UTC${sign}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`
}

function isKnownZone(zone: string): boolean {
  try {
    new Intl.DateTimeFormat('en-US', { timeZone: zone }).format(0)
    return true
  } catch {
    return false
  }
}

function effectiveOffsetMinutes(form: FormState): number | null {
  if (!form.timezone_id || !form.birth_date || !form.birth_time) return null
  try {
    return resolveTimezoneOffsetMinutes(form.birth_date, form.birth_time, form.timezone_id)
  } catch {
    return null
  }
}

const INPUT =
  'jw-control w-full min-h-11 border bg-[#050505] px-3 text-sm text-[var(--jw-ink)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]'

function inputClass(error?: string) {
  return cn(INPUT, error ? 'border-[var(--jw-danger)]' : 'border-[var(--jw-rule)]')
}

function FieldError({ id, msg }: { id: string; msg?: string }) {
  if (!msg) return null
  return (
    <p id={id} className="text-xs text-[var(--jw-danger)]">
      {msg}
    </p>
  )
}

function Group({ legend, children }: { legend: string; children: React.ReactNode }) {
  return (
    <fieldset className="jw-panel grid gap-4 px-5 pb-5 pt-3">
      <legend className="jw-eyebrow px-1">{legend}</legend>
      {children}
    </fieldset>
  )
}

export function EditClientForm({ chart }: { chart: EditableChart }) {
  const router = useRouter()
  const submitRef = useRef<HTMLButtonElement>(null)

  const initial = useMemo<FormState>(
    () => ({
      full_name: chart.name,
      preferred_name: chart.preferred_name ?? '',
      subject_name: chart.subject_name ?? '',
      birth_date: chart.birth_date,
      birth_time: initialTime(chart.birth_time),
      birth_place: chart.birth_place,
      latitude: chart.birth_lat != null ? String(chart.birth_lat) : '',
      longitude: chart.birth_lng != null ? String(chart.birth_lng) : '',
      timezone_id: chart.timezone_id ?? '',
      ayanamshas: chart.ayanamshas.filter((a): a is AyanamshaId => AYANAMSHA_OPTIONS.some((o) => o.id === a)),
    }),
    [chart],
  )

  const [form, setForm] = useState<FormState>(initial)
  const [errors, setErrors] = useState<FormErrors>(
    chart.timezone_id && chart.tz_offset_hours !== null
      ? {}
      : { timezone_id: 'Choose the birth timezone before saving — it is missing or unrecognised.' },
  )
  const [loading, setLoading] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [placesUnavailable, setPlacesUnavailable] = useState(false)

  const changed = (key: FieldKey) => comparable(key, initial[key]) !== comparable(key, form[key])
  const requiresRecompute = COMPUTATION_KEYS.some(changed)
  const changes: ChangedField[] = [...DISPLAY_KEYS, ...COMPUTATION_KEYS].filter(changed).map((key) => ({
    key: key === 'full_name' ? 'name' : key,
    label: FIELD_LABELS[key],
    before: describe(key, initial[key]),
    after: describe(key, form[key]),
  }))
  const offsetMinutes = effectiveOffsetMinutes(form)
  // Birthplace edits are computation-safe (mirrors the server rule): a new place
  // must bring its own coordinates and timezone, never the former place's.
  const placeChanged = changed('birth_place')
  const locationIncomplete = placeChanged && !(changed('latitude') && changed('longitude'))
  const usePlaces = isGoogleMapsKeyConfigured() && !placesUnavailable
  const timezoneOptions = TIMEZONES.some((t) => t.value === form.timezone_id) || !form.timezone_id
    ? TIMEZONES.map((t) => t.value)
    : [form.timezone_id, ...TIMEZONES.map((t) => t.value)]

  function setField<K extends FieldKey>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined, api: undefined }))
  }

  function toggleAyanamsha(id: AyanamshaId) {
    setField(
      'ayanamshas',
      form.ayanamshas.includes(id) ? form.ayanamshas.filter((a) => a !== id) : [...form.ayanamshas, id],
    )
  }

  function handlePlaceResolved(result: PlacesResult) {
    // Place, coordinates and timezone come from the one selected location, together.
    const zone = result.timezone_id && isKnownZone(result.timezone_id) ? result.timezone_id : ''
    setForm((prev) => ({
      ...prev,
      birth_place: result.description,
      latitude: String(result.lat),
      longitude: String(result.lng),
      timezone_id: zone,
    }))
    setErrors((prev) => ({ ...prev, birth_place: undefined, latitude: undefined, longitude: undefined, timezone_id: undefined, api: undefined }))
  }

  function validate(): FormErrors {
    const errs: FormErrors = {}
    if (!form.full_name.trim()) errs.full_name = 'Full name is required.'
    if (!form.birth_date) errs.birth_date = 'Date of birth is required.'
    if (!form.birth_time) errs.birth_time = 'Time of birth is required.'
    if (!form.birth_place.trim()) errs.birth_place = 'Birth place is required.'
    if (form.latitude === '' || Number.isNaN(Number(form.latitude))) errs.latitude = 'Latitude is required.'
    if (form.longitude === '' || Number.isNaN(Number(form.longitude))) errs.longitude = 'Longitude is required.'
    if (!form.timezone_id || offsetMinutes === null) {
      errs.timezone_id = 'Choose the birth timezone before saving — it is missing or unrecognised.'
    }
    if (form.ayanamshas.length === 0) errs.ayanamshas = 'Select at least one ayanāṃśa.'
    if (locationIncomplete) {
      errs.birth_place = 'The birth place changed but its coordinates did not — reselect the new place so its latitude, longitude and timezone update together.'
      errs.latitude ??= 'Enter the latitude of the new place.'
      errs.longitude ??= 'Enter the longitude of the new place.'
    }
    return errs
  }

  async function submit() {
    setLoading(true)
    try {
      const response = await fetch(`/api/charts/${chart.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.full_name.trim(),
          preferred_name: form.preferred_name.trim() || null,
          subject_name: form.subject_name.trim() || null,
          birth_date: form.birth_date,
          birth_time: form.birth_time,
          birth_place: form.birth_place.trim(),
          lat: Number(form.latitude),
          lon: Number(form.longitude),
          timezone_id: form.timezone_id,
          tz_offset: (offsetMinutes ?? 0) / 60,
          ayanamshas: [...form.ayanamshas].sort(),
        }),
      })
      const body = await response.json().catch(() => ({}))

      // A committed degraded result: inputs corrected, old results cleared, the
      // rebuild did not start. The workspace explains it and offers the retry.
      if (response.status === 503 && body?.code === 'JOB_DISPATCH_FAILED' && body?.data?.runId) {
        router.push(`/clients/${chart.id}?status=needs-rebuild&run=${encodeURIComponent(body.data.runId)}`)
        router.refresh()
        return
      }
      if (!response.ok) {
        if (response.status === 409) {
          setErrors({ api: 'A build is in progress for this chart. Your changes are kept — save again when it finishes.' })
          return
        }
        const fieldErrors: FormErrors = {}
        for (const [serverKey, message] of Object.entries((body?.fields ?? {}) as Record<string, string>)) {
          const formKey = SERVER_FIELD_TO_FORM[serverKey]
          if (formKey) fieldErrors[formKey] ??= message
        }
        if (Object.keys(fieldErrors).length === 0) fieldErrors.api = body?.error ?? 'The chart could not be updated.'
        setErrors(fieldErrors)
        return
      }
      router.push(`/clients/${chart.id}`)
      router.refresh()
    } catch {
      setErrors({ api: 'Network error — your changes are kept. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const validation = validate()
    if (Object.keys(validation).length > 0) {
      setErrors(validation)
      return
    }
    if (requiresRecompute) setConfirmOpen(true)
    else void submit()
  }

  const fieldProps = (key: FieldKey) => ({
    id: key,
    'aria-invalid': errors[key] ? true : undefined,
    'aria-describedby': errors[key] ? `${key}-error` : undefined,
    className: inputClass(errors[key]),
  })

  const birthLine = [formatDate(chart.birth_date), initialTime(chart.birth_time), chart.birth_place].filter(Boolean).join(' · ')

  return (
    <div className="jw-root min-h-full px-4 py-8 sm:px-6">
      <div className="mx-auto flex max-w-2xl flex-col gap-6">
        <header className="flex flex-col gap-2">
          <Link
            href={`/clients/${chart.id}`}
            className="jw-touch inline-flex min-h-11 w-fit items-center text-xs uppercase tracking-[0.2em] text-[var(--jw-gold-dim)] hover:text-[var(--jw-gold)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
          >
            ← Jātaka workspace
          </Link>
          <p className="jw-eyebrow">Edit chart details</p>
          <h1 className="jw-display text-4xl">{chart.name}</h1>
          <p className="text-sm text-[var(--jw-ink-dim)]">{birthLine}</p>
        </header>

        <form onSubmit={handleSubmit} noValidate className="grid gap-5">
          <Group legend="Identity">
            <div className="grid gap-1.5">
              <label htmlFor="full_name" className="text-sm text-[var(--jw-ink-dim)]">Full name</label>
              <input type="text" maxLength={200} aria-required="true" value={form.full_name}
                onChange={(e) => setField('full_name', e.target.value)} {...fieldProps('full_name')} />
              <FieldError id="full_name-error" msg={errors.full_name} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <label htmlFor="preferred_name" className="text-sm text-[var(--jw-ink-dim)]">Preferred name</label>
                <input type="text" maxLength={100} value={form.preferred_name}
                  onChange={(e) => setField('preferred_name', e.target.value)} {...fieldProps('preferred_name')} />
                <FieldError id="preferred_name-error" msg={errors.preferred_name} />
              </div>
              <div className="grid gap-1.5">
                <label htmlFor="subject_name" className="text-sm text-[var(--jw-ink-dim)]">Subject label</label>
                <input type="text" maxLength={200} value={form.subject_name}
                  onChange={(e) => setField('subject_name', e.target.value)} {...fieldProps('subject_name')} />
                <FieldError id="subject_name-error" msg={errors.subject_name} />
              </div>
            </div>
          </Group>

          <Group legend="Birth coordinates">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <label htmlFor="birth_date" className="text-sm text-[var(--jw-ink-dim)]">Date of birth</label>
                <input type="date" min="1800-01-01" aria-required="true" value={form.birth_date}
                  onChange={(e) => setField('birth_date', e.target.value)} {...fieldProps('birth_date')} />
                <FieldError id="birth_date-error" msg={errors.birth_date} />
              </div>
              <div className="grid gap-1.5">
                <label htmlFor="birth_time" className="text-sm text-[var(--jw-ink-dim)]">Time of birth (24 h)</label>
                <input type="time" step={1} aria-required="true" value={form.birth_time}
                  onChange={(e) => setField('birth_time', e.target.value)} {...fieldProps('birth_time')} />
                <FieldError id="birth_time-error" msg={errors.birth_time} />
              </div>
            </div>
            {usePlaces && (
              <div className="grid gap-1.5">
                <span className="text-sm text-[var(--jw-ink-dim)]">Search for a new birth place</span>
                <PlacesAutocompleteNew
                  hasError={!!errors.birth_place}
                  onTextChange={() => undefined}
                  onPlaceResolved={handlePlaceResolved}
                  onLoadError={() => setPlacesUnavailable(true)}
                />
              </div>
            )}
            <div className="grid gap-1.5">
              <label htmlFor="birth_place" className="text-sm text-[var(--jw-ink-dim)]">Birth place</label>
              <input type="text" maxLength={300} aria-required="true" value={form.birth_place}
                onChange={(e) => setField('birth_place', e.target.value)} {...fieldProps('birth_place')} />
              <FieldError id="birth_place-error" msg={errors.birth_place} />
              {locationIncomplete && !errors.birth_place && (
                <p role="note" aria-label="Reselect location" className="text-xs text-amber-200/80">
                  Birth place changed — reselect it{usePlaces ? ' above' : ''} or enter the new place’s latitude, longitude and timezone.
                </p>
              )}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <label htmlFor="latitude" className="text-sm text-[var(--jw-ink-dim)]">Latitude</label>
                <input type="number" step="0.0001" min={-90} max={90} aria-required="true" value={form.latitude}
                  onChange={(e) => setField('latitude', e.target.value)} {...fieldProps('latitude')} />
                <FieldError id="latitude-error" msg={errors.latitude} />
              </div>
              <div className="grid gap-1.5">
                <label htmlFor="longitude" className="text-sm text-[var(--jw-ink-dim)]">Longitude</label>
                <input type="number" step="0.0001" min={-180} max={180} aria-required="true" value={form.longitude}
                  onChange={(e) => setField('longitude', e.target.value)} {...fieldProps('longitude')} />
                <FieldError id="longitude-error" msg={errors.longitude} />
              </div>
            </div>
          </Group>

          <Group legend="Time standard">
            <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
              <div className="grid gap-1.5">
                <label htmlFor="timezone_id" className="text-sm text-[var(--jw-ink-dim)]">Timezone</label>
                <select aria-required="true" value={form.timezone_id}
                  onChange={(e) => setField('timezone_id', e.target.value)} {...fieldProps('timezone_id')}>
                  <option value="" disabled>Select a timezone</option>
                  {timezoneOptions.map((zone) => (
                    <option key={zone} value={zone}>{zone}</option>
                  ))}
                </select>
              </div>
              <p className="min-h-11 content-center font-mono text-sm text-[var(--jw-gold)]" data-testid="effective-offset" aria-live="polite">
                {offsetMinutes === null ? '—' : formatOffset(offsetMinutes)}
                <span className="ml-2 font-sans text-xs text-[var(--jw-ink-dim)]">at birth</span>
              </p>
            </div>
            <FieldError id="timezone_id-error" msg={errors.timezone_id} />
          </Group>

          <Group legend="Computation frame">
            <div className="flex flex-wrap gap-2">
              {AYANAMSHA_OPTIONS.map((option) => {
                const checked = form.ayanamshas.includes(option.id)
                return (
                  <label
                    key={option.id}
                    className={cn(
                      'jw-control jw-touch flex min-h-11 cursor-pointer items-center gap-2 border px-3 text-sm',
                      checked ? 'border-[var(--jw-gold)] bg-[var(--jw-tint)] text-[var(--jw-ink)]' : 'border-[var(--jw-rule)] text-[var(--jw-ink-dim)]',
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleAyanamsha(option.id)}
                      aria-label={option.label}
                      className="h-4 w-4 accent-[#c9a24c]"
                    />
                    <span aria-hidden="true">{option.label}</span>
                    <span aria-hidden="true" className="font-mono text-[10px] text-[var(--jw-gold-dim)]">{option.sub}</span>
                  </label>
                )
              })}
            </div>
            <FieldError id="ayanamshas-error" msg={errors.ayanamshas} />
          </Group>

          {requiresRecompute && (
            <p role="note" className="text-sm text-[var(--jw-ink-dim)]">
              These changes affect the computed chart. Saving recomputes it and archives prior Paripraśna conversations as read-only history.
            </p>
          )}

          {errors.api && (
            <p role="alert" className="jw-panel border-[var(--jw-danger)] px-4 py-3 text-sm text-[var(--jw-danger)]">
              {errors.api}
            </p>
          )}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Link
              href={`/clients/${chart.id}`}
              className="jw-control jw-touch inline-flex min-h-11 items-center justify-center px-4 text-sm text-[var(--jw-ink-dim)] hover:text-[var(--jw-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
            >
              Cancel
            </Link>
            <button
              ref={submitRef}
              type="submit"
              disabled={loading}
              className="jw-control jw-touch min-h-11 bg-[var(--jw-gold)] px-6 text-sm font-medium text-black hover:bg-[#d8b25e] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)] focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:opacity-50"
            >
              {loading ? 'Saving…' : requiresRecompute ? 'Save and recompute' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>

      <EditRebuildConfirmDialog
        chartName={chart.name}
        open={confirmOpen}
        changes={changes}
        onCancel={() => {
          setConfirmOpen(false)
          // Return focus to the trigger now and again after the dialog's own
          // close/unmount focus handling has run.
          submitRef.current?.focus()
          requestAnimationFrame(() => submitRef.current?.focus())
        }}
        onConfirm={() => {
          setConfirmOpen(false)
          void submit()
        }}
      />
    </div>
  )
}
