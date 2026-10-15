/**
 * Authoritative chart-change validation, normalisation and classification
 * (Jātaka chart workspace, Task 6). The server decides whether an edit is
 * display-only or computation-affecting; the browser's hint never does.
 */
import { describe, expect, it } from 'vitest'
import {
  classifyChartChanges,
  normalizeChartUpdate,
  normalizeStoredChart,
  resolveTimezoneOffsetMinutes,
  type NormalizedChartInputs,
  type NormalizedChartUpdate,
  validateLocationChange,
} from '../updateChart'

const VALID = {
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar, Odisha',
  lat: 20.2961,
  lon: 85.8245,
  timezone_id: 'Asia/Kolkata',
  tz_offset: 5.5,
  ayanamshas: ['lahiri'],
}

const STORED_ROW = {
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar, Odisha',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  ayanamsa: 'lahiri',
}

function ok(input: unknown): NormalizedChartUpdate {
  const result = normalizeChartUpdate(input)
  if (!result.ok) throw new Error(`expected valid, got ${JSON.stringify(result.fields)}`)
  return result.value
}

function fieldsOf(input: unknown): Record<string, string> {
  const result = normalizeChartUpdate(input)
  if (result.ok) throw new Error('expected validation failure')
  return result.fields
}

const stored = normalizeStoredChart(STORED_ROW)

describe('normalizeChartUpdate', () => {
  it('normalises whitespace, time precision, ayanāṃśa order and duplicates', () => {
    const v = ok({
      ...VALID,
      name: '  Test   Native ',
      preferred_name: '  ',
      birth_place: ' Bhubaneswar,  Odisha ',
      birth_time: '10:43',
      ayanamshas: ['true_chitra', 'lahiri', 'lahiri'],
    })
    expect(v.name).toBe('Test Native')
    expect(v.preferred_name).toBeNull()
    expect(v.birth_place).toBe('Bhubaneswar, Odisha')
    expect(v.birth_time).toBe('10:43:00')
    expect(v.ayanamshas).toEqual(['lahiri', 'true_chitra'])
    expect(v.effective_tz_offset_minutes).toBe(330)
  })

  it('accepts seconds precision without changing it', () => {
    expect(ok({ ...VALID, birth_time: '10:43:27' }).birth_time).toBe('10:43:27')
  })

  it.each([
    ['name', { name: '   ' }],
    ['birth_date', { birth_date: '1984-02-30' }],
    ['birth_time', { birth_time: '25:00' }],
    ['lat', { lat: 91 }],
    ['lon', { lon: 'east' }],
    ['timezone_id', { timezone_id: 'Mars/Olympus_Mons' }],
    ['ayanamshas', { ayanamshas: [] }],
    ['ayanamshas', { ayanamshas: ['fagan_bradley'] }],
    ['tz_offset', { tz_offset: 99 }],
  ])('rejects a malformed %s', (field, patch) => {
    expect(Object.keys(fieldsOf({ ...VALID, ...patch }))).toContain(field)
  })

  it('rejects unknown fields (strict request shape)', () => {
    expect(normalizeChartUpdate({ ...VALID, owner_id: 'attacker' }).ok).toBe(false)
  })

  it('rejects a submitted offset that disagrees with the timezone at the birth instant', () => {
    expect(fieldsOf({ ...VALID, tz_offset: 5 })).toHaveProperty('tz_offset')
  })

  it('accepts an offset within one minute of the timezone’s effective offset', () => {
    expect(ok({ ...VALID, tz_offset: 5.5 + 0.5 / 60 }).effective_tz_offset_minutes).toBe(330)
  })

  it('rejects a non-object body', () => {
    expect(normalizeChartUpdate(null).ok).toBe(false)
    expect(normalizeChartUpdate('x').ok).toBe(false)
  })
})

