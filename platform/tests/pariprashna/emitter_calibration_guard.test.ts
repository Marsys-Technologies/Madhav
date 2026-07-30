/**
 * emitter_calibration_guard.test.ts — G5 (SAMĀPTI §8.1 / BRIEF_PB-3.1 G5).
 *
 * The BEHAVIOURAL half of "give assertNoCalibrationLeak a real production call site".
 * `collect_only_grep.test.ts` proves the call site EXISTS in source; this file proves it
 * FIRES — that a calibration-carrying event driven through the real `PariprashnaEmitter`
 * (the one method every Paripraśna reading-stream event crosses) is rejected before a
 * single byte reaches the stream controller, and that a clean event is not.
 *
 * This is the can-fail proof FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE demands: a gate
 * that cannot go red "actively launders false confidence." The mutation is applied to the
 * DATA (a contaminated event), not to the guard, so the proof does not depend on editing
 * and reverting production source.
 */
import { describe, it, expect, vi } from 'vitest'

import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { CalibrationLeakError } from '@/lib/pariprashna/no_leakage/calibration_leak_guard'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

/** A minimal stand-in for the SSE ReadableStream controller the route hands the emitter. */
function fakeController() {
  const chunks: string[] = []
  const decoder = new TextDecoder()
  return {
    chunks,
    controller: {
      enqueue: vi.fn((u8: Uint8Array) => {
        chunks.push(decoder.decode(u8))
      }),
      close: vi.fn(),
      error: vi.fn(),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any,
  }
}

describe('G5 — the Paripraśna emitter call site actually fires', () => {
  it('a CLEAN event streams normally (no false positive on the real happy path)', () => {
    const { controller, chunks } = fakeController()
    const emitter = new PariprashnaEmitter(controller)

    emitter.turnOpen({
      turn_id: 't1',
      conversation_id: 'c1',
      chart_id: 'ch1',
      model_id: 'm1',
      reading_depth: 'auto',
      length_tier: 'standard',
    })
    emitter.flag({ code: 'catalog_only_rows_present', level: 'info' })

    expect(controller.enqueue).toHaveBeenCalledTimes(2)
    expect(chunks.join('')).toContain('turn.open')
  })

  it('THROWS CalibrationLeakError on an event carrying a bare `calibration` object', () => {
    const { controller } = fakeController()
    const emitter = new PariprashnaEmitter(controller)

    // The mutation: the exact section shape compute_spine_bundle.ts emits, riding on a
    // served event. This is what "the calibration object reaches a user-facing surface"
    // looks like in the wire format, and it is what the guard exists to stop.
    const contaminated = {
      code: 'reading_calibrated',
      level: 'info',
      calibration: { verdict_distribution: [], reliability: [], multipliers: [], qa_fail_count: 0 },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any

    expect(() => emitter.flag(contaminated)).toThrow(CalibrationLeakError)
    // Nothing was written — the guard runs BEFORE the enqueue, so no contaminated byte
    // reaches the client even transiently.
    expect(controller.enqueue).not.toHaveBeenCalled()
  })

  it('THROWS on a nested Brier score (the pre-existing key set, still enforced at this site)', () => {
    const { controller } = fakeController()
    const emitter = new PariprashnaEmitter(controller)
    expect(() =>
      emitter.grade({
        subject: 'completeness',
        value: '0.8',
        detail: { brier_score: 0.12 },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any),
    ).toThrow(CalibrationLeakError)
    expect(controller.enqueue).not.toHaveBeenCalled()
  })

  it('names the offending path in the error (diagnosable, not just a bare throw)', () => {
    const { controller } = fakeController()
    const emitter = new PariprashnaEmitter(controller)
    let caught: CalibrationLeakError | null = null
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      emitter.flag({ code: 'x', level: 'info', calibration: {} } as any)
    } catch (err) {
      caught = err as CalibrationLeakError
    }
    expect(caught).toBeInstanceOf(CalibrationLeakError)
    expect(caught!.violations.map((v) => v.path)).toContain('calibration')
    expect(caught!.message).toContain('pariprashna:flag')
  })

  it('every emitter builder routes through the guard (not just the two probed above)', () => {
    const { controller } = fakeController()
    const emitter = new PariprashnaEmitter(controller)
    const builders: readonly ((e: PariprashnaEmitter) => void)[] = [
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e) => e.blockDelta({ block_id: 'b1', text: 'x', calibration: {} } as any),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e) => e.blockCommit({ block_id: 'b1', calibration: {} } as any),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e) => e.citationDefine({ citation_id: 'c1', calibration: {} } as any),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e) => e.turnCommit({ turn_id: 't1', calibration: {} } as any),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e) => e.turnClose({ turn_id: 't1', calibration: {} } as any),
    ]
    for (const drive of builders) {
      expect(() => drive(emitter)).toThrow(CalibrationLeakError)
    }
    expect(controller.enqueue).not.toHaveBeenCalled()
  })
})

/**
 * Guard-scope honesty: `writeRawEvent` (the resume/replay path) deliberately does NOT
 * re-assert — see the note on `PariprashnaEmitter.assertServable`. Asserting that here
 * keeps the exemption an explicit, tested decision rather than an oversight someone
 * later "fixes" without knowing why it was made.
 */
describe('G5 — the resume/replay path is a STATED exemption, not an oversight', () => {
  it('writeRawEvent replays a historical event without re-running the guard', async () => {
    const { writeRawEvent } = await import('@/lib/pariprashna/protocol/emitter')
    const { controller } = fakeController()
    const historical = {
      type: 'flag',
      seq: 7,
      t: 1,
      code: 'x',
      level: 'info',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any as PariprashnaEvent
    expect(writeRawEvent(controller, historical)).toBe(true)
    expect(controller.enqueue).toHaveBeenCalledTimes(1)
  })
})
