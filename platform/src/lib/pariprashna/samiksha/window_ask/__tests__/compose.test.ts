/**
 * The window-opening ask — composition unit tests (lane P4-G).
 *
 * Pure, zero-I/O tests over `compose.ts`. Written the way a refuter would write them: every
 * assertion is a way the composer could leak internal vocabulary, misdate a window, or
 * volunteer a severity-suppressed finding.
 */

import { describe, it, expect } from 'vitest'
import {
  composeWindowAsk,
  dechromeClaim,
  shortenClaim,
  renderMonth,
  renderDay,
  windowLastDay,
  SEVERITY_SUPPRESSED_DOMAINS,
  DOMAIN_PHRASE,
  CLAIM_QUOTE_MAX,
} from '../compose'
import type { LedgerRow } from '../../schema'

function row(overrides: Partial<LedgerRow> = {}): LedgerRow {
  return {
    id: '11111111-1111-1111-1111-111111111111',
    chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
    message_part_id: null,
    claim_text: 'Native transitions to a leadership role in the second half of the year.',
    domain: 'career',
    window: '[2026-01-01,2026-07-01)',
    confidence: '[0.55,0.7)',
    direction: 'positive',
    technique_refs: [],
    grounding_fact_ids: [],
    created_from_channel: 'pariprashna',
    lifecycle_status: 'window_closed',
    build_id: null,
    priors_version: null,
    formula_versions: null,
    ranking_config: null,
    now_context_date: null,
    stamp_copied_at: null,
    outcome: null,
    outcome_value: null,
    outcome_note: null,
    outcome_recorded_at: null,
    confirmed_at: '2026-01-05T00:00:00.000Z',
    dismissed_reason: null,
    created_at: '2026-01-01T00:00:00.000Z',
    updated_at: '2026-01-01T00:00:00.000Z',
    ...overrides,
  }
}

describe('windowLastDay — the off-by-one that would misreport when a window closed', () => {
  it('converts an exclusive upper bound to the INCLUSIVE last day', () => {
    expect(windowLastDay('[2026-01-01,2026-12-31)')).toBe('2026-12-30')
  })
  it('handles an inclusive upper bound (])', () => {
    expect(windowLastDay('[2026-01-01,2026-12-31]')).toBe('2026-12-31')
  })
  it('returns null for a null / unparseable literal', () => {
    expect(windowLastDay(null)).toBeNull()
    expect(windowLastDay('garbage')).toBeNull()
    expect(windowLastDay('[2026-01-01,not-a-date)')).toBeNull()
  })
})

describe('renderMonth / renderDay — year elided only when it matches asOf', () => {
  it('omits the year when it matches nowYear', () => {
    expect(renderMonth('2026-03-15', 2026)).toBe('March')
    expect(renderDay('2026-12-30', 2026)).toBe('30 December')
  })
  it('includes the year when it does not match nowYear', () => {
    expect(renderMonth('2025-03-15', 2026)).toBe('March 2025')
    expect(renderDay('2025-12-30', 2026)).toBe('30 December 2025')
  })
  it('returns null for unparseable input', () => {
    expect(renderMonth(null, 2026)).toBeNull()
    expect(renderDay('not-a-date', 2026)).toBeNull()
  })
})

describe('dechromeClaim — strips authoring chrome, never content', () => {
  it('strips a leading bullet', () => {
    expect(dechromeClaim('- The native takes a leadership role.')).toBe('The native takes a leadership role.')
  })
  it('strips a leading bolded label', () => {
    expect(dechromeClaim('**Prediction:** the native relocates by June.')).toBe('the native relocates by June.')
  })
  it('strips emphasis markers but keeps the words between them', () => {
    expect(dechromeClaim('This is **very** likely to happen.')).toBe('This is very likely to happen.')
  })
  it('strips inline code and link chrome, keeping visible text', () => {
    expect(dechromeClaim('See [the transit](https://example.com) for `Saturn`.')).toBe(
      'See the transit for Saturn.',
    )
  })
  it('does NOT strip an unbolded leading label — that is content, not chrome', () => {
    expect(dechromeClaim('Trajectory to 2027: the native changes career.')).toBe(
      'Trajectory to 2027: the native changes career.',
    )
  })
})

describe('shortenClaim — never cuts mid-thought, always discloses shortening', () => {
  it('leaves a short claim untouched', () => {
    const r = shortenClaim('Short claim.')
    expect(r).toEqual({ text: 'Short claim.', shortened: false })
  })
  it('cuts at a sentence boundary when one exists past 40% of max', () => {
    const long = 'A. '.repeat(200) // way over CLAIM_QUOTE_MAX, full of sentence boundaries
    const r = shortenClaim(long)
    expect(r.shortened).toBe(true)
    expect(r.text.length).toBeLessThanOrEqual(CLAIM_QUOTE_MAX)
    expect(/\.$/.test(r.text)).toBe(true)
  })
  it('falls back to an ellipsis cut at a word boundary when no good sentence break exists', () => {
    const long = 'word '.repeat(200) // no sentence punctuation at all
    const r = shortenClaim(long)
    expect(r.shortened).toBe(true)
    expect(r.text.endsWith('…')).toBe(true)
  })
})

