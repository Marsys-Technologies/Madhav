import { z } from 'zod'
import { VALID_AYANAMSHAS } from '@/lib/ayanamsha'

/**
 * Chart-update request contract, normalisation and authoritative change
 * classification (Jātaka chart workspace, Task 6).
 *
 * The server compares normalised stored and submitted values; the browser's
 * `isBirthAffecting` hint only chooses copy. Display-only: name, preferred
 * name, subject label. Computation-affecting: birth date, time, place,
 * coordinates, timezone (and so its effective offset) and selected ayanāṃśas.
 *
 * `tz_offset` is not stored: the orchestrator derives the offset from
 * `charts.timezone_id` at the birth instant, so a submitted offset is only
 * checked for agreement with that derivation.
 */

export const ChartUpdateInputSchema = z.strictObject({
  name: z.string().trim().min(1).max(200),
  preferred_name: z.string().trim().max(100).nullable().optional(),
  subject_name: z.string().trim().max(200).nullable().optional(),
  birth_date: z.iso.date(),
  birth_time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/),
  birth_place: z.string().trim().min(1).max(300),
  lat: z.number().finite().min(-90).max(90),
  lon: z.number().finite().min(-180).max(180),
  timezone_id: z.string().trim().min(1).max(100),
  tz_offset: z.number().finite().min(-14).max(14),
  ayanamshas: z.array(z.enum(VALID_AYANAMSHAS)).min(1),
})

export type ChartUpdateInput = z.infer<typeof ChartUpdateInputSchema>

/** Chart-defining inputs in one canonical representation, stored or submitted. */
export interface NormalizedChartInputs {
  name: string
  preferred_name: string | null
  subject_name: string | null
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number | null
  birth_lng: number | null
  timezone_id: string | null
  ayanamshas: string[]
}

export type NormalizedChartUpdate = NormalizedChartInputs & {
  birth_lat: number
  birth_lng: number
  timezone_id: string
  effective_tz_offset_minutes: number
}

export type ChartChangeField = keyof NormalizedChartInputs

export const DISPLAY_FIELDS = ['name', 'preferred_name', 'subject_name'] as const satisfies readonly ChartChangeField[]
export const COMPUTATION_FIELDS = [
  'birth_date',
  'birth_time',
  'birth_place',
  'birth_lat',
  'birth_lng',
  'timezone_id',
  'ayanamshas',
] as const satisfies readonly ChartChangeField[]

export type ChartChangeClassification =
  | { mode: 'noop'; changedFields: [] }
  | { mode: 'display-only' | 'recompute'; changedFields: ChartChangeField[] }

/** Coordinates are compared at 1e-6° (~0.1 m): NUMERIC round-trips never read as a change. */
const COORDINATE_DECIMALS = 6

function collapse(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

function nullableLabel(value: string | null | undefined): string | null {
  if (value === null || value === undefined) return null
  const collapsed = collapse(value)
  return collapsed === '' ? null : collapsed
}

function normalizeTime(value: string): string {
  const [h, m, s = '00'] = value.split(':')
  return `${h.padStart(2, '0')}:${m.padStart(2, '0')}:${s.padStart(2, '0')}`
}

function roundCoordinate(value: number | null): number | null {
  if (value === null || !Number.isFinite(value)) return null
  return Number(value.toFixed(COORDINATE_DECIMALS))
}

function normalizeAyanamshas(values: readonly string[]): string[] {
  return [...new Set(values.map((v) => v.trim()).filter(Boolean))].sort()
}

function zoneOffsetMinutesAt(instantMs: number, timeZone: string): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(new Date(instantMs))
  const get = (type: Intl.DateTimeFormatPartTypes) => Number(parts.find((p) => p.type === type)?.value)
  const wallAsUtc = Date.UTC(get('year'), get('month') - 1, get('day'), get('hour'), get('minute'), get('second'))
  return Math.round((wallAsUtc - instantMs) / 60000)
}

