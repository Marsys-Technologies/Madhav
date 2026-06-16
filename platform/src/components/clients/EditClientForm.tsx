'use client'

import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { EditRebuildConfirmDialog } from '@/components/dialogs/EditRebuildConfirmDialog'
import { cn } from '@/lib/utils'
import { AYANAMSHA_OPTIONS } from './NewClientForm'
import type { AyanamshaId } from './NewClientForm'

interface ChartData {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number | null
  birth_lng: number | null
  ayanamsa: string
}

interface Props {
  chart: ChartData
}

interface FormState {
  full_name: string
  birth_date: string
  birth_time: string
  birth_place: string
  latitude: string
  longitude: string
  timezone_id: string
  tz_offset: string
  ayanamshas: AyanamshaId[]
}

interface FormErrors {
  full_name?: string
  birth_date?: string
  birth_time?: string
  birth_place?: string
  latitude?: string
  longitude?: string
  tz_offset?: string
  ayanamshas?: string
  api?: string
}

function isBirthAffecting(original: FormState, current: FormState): boolean {
  return (
    original.birth_date !== current.birth_date ||
    original.birth_time !== current.birth_time ||
    original.birth_place !== current.birth_place ||
    original.latitude !== current.latitude ||
    original.longitude !== current.longitude ||
    original.tz_offset !== current.tz_offset ||
    JSON.stringify(original.ayanamshas.sort()) !== JSON.stringify(current.ayanamshas.sort())
  )
}

function todayIso() {
  return new Date().toISOString().split('T')[0]
}

function inputCls(hasError?: boolean): string {
  return cn(
    'w-full rounded-md border bg-[#08070a] px-3 py-2 text-sm text-[#f5f0e8] outline-none focus:ring-1 focus:ring-[#d4a648]',
    hasError ? 'border-red-500' : 'border-[#1f1c17]',
  )
}

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null
  return <p role="alert" style={{ fontSize: 12, color: '#c0392b', marginTop: 2 }}>{msg}</p>
}

