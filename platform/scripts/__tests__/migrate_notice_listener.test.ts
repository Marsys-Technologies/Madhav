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