const DAY_MS = 86_400_000

/**
 * Effective UTC offset (minutes) of an IANA zone at a local wall-clock birth
 * time, honouring historical rules and DST. Throws for an unknown zone.
 *
 * Matches the orchestrator (`birth_params.py`: `ZoneInfo(...).utcoffset()` on a
 * naive datetime, i.e. fold=0): inside a DST overlap the earlier occurrence and
 * inside a DST gap the pre-transition offset — in both cases the offset in force
 * before the transition, when that offset reads the wall time, or when neither does.
 */
export function resolveTimezoneOffsetMinutes(birthDate: string, birthTime: string, timeZone: string): number {
  // Throws RangeError for an unknown zone.
  new Intl.DateTimeFormat('en-US', { timeZone }).format(0)
  const [y, mo, d] = birthDate.split('-').map(Number)
  const [h, mi, s] = normalizeTime(birthTime).split(':').map(Number)
  const wallAsUtc = Date.UTC(y, mo - 1, d, h, mi, s)
  const before = zoneOffsetMinutesAt(wallAsUtc - DAY_MS, timeZone)
  const after = zoneOffsetMinutesAt(wallAsUtc + DAY_MS, timeZone)
  const readsWall = (offset: number) => zoneOffsetMinutesAt(wallAsUtc - offset * 60000, timeZone) === offset
  if (before === after) {
    const firstGuess = zoneOffsetMinutesAt(wallAsUtc, timeZone)
    return zoneOffsetMinutesAt(wallAsUtc - firstGuess * 60000, timeZone)
  }
  if (readsWall(before)) return before // unique before-transition time, or an overlap (fold=0)
  if (readsWall(after)) return after // unique after-transition time
  return before // a gap: fold=0 keeps the pre-transition offset
}

/** True for a timezone the runtime recognises as an IANA zone. Shared with the edit form. */
export function isKnownTimeZone(timeZone: string): boolean {
  try {
    new Intl.DateTimeFormat('en-US', { timeZone }).format(0)
    return true
  } catch {
    return false
  }
}

export function normalizeChartUpdate(
  input: unknown,
): { ok: true; value: NormalizedChartUpdate } | { ok: false; fields: Record<string, string> } {
  const parsed = ChartUpdateInputSchema.safeParse(input)
  if (!parsed.success) {
    const fields: Record<string, string> = {}
    for (const issue of parsed.error.issues) {
      const key = issue.path.length > 0 ? String(issue.path[0]) : issue.code === 'unrecognized_keys' ? 'body' : 'body'
      fields[key] ??= issue.message
    }
    return { ok: false, fields }
  }
  const data = parsed.data
  if (!isKnownTimeZone(data.timezone_id)) {
    return { ok: false, fields: { timezone_id: 'Unknown IANA timezone identifier' } }
  }
  const birthTime = normalizeTime(data.birth_time)
  const effective = resolveTimezoneOffsetMinutes(data.birth_date, birthTime, data.timezone_id)
  if (Math.abs(data.tz_offset * 60 - effective) > 1) {
    return {
      ok: false,
      fields: {
        tz_offset: `Offset disagrees with ${data.timezone_id} at the birth time (expected ${effective / 60} hours)`,
      },
    }
  }
  return {
    ok: true,
    value: {
      name: collapse(data.name),
      preferred_name: nullableLabel(data.preferred_name),
      subject_name: nullableLabel(data.subject_name),
      birth_date: data.birth_date,
      birth_time: birthTime,
      birth_place: collapse(data.birth_place),
      birth_lat: roundCoordinate(data.lat)!,
      birth_lng: roundCoordinate(data.lon)!,
      timezone_id: data.timezone_id,
      ayanamshas: normalizeAyanamshas(data.ayanamshas),
      effective_tz_offset_minutes: effective,
    },
  }
}