describe('resolveTimezoneOffsetMinutes', () => {
  it('resolves the historical effective offset at the birth wall-clock time, including DST', () => {
    expect(resolveTimezoneOffsetMinutes('1984-02-05', '10:43:00', 'Asia/Kolkata')).toBe(330)
    expect(resolveTimezoneOffsetMinutes('2020-07-01', '12:00:00', 'America/New_York')).toBe(-240)
    expect(resolveTimezoneOffsetMinutes('2020-01-01', '12:00:00', 'America/New_York')).toBe(-300)
    // Nepal moved from +05:30 to +05:45 in 1986 — historical rules, not today's offset.
    expect(resolveTimezoneOffsetMinutes('1985-06-15', '08:00:00', 'Asia/Kathmandu')).toBe(330)
    expect(resolveTimezoneOffsetMinutes('1990-06-15', '08:00:00', 'Asia/Kathmandu')).toBe(345)
  })

  it('matches the orchestrator (zoneinfo, fold=0) inside a DST overlap: the earlier, pre-transition offset', () => {
    // 01:30 occurs twice in London on 2023-10-29; fold=0 is the first (BST).
    expect(resolveTimezoneOffsetMinutes('2023-10-29', '01:30:00', 'Europe/London')).toBe(60)
    expect(resolveTimezoneOffsetMinutes('2023-11-05', '01:30:00', 'America/New_York')).toBe(-240)
  })

  it('matches the orchestrator (zoneinfo, fold=0) inside a DST gap: the pre-transition offset', () => {
    // 02:30 does not exist in New York on 2023-03-12; fold=0 uses standard time.
    expect(resolveTimezoneOffsetMinutes('2023-03-12', '02:30:00', 'America/New_York')).toBe(-300)
    expect(resolveTimezoneOffsetMinutes('2023-03-26', '01:30:00', 'Europe/London')).toBe(0)
  })

  it('is unaffected next to, but outside, a transition', () => {
    expect(resolveTimezoneOffsetMinutes('2023-03-12', '03:30:00', 'America/New_York')).toBe(-240)
    expect(resolveTimezoneOffsetMinutes('2023-10-29', '02:30:00', 'Europe/London')).toBe(0)
  })

  it('throws for an unknown timezone', () => {
    expect(() => resolveTimezoneOffsetMinutes('1984-02-05', '10:43:00', 'Nowhere/Invalid')).toThrow()
  })
})

describe('normalizeStoredChart', () => {
  it('reads the legacy comma-separated ayanamsa column as a sorted list', () => {
    expect(normalizeStoredChart({ ...STORED_ROW, ayanamsa: 'true_chitra,lahiri' }).ayanamshas).toEqual(['lahiri', 'true_chitra'])
    expect(stored.ayanamshas).toEqual(['lahiri'])
  })

  it('keeps missing legacy values as null rather than inventing them', () => {
    const legacy = normalizeStoredChart({ ...STORED_ROW, timezone_id: null, birth_lat: null, birth_lng: null, ayanamsa: null })
    expect(legacy.timezone_id).toBeNull()
    expect(legacy.birth_lat).toBeNull()
    expect(legacy.ayanamshas).toEqual([])
  })
})

