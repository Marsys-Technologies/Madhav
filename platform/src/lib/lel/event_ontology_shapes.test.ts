/**
 * event_ontology_shapes.test.ts — D-4a Lane A-2 acceptance proof.
 *
 * BRIEF_D4A.md §G.3 gate item: "Ontology published; matcher + ledger provably consume its shapes
 * (schema-violation test)." This file IS that proof: it demonstrates a claim/event that does not
 * match its declared event_class's canonical DR-13 shape gets REJECTED, using fixture ontology
 * entries whose data is transcribed verbatim from migration
 * 456_brahma_event_ontology_dr13_shapes.sql (career_entry=point, major_gain=interval,
 * business_launch=chain w/ irreversibility_milestone=first_revenue).
 *
 * Pure-logic test — no DB required (see event_ontology_shapes.ts's module doc for why the
 * validator is deliberately DB-agnostic).
 */
import { describe, it, expect } from 'vitest'
import {
  validateClaimShape,
  assertClaimShape,
  checkKillSwitch,
  type EventClassOntologyEntry,
} from './event_ontology_shapes'

// Fixtures mirror migration 456's backfilled rows exactly (kept in sync manually; a drift check
// against the live table is out of this pure-unit-test's scope and belongs to an integration
// suite once A-1/A-4 land their DB-backed callers).

const CAREER_ENTRY: EventClassOntologyEntry = {
  event_class_id: 'career_entry',
  temporal_shape: 'point',
  duration_prior: null,
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'gain',
    externally_verifiable: true,
    verification_sources: ['offer letter', 'joining letter', 'HR record'],
    self_report_risk: 'low',
  },
  self_report_non_discriminating: false,
  kill_switch_criteria: [],
}

const MAJOR_GAIN: EventClassOntologyEntry = {
  event_class_id: 'major_gain',
  temporal_shape: 'interval',
  duration_prior: { min_days: 14, typical_days: 90, max_days: 365 },
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'gain',
    externally_verifiable: true,
    verification_sources: ['bank credit record', 'payment receipt', 'settlement statement'],
    self_report_risk: 'low',
  },
  self_report_non_discriminating: false,
  kill_switch_criteria: [],
}

const BUSINESS_LAUNCH: EventClassOntologyEntry = {
  event_class_id: 'business_launch',
  temporal_shape: 'chain',
  duration_prior: null,
  milestone_template: [
    { milestone_id: 'decision', name_en: 'Decision to found/launch', typical_offset_days_from_first: 0 },
    { milestone_id: 'registration', name_en: 'Legal/business registration', typical_offset_days_from_first: 45 },
    { milestone_id: 'first_revenue', name_en: 'First revenue booked', typical_offset_days_from_first: 120 },
  ],
  irreversibility_milestone: 'first_revenue',
  evidence_requirements: {
    valence: 'gain',
    externally_verifiable: true,
    verification_sources: ['registration certificate', 'first invoice/payment record'],
    self_report_risk: 'low',
  },
  self_report_non_discriminating: false,
  kill_switch_criteria: [],
}

const SPIRITUAL_TURN: EventClassOntologyEntry = {
  event_class_id: 'spiritual_turn',
  temporal_shape: 'interval',
  duration_prior: { min_days: 7, typical_days: 120, max_days: 730 },
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'gain',
    externally_verifiable: false,
    verification_sources: ['dated ritual/initiation record where one exists'],
    self_report_risk: 'high',
  },
  self_report_non_discriminating: true,
  kill_switch_criteria: [
    {
      criterion_id: 'internal_state_only',
      description:
        'A devotional/practice-intensity shift with no externally observable marker is diagnostic-battery-only, never primary hit-rate scoring.',
    },
  ],
}

