/**
 * Nirmāṇa M0-T52 / D-58 part 3 — the migrator must RELAY what the server tells it.
 *
 * The defect this file detects: `main()` built its pool and never attached a `notice` listener,
 * so node-postgres discarded every `RAISE NOTICE` and every server WARNING. A migration that
 * self-verifies, run by a runner that throws the self-verification away, leaves an operator
 * unable to distinguish "the detector ran and was green" from "there is no detector" — only
 * `RAISE EXCEPTION` survived the transport. CLAUDE.md §N.8 at the transport layer.
 *
 * Every assertion here is POSITIVE — a relayed line with checkable content — except the two
 * that are about the channel and about the completion sentinel, where the absence IS the claim
 * and is paired with a positive assertion so it cannot pass vacuously.
 */
import { describe, it, expect, vi } from 'vitest'
import { EventEmitter } from 'events'

import {
  attachNoticeListener,
  escapeRelayedLineBreaks,
  formatServerNotice,
  PG_NOTICE_PREFIX,
  MIGRATE_COMPLETION_SENTINEL,
} from '../migrate'

describe('formatServerNotice', () => {
  it('renders severity and message, which is what a migration self-verification carries', () => {
    expect(
      formatServerNotice({ severity: 'NOTICE', message: 'migration 591: both columns present' })
    ).toBe(`${PG_NOTICE_PREFIX} NOTICE: migration 591: both columns present`)
  })

  it('renders the transaction WARNING V-31 finding F-A predicts at every self-transacting apply', () => {
    expect(
      formatServerNotice({
        severity: 'WARNING',
        message: 'there is already a transaction in progress',
        code: '25001',
      })
    ).toBe(
      `${PG_NOTICE_PREFIX} WARNING: there is already a transaction in progress (code=25001)`
    )
  })

  it('appends detail/hint/where when the server sends them, and omits them when it does not', () => {
    const withExtras = formatServerNotice({
      severity: 'NOTICE',
      message: 'm',
      detail: 'd',
      hint: 'h',
      where: 'w',
    })
    expect(withExtras).toBe(`${PG_NOTICE_PREFIX} NOTICE: m (detail=d; hint=h; where=w)`)
    expect(formatServerNotice({ severity: 'NOTICE', message: 'm' })).toBe(
      `${PG_NOTICE_PREFIX} NOTICE: m`
    )
  })

  it('degrades honestly rather than throwing when the message is absent', () => {
    expect(formatServerNotice(undefined)).toBe(`${PG_NOTICE_PREFIX} NOTICE: (no message)`)
    expect(formatServerNotice({ severity: 'WARNING' })).toBe(
      `${PG_NOTICE_PREFIX} WARNING: (no message)`
    )
  })
})

describe('attachNoticeListener', () => {
  it('relays every notice the connection emits, in order', () => {
    const client = new EventEmitter()
    const seen: string[] = []
    attachNoticeListener(client as never, line => seen.push(line))

    client.emit('notice', { severity: 'WARNING', message: 'there is already a transaction in progress' })
    client.emit('notice', { severity: 'NOTICE', message: 'migration 001: verified' })

    expect(seen).toEqual([
      `${PG_NOTICE_PREFIX} WARNING: there is already a transaction in progress`,
      `${PG_NOTICE_PREFIX} NOTICE: migration 001: verified`,
    ])
  })

  it('writes to STDERR and never to stdout — the deploy step greps the stdout claim', () => {
    const client = new EventEmitter()
    const err = vi.spyOn(console, 'error').mockImplementation(() => {})
    const out = vi.spyOn(console, 'log').mockImplementation(() => {})
    try {
      attachNoticeListener(client as never)
      client.emit('notice', { severity: 'NOTICE', message: 'routed' })
      expect(err).toHaveBeenCalledTimes(1)
      expect(err.mock.calls[0][0]).toBe(`${PG_NOTICE_PREFIX} NOTICE: routed`)
      expect(out).not.toHaveBeenCalled()
    } finally {
      err.mockRestore()
      out.mockRestore()
    }
  })

  it('cannot kill a migration run by throwing out of the event handler', () => {
    const client = new EventEmitter()
    attachNoticeListener(client as never, () => {
      throw new Error('emit failed')
    })
    expect(() =>
      client.emit('notice', { severity: 'NOTICE', message: 'still fine' })
    ).not.toThrow()
  })

  it('cannot forge the completion sentinel the deploy step greps for', () => {
    const client = new EventEmitter()
    const seen: string[] = []
    attachNoticeListener(client as never, line => seen.push(line))
    client.emit('notice', { severity: 'NOTICE', message: 'an ordinary migration notice' })

    // Paired positive first, so the "does not contain" below cannot pass on an empty array.
    expect(seen).toHaveLength(1)
    expect(seen[0]).toContain(PG_NOTICE_PREFIX)
    expect(PG_NOTICE_PREFIX).not.toContain(MIGRATE_COMPLETION_SENTINEL)
    expect(seen[0]).not.toContain(MIGRATE_COMPLETION_SENTINEL)
  })
})