describe('classifyChartChanges', () => {
  const same = ok(VALID)

  it('an unchanged submission is a no-op', () => {
    expect(classifyChartChanges(stored, same)).toEqual({ mode: 'noop', changedFields: [] })
  })

  it('treats representation-only differences as unchanged', () => {
    const v = ok({ ...VALID, birth_time: '10:43:00', lat: 20.29610000001, name: ' Test  Native ' })
    expect(classifyChartChanges(stored, v).mode).toBe('noop')
  })

  it('a name-only change is display-only', () => {
    expect(classifyChartChanges(stored, { ...same, name: 'New display name' })).toEqual({
      mode: 'display-only',
      changedFields: ['name'],
    })
  })

  it('preferred and subject labels are display-only too', () => {
    expect(classifyChartChanges(stored, { ...same, preferred_name: 'Abhi', subject_name: 'Native A' })).toEqual({
      mode: 'display-only',
      changedFields: ['preferred_name', 'subject_name'],
    })
  })

  const changed = (field: keyof NormalizedChartInputs): NormalizedChartInputs => {
    const alter: Partial<NormalizedChartInputs> = {
      birth_date: '1984-02-06',
      birth_time: '10:44:00',
      birth_place: 'Cuttack',
      birth_lat: 20.4625,
      birth_lng: 85.883,
      timezone_id: 'Asia/Calcutta',
      ayanamshas: ['kp', 'lahiri'],
    }
    return { ...same, [field]: alter[field] }
  }

  for (const field of ['birth_date', 'birth_time', 'birth_place', 'birth_lat', 'birth_lng', 'timezone_id', 'ayanamshas'] as const) {
    it(`a ${field} change requires recomputation`, () => {
      expect(classifyChartChanges(stored, changed(field))).toEqual({ mode: 'recompute', changedFields: [field] })
    })
  }

  it('a mixed display + computation change recomputes and lists both', () => {
    expect(classifyChartChanges(stored, { ...changed('birth_time'), name: 'Renamed' })).toEqual({
      mode: 'recompute',
      changedFields: ['name', 'birth_time'],
    })
  })

  it('supplying a timezone to a legacy chart that had none recomputes', () => {
    const legacy = normalizeStoredChart({ ...STORED_ROW, timezone_id: null })
    expect(classifyChartChanges(legacy, same)).toEqual({ mode: 'recompute', changedFields: ['timezone_id'] })
  })
})

describe('validateLocationChange — birthplace edits are computation-safe', () => {
  const same = ok(VALID)

  it('accepts an unchanged place', () => {
    expect(validateLocationChange(stored, same)).toBeNull()
  })

  it('accepts a new place that arrives with its own coordinates and timezone', () => {
    expect(validateLocationChange(stored, { ...same, birth_place: 'Cuttack, Odisha', birth_lat: 20.4625, birth_lng: 85.883 })).toBeNull()
  })

  it('rejects a new place that keeps the former coordinates, naming what to reselect', () => {
    const fields = validateLocationChange(stored, { ...same, birth_place: 'Cuttack, Odisha' })
    expect(fields).not.toBeNull()
    expect(Object.keys(fields!).sort()).toEqual(['birth_place', 'lat', 'lon'])
    expect(fields!.birth_place).toMatch(/reselect/i)
    expect(fields!.lat).toMatch(/new place/i)
  })

  it('rejects a new place that changes only one coordinate', () => {
    const fields = validateLocationChange(stored, { ...same, birth_place: 'Cuttack, Odisha', birth_lat: 20.4625 })
    expect(fields).not.toBeNull()
    expect(Object.keys(fields!)).toContain('lon')
  })

  it('treats whitespace-only place differences as unchanged', () => {
    expect(validateLocationChange(stored, ok({ ...VALID, birth_place: ' Bhubaneswar,  Odisha ' }))).toBeNull()
  })

  it('allows correcting coordinates for the same place', () => {
    expect(validateLocationChange(stored, { ...same, birth_lat: 20.3 })).toBeNull()
  })

  describe('timezone plausibility', () => {
    const NEW_YORK = { birth_place: 'New York, USA', birth_lat: 40.7128, birth_lng: -74.006 }

    it('rejects a new place whose coordinates arrived but whose timezone is still the former place\'s', () => {
      const fields = validateLocationChange(stored, { ...same, ...NEW_YORK, timezone_id: 'Asia/Kolkata' })
      expect(fields).not.toBeNull()
      expect(Object.keys(fields!)).toEqual(['timezone_id'])
      expect(fields!.timezone_id).toMatch(/timezone/i)
    })

    it('accepts a new place with its own timezone', () => {
      expect(validateLocationChange(stored, { ...same, ...NEW_YORK, timezone_id: 'America/New_York' })).toBeNull()
    })

    it('rejects a timezone-only change that does not fit the coordinates', () => {
      expect(validateLocationChange(stored, { ...same, timezone_id: 'America/New_York' })).toHaveProperty('timezone_id')
    })

    it.each([
      ['a single-zone country far from its meridian (Kashgar on China time)', { birth_place: 'Kashgar', birth_lat: 39.47, birth_lng: 75.99, timezone_id: 'Asia/Shanghai' }],
      ['a zone across the date line (Kiritimati, UTC+14)', { birth_place: 'Kiritimati', birth_lat: 1.87, birth_lng: -157.43, timezone_id: 'Pacific/Kiritimati' }],
      ['western Europe on central European time', { birth_place: 'A Coruña', birth_lat: 43.36, birth_lng: -8.41, timezone_id: 'Europe/Madrid' }],
    ])('accepts %s', (_label, place) => {
      expect(validateLocationChange(stored, { ...same, ...place })).toBeNull()
    })

    it('never blocks an edit that does not touch the location', () => {
      const oddStored = { ...stored, timezone_id: 'America/New_York' }
      expect(validateLocationChange(oddStored, { ...same, timezone_id: 'America/New_York', name: 'Renamed' })).toBeNull()
    })
  })
})

