/**
 * byte_identity_probe.ts — the serving byte-identity harness PB-3's Final Proof
 * depends on (BRIEF_PB-3 §G item 11 + Final proof: a fixed serving question's
 * response must be byte-identical before and after the whole predict→confirm→
 * resolve→calibrate cycle. "If serving moved, or no row landed, no wave.").
 *
 * A GENERIC before/after probe: capture the exact bytes a fixed serving question
 * produces, run some intervening state change (for the Final Proof: a full
 * calibration loop; for this lane's own smoke: anything), capture again, and
 * assert byte-for-byte identity. It takes the capture + the intervening mutation
 * as callbacks so the INTEGRATE step can invoke it before/after the real
 * L-1..L-5 loop test without this module knowing anything about that loop.
 *
 * The authoritative verdict (`identical`) comes from a byte-for-byte scan
 * (`firstDivergence`), never from a digest collision. The `digest` field is a
 * cheap FNV-1a fingerprint kept ONLY for compact logging; it is intentionally
 * not the source of truth (a hash-only gate could be fooled by a collision, and
 * this is the integrity lane). No crypto dependency is taken for that reason.
 *
 * Anti-gaming (BRIEF_PB-3 §G, verbatim): the charge names "a byte-identity check
 * against a cached response" as a way to fake this gate. The SAME `captureServing`
 * callback is invoked for BOTH captures, so there is no cached "before" blob to
 * diff against — the before-bytes are produced by re-running the real capture,
 * live, each time. Every capture is additionally run through the COLLECT-ONLY
 * runtime guard (`assertNoCalibrationLeak`) when the bytes parse as JSON, so a
 * capture that is byte-identical but carries calibration data still fails.
 */

import { assertNoCalibrationLeak } from './calibration_leak_guard'

/** A single capture of a serving response's bytes. */
export interface ServingCapture {
  readonly bytes: Uint8Array
  /** FNV-1a fingerprint (hex) — for compact logging only, NOT the verdict source. */
  readonly digest: string
  readonly length: number
}

/** Result of a before/after byte-identity probe. */
export interface ByteIdentityResult {
  readonly identical: boolean
  readonly before: ServingCapture
  readonly after: ServingCapture
  /** Index of the first differing byte, or -1 if identical. */
  readonly firstDivergenceByte: number
  readonly summary: string
}

/** What the harness accepts from a capture callback (bytes in any common form). */
export type CaptureResult = Uint8Array | ArrayBuffer | string

function toBytes(result: CaptureResult): Uint8Array {
  if (typeof result === 'string') return new TextEncoder().encode(result)
  if (result instanceof Uint8Array) return result
  return new Uint8Array(result)
}

/** FNV-1a 32-bit fingerprint, hex. Logging convenience only — never the verdict. */
function fnv1aHex(bytes: Uint8Array): string {
  let h = 0x811c9dc5
  for (let i = 0; i < bytes.length; i++) {
    h ^= bytes[i]
    h = Math.imul(h, 0x01000193)
  }
  return (h >>> 0).toString(16).padStart(8, '0')
}

/** First index at which two byte arrays differ; -1 if equal (incl. equal length). */
function firstDivergence(a: Uint8Array, b: Uint8Array): number {
  const n = Math.min(a.length, b.length)
  for (let i = 0; i < n; i++) {
    if (a[i] !== b[i]) return i
  }
  if (a.length !== b.length) return n
  return -1
}

/**
 * Capture a serving response's bytes once, fingerprint them, and — if they parse
 * as JSON — run the COLLECT-ONLY leak guard on the parsed payload. Throws
 * `CalibrationLeakError` if the captured response carries calibration data.
 */
export async function captureServingBytes(
  capture: () => Promise<CaptureResult> | CaptureResult,
  context = 'serving-capture',
): Promise<ServingCapture> {
  const bytes = toBytes(await capture())
  const text = new TextDecoder().decode(bytes)
  const trimmed = text.trim()
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      const parsed = JSON.parse(trimmed) as unknown
      assertNoCalibrationLeak(parsed, context)
    } catch (err) {
      if (err instanceof Error && err.name === 'CalibrationLeakError') throw err
    }
  }
  return { bytes, digest: fnv1aHex(bytes), length: bytes.length }
}

/**
 * Run a before/after byte-identity probe. `captureServing` is invoked LIVE for
 * BOTH captures (never a cached blob). `mutateState` is the intervening state
 * change to prove serving is invariant under (for the Final Proof: the full
 * predict→confirm→resolve→calibrate loop). May be a no-op for a trivial smoke.
 */
export async function runByteIdentityProbe(args: {
  captureServing: () => Promise<CaptureResult> | CaptureResult
  mutateState: () => Promise<void> | void
  context?: string
}): Promise<ByteIdentityResult> {
  const context = args.context ?? 'byte-identity-probe'
  const before = await captureServingBytes(args.captureServing, `${context}:before`)
  await args.mutateState()
  const after = await captureServingBytes(args.captureServing, `${context}:after`)

  const firstDivergenceByte = firstDivergence(before.bytes, after.bytes)
  const identical = firstDivergenceByte === -1

  const summary = identical
    ? `byte-identical (${before.length}B, fnv1a=${before.digest}) across ${context}`
    : `SERVING MOVED across ${context}: before ${before.length}B (fnv1a=${before.digest}) ` +
      `after ${after.length}B (fnv1a=${after.digest}); first diverging byte at index ${firstDivergenceByte}`

  return { identical, before, after, firstDivergenceByte, summary }
}

/**
 * Convenience assertion wrapper: runs the probe and throws if serving moved.
 * "If serving moved … no wave."
 */
export async function assertServingByteIdentical(args: {
  captureServing: () => Promise<CaptureResult> | CaptureResult
  mutateState: () => Promise<void> | void
  context?: string
}): Promise<ByteIdentityResult> {
  const result = await runByteIdentityProbe(args)
  if (!result.identical) {
    throw new Error(result.summary)
  }
  return result
}