export interface StoredChartRow {
  name: string
  preferred_name: string | null
  subject_name: string | null
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number | string | null
  birth_lng: number | string | null
  timezone_id: string | null
  /** Legacy single-value column; holds the selected list comma-joined. */
  ayanamsa: string | null
}

export function normalizeStoredChart(row: StoredChartRow): NormalizedChartInputs {
  const coordinate = (value: number | string | null) => (value === null ? null : roundCoordinate(Number(value)))
  return {
    name: collapse(row.name),
    preferred_name: nullableLabel(row.preferred_name),
    subject_name: nullableLabel(row.subject_name),
    birth_date: String(row.birth_date).slice(0, 10),
    birth_time: normalizeTime(String(row.birth_time).slice(0, 8)),
    birth_place: collapse(row.birth_place),
    birth_lat: coordinate(row.birth_lat),
    birth_lng: coordinate(row.birth_lng),
    timezone_id: row.timezone_id ? row.timezone_id.trim() : null,
    ayanamshas: normalizeAyanamshas((row.ayanamsa ?? '').split(',')),
  }
}

function sameValue(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => v === b[i])
  return a === b
}

export function classifyChartChanges(
  stored: NormalizedChartInputs,
  submitted: NormalizedChartInputs,
): ChartChangeClassification {
  const changed = (field: ChartChangeField) => !sameValue(stored[field], submitted[field])
  const display = DISPLAY_FIELDS.filter(changed)
  const computation = COMPUTATION_FIELDS.filter(changed)
  const changedFields: ChartChangeField[] = [...display, ...computation]
  if (changedFields.length === 0) return { mode: 'noop', changedFields: [] }
  return { mode: computation.length > 0 ? 'recompute' : 'display-only', changedFields }
}

/**
 * Birthplace edits are computation-safe: a new place must arrive with its own
 * coordinates (and the timezone the form resolved with them), never with the
 * former place's coordinates silently kept. Returns field errors naming what to
 * reselect, or null. Correcting coordinates for the same place is allowed.
 */
export function validateLocationChange(
  stored: NormalizedChartInputs,
  submitted: NormalizedChartInputs,
): Record<string, string> | null {
  const placeChanged = stored.birth_place !== submitted.birth_place
  const latChanged = stored.birth_lat !== submitted.birth_lat
  const lonChanged = stored.birth_lng !== submitted.birth_lng
  if (placeChanged && !(latChanged && lonChanged)) {
    const reselect = 'The birth place changed but its coordinates did not — reselect the new place so its latitude, longitude and timezone update together.'
    return {
      birth_place: reselect,
      lat: 'Enter the latitude of the new place.',
      lon: 'Enter the longitude of the new place.',
    }
  }
  const locationChanged = placeChanged || latChanged || lonChanged || stored.timezone_id !== submitted.timezone_id
  if (locationChanged && !isTimezonePlausible(submitted)) {
    return {
      timezone_id: 'This timezone does not fit the birth place’s longitude — reselect the place or choose its timezone.',
    }
  }
  return null
}

/** Largest accepted gap between a zone's offset and the longitude's solar time. */
const MAX_ZONE_SOLAR_GAP_MINUTES = 4 * 60

/**
 * Plausibility, not proof: the zone's effective offset at the birth moment
 * must lie within four hours of the longitude's mean solar time (wrapping
 * across the date line). Real zones stay well inside that — single-zone
 * countries, date-line zones and DST included — while a zone left over from a
 * distant former place falls outside it. Nearby wrong zones are not caught.
 */
function isTimezonePlausible(inputs: NormalizedChartInputs): boolean {
  if (inputs.birth_lng === null || !inputs.timezone_id) return true
  let offset: number
  try {
    offset = resolveTimezoneOffsetMinutes(inputs.birth_date, inputs.birth_time, inputs.timezone_id)
  } catch {
    return false
  }
  const gap = Math.abs(offset - inputs.birth_lng * 4) % 1440
  return Math.min(gap, 1440 - gap) <= MAX_ZONE_SOLAR_GAP_MINUTES
}