describe('ayanamsha spelling and omission (SS N-319)', () => {
  it('folds long and legacy stored spellings to the short ids, deduplicated and ordered', () => {
    const row = (ayanamsa: string | null) => normalizeStoredChart({ ...STORED_ROW, ayanamsa }).ayanamshas
    expect(row('lahiri_chitrapaksha')).toEqual(['lahiri'])
    expect(row('krishnamurti, lahiri_chitrapaksha,lahiri')).toEqual(['kp', 'lahiri'])
    expect(row('surya_siddhanta_classical,raman,true_citra')).toEqual(['raman', 'surya_siddhanta', 'true_chitra'])
  })

  it('keeps True Chitra distinct from Lahiri', () => {
    expect(normalizeStoredChart({ ...STORED_ROW, ayanamsa: 'true_chitra' }).ayanamshas).toEqual(['true_chitra'])
  })

  it('keeps an id it does not recognise (never silently dropped)', () => {
    expect(normalizeStoredChart({ ...STORED_ROW, ayanamsa: 'lahiri,fagan_bradley' }).ayanamshas).toEqual(['fagan_bradley', 'lahiri'])
  })

  it('a long-form stored list and the equivalent short list in another order classify as no-op', () => {
    const longStored = normalizeStoredChart({ ...STORED_ROW, ayanamsa: 'krishnamurti,lahiri_chitrapaksha' })
    expect(classifyChartChanges(longStored, ok({ ...VALID, ayanamshas: ['lahiri', 'kp'] }))).toEqual({ mode: 'noop', changedFields: [] })
    expect(classifyChartChanges(longStored, ok({ ...VALID, ayanamshas: ['kp', 'lahiri'] }))).toEqual({ mode: 'noop', changedFields: [] })
  })

  it('a genuinely different set is still an ayanamshas change', () => {
    const longStored = normalizeStoredChart({ ...STORED_ROW, ayanamsa: 'lahiri_chitrapaksha' })
    expect(classifyChartChanges(longStored, ok({ ...VALID, ayanamshas: ['lahiri', 'raman'] }))).toEqual({
      mode: 'recompute',
      changedFields: ['ayanamshas'],
    })
  })

  it('accepts a request without ayanamshas and flags it as omitted', () => {
    const { ayanamshas: _omit, ...rest } = VALID
    void _omit
    const v = ok(rest)
    expect(v.ayanamshas_omitted).toBe(true)
    expect(v.ayanamshas).toEqual([])
    expect(ok(VALID).ayanamshas_omitted).toBe(false)
  })

  it('still rejects an empty ayanamshas list when one is sent', () => {
    expect(Object.keys(fieldsOf({ ...VALID, ayanamshas: [] }))).toContain('ayanamshas')
  })

  it('reads confirm_destructive as a strict boolean, false by default', () => {
    expect(ok(VALID).confirm_destructive).toBe(false)
    expect(ok({ ...VALID, confirm_destructive: true }).confirm_destructive).toBe(true)
    expect(ok({ ...VALID, confirm_destructive: false }).confirm_destructive).toBe(false)
    expect(Object.keys(fieldsOf({ ...VALID, confirm_destructive: 'yes' }))).toContain('confirm_destructive')
  })
})