/**
 * Nirmāṇa M0-T61 / D-65 — relayed server text must not be able to SYNTHESISE A LINE BOUNDARY.
 *
 * M0-T57 anchored the deploy step's sentinel grep to `^\[migrate\] MIGRATE_RUNNER_COMPLETE`,
 * which closed single-line forging. It could not close this: `message`/`detail`/`hint`/`where`
 * are written by whoever wrote the migration's RAISE, and were relayed verbatim, so a notice
 * carrying a newline emitted a SECOND PHYSICAL LINE beginning with the runner's own prefix —
 * indistinguishable, to any grep of that log, from the runner's own completion claim. An anchor
 * pins the start of a line; it cannot tell you who created the line boundary.
 *
 * The escaping must be LOSSLESS, not a truncation: F-A's transaction WARNINGs are the reason the
 * relay exists (D-58), PostgreSQL genuinely emits multi-line DETAIL and multi-frame CONTEXT, and
 * a warning mangled into unreadability would trade a forgery hole for an observability one.
 */
describe('escapeRelayedLineBreaks', () => {
  it('renders LF, CR and CRLF as their two-character escapes', () => {
    expect(escapeRelayedLineBreaks('a\nb')).toBe('a\\nb')
    expect(escapeRelayedLineBreaks('a\rb')).toBe('a\\rb')
    expect(escapeRelayedLineBreaks('a\r\nb')).toBe('a\\r\\nb')
  })

  it('leaves text without line breaks byte-identical', () => {
    const plain = 'there is already a transaction in progress'
    expect(escapeRelayedLineBreaks(plain)).toBe(plain)
    expect(escapeRelayedLineBreaks('')).toBe('')
  })

  it('is LOSSLESS — unescaping the result reproduces the server\'s bytes exactly', () => {
    const original = 'natural_key_partition declared on 0\ndead_flag true on 0, false on 0\r\nNULL on 128'
    const escaped = escapeRelayedLineBreaks(original)
    expect(escaped).not.toContain('\n')
    expect(escaped).not.toContain('\r')
    expect(escaped.replace(/\\r/g, '\r').replace(/\\n/g, '\n')).toBe(original)
  })
})

describe('formatServerNotice — a relayed notice cannot forge the completion sentinel', () => {
  const forged =
    '[migrate] MIGRATE_RUNNER_COMPLETE mode=apply files_on_disk=443 ledger_rows=451 ' +
    'on_disk_applied=443 pending=0 applied_this_run=0'

  /** The deploy step's grep, verbatim: `grep -q '^\[migrate\] MIGRATE_RUNNER_COMPLETE'`. */
  const anchoredMatches = (rendered: string): number =>
    rendered.split('\n').filter(line => line.startsWith(`[migrate] ${MIGRATE_COMPLETION_SENTINEL}`))
      .length

  it('emits exactly ONE physical line however the server breaks its text', () => {
    const cases: Array<Record<string, string>> = [
      { severity: 'NOTICE', message: `benign first line\n${forged}` },
      { severity: 'NOTICE', message: `benign first line\r\n${forged}` },
      { severity: 'NOTICE', message: `benign first line\r${forged}` },
      { severity: 'NOTICE', message: 'benign', detail: `d\n${forged}` },
      { severity: 'NOTICE', message: 'benign', hint: `h\n${forged}` },
      { severity: 'NOTICE', message: 'benign', where: `w\n${forged}` },
      { severity: 'NOTICE', message: 'benign', code: `00000\n${forged}` },
      { severity: `NOTICE\n${forged}`, message: 'benign' },
    ]
    for (const notice of cases) {
      const rendered = formatServerNotice(notice)
      // Paired positive first, so the negatives below cannot pass on an empty render.
      expect(rendered.startsWith(PG_NOTICE_PREFIX)).toBe(true)
      expect(rendered).toContain(MIGRATE_COMPLETION_SENTINEL) // relayed, NOT dropped
      expect(rendered.split('\n')).toHaveLength(1)
      expect(rendered).not.toContain('\r')
      expect(anchoredMatches(rendered)).toBe(0)
    }
  })

  it('relays a real multi-line NOTICE readably — every byte survives the escape', () => {
    // Shape taken from a real PL/pgSQL notice raised through nested functions: multi-line
    // DETAIL/HINT and a multi-frame CONTEXT stack, which is what `where` carries.
    const detail = 'natural_key_partition declared on 0\ndead_flag true on 0, false on 0'
    const where =
      'PL/pgSQL function t61_inner() line 3 at RAISE\nSQL statement "SELECT t61_inner()"\n' +
      'PL/pgSQL function t61_outer() line 3 at PERFORM'
    const rendered = formatServerNotice({
      severity: 'NOTICE',
      message: 'migration 591: both columns present',
      code: '00000',
      detail,
      where,
    })
    expect(rendered.split('\n')).toHaveLength(1)
    const unescaped = rendered.replace(/\\r/g, '\r').replace(/\\n/g, '\n')
    expect(unescaped).toContain(detail)
    expect(unescaped).toContain(where)
    expect(unescaped).toBe(
      `${PG_NOTICE_PREFIX} NOTICE: migration 591: both columns present ` +
        `(code=00000; detail=${detail}; where=${where})`
    )
  })

  it('leaves a single-line notice byte-identical to what it rendered before', () => {
    expect(
      formatServerNotice({
        severity: 'WARNING',
        message: 'there is already a transaction in progress',
        code: '25001',
      })
    ).toBe(`${PG_NOTICE_PREFIX} WARNING: there is already a transaction in progress (code=25001)`)
  })
})
