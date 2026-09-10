/**
 * P1 G1-B — subject-consent entitlement resolution (PPR-14, abuse case A9).
 *
 * Two things are under test and they are equally load-bearing:
 *   (a) with the flag OFF, NOTHING here is reachable — proven by counting the
 *       statements the DB double was asked to run (zero);
 *   (b) with the flag ON, every refusal path refuses and every allow path is
 *       one the spec actually authorizes — with the `native_self` strictness
 *       and the minor carve-out pinned individually.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { configService } from '@/lib/config'

import { CONSENT_FLAG } from '../flag'
import { resolveSubjectConsent } from '../resolve'
import { makeFakeDb } from './fake_db'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const NOW = new Date('2026-08-19T12:00:00.000Z')

function on() {
  configService.setFlag(CONSENT_FLAG, true)
}

beforeEach(() => configService.setFlag(CONSENT_FLAG, false))
afterEach(() => configService.setFlag(CONSENT_FLAG, false))

describe('flag OFF — the merge-safety guarantee', () => {
  it('is the DEFAULT state', () => {
    expect(configService.getFlag(CONSENT_FLAG)).toBe(false)
  })

  it('allows, marks itself unenforced, and issues ZERO database statements', async () => {
    const db = makeFakeDb({ consent: null }) // would refuse if it were consulted
    const d = await resolveSubjectConsent({ chartId: CHART, principalId: 'uid-x', db, asOf: NOW })

    expect(d.outcome).toBe('allow')
    expect(d.reason).toBe('enforcement_disabled')
    expect(d.enforced).toBe(false)
    expect(db.calls).toEqual([]) // ← the claim, measured
    expect(db.exclusions).toEqual([])
  })

  it('allows even the cases that would be the hardest refusals when ON', async () => {
    for (const seed of [
      { consent: null },
      { consent: { consent_state: 'withdrawn' as const, withdrawn_at: '2026-01-01T00:00:00Z' } },
      { chart: { birth_date: '2015-01-01' } },
      { consent: { vulnerable_exclusion_flag: true } },
    ]) {
      const db = makeFakeDb(seed)
      const d = await resolveSubjectConsent({
        chartId: CHART,
        principalId: 'uid-stranger',
        db,
        asOf: NOW,
      })
      expect(d.outcome).toBe('allow')
      expect(db.calls.length).toBe(0)
    }
  })
})

describe('flag ON — refusals', () => {
  beforeEach(on)

  it('refuses a chart with NO consent row — the A9 defense', async () => {
    const db = makeFakeDb({ consent: null })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })

    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('no_consent_row')
    expect(d.enforced).toBe(true)
    if (d.outcome === 'refuse') {
      expect(d.message).toMatch(/no subject-consent record/i)
      expect(d.registered).toBe(true)
    }
    expect(db.exclusions.map((e) => e.exclusion_reason)).toEqual(['no_consent_row'])
    expect(db.exclusions[0].detector).toBe('consent.resolveSubjectConsent')
  })

  it('reports registered:false honestly when the register write fails', async () => {
    const db = makeFakeDb({ consent: null, failRegisterWrite: true })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
    if (d.outcome === 'refuse') expect(d.registered).toBe(false)
  })

  it('refuses a withdrawn subject', async () => {
    const db = makeFakeDb({
      consent: { consent_state: 'withdrawn', withdrawn_at: '2026-05-01T00:00:00.000Z' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('consent_withdrawn')
  })

  it('refuses a subject whose deletion was verified, ahead of every other check', async () => {
    const db = makeFakeDb({
      consent: {
        consent_state: 'withdrawn',
        withdrawn_at: '2026-05-01T00:00:00.000Z',
        verified_deletion_at: '2026-05-02T00:00:00.000Z',
      },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('subject_deleted')
  })

  it('refuses a vulnerable-subject exclusion', async () => {
    const db = makeFakeDb({ consent: { vulnerable_exclusion_flag: true } })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('vulnerable_subject')
  })

  it('fails CLOSED when the birth date cannot be read', async () => {
    const db = makeFakeDb({ chart: { birth_date: null } })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('birth_date_unavailable')
    expect(d.is_minor).toBeNull()
  })
})

describe('flag ON — native_self is STRICT, not self-certified', () => {
  beforeEach(on)

  it('allows when the subject IS the account holder and IS the caller', async () => {
    const db = makeFakeDb({
      chart: { owner_id: 'uid-native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-native' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('allow')
    expect(d.reason).toBe('native_self')
    expect(d.enforced).toBe(true)
  })

  it('REFUSES a native_self row whose subject is not the chart owner (the A9 shape)', async () => {
    // The abuse: create a chart for your spouse, stamp it native_self.
    const db = makeFakeDb({
      chart: { owner_id: 'uid-native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-spouse' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('native_self_claim_invalid')
    expect(db.exclusions[0].exclusion_reason).toBe('native_self_claim_invalid')
  })

  it('REFUSES when the caller is not the subject, even for a valid native_self row', async () => {
    const db = makeFakeDb({
      chart: { owner_id: 'uid-native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-native' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-someone-else',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('native_self_claim_invalid')
  })

  it('has NO super_admin bypass — role is not consulted at all', async () => {
    const db = makeFakeDb({
      chart: { owner_id: 'uid-native', role: 'native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-spouse' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-super-admin',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
  })
})

describe('flag ON — minors (§3.5.F)', () => {
  beforeEach(on)

  const minorSeed = (extra: Record<string, unknown> = {}) => ({
    chart: { birth_date: '2012-06-15', owner_id: 'uid-native' },
    consent: {
      subject_kind: 'native_self' as const,
      subject_principal_id: 'uid-native',
      guardian_principal_id: 'uid-guardian',
      ...extra,
    },
  })

  it('allows the RECORDED GUARDIAN only', async () => {
    const db = makeFakeDb(minorSeed())
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-guardian',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('allow')
    expect(d.reason).toBe('guardian_minor')
    expect(d.is_minor).toBe(true)
    expect(d.subject_age_years).toBe(14)
  })

  it('refuses anyone who is not the recorded guardian', async () => {
    const db = makeFakeDb(minorSeed())
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('minor')
    expect(db.exclusions[0].evidence).toMatchObject({
      rule: 'minor_servable_only_to_recorded_guardian',
    })
  })

  it('refuses when no guardian was recorded at all', async () => {
    const db = makeFakeDb({
      chart: { birth_date: '2012-06-15' },
      consent: { guardian_principal_id: null },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('minor')
    expect(db.exclusions[0].evidence).toMatchObject({ guardian_recorded: false })
  })

  it('NEVER admits a minor as a cohort subject — even with a guardian and a document', async () => {
    const db = makeFakeDb({
      chart: { birth_date: '2012-06-15' },
      consent: {
        subject_kind: 'cohort',
        consent_document_ref: 'consent/2026/minor.pdf',
        guardian_principal_id: 'uid-guardian',
      },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-guardian', // the guardian themself
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('minor')
    expect(db.exclusions[0].evidence).toMatchObject({ rule: 'minor_never_enters_cohort' })
  })

  it('THE BOUNDARY — a subject one day short of 18 is still a minor', async () => {
    // birth 2008-06-15, evaluated 2026-06-14 — the caller here IS the chart
    // owner and the named subject, so ONLY the age keeps this refused.
    const db = makeFakeDb({
      chart: { birth_date: '2008-06-15', owner_id: 'uid-native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-native' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: new Date('2026-06-14T12:00:00.000Z'),
    })
    expect(d.is_minor).toBe(true)
    expect(d.subject_age_years).toBe(17)
    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('minor')
    expect(db.exclusions[0].exclusion_reason).toBe('minor')
  })

  it('THE BOUNDARY — the same subject on their 18th birthday resolves as an adult', async () => {
    const db = makeFakeDb({
      chart: { birth_date: '2008-06-15', owner_id: 'uid-native' },
      consent: { subject_kind: 'native_self', subject_principal_id: 'uid-native' },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-native',
      db,
      asOf: new Date('2026-06-15T12:00:00.000Z'),
    })
    expect(d.is_minor).toBe(false)
    expect(d.subject_age_years).toBe(18)
    expect(d.outcome).toBe('allow')
    expect(d.reason).toBe('native_self')
    // …and the now-stale `minor` exclusion is cleared, not left open forever.
    expect(db.cleared).toEqual([
      expect.objectContaining({ chart_id: CHART, reason: 'minor' }),
    ])
  })
})

describe('flag ON — cohort and test subjects', () => {
  beforeEach(on)

  it('allows a granted, documented cohort subject', async () => {
    const db = makeFakeDb({
      consent: {
        subject_kind: 'cohort',
        subject_principal_id: null,
        consent_document_ref: 'consent/2026-08-19/subject-42.pdf',
        anonymization_choice: 'anonymous',
        redaction_requests: [{ scope: 'health', requested_at: '2026-08-19' }],
      },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-researcher',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('allow')
    expect(d.reason).toBe('cohort_consent_granted')
    // The serving layer must be able to see the choice and the redactions.
    expect(d.anonymization_choice).toBe('anonymous')
    expect(d.redaction_requests).toHaveLength(1)
  })

  it('allows a test subject', async () => {
    const db = makeFakeDb({
      consent: { subject_kind: 'test', subject_principal_id: null },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-anyone',
      db,
      asOf: NOW,
    })
    expect(d.reason).toBe('test_subject')
  })

  it('fails closed on an unexpected subject_kind', async () => {
    const db = makeFakeDb({
      consent: { subject_kind: 'something_new' as never, subject_principal_id: null },
    })
    const d = await resolveSubjectConsent({
      chartId: CHART,
      principalId: 'uid-anyone',
      db,
      asOf: NOW,
    })
    expect(d.outcome).toBe('refuse')
  })
})
