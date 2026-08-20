/**
 * kala_envelope.test.ts — ṢAḌ-DARŚANA W0.3 · W2 (w2-envelope-real-snapshot).
 * Covers: argument-reading well-formedness, the REAL field_snapshot_id read
 * (`resolveFieldSnapshot` — served / field_not_yet_built / field_snapshot_unreachable
 * honesty states, replacing the retired W0 'stub:' composer), tri-plane pointer honesty,
 * 3-state coverage builders, freshness staleness detection, the LEL-absent
 * calibration_maturity scenario (Elevation §7), envelope assembly, and the hardFloor
 * trimmable-section integration with response_budget.ts's actual trim mechanics.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import {
  isWellFormedArgumentReading,
  resolveFieldSnapshot,
  FIELD_NOT_YET_BUILT,
  FIELD_SNAPSHOT_UNREACHABLE,
  pointerTo,
  explainPointerTo,
  noLeverPointer,
  isNoLever,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  noLelCalibrationMaturity,
  makeKalaEnvelope,
  kalaEvidenceTrimmableSection,
  type ArgumentReading,
  type FieldSnapshotResolution,
} from './kala_envelope.js'
import { applyResponseBudget } from './response_budget.js'

const READING: ArgumentReading = {
  thesis: 'Mercury clears combustion this week, lifting a three-week fog on communication.',
  evidence: [
    { claim: 'Mercury combust since 3 days ago', fact_ids: ['fact_1'], strength: 'strong' },
    { claim: 'Mercury dasha-lord role active', fact_ids: ['fact_2'], strength: 'moderate' },
  ],
  dissent: [],
  verdict: { statement: 'Communication friction eases starting Thursday', tier: 'structural_prior' },
  falsifier: { statement: 'no improvement felt by next new moon', resolves_by: '2026-08-13' },
}

describe('isWellFormedArgumentReading', () => {
  it('true for a reading with non-empty thesis and verdict statement', () => {
    expect(isWellFormedArgumentReading(READING)).toBe(true)
  })

  it('false when thesis is blank', () => {
    expect(isWellFormedArgumentReading({ ...READING, thesis: '   ' })).toBe(false)
  })

  it('false when verdict statement is blank', () => {
    expect(
      isWellFormedArgumentReading({ ...READING, verdict: { statement: '', tier: 'unresolved' } }),
    ).toBe(false)
  })
})

describe('resolveFieldSnapshot — W2 real read, 3 honesty states', () => {
  const PRINCIPAL = { user_uid: 'u1', key_id: 'k1' }

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  function stubDbQuery(response: { ok: boolean; status?: number; rows?: unknown[]; bodyText?: string }) {
    const fetchMock = vi.fn(async () => ({
      ok: response.ok,
      status: response.status ?? (response.ok ? 200 : 400),
      json: async () => ({ rows: response.rows ?? [] }),
      text: async () => response.bodyText ?? '',
    }))
    vi.stubGlobal('fetch', fetchMock)
    return fetchMock
  }

  it('serves the newest real kfs_/kfh_ pair when a snapshot row exists', async () => {
    const fetchMock = stubDbQuery({
      ok: true,
      rows: [{ field_snapshot_id: 'kfs_' + 'a'.repeat(32), field_content_hash: 'kfh_' + 'b'.repeat(32) }],
    })
    const r = await resolveFieldSnapshot('chart-1', PRINCIPAL)
    expect(r.field_snapshot_state).toBe('served')
    expect(r.field_snapshot_id).toBe('kfs_' + 'a'.repeat(32))
    expect(r.field_content_hash).toBe('kfh_' + 'b'.repeat(32))
    expect(r.field_snapshot_reason).toBeNull()
    // The query is a total-order newest-row read against kala_field_snapshots (§N.7 item 2).
    const body = JSON.parse((fetchMock.mock.calls[0] as unknown as [string, { body: string }])[1].body) as {
      sql: string
      params: unknown[]
    }
    expect(body.sql).toContain('FROM kala_field_snapshots')
    expect(body.sql).toContain('ORDER BY built_at DESC, field_snapshot_id DESC LIMIT 1')
    expect(body.params).toEqual(['chart-1'])
  })

  it('serves the explicit field_not_yet_built marker when the chart has no row (production today)', async () => {
    stubDbQuery({ ok: true, rows: [] })
    const r = await resolveFieldSnapshot('chart-1', PRINCIPAL)
    expect(r.field_snapshot_state).toBe('field_not_yet_built')
    expect(r.field_snapshot_id).toBe(FIELD_NOT_YET_BUILT)
    expect(r.field_content_hash).toBeNull()
    expect(r.field_snapshot_reason).toContain('no kala_field_snapshots row')
  })

  it('serves the DISTINCT unreachable marker (never a fabricated id) when the read fails', async () => {
    stubDbQuery({ ok: false, status: 400, bodyText: "Table 'kala_field_snapshots' is not in the read-only whitelist" })
    const r = await resolveFieldSnapshot('chart-1', PRINCIPAL)
    expect(r.field_snapshot_state).toBe('field_snapshot_unreachable')
    expect(r.field_snapshot_id).toBe(FIELD_SNAPSHOT_UNREACHABLE)
    expect(r.field_content_hash).toBeNull()
    expect(r.field_snapshot_reason).toContain('HTTP 400')
  })

  it('serves the unreachable marker when fetch throws (DB proxy down)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new Error('ECONNREFUSED')
    }))
    const r = await resolveFieldSnapshot('chart-1', PRINCIPAL)
    expect(r.field_snapshot_state).toBe('field_snapshot_unreachable')
    expect(r.field_snapshot_id).toBe(FIELD_SNAPSHOT_UNREACHABLE)
    expect(r.field_snapshot_reason).toContain('ECONNREFUSED')
  })

  it('never emits a stub-shaped id in any state', async () => {
    stubDbQuery({ ok: true, rows: [] })
    const empty = await resolveFieldSnapshot('chart-1', PRINCIPAL)
    expect(empty.field_snapshot_id).not.toContain('stub:')
  })
})

// NOTE: test fixtures below deliberately use ALREADY-REGISTERED live MCP tool names
// (e.g. 'kala_windows_get', 'kala_bundle_get') as stand-ins for a generic instrument
// pointer, NOT the eight future kala_* view/capability tool names this campaign will
// register in a later lane (W0.4+). The CI boot-time pointer validator (SC-17/18/19,
// platform/scripts/audit/tap/sc_pointer_validation.ts) statically scans every
// `instrument: '<name>'` literal in the repo — including test fixtures — against the
// currently-registered tool set; a fixture naming a not-yet-built tool reads as a real
// regression to that gate.

describe('tri-plane pointer helpers', () => {
  it('pointerTo builds a live drill pointer', () => {
    expect(pointerTo('kala_bundle_get', 'see the forward window')).toEqual({
      instrument: 'kala_bundle_get',
      hint: 'see the forward window',
    })
  })

  it('noLeverPointer + isNoLever round-trip honestly', () => {
    const p = noLeverPointer('no intervention lever exists for a pure NOW state')
    expect(isNoLever(p)).toBe(true)
    expect(p.reason).toContain('no intervention lever')
  })

  it('isNoLever is false for a live pointer and for null/undefined', () => {
    expect(isNoLever(pointerTo('kala_windows_get', 'x'))).toBe(false)
    expect(isNoLever(null)).toBe(false)
    expect(isNoLever(undefined)).toBe(false)
  })

  // F-123 (CL-11 dead pointer): DrillPointerLike gained an optional `args` field so a pointer
  // can carry the required-argument payload its target needs to actually resolve.
  it('pointerTo carries an optional args payload when supplied', () => {
    expect(pointerTo('kala_explain_get', 'why', { domain: 'career' })).toEqual({
      instrument: 'kala_explain_get',
      hint: 'why',
      args: { domain: 'career' },
    })
  })

  it('pointerTo omits args (not just empty) when not supplied — unchanged 2-arg shape', () => {
    expect(pointerTo('kala_bundle_get', 'see the forward window')).toEqual({
      instrument: 'kala_bundle_get',
      hint: 'see the forward window',
    })
    expect(Object.hasOwn(pointerTo('kala_bundle_get', 'x'), 'args')).toBe(false)
  })

  describe('explainPointerTo — typed kala_explain_get pointer constructor', () => {
    it('with a domain arg, carries it', () => {
      const p = explainPointerTo('why', { domain: 'career' })
      expect(p).toEqual({ instrument: 'kala_explain_get', hint: 'why', args: { domain: 'career' } })
    })

    it('with a bhava arg, carries it', () => {
      const p = explainPointerTo('why', { bhava: 7 })
      expect(p).toEqual({ instrument: 'kala_explain_get', hint: 'why', args: { bhava: 7 } })
    })

    it('with null args, degrades honestly instead of fabricating a domain', () => {
      const p = explainPointerTo('why', null)
      expect(p.instrument).toBe('kala_explain_get')
      expect(p.args).toBeUndefined()
      expect(p.hint).toBe('why — pass domain or bhava when calling.')
    })
  })
})

describe('3-state coverage builders', () => {
  it('computedCoverage carries no reason', () => {
    expect(computedCoverage('recurrence_ladder')).toEqual({ concept: 'recurrence_ladder', state: 'computed' })
  })

  it('honestEmptyCoverage requires and carries a reason', () => {
    expect(honestEmptyCoverage('mode1_rituals', 'no qualifying window in the searched horizon')).toEqual({
      concept: 'mode1_rituals',
      state: 'honest_empty',
      reason: 'no qualifying window in the searched horizon',
    })
  })

  it('notInCorpusCoverage requires and carries a reason', () => {
    expect(notInCorpusCoverage('agnivasa_residence', 'rule table not yet ingested')).toEqual({
      concept: 'agnivasa_residence',
      state: 'not_in_corpus',
      reason: 'rule table not yet ingested',
    })
  })
})

describe('buildKalaFreshness', () => {
  it('stale:false with no reason when no horizon is declared', () => {
    const f = buildKalaFreshness({ ephemerisVersion: 'v1', sweepBuildDate: '2026-07-01', fieldHash: null })
    expect(f.stale).toBe(false)
    expect(f.stale_reason).toBeNull()
  })

  it('stale:true with a named reason once now() passes staleAfter', () => {
    const f = buildKalaFreshness({
      ephemerisVersion: 'v1',
      sweepBuildDate: '2026-07-01',
      fieldHash: null,
      staleAfter: '2026-07-01',
      now: new Date('2026-07-29'),
    })
    expect(f.stale).toBe(true)
    expect(f.stale_reason).toContain('2026-07-01')
  })

  it('stale:false when now() is before staleAfter', () => {
    const f = buildKalaFreshness({
      ephemerisVersion: 'v1',
      sweepBuildDate: '2026-07-01',
      fieldHash: null,
      staleAfter: '2031-01-01',
      now: new Date('2026-07-29'),
    })
    expect(f.stale).toBe(false)
  })
})

describe('noLelCalibrationMaturity — Elevation §7 LEL-absent scenario', () => {
  it('serves an honest all-zero/null maturity block, never omitted', () => {
    expect(noLelCalibrationMaturity()).toEqual({
      n_events: 0,
      prospective_resolutions: 0,
      event_class_coverage: 0,
      weights_version: null,
      skill_score: null,
    })
  })
})

const SERVED_SNAPSHOT: FieldSnapshotResolution = {
  field_snapshot_id: 'kfs_' + 'a'.repeat(32),
  field_content_hash: 'kfh_' + 'b'.repeat(32),
  field_snapshot_state: 'served',
  field_snapshot_reason: null,
}

const NOT_BUILT_SNAPSHOT: FieldSnapshotResolution = {
  field_snapshot_id: FIELD_NOT_YET_BUILT,
  field_content_hash: null,
  field_snapshot_state: 'field_not_yet_built',
  field_snapshot_reason: 'ka_kshetra has written no kala_field_snapshots row for this chart yet.',
}

describe('makeKalaEnvelope', () => {
  it('assembles every declared slot without silently defaulting a required one', () => {
    const envelope = makeKalaEnvelope({
      reading: READING,
      questionFrame: { domain: 'career', intent_verb: 'should_i' },
      fieldSnapshot: SERVED_SNAPSHOT,
      triPlane: {
        interpretation_ref: null,
        prediction_ref: pointerTo('kala_bundle_get', 'forward window'),
        intervention_ref: noLeverPointer('pure interpretation-plane NOW state'),
      },
      coverage: [computedCoverage('mercury_combustion')],
      freshness: buildKalaFreshness({ ephemerisVersion: 'v1', sweepBuildDate: '2026-07-29', fieldHash: SERVED_SNAPSHOT.field_content_hash }),
      calibrationMaturity: noLelCalibrationMaturity(),
    })

    expect(envelope.reading).toBe(READING)
    expect(envelope.question_frame).toEqual({ domain: 'career', intent_verb: 'should_i' })
    expect(envelope.field_snapshot_id).toBe('kfs_' + 'a'.repeat(32))
    expect(envelope.field_snapshot_state).toBe('served')
    expect(envelope.field_snapshot_reason).toBeNull()
    expect(envelope.tri_plane.interpretation_ref).toBeNull()
    expect(isNoLever(envelope.tri_plane.intervention_ref)).toBe(true)
    expect(envelope.coverage).toHaveLength(1)
    expect(envelope.freshness.stale).toBe(false)
    expect(envelope.freshness.field_hash).toBe('kfh_' + 'b'.repeat(32))
    expect(envelope.calibration_maturity.n_events).toBe(0)
  })

  it('carries the honest not-yet-built marker + reason through to the envelope', () => {
    const envelope = makeKalaEnvelope({
      reading: READING,
      fieldSnapshot: NOT_BUILT_SNAPSHOT,
      triPlane: { interpretation_ref: null, prediction_ref: null, intervention_ref: null },
      coverage: [],
      freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
      calibrationMaturity: noLelCalibrationMaturity(),
    })
    expect(envelope.field_snapshot_id).toBe(FIELD_NOT_YET_BUILT)
    expect(envelope.field_snapshot_state).toBe('field_not_yet_built')
    expect(envelope.field_snapshot_reason).toContain('no kala_field_snapshots row')
  })

  it('defaults question_frame to null (not undefined) when omitted', () => {
    const envelope = makeKalaEnvelope({
      reading: READING,
      fieldSnapshot: NOT_BUILT_SNAPSHOT,
      triPlane: { interpretation_ref: null, prediction_ref: null, intervention_ref: null },
      coverage: [],
      freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
      calibrationMaturity: noLelCalibrationMaturity(),
    })
    expect(envelope.question_frame).toBeNull()
  })
})

describe('kalaEvidenceTrimmableSection — §N.6 hardFloor discipline', () => {
  type Content = { reading: ArgumentReading; padding: string }

  it('declares hardFloor:true and a minKeep of 1', () => {
    const section = kalaEvidenceTrimmableSection<Content>({ instrument: 'kala_windows_get', hint: 'recall full evidence' })
    expect(section.hardFloor).toBe(true)
    expect(section.minKeep).toBe(1)
    expect(section.path).toBe('reading.evidence')
  })

  it('survives PASS 1 (declared minKeep) even when a non-hardFloor section is bigger', () => {
    // A big, disposable catalog array alongside the small, dense evidence array. Padding
    // makes the disposable section serialize far bigger than evidence, so a naive
    // biggest-first-only trimmer would zero evidence first — the exact regression
    // hardFloor (response_budget.ts) exists to prevent (CLAUDE.md §N.6 part 2).
    const content: Content & { catalog: { id: string; note: string }[] } = {
      reading: { ...READING },
      padding: 'x'.repeat(200),
      catalog: Array.from({ length: 200 }, (_, i) => ({ id: `row_${i}`, note: 'y'.repeat(200) })),
    }

    const evidenceSection = kalaEvidenceTrimmableSection<typeof content>({
      instrument: 'kala_windows_get',
      hint: 'recall full evidence',
    })
    const catalogSection = {
      path: 'catalog',
      label: 'catalog rows',
      minKeep: 0,
      getArray: (c: typeof content) => c.catalog,
      setArray: (c: typeof content, kept: unknown[]) => {
        c.catalog = kept as typeof content.catalog
      },
      recover: { instrument: 'kala_windows_get', hint: 'call again for the full catalog' },
    }

    const result = applyResponseBudget(content, 1, [evidenceSection, catalogSection])
    expect(result.trimmed).toBe(true)
    // Evidence never dropped below its declared floor (1), even though the catalog
    // section was far larger and PASS 2's hard-cap fallback ran.
    expect(content.reading.evidence.length).toBeGreaterThanOrEqual(1)
    expect(content.catalog.length).toBeLessThan(200)
  })
})
