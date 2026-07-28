/**
 * SAMĪKṢĀ daily-job UNIT tests — PB-3 lane L-4.
 *
 * Pure, DB-free coverage of the genuinely-pure pieces: daterange upper decoding, the digest
 * emptiness rule, the golden digest render, the W-5 log-only transport's honesty
 * (realDelivery=false, never faked), the in-memory journal's per-day semantics, and
 * runDailyJob's input validation.
 *
 * The JOB'S CORE BEHAVIOUR (window closes, closing-soon detection, single-digest idempotency)
 * is deliberately NOT tested here with a fake exec — that would be the PB-2 false-confidence
 * anti-pattern (mock the thing you're proving). It is proven against a REAL migrated Postgres
 * in samiksha_daily_job.integration.test.ts, which runs the job TWICE and asserts the second
 * run does nothing.
 */

import { describe, it, expect } from 'vitest'
import {
  upperDateOfRange,
  digestIsEmpty,
  renderDigest,
  LogOnlyTransport,
  RecordingTransport,
  type DigestPayload,
} from '@/lib/pariprashna/samiksha/digest'
import { InMemoryDigestJournal } from '@/lib/pariprashna/samiksha/digest_journal'
import { runDailyJob } from '@/lib/pariprashna/samiksha/daily_job'

describe('upperDateOfRange', () => {
  it('decodes the exclusive upper of a daterange literal', () => {
    expect(upperDateOfRange('[2026-07-01,2027-01-01)')).toBe('2027-01-01')
    expect(upperDateOfRange('[2026-01-01,2026-06-01)')).toBe('2026-06-01')
  })
  it('returns null for null/empty/unbounded upper', () => {
    expect(upperDateOfRange(null)).toBeNull()
    expect(upperDateOfRange('')).toBeNull()
    expect(upperDateOfRange('[2026-01-01,)')).toBeNull()
  })
})

function payload(over: Partial<DigestPayload> = {}): DigestPayload {
  return {
    as_of: '2026-07-15',
    closed: [],
    closing_soon: [],
    closing_soon_days: 14,
    generated_at: '2026-07-15T03:00:00.000Z',
    ...over,
  }
}

describe('digestIsEmpty', () => {
  it('is empty when both sections are empty', () => {
    expect(digestIsEmpty(payload())).toBe(true)
  })
  it('is non-empty when there is a closed item', () => {
    expect(
      digestIsEmpty(
        payload({
          closed: [
            { id: 'a', chart_id: 'c', claim_text: 'x', domain: null, window: null, confidence: null, direction: null, window_end: null },
          ],
        }),
      ),
    ).toBe(false)
  })
  it('is non-empty when there is only a closing-soon item', () => {
    expect(
      digestIsEmpty(
        payload({
          closing_soon: [
            { id: 'b', chart_id: 'c', claim_text: 'y', domain: null, window: null, confidence: null, direction: null, window_end: null },
          ],
        }),
      ),
    ).toBe(false)
  })
})

describe('renderDigest (golden)', () => {
  it('renders subject + both sections deterministically', () => {
    const p = payload({
      closed: [
        {
          id: '11111111-1111-1111-1111-111111111111',
          chart_id: 'c',
          claim_text: 'Native transitions to a leadership role.',
          domain: 'career',
          window: '[2026-01-01,2026-06-01)',
          confidence: '[0.55,0.7)',
          direction: 'positive',
          window_end: '2026-06-01',
        },
      ],
      closing_soon: [
        {
          id: '22222222-2222-2222-2222-222222222222',
          chart_id: 'c',
          claim_text: 'A relocation window opens.',
          domain: 'relocation',
          window: '[2026-07-10,2026-07-20)',
          confidence: null,
          direction: null,
          window_end: '2026-07-20',
        },
      ],
    })
    const { subject, text } = renderDigest(p)
    expect(subject).toBe('[Samīkṣā] 1 window(s) closed, 1 closing soon — as of 2026-07-15')
    expect(text).toContain('── Windows closed today (1) — awaiting resolution ──')
    expect(text).toContain('Native transitions to a leadership role.')
    expect(text).toContain('[career · window [2026-01-01,2026-06-01) · p=[0.55,0.7) · positive]')
    expect(text).toContain('── Closing soon within 14d (1) ──')
    expect(text).toContain('A relocation window opens.')
    expect(text).toContain('(id 22222222-2222-2222-2222-222222222222)')
  })
})

describe('LogOnlyTransport (W-5 stub — never fakes a send)', () => {
  it('logs a clearly-marked stub block and reports realDelivery=false', async () => {
    const logs: string[] = []
    const t = new LogOnlyTransport({ info: (m?: unknown) => logs.push(String(m)) })
    const res = await t.send({ subject: 's', text: 'body', payload: payload() })
    expect(res.ok).toBe(true)
    expect(res.mode).toBe('log-only-stub')
    expect(res.realDelivery).toBe(false) // the honesty invariant
    expect(logs.join('\n')).toContain('STUB TRANSPORT (W-5) — LOG-ONLY, NOT EMAILED.')
  })
})

describe('RecordingTransport', () => {
  it('records every message it is asked to send', async () => {
    const t = new RecordingTransport()
    await t.send({ subject: 'a', text: 'b', payload: payload() })
    expect(t.sent).toHaveLength(1)
    expect(t.sent[0].subject).toBe('a')
  })
})

describe('InMemoryDigestJournal', () => {
  it('reports hasSent only after markSent for that date', async () => {
    const j = new InMemoryDigestJournal()
    expect(await j.hasSent('2026-07-15')).toBe(false)
    await j.markSent('2026-07-15', {
      as_of: '2026-07-15',
      sent_at: 'now',
      closed_count: 1,
      closing_soon_count: 0,
      transport_mode: 'log-only-stub',
      real_delivery: false,
    })
    expect(await j.hasSent('2026-07-15')).toBe(true)
    expect(await j.hasSent('2026-07-16')).toBe(false) // isolated per date
  })
  it('rejects a malformed as_of', async () => {
    const j = new InMemoryDigestJournal()
    await expect(j.hasSent('07/15/2026')).rejects.toThrow(/yyyy-mm-dd/)
  })
})

describe('runDailyJob input validation', () => {
  it('rejects a non-ISO asOf before touching the DB', async () => {
    await expect(runDailyJob({ asOf: '2026/07/15' })).rejects.toThrow(/asOf must be ISO/)
  })
  it('rejects a negative closingSoonDays', async () => {
    await expect(runDailyJob({ asOf: '2026-07-15', closingSoonDays: -1 })).rejects.toThrow(
      /closingSoonDays/,
    )
  })
})
