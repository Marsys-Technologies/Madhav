/**
 * kala_period_snapshot.test.ts — BRAHMA-KA-3-3: period_snapshot contract tests
 *
 * Tests run without a live DB — validates the embedded Vimshottari schedule
 * logic and the shape/provenance contract of computePeriodSnapshot.
 *
 * Contract gates (KA-3-3):
 *   ✓ period_snapshot("2010-01-01") returns non-null dasha (Saturn MD)
 *   ✓ period_snapshot("2002-01-01") returns Saturn MD
 *   ✓ provenance_envelope is present on every snapshot
 *   ✓ source_citation = "PyJHora/SwissEph DE441 + Brahma-L1" on all rows
 *   ✓ severity values are floats — checked as range, not exact value
 *   ✓ tool smoke: computePeriodSnapshot resolves without throw
 *
 * BRAHMA-KA-3-3
 */

import { describe, it, expect, beforeAll } from 'vitest'
import {
  computePeriodSnapshot,
} from '../src/tools/kala_period_snapshot.js'
import type { PeriodSnapshotResult } from '../src/tools/kala_period_snapshot.js'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SOURCE_CITATION_EXPECTED = 'PyJHora/SwissEph DE441 + Brahma-L1'

// ── Schedule integrity via computePeriodSnapshot ──────────────────────────────
// The schedule is internal to the module; we verify it through public API calls.

describe('schedule integrity (via computePeriodSnapshot)', () => {
  it('Saturn MD starts at 1991-08-21: snapshot for that date returns Saturn MD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '1991-08-21')
    expect(snap.active_dasha).toBe('Saturn')
  })

  it('Mercury MD starts at 2010-08-21: snapshot for that date returns Mercury MD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-08-21')
    expect(snap.active_dasha).toBe('Mercury')
  })

  it('Saturn MD ends before Mercury starts: 2010-08-20 is still Saturn MD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-08-20')
    expect(snap.active_dasha).toBe('Saturn')
  })

  it('dasha_period.start and .end are non-empty strings', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(typeof snap.dasha_period?.start).toBe('string')
    expect(typeof snap.dasha_period?.end).toBe('string')
    expect(snap.dasha_period!.start.length).toBeGreaterThan(0)
    expect(snap.dasha_period!.end.length).toBeGreaterThan(0)
  })

  it('dasha_row_id follows DSH.V.NNN format', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.dasha_row_id).toMatch(/^DSH\.V\.\d{3}$/)
  })
})

// ── computePeriodSnapshot — dasha state ───────────────────────────────────────

describe('computePeriodSnapshot — dasha state', () => {
  it('AC1: 2010-01-01 returns non-null active_dasha (Saturn MD)', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-01-01')
    expect(snap.active_dasha).not.toBeNull()
    expect(snap.active_dasha).toBe('Saturn')
  })

  it('AC2: 2002-01-01 returns Saturn MD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.active_dasha).toBe('Saturn')
  })

  it('2010-08-21 returns Mercury MD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-08-21')
    expect(snap.active_dasha).toBe('Mercury')
  })

  it('2005-04-03 returns Saturn MD / Rahu AD', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2005-04-03')
    expect(snap.active_dasha).toBe('Saturn')
    expect(snap.active_antardasha).toBe('Rahu')
  })

  it('dasha_row_id is non-null for 2002-01-01', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.dasha_row_id).not.toBeNull()
    expect(typeof snap.dasha_row_id).toBe('string')
  })

  it('dasha_period start <= snapshot_date < end for 2010-01-01', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-01-01')
    expect(snap.dasha_period).not.toBeNull()
    const start = new Date(snap.dasha_period!.start).getTime()
    const end = new Date(snap.dasha_period!.end).getTime()
    const target = new Date('2010-01-01').getTime()
    expect(start).toBeLessThanOrEqual(target)
    expect(target).toBeLessThan(end)
  })
})

// ── computePeriodSnapshot — result shape ──────────────────────────────────────

