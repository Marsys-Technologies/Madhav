/**
 * kala_envelope.test.ts — ṢAḌ-DARŚANA W0.3.
 * Covers: argument-reading well-formedness, field_snapshot_id stub determinism, tri-plane
 * pointer honesty, 3-state coverage builders, freshness staleness detection, the LEL-absent
 * calibration_maturity scenario (Elevation §7), envelope assembly, and the hardFloor
 * trimmable-section integration with response_budget.ts's actual trim mechanics.
 */
import { describe, it, expect } from 'vitest'
import {
  isWellFormedArgumentReading,
  buildFieldSnapshotIdStub,
  pointerTo,
  noLeverPointer,
  isNoLever,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  FRESHNESS_UNDETERMINED_NO_HORIZON,
  FRESHNESS_UNDETERMINED_BAD_HORIZON,
  noLelCalibrationMaturity,
  makeKalaEnvelope,
  kalaEvidenceTrimmableSection,
  type ArgumentReading,
} from './kala_envelope.js'
import { composeFreshnessSentence } from './argument_composer.js'
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

describe('buildFieldSnapshotIdStub', () => {
  it('is deterministic regardless of input key order', () => {
    const a = buildFieldSnapshotIdStub({ ka_dasha_kala: 'b1', ga_chart_facts: 'a1' })
    const b = buildFieldSnapshotIdStub({ ga_chart_facts: 'a1', ka_dasha_kala: 'b1' })
    expect(a).toBe(b)
    expect(a).toBe('stub:ga_chart_facts=a1;ka_dasha_kala=b1')
  })

  it('drops null/undefined/empty-string entries', () => {
    const id = buildFieldSnapshotIdStub({ ga_chart_facts: 'a1', ka_gochara_sweep: null, ka_dasha_kala: undefined, x: '' })
    expect(id).toBe('stub:ga_chart_facts=a1')
  })

  it('falls back to an honest unknown marker when nothing resolves', () => {
    expect(buildFieldSnapshotIdStub({})).toBe('stub:unknown')
    expect(buildFieldSnapshotIdStub({ a: null, b: undefined })).toBe('stub:unknown')
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
  // SAMĀPTI A7-N8-AUDIT F-20. This test previously asserted `stale:false` here, which
  // encoded the defect: with no horizon declared, nothing was checked, so `false` was an
  // unearned positive freshness claim — and since ZERO of the eight kala_views/*.ts call
  // sites pass `staleAfter`, `false` was the only value the field could ever take in
  // production. The honest value for "not determinable" is `null`, matching the
  // three-state discipline KalaCoverageEntry already uses in the same module.
  it('stale:null WITH a named reason when no horizon is declared (F-20)', () => {
    const f = buildKalaFreshness({ ephemerisVersion: 'v1', sweepBuildDate: '2026-07-01', fieldHash: null })
    expect(f.stale).toBeNull()
    expect(f.stale).not.toBe(false)
    expect(f.stale_reason).toBe(FRESHNESS_UNDETERMINED_NO_HORIZON)
  })

  it('stale:null when the declared horizon is unparseable — never silently "current" (F-20)', () => {
    const f = buildKalaFreshness({
      ephemerisVersion: 'v1',
      sweepBuildDate: '2026-07-01',
      fieldHash: null,
      staleAfter: 'not-a-date',
      now: new Date('2026-07-29'),
    })
    expect(f.stale).toBeNull()
    expect(f.stale_reason).toBe(FRESHNESS_UNDETERMINED_BAD_HORIZON)
  })

  // The estate-wide reachability proof, asserted rather than asserted-about: every
  // production kala_views/*.ts call site invokes buildKalaFreshness with exactly this
  // argument shape (all three provenance fields null, no staleAfter). If a future call
  // site starts declaring a horizon this test still passes — it only pins that the
  // NO-HORIZON shape can never again read as a positive freshness claim.
  it('the estate-wide production call shape yields UNKNOWN, not "current" (F-20)', () => {
    const f = buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null })
    expect(f.stale).toBeNull()
    expect(composeFreshnessSentence(f)).toContain('UNKNOWN')
    expect(composeFreshnessSentence(f)).not.toBe('Freshness: current.')
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

describe('makeKalaEnvelope', () => {
  it('assembles every declared slot without silently defaulting a required one', () => {
    const envelope = makeKalaEnvelope({
      reading: READING,
      questionFrame: { domain: 'career', intent_verb: 'should_i' },
      fieldSnapshotId: buildFieldSnapshotIdStub({ ga_chart_facts: 'a1' }),
      triPlane: {
        interpretation_ref: null,
        prediction_ref: pointerTo('kala_bundle_get', 'forward window'),
        intervention_ref: noLeverPointer('pure interpretation-plane NOW state'),
      },
      coverage: [computedCoverage('mercury_combustion')],
      freshness: buildKalaFreshness({ ephemerisVersion: 'v1', sweepBuildDate: '2026-07-29', fieldHash: null }),
      calibrationMaturity: noLelCalibrationMaturity(),
    })

    expect(envelope.reading).toBe(READING)
    expect(envelope.question_frame).toEqual({ domain: 'career', intent_verb: 'should_i' })
    expect(envelope.field_snapshot_id).toBe('stub:ga_chart_facts=a1')
    expect(envelope.tri_plane.interpretation_ref).toBeNull()
    expect(isNoLever(envelope.tri_plane.intervention_ref)).toBe(true)
    expect(envelope.coverage).toHaveLength(1)
    // F-20: this envelope declares no substrate horizon, so staleness is UNDETERMINED —
    // `null`, not the unearned `false` this assertion used to pin.
    expect(envelope.freshness.stale).toBeNull()
    expect(envelope.calibration_maturity.n_events).toBe(0)
  })

  it('defaults question_frame to null (not undefined) when omitted', () => {
    const envelope = makeKalaEnvelope({
      reading: READING,
      fieldSnapshotId: 'stub:unknown',
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
