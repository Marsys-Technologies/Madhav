/**
 * serving_byte_identity.test.ts — demonstrates the serving byte-identity harness
 * (PB-3 lane L-6 deliverable 4; BRIEF_PB-3 §G item 11 + Final proof). Acceptance:
 * "the serving byte-identity harness (used by the final proof) built and
 * demonstrated" — shown here on a trivial before/after case, ahead of the real
 * L-1..L-5 loop existing to test against.
 *
 * The harness is generic (capture + mutation callbacks), so the INTEGRATE step
 * points `captureServing` at the deployed flagged route and `mutateState` at the
 * full predict→confirm→resolve→calibrate loop, unchanged.
 */
import { describe, it, expect } from 'vitest'

import {
  runByteIdentityProbe,
  assertServingByteIdentical,
  captureServingBytes,
} from '@/lib/pariprashna/no_leakage/byte_identity_probe'
import { CalibrationLeakError } from '@/lib/pariprashna/no_leakage/calibration_leak_guard'

// A stand-in "serving path": deterministic bytes for a fixed question, plus some
// mutable side state the loop could touch. The Final Proof swaps this for the
// real route; the harness contract is identical.
function makeFixedServingWorld() {
  const state = { calibrationRowsWritten: 0, priorsVersion: 'v3' }
  // The served answer is a pure function of the CHART, never of calibration
  // state — that is exactly what collect-only guarantees. So the capture ignores
  // `state` entirely (the whole point).
  const captureServing = () =>
    JSON.stringify({
      question: 'What does my 10th house indicate for career?',
      verdict: 'Saturn in the 10th, dig-bala; disciplined ascent.',
      grounding: ['fact:sat_10', 'fact:digbala'],
      provenance: { build_id: 'b1', priors_version: state.priorsVersion },
    })
  return { state, captureServing }
}

describe('serving byte-identity harness — demonstrated on a trivial before/after', () => {
  it('serving is BYTE-IDENTICAL across a full "calibration loop" that does NOT touch serving', async () => {
    const { state, captureServing } = makeFixedServingWorld()

    const result = await runByteIdentityProbe({
      captureServing,
      // Simulates the loop: rows land in calibration, but serving must not move.
      mutateState: () => {
        state.calibrationRowsWritten += 1
      },
      context: 'trivial-loop',
    })

    expect(result.identical).toBe(true)
    expect(result.firstDivergenceByte).toBe(-1)
    expect(state.calibrationRowsWritten).toBe(1) // the loop really ran
    expect(result.summary).toContain('byte-identical')
  })

  it('assertServingByteIdentical does NOT throw when serving holds steady', async () => {
    const { captureServing } = makeFixedServingWorld()
    await expect(
      assertServingByteIdentical({ captureServing, mutateState: () => {}, context: 'steady' }),
    ).resolves.toBeDefined()
  })

  // ── Demonstrated-can-fail: if serving DID move, the harness catches it. ──────
  it('DETECTS a moved serving response and reports the first diverging byte', async () => {
    // A capture that leaks state into the answer — the exact bug collect-only
    // forbids. The harness must catch it (this is the gate's can-fail proof).
    const state = { priorsVersion: 'v3' }
    let calls = 0
    const leakyCapture = () => {
      calls += 1
      return JSON.stringify({ answer: 'career ascent', priors_version: state.priorsVersion })
    }

    const result = await runByteIdentityProbe({
      captureServing: leakyCapture,
      mutateState: () => {
        // A priors bump that the leaky serving path then reflects — serving moves.
        state.priorsVersion = 'v4'
      },
      context: 'leaky-loop',
    })

    expect(result.identical).toBe(false)
    expect(result.firstDivergenceByte).toBeGreaterThanOrEqual(0)
    expect(result.summary).toContain('SERVING MOVED')
    expect(calls).toBe(2) // captured live BOTH times (no cached before-blob)
  })

  it('assertServingByteIdentical THROWS when serving moved', async () => {
    let flip = 0
    await expect(
      assertServingByteIdentical({
        captureServing: () => `answer-${flip}`,
        mutateState: () => {
          flip = 1
        },
        context: 'throws-when-moved',
      }),
    ).rejects.toThrow(/SERVING MOVED/)
  })

  // ── Byte-identity alone is not enough: a stable-but-tainted capture must fail. ─
  it('a capture that is stable but carries calibration data still FAILS (leak guard on every capture)', async () => {
    const taintedCapture = () =>
      JSON.stringify({ answer: 'career ascent', calibration_badge: { brier_score: 0.1 } })
    await expect(captureServingBytes(taintedCapture, 'tainted')).rejects.toThrow(CalibrationLeakError)
  })
})