describe('computePeriodSnapshot — result shape', () => {
  let snap: PeriodSnapshotResult

  beforeAll(async () => {
    snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2010-01-01')
  })

  it('chart_id matches input', () => {
    expect(snap.chart_id).toBe(NATIVE_CHART_ID)
  })

  it('snapshot_date matches input', () => {
    expect(snap.snapshot_date).toBe('2010-01-01')
  })

  it('active_signals_count is non-negative', () => {
    expect(snap.active_signals_count).toBeGreaterThanOrEqual(0)
  })

  it('convergence_score is in [0.0, 1.0]', () => {
    expect(snap.convergence_score).toBeGreaterThanOrEqual(0.0)
    expect(snap.convergence_score).toBeLessThanOrEqual(1.0)
  })

  it('obstructions is an array', () => {
    expect(Array.isArray(snap.obstructions)).toBe(true)
  })

  it('contains all required top-level keys', () => {
    const required: Array<keyof PeriodSnapshotResult> = [
      'chart_id',
      'snapshot_date',
      'active_dasha',
      'active_antardasha',
      'dasha_row_id',
      'dasha_period',
      'transit_positions',
      'active_signals_count',
      'convergence_score',
      'obstructions',
      'provenance_envelope',
    ]
    for (const key of required) {
      expect(snap).toHaveProperty(key)
    }
  })
})

// ── computePeriodSnapshot — provenance_envelope ───────────────────────────────

describe('computePeriodSnapshot — provenance_envelope', () => {
  it('provenance_envelope is present', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.provenance_envelope).toBeDefined()
    expect(snap.provenance_envelope).not.toBeNull()
  })

  it('provenance_envelope.source_citation equals canonical constant', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.provenance_envelope.source_citation).toBe(SOURCE_CITATION_EXPECTED)
  })

  it('provenance_envelope has required keys', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    const env = snap.provenance_envelope
    expect(env).toHaveProperty('source')
    expect(env).toHaveProperty('source_citation')
    expect(env).toHaveProperty('computed_at')
    expect(env).toHaveProperty('chart_id')
    expect(env).toHaveProperty('snapshot_date')
  })

  it('provenance_envelope.chart_id matches input', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.provenance_envelope.chart_id).toBe(NATIVE_CHART_ID)
  })

  it('provenance_envelope.snapshot_date matches input', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    expect(snap.provenance_envelope.snapshot_date).toBe('2002-01-01')
  })

  it('provenance_envelope.computed_at is a valid ISO timestamp string', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2002-01-01')
    const ts = snap.provenance_envelope.computed_at
    expect(typeof ts).toBe('string')
    expect(new Date(ts).getTime()).toBeGreaterThan(0)
  })
})

// ── tool smoke ────────────────────────────────────────────────────────────────

describe('tool smoke', () => {
  it('computePeriodSnapshot resolves without throwing for native chart', async () => {
    await expect(
      computePeriodSnapshot(NATIVE_CHART_ID, '2010-01-01')
    ).resolves.toBeDefined()
  })

  it('computePeriodSnapshot handles date before schedule range gracefully', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '1980-01-01')
    expect(snap.active_dasha).toBeNull()
    expect(snap.provenance_envelope).toBeDefined()
  })

  it('severity in obstructions is a float (range check, not exact)', async () => {
    // Saturn/Rahu AD period — obstructions may be present if kala_obstruction is populated
    // We check the structure contract on any returned obstructions
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2006-06-01')
    for (const obs of snap.obstructions) {
      expect(typeof obs.severity).toBe('number')
      // Range check — never exact float assertion
      expect(obs.severity).toBeGreaterThanOrEqual(0.0)
      expect(obs.severity).toBeLessThanOrEqual(1.0)
    }
  })

  it('obstruction source_citation is non-null when obstructions present', async () => {
    const snap = await computePeriodSnapshot(NATIVE_CHART_ID, '2006-06-01')
    for (const obs of snap.obstructions) {
      expect(obs.source_citation).toBeTruthy()
    }
  })
})
