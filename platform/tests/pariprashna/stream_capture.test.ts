/**
 * SAMĀPTI lane B-PB8-BYTEEQ — `src/lib/pariprashna/protocol/stream_capture.ts`.
 *
 * This module sits on the LIVE streaming hot path of every real reading, so the
 * properties that matter most are the negative ones: with the flag unset it must
 * touch nothing, and a DB failure must never surface to the reader. Those are
 * the first assertions below, and each one can go red (proven by the mocked
 * `query` spy's call count / a forced rejection).
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const queryMock = vi.fn(async () => ({ rows: [], rowCount: 0 }))
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...(args as [])) }))

import {
  beginTurnCapture,
  captureEvent,
  endTurnCapture,
  isTurnCaptured,
  isStreamCaptureEnabled,
  streamCaptureSampleRate,
  __resetStreamCaptureForTests,
} from '@/lib/pariprashna/protocol/stream_capture'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

const TURN = { turnId: 't-1', conversationId: 'c-1', chartId: 'chart-1' }
const EV: PariprashnaEvent = { type: 'block.commit', seq: 3, t: 30, block_id: 'b1', text: 'hello' }

const savedEnv = { ...process.env }

beforeEach(() => {
  queryMock.mockClear()
  queryMock.mockImplementation(async () => ({ rows: [], rowCount: 0 }))
  __resetStreamCaptureForTests()
})
afterEach(() => {
  process.env = { ...savedEnv }
})

describe('stream_capture — off by default', () => {
  it('is disabled unless PARIPRASHNA_STREAM_CAPTURE is 1/true', () => {
    delete process.env.PARIPRASHNA_STREAM_CAPTURE
    expect(isStreamCaptureEnabled()).toBe(false)
    process.env.PARIPRASHNA_STREAM_CAPTURE = '0'
    expect(isStreamCaptureEnabled()).toBe(false)
    process.env.PARIPRASHNA_STREAM_CAPTURE = '1'
    expect(isStreamCaptureEnabled()).toBe(true)
    process.env.PARIPRASHNA_STREAM_CAPTURE = 'true'
    expect(isStreamCaptureEnabled()).toBe(true)
  })

  it('writes ZERO rows when the flag is unset, even if captureEvent is called', async () => {
    delete process.env.PARIPRASHNA_STREAM_CAPTURE
    expect(beginTurnCapture(TURN)).toBe(false)
    await captureEvent(TURN.turnId, EV)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('stream_capture — sampling is per TURN, never per event', () => {
  beforeEach(() => {
    process.env.PARIPRASHNA_STREAM_CAPTURE = '1'
  })

  it('a sampled-out turn captures NONE of its events', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '0.1'
    expect(beginTurnCapture(TURN, () => 0.9)).toBe(false)
    for (const seq of [0, 1, 2]) await captureEvent(TURN.turnId, { ...EV, seq })
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('a sampled-in turn captures ALL of its events (whole or nothing)', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '0.1'
    expect(beginTurnCapture(TURN, () => 0.05)).toBe(true)
    for (const seq of [0, 1, 2]) await captureEvent(TURN.turnId, { ...EV, seq })
    expect(queryMock).toHaveBeenCalledTimes(3)
  })

  it('sample rate 0 disables capture even with the flag on', () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '0'
    expect(streamCaptureSampleRate()).toBe(0)
    expect(beginTurnCapture(TURN, () => 0)).toBe(false)
  })

  it('an unmarked turn is a pure no-op', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '1'
    beginTurnCapture(TURN)
    await captureEvent('some-other-turn', EV)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('endTurnCapture releases the mark', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '1'
    beginTurnCapture(TURN)
    expect(isTurnCaptured(TURN.turnId)).toBe(true)
    endTurnCapture(TURN.turnId)
    expect(isTurnCaptured(TURN.turnId)).toBe(false)
    await captureEvent(TURN.turnId, EV)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('stream_capture — a forensic sink must never break a live reading', () => {
  it('swallows a DB failure instead of propagating it to the stream', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE = '1'
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '1'
    beginTurnCapture(TURN)
    queryMock.mockImplementation(async () => {
      throw new Error('relation "pariprashna_stream_capture" does not exist')
    })
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    await expect(captureEvent(TURN.turnId, EV)).resolves.toBeUndefined()
    expect(warn).toHaveBeenCalled()
    warn.mockRestore()
  })

  it('the insert is idempotent on the wire seq natural key', async () => {
    process.env.PARIPRASHNA_STREAM_CAPTURE = '1'
    process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE = '1'
    beginTurnCapture(TURN)
    await captureEvent(TURN.turnId, EV)
    const sql = String((queryMock.mock.calls[0] as unknown as [string])[0])
    expect(sql).toContain('ON CONFLICT (turn_id, seq) DO NOTHING')
  })
})

describe('stream_capture — privacy claim is checked against the protocol, not asserted', () => {
  it('no PariprashnaEvent member carries the user question, so captures hold assistant-side data only', () => {
    // The migration + module both claim "no user text is captured". That claim
    // is only as good as the wire schema, so verify it against the schema
    // source rather than restating it. Same technique as ring_buffer.test.ts's
    // source-grep exclusion proof.
    const events = readFileSync(
      join(__dirname, '..', '..', 'src', 'lib', 'pariprashna', 'protocol', 'events.ts'),
      'utf8',
    )
    // Field names that would indicate the native's own question riding the wire.
    for (const forbidden of ['user_text:', 'userText:', 'prompt:', 'question:', 'user_message:']) {
      expect(events, `protocol/events.ts must not carry ${forbidden}`).not.toContain(forbidden)
    }
  })
})