describe('validateClaimShape — DR-13 schema-violation enforcement (D-4a Lane A-2 gate proof)', () => {
  it('REJECTS a point-claim for an interval-class event (the brief\'s own worked example)', () => {
    const pointClaim = { kind: 'point' as const, date: '2027-03-01' }
    const violations = validateClaimShape(MAJOR_GAIN, pointClaim)
    expect(violations).toHaveLength(1)
    expect(violations[0]?.code).toBe('SHAPE_MISMATCH')
    expect(violations[0]?.message).toMatch(/major_gain.*interval.*point/s)
  })

  it('REJECTS an interval-claim for a point-class event (the inverse mismatch)', () => {
    const intervalClaim = { kind: 'interval' as const, start: '2015-05-01', end: '2015-06-01' }
    const violations = validateClaimShape(CAREER_ENTRY, intervalClaim)
    expect(violations).toHaveLength(1)
    expect(violations[0]?.code).toBe('SHAPE_MISMATCH')
  })

  it('REJECTS a chain-claim for a point-class event', () => {
    const chainClaim = {
      kind: 'chain' as const,
      milestones: [{ milestone_id: 'x', date: '2015-06-01' }],
    }
    const violations = validateClaimShape(CAREER_ENTRY, chainClaim)
    expect(violations).toHaveLength(1)
    expect(violations[0]?.code).toBe('SHAPE_MISMATCH')
  })

  it('ACCEPTS a correctly-shaped point claim', () => {
    expect(validateClaimShape(CAREER_ENTRY, { kind: 'point', date: '2015-06-01' })).toEqual([])
  })

  it('ACCEPTS a correctly-shaped interval claim', () => {
    const claim = { kind: 'interval' as const, start: '2027-04-09', end: '2027-08-18' }
    expect(validateClaimShape(MAJOR_GAIN, claim)).toEqual([])
  })

  it('REJECTS an interval claim whose end precedes its start', () => {
    const claim = { kind: 'interval' as const, start: '2027-08-18', end: '2027-04-09' }
    const violations = validateClaimShape(MAJOR_GAIN, claim)
    expect(violations).toHaveLength(1)
    expect(violations[0]?.code).toBe('INVERTED_INTERVAL')
  })

  it('ACCEPTS a chain claim naming only milestones present in the template', () => {
    const claim = {
      kind: 'chain' as const,
      milestones: [
        { milestone_id: 'decision', date: '2020-01-01' },
        { milestone_id: 'first_revenue', date: '2020-05-01' },
      ],
    }
    expect(validateClaimShape(BUSINESS_LAUNCH, claim)).toEqual([])
  })

  it('REJECTS a chain claim naming a milestone not in the class\'s milestone_template', () => {
    const claim = {
      kind: 'chain' as const,
      milestones: [{ milestone_id: 'ipo', date: '2020-01-01' }],
    }
    const violations = validateClaimShape(BUSINESS_LAUNCH, claim)
    expect(violations).toHaveLength(1)
    expect(violations[0]?.code).toBe('UNKNOWN_MILESTONE')
  })

  it('REJECTS a chain claim naming zero milestones', () => {
    const claim = { kind: 'chain' as const, milestones: [] }
    const violations = validateClaimShape(BUSINESS_LAUNCH, claim)
    expect(violations.map((v) => v.code)).toContain('EMPTY_CHAIN_CLAIM')
  })

  it('assertClaimShape throws with the violation detail for a mis-shaped claim', () => {
    expect(() =>
      assertClaimShape(MAJOR_GAIN, { kind: 'point', date: '2027-03-01' })
    ).toThrowError(/SHAPE_MISMATCH/)
  })

  it('assertClaimShape does not throw for a correctly-shaped claim', () => {
    expect(() =>
      assertClaimShape(CAREER_ENTRY, { kind: 'point', date: '2015-06-01' })
    ).not.toThrow()
  })
})

describe('checkKillSwitch — kill-switch criteria as data', () => {
  it('returns empty for a class with no kill_switch_criteria', () => {
    expect(checkKillSwitch(CAREER_ENTRY, ['anything'])).toEqual([])
  })

  it('returns the matching criterion when a met-criterion id is passed', () => {
    const result = checkKillSwitch(SPIRITUAL_TURN, ['internal_state_only'])
    expect(result).toHaveLength(1)
    expect(result[0]?.criterion_id).toBe('internal_state_only')
  })

  it('returns empty when no passed id matches this class\'s criteria', () => {
    expect(checkKillSwitch(SPIRITUAL_TURN, ['unrelated_criterion'])).toEqual([])
  })

  it('self_report_non_discriminating discriminates gain-evidence classes from high-self-report classes', () => {
    // The brief's own ask: a financial-gain class and a self-report-only class must not share an
    // undifferentiated evidence bucket. major_gain is externally verifiable; spiritual_turn is not.
    expect(MAJOR_GAIN.self_report_non_discriminating).toBe(false)
    expect(MAJOR_GAIN.evidence_requirements.externally_verifiable).toBe(true)
    expect(SPIRITUAL_TURN.self_report_non_discriminating).toBe(true)
    expect(SPIRITUAL_TURN.evidence_requirements.self_report_risk).toBe('high')
  })
})
