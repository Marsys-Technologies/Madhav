/**
 * event_class_resolution.test.ts — D-4b Lane F-1 (resonance-map coverage).
 *
 * SYNTHETIC fixtures only (no live DB — same discipline as
 * `roster_bind.test.ts` / `permission_model.test.ts`). The marriage
 * specimen fixture below (`category='family'`, `domain='family/marriage'`)
 * mirrors chart 482012f1's real `life_events` row for EVT.2013.12.11.01
 * exactly (live-verified this session, see PR description) — proving THIS
 * module resolves it to `event_class='marriage'` is the acceptance bar
 * F-1's own task names explicitly.
 */
import { describe, it, expect } from 'vitest'
import {
  resolveEventClass,
  assertEventClassCoverage,
  EventClassCoverageIntegrityError,
  DOMAIN_TO_EVENT_CLASS,
  type RawEventForResolution,
} from '../event_class_resolution'

describe('resolveEventClass — the marriage specimen (verifier bar)', () => {
  it('resolves category="family", domain="family/marriage" to event_class="marriage" (matches the reproduced B1_NARROWED_STATUS proof)', () => {
    const res = resolveEventClass({ eventId: 'EVT.2013.12.11.01', category: 'family', domain: 'family/marriage' })
    expect(res.eventClass).toBe('marriage')
    expect(res.resolved).toBe(true)
    expect(res.method).toBe('domain_exact_match')
  })
})

describe('resolveEventClass — the original bug (raw category passthrough) is NOT reproduced', () => {
  it('does NOT resolve category="family" alone (no domain) to "marriage" or anything else', () => {
    const res = resolveEventClass({ eventId: 'x', category: 'family' })
    expect(res.eventClass).toBeNull()
    expect(res.resolved).toBe(false)
  })

  it('does NOT resolve an unrelated family-domain event (childbirth) to "marriage"', () => {
    const res = resolveEventClass({ eventId: 'EVT.2022.01.03.01', category: 'family', domain: 'family/child_birth' })
    expect(res.eventClass).toBeNull()
    expect(res.resolved).toBe(false)
  })
})

describe('resolveEventClass — major_gain (finance/windfall specimens)', () => {
  it('resolves the 2010 family-windfall event', () => {
    const res = resolveEventClass({ eventId: 'x', category: 'finance', domain: 'finance/family_windfall' })
    expect(res.eventClass).toBe('major_gain')
  })
  it('resolves the 2025 Marsys windfall event', () => {
    const res = resolveEventClass({ eventId: 'y', category: 'finance', domain: 'finance/business_milestone_windfall' })
    expect(res.eventClass).toBe('major_gain')
  })
})

describe('resolveEventClass — does NOT over-resolve career-category events to career_advancement', () => {
  it('a career ENTRY event is left unresolved, not stamped career_advancement', () => {
    const res = resolveEventClass({ eventId: 'x', category: 'career', domain: 'career/first_job_joined' })
    expect(res.eventClass).toBeNull()
    expect(res.resolved).toBe(false)
  })
  it('a career SETBACK event is left unresolved, not stamped career_advancement', () => {
    const res = resolveEventClass({ eventId: 'x', category: 'career', domain: 'career/employer_instability' })
    expect(res.eventClass).toBeNull()
  })
  it('the closest-sounding candidate (award_selection) is still left unresolved, not force-mapped', () => {
    const res = resolveEventClass({ eventId: 'x', category: 'career', domain: 'career/award_selection' })
    expect(res.eventClass).toBeNull()
  })
})

describe('resolveEventClass — categories with no populated-class evidence stay unresolved (no silent gap)', () => {
  it.each(['health', 'education', 'psychological', 'spiritual', 'travel', 'loss', 'other', 'creative', 'residential+travel'])(
    'category=%s with no domain match resolves to null, not a guess',
    (category) => {
      const res = resolveEventClass({ eventId: 'x', category, domain: `${category}/some_subtype` })
      expect(res.eventClass).toBeNull()
      expect(res.resolved).toBe(false)
    }
  )
})

describe('DOMAIN_TO_EVENT_CLASS — every value is one of the 3 populated classes this table is scoped to', () => {
  it('contains only marriage/major_gain/career_advancement values', () => {
    const values = new Set(Object.values(DOMAIN_TO_EVENT_CLASS))
    for (const v of values) {
      expect(['marriage', 'major_gain', 'career_advancement']).toContain(v)
    }
  })
})

describe('assertEventClassCoverage — the task item (c) contract', () => {
  const events: RawEventForResolution[] = [
    { eventId: 'EVT.marriage', category: 'family', domain: 'family/marriage' },
    { eventId: 'EVT.windfall1', category: 'finance', domain: 'finance/family_windfall' },
    { eventId: 'EVT.health', category: 'health', domain: 'health/chronic_onset' },
    { eventId: 'EVT.no-domain', category: 'other' },
  ]
  const populated = ['career_advancement', 'major_gain', 'marriage']

  it('reports every event (no silent drop), split resolved-and-populated vs unresolved', () => {
    const report = assertEventClassCoverage('synthetic-chart', events, populated)
    expect(report.entries).toHaveLength(4)
    expect(report.resolvedAndPopulatedCount).toBe(2)
    expect(report.unresolvedCount).toBe(2)
    const marriage = report.entries.find((e) => e.eventId === 'EVT.marriage')!
    expect(marriage.resolved).toBe(true)
    expect(marriage.populated).toBe(true)
    const health = report.entries.find((e) => e.eventId === 'EVT.health')!
    expect(health.resolved).toBe(false)
    expect(health.populated).toBe(false)
    expect(health.reason).toBeTruthy()
  })

  it('carries the live populatedEventClassesLive list through verbatim (never hardcoded downstream)', () => {
    const report = assertEventClassCoverage('synthetic-chart', events, populated)
    expect(report.populatedEventClassesLive).toEqual(populated)
  })

  it('throws EventClassCoverageIntegrityError if a resolution names a class that is NOT in the live-populated set (resolver/DB drift, a real bug)', () => {
    // Simulates the populated set shrinking (or the resolver table drifting)
    // relative to what's actually live in gochara_resonance_map -- must fail
    // loudly, never silently re-degrade to the fallback path.
    const staleSet = ['career_advancement'] // 'marriage' no longer reported live
    expect(() => assertEventClassCoverage('synthetic-chart', events, staleSet)).toThrow(EventClassCoverageIntegrityError)
  })

  it('an empty event list produces an empty, valid report (not an error)', () => {
    const report = assertEventClassCoverage('synthetic-chart', [], populated)
    expect(report.entries).toHaveLength(0)
    expect(report.resolvedAndPopulatedCount).toBe(0)
    expect(report.unresolvedCount).toBe(0)
  })
})