export function EditClientForm({ chart }: Props) {
  const router = useRouter()

  const initialAyanamshas: AyanamshaId[] = chart.ayanamsa
    ? (chart.ayanamsa.split(',').filter((a) =>
        AYANAMSHA_OPTIONS.some((o) => o.id === a)
      ) as AyanamshaId[])
    : AYANAMSHA_OPTIONS.map((o) => o.id)

  const initial: FormState = {
    full_name: chart.name,
    birth_date: chart.birth_date,
    birth_time: chart.birth_time,
    birth_place: chart.birth_place,
    latitude: chart.birth_lat != null ? String(chart.birth_lat) : '',
    longitude: chart.birth_lng != null ? String(chart.birth_lng) : '',
    timezone_id: 'Asia/Kolkata',
    tz_offset: '5.5',
    ayanamshas: initialAyanamshas.length > 0 ? initialAyanamshas : AYANAMSHA_OPTIONS.map((o) => o.id),
  }

  const [form, setForm] = useState<FormState>(initial)
  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const pendingSubmitRef = useRef(false)

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
  }

  function validate(): FormErrors {
    const errs: FormErrors = {}
    if (!form.full_name.trim()) errs.full_name = 'Full name is required.'
    if (!form.birth_date) errs.birth_date = 'Birth date is required.'
    else if (form.birth_date < '1900-01-01') errs.birth_date = 'Birth date must be on or after 1900-01-01.'
    else if (form.birth_date > todayIso()) errs.birth_date = 'Birth date cannot be in the future.'
    if (!form.birth_time) errs.birth_time = 'Birth time is required.'
    if (!form.birth_place.trim()) errs.birth_place = 'Birth place is required.'
    if (form.latitude === '') errs.latitude = 'Latitude is required.'
    if (form.longitude === '') errs.longitude = 'Longitude is required.'
    if (form.ayanamshas.length === 0) errs.ayanamshas = 'At least one ayanamsha must be selected.'
    return errs
  }

  async function doSubmit() {
    setLoading(true)
    setErrors({})
    try {
      const res = await fetch(`/api/clients/${chart.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.full_name.trim(),
          birth_date: form.birth_date,
          birth_time: form.birth_time,
          birth_place: form.birth_place.trim(),
          lat: parseFloat(form.latitude),
          lon: parseFloat(form.longitude),
          tz_offset: parseFloat(form.tz_offset),
          timezone_id: form.timezone_id,
          ayanamshas: form.ayanamshas,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setErrors({ api: data?.error ?? 'Update failed.' })
        return
      }
      if (isBirthAffecting(initial, form)) {
        router.push(`/clients/${chart.id}/nirmana`)
      } else {
        router.push('/dashboard')
      }
    } catch {
      setErrors({ api: 'Network error — please try again.' })
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const validationErrors = validate()
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    if (isBirthAffecting(initial, form)) {
      pendingSubmitRef.current = true
      setConfirmOpen(true)
    } else {
      await doSubmit()
    }
  }

  return (
    <div
      className="min-h-screen px-4 py-10"
      style={{ background: 'var(--obsidian-bg, #08070a)', color: 'var(--text-primary, #e8e6df)' }}
    >
      <div className="mx-auto max-w-2xl">

        {/* Rebuild warning banner */}
        <div
          role="note"
          style={{
            borderRadius: 8,
            border: '1px solid rgba(212,175,55,0.3)',
            background: 'rgba(212,175,55,0.06)',
            padding: '12px 16px',
            marginBottom: 24,
            fontSize: 13,
            color: '#d4a648',
          }}
        >
          Editing birth details will rebuild this entire chart (Gaṇita → Mīmāṃsā) from scratch.
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1
            style={{
              fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
              fontStyle: 'italic',
              fontSize: 36,
              color: 'var(--gold-primary, #d4a648)',
              lineHeight: 1.15,
              marginBottom: 8,
            }}
          >
            Edit · {chart.name}
          </h1>
        </div>

        <form onSubmit={handleSubmit} noValidate style={{ display: 'grid', gap: 16 }}>

          {/* Name */}
          <div
            style={{ background: '#0a0908', border: '1px solid #1f1c17', borderRadius: 12, padding: 20 }}
          >
            <div className="flex flex-col gap-1">
              <Label htmlFor="full_name" className="text-[#c8bfb0] text-sm">Full name *</Label>
              <Input
                id="full_name"
                type="text"
                value={form.full_name}
                maxLength={200}
                aria-required="true"
                aria-invalid={!!errors.full_name}
                className={inputCls(!!errors.full_name)}
                onChange={(e) => setField('full_name', e.target.value)}
              />
              <FieldError msg={errors.full_name} />
            </div>
          </div>

          {/* Birth fields */}
          <div
            style={{ background: '#0a0908', border: '1px solid #1f1c17', borderRadius: 12, padding: 20, display: 'grid', gap: 16 }}
          >
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_date" className="text-[#c8bfb0] text-sm">Date *</Label>
                <input
                  id="birth_date"
                  type="date"
                  value={form.birth_date}
                  min="1900-01-01"
                  max={todayIso()}
                  aria-required="true"
                  className={inputCls(!!errors.birth_date)}
                  onChange={(e) => setField('birth_date', e.target.value)}
                />
                <FieldError msg={errors.birth_date} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="birth_time" className="text-[#c8bfb0] text-sm">Time (24 h) *</Label>
                <input
                  id="birth_time"
                  type="time"
                  value={form.birth_time}
                  aria-required="true"
                  className={inputCls(!!errors.birth_time)}
                  onChange={(e) => setField('birth_time', e.target.value)}
                />
                <FieldError msg={errors.birth_time} />
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="birth_place" className="text-[#c8bfb0] text-sm">Birth place *</Label>
              <Input
                id="birth_place"
                type="text"
                value={form.birth_place}
                aria-required="true"
                className={inputCls(!!errors.birth_place)}
                onChange={(e) => setField('birth_place', e.target.value)}
              />
              <FieldError msg={errors.birth_place} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <Label htmlFor="latitude" className="text-[#c8bfb0] text-sm">Latitude *</Label>
                <input
                  id="latitude"
                  type="number"
                  step="0.0001"
                  min={-90}
                  max={90}
                  value={form.latitude}
                  aria-required="true"
                  className={inputCls(!!errors.latitude)}
                  onChange={(e) => setField('latitude', e.target.value)}
                />
                <FieldError msg={errors.latitude} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="longitude" className="text-[#c8bfb0] text-sm">Longitude *</Label>
                <input
                  id="longitude"
                  type="number"
                  step="0.0001"
                  min={-180}
                  max={180}
                  value={form.longitude}
                  aria-required="true"
                  className={inputCls(!!errors.longitude)}
                  onChange={(e) => setField('longitude', e.target.value)}
                />
                <FieldError msg={errors.longitude} />
              </div>
            </div>
          </div>

          {/* Ayanamsha */}
          <div
            style={{ background: '#0a0908', border: '1px solid #1f1c17', borderRadius: 12, padding: 20 }}
          >
            <h3
              style={{
                fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
                fontStyle: 'italic',
                fontSize: 18,
                color: 'var(--gold-primary, #d4a648)',
                fontWeight: 500,
                marginBottom: 12,
              }}
            >
              Ganana · Compute
            </h3>
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
                    <span style={{ fontSize: 13, fontWeight: 500, color: checked ? '#d4a648' : '#c8bfb0' }}>
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
          </div>

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

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, paddingBottom: 16 }}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => router.back()}
              style={{ color: '#888373', fontSize: 13 }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              style={{
                background: 'var(--gold-primary, #d4a648)',
                color: 'var(--obsidian-bg, #08070a)',
                fontSize: 13,
                fontWeight: 500,
                padding: '0 24px',
                opacity: loading ? 0.5 : 1,
              }}
            >
              {loading ? 'Saving…' : 'Save changes'}
            </Button>
          </div>
        </form>
      </div>

      <EditRebuildConfirmDialog
        chartName={chart.name}
        open={confirmOpen}
        onCancel={() => {
          setConfirmOpen(false)
          pendingSubmitRef.current = false
        }}
        onConfirm={() => {
          setConfirmOpen(false)
          doSubmit()
        }}
      />
    </div>
  )
}