describe('composeWindowAsk — severity suppression is a HARD refusal, not a preference', () => {
  it.each(SEVERITY_SUPPRESSED_DOMAINS)('never composes for domain "%s"', (domain) => {
    const result = composeWindowAsk(row({ domain }), '2026-08-23')
    expect(result.composed).toBe(false)
    if (!result.composed) expect(result.reason).toBe('severity_suppressed_domain')
  })
  it('is case- and whitespace-insensitive on the domain match', () => {
    const result = composeWindowAsk(row({ domain: '  Health  ' }), '2026-08-23')
    expect(result.composed).toBe(false)
    if (!result.composed) expect(result.reason).toBe('severity_suppressed_domain')
  })
  it('composes normally for a non-suppressed domain', () => {
    const result = composeWindowAsk(row({ domain: 'career' }), '2026-08-23')
    expect(result.composed).toBe(true)
  })
})

describe('composeWindowAsk — refuses an unusable claim rather than quoting near-nothing', () => {
  it('refuses when the de-chromed claim is under 12 characters', () => {
    const result = composeWindowAsk(row({ claim_text: '- Yes.' }), '2026-08-23')
    expect(result.composed).toBe(false)
    if (!result.composed) expect(result.reason).toBe('claim_text_unusable')
  })
})

describe('composeWindowAsk — refuses an unparseable window rather than guessing a date', () => {
  it('refuses when window is null', () => {
    const result = composeWindowAsk(row({ window: null }), '2026-08-23')
    expect(result.composed).toBe(false)
    if (!result.composed) expect(result.reason).toBe('window_missing_or_unparseable')
  })
  it('refuses when window is a garbage literal', () => {
    const result = composeWindowAsk(row({ window: 'not-a-range' }), '2026-08-23')
    expect(result.composed).toBe(false)
    if (!result.composed) expect(result.reason).toBe('window_missing_or_unparseable')
  })
})

describe('composeWindowAsk — the successful path: what is fact vs. fixed prose', () => {
  it('mentions the domain phrase, the month it was said, and the last day, never internal tokens', () => {
    const r = row({
      domain: 'career',
      claim_text: 'The native takes on a senior leadership position.',
      window: '[2026-01-01,2026-07-01)',
      confirmed_at: '2026-01-05T00:00:00.000Z',
    })
    const result = composeWindowAsk(r, '2026-08-23')
    expect(result.composed).toBe(true)
    if (!result.composed) return
    const { text, derivedFrom } = result.ask
    expect(text).toContain('your work')
    expect(text).toContain('January')
    expect(text).toContain('30 June')
    expect(text).toContain('The native takes on a senior leadership position.')
    expect(text).toContain('What happened?')
    expect(text).toContain('If you cannot tell, say so')

    // LEAKAGE — none of the internal vocabulary may appear in the reader-facing text.
    expect(text).not.toMatch(/\bwindow_closed\b/)
    expect(text).not.toMatch(/\blifecycle\b/)
    expect(text).not.toMatch(/\bconfidence\b/)
    expect(text).not.toMatch(/\bbrier\b/i)
    expect(text).not.toMatch(/\bcalibration\b/i)
    expect(text).not.toContain(r.id)

    expect(derivedFrom.domain_phrase).toBe(DOMAIN_PHRASE.career)
    expect(derivedFrom.window_last_day).toBe('2026-06-30')
  })

  it('an unmapped domain token contributes nothing to the text (never passed through raw)', () => {
    const result = composeWindowAsk(row({ domain: 'zzz_internal_token' }), '2026-08-23')
    expect(result.composed).toBe(true)
    if (!result.composed) return
    expect(result.ask.text).not.toContain('zzz_internal_token')
    expect(result.ask.derivedFrom.domain_phrase).toBeNull()
  })

  it('a null domain omits the domain phrase entirely, without erroring', () => {
    const result = composeWindowAsk(row({ domain: null }), '2026-08-23')
    expect(result.composed).toBe(true)
    if (!result.composed) return
    expect(result.ask.derivedFrom.domain_phrase).toBeNull()
    expect(result.ask.text).toMatch(/^Before I answer — in .+ I said:/)
  })

  it('composition is always the literal "deterministic"', () => {
    const result = composeWindowAsk(row(), '2026-08-23')
    expect(result.composed).toBe(true)
    if (result.composed) expect(result.ask.composition).toBe('deterministic')
  })

  it('is pure: the same row + same asOf produce byte-identical text', () => {
    const r = row()
    const a = composeWindowAsk(r, '2026-08-23')
    const b = composeWindowAsk(r, '2026-08-23')
    expect(a).toEqual(b)
  })
})
