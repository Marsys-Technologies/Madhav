/**
 * calibration_leak_guard.ts — the COLLECT-ONLY *runtime* assertion (PB-3 lane
 * L-6, §14.6 C1 / wave ruling W-3). Companion to the static grep gate
 * (`serving_path_manifest.ts` + `collect_only_grep.test.ts`).
 *
 * The brief requires collect-only be proven "with a grep test + runtime
 * assertion, not config." The grep gate proves the *source* has no code path
 * from a calibration write to a priors bump / serving annotation. This guard is
 * the *runtime* half: a pure, throw-on-violation check that a served envelope
 * (or any object about to cross the serving boundary) carries NO calibration-
 * derived content — so that if some future code path ever did leak calibration
 * data into a serving response at runtime, it fails loudly and immediately
 * rather than silently shipping a non-byte-identical answer.
 *
 * ── Grant honesty (disclosed) ─────────────────────────────────────────────────
 * Lane L-6's `may_touch` covers `platform/src/lib/pariprashna/**` and the
 * registry, but NOT the serving route files themselves (`api/pariprashna`,
 * `api/chat`). This module is therefore the reusable guard; it is exercised by
 * the byte-identity harness (which runs it on every capture) and unit-proven
 * here. Wiring `assertNoCalibrationLeak()` into the live route/envelope emit
 * seam is a one-line ADDITIVE call the INTEGRATE step (or a follow-up in-grant of
 * the route) should add — recorded as a recommendation in REPORT_PB-3, never
 * silently claimed as already-wired. The guard is real and demonstrated-can-fail
 * regardless of where it is called from.
 */

/**
 * Tokens that only appear on a served payload if calibration data leaked into
 * it. Deliberately EXCLUDES the bare token `priors_version` — the D-16
 * provenance stamp carries `priors_version` legitimately as DB-only audit
 * metadata that is never streamed (route.ts). What is forbidden on a SERVED
 * envelope is a calibration *result* (a Brier score, a reliability/calibration
 * adjustment, a "priors bumped" marker), not the version string an audit stamp
 * records.
 */
const CALIBRATION_LEAK_KEYS: readonly RegExp[] = [
  /brier[_-]?score/i,
  /calibration[_-]?(annotation|badge|adjustment|weight|applied)/i,
  /priors[_-]?bumped/i,
  /outcome[_-]?recorded/i,
  /mimamsa_calibration/i,
]

export interface CalibrationLeakViolation {
  /** The dotted path to the offending key within the payload. */
  readonly path: string
  /** Which leak-key pattern matched. */
  readonly matched: string
}

/**
 * Deep-scans an arbitrary payload for calibration-leak keys. Pure; returns every
 * violation found (empty array = clean). Recurses objects + arrays; matches on
 * OBJECT KEYS (a served envelope leaks by carrying a calibration field, not by
 * mentioning the word in free prose — prose is the register-leak lint's job,
 * a separate concern). Guards against cycles.
 */
export function findCalibrationLeaks(payload: unknown): CalibrationLeakViolation[] {
  const violations: CalibrationLeakViolation[] = []
  const seen = new WeakSet<object>()

  const walk = (node: unknown, path: string): void => {
    if (node === null || typeof node !== 'object') return
    if (seen.has(node as object)) return
    seen.add(node as object)

    if (Array.isArray(node)) {
      node.forEach((child, i) => walk(child, `${path}[${i}]`))
      return
    }

    for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
      const childPath = path ? `${path}.${key}` : key
      for (const rx of CALIBRATION_LEAK_KEYS) {
        if (rx.test(key)) {
          violations.push({ path: childPath, matched: rx.source })
          break
        }
      }
      walk(value, childPath)
    }
  }

  walk(payload, '')
  return violations
}

/** Thrown by `assertNoCalibrationLeak` when a served payload carries calibration data. */
export class CalibrationLeakError extends Error {
  readonly violations: readonly CalibrationLeakViolation[]
  constructor(violations: readonly CalibrationLeakViolation[], context?: string) {
    const where = context ? ` in ${context}` : ''
    super(
      `COLLECT-ONLY violation${where}: served payload carries calibration-derived ` +
        `field(s) [${violations.map((v) => v.path).join(', ')}]. Collect-only (§14.6 C1 / W-3) ` +
        `forbids any calibration result reaching a serving envelope — serving must be ` +
        `byte-identical whether or not calibration data exists.`,
    )
    this.name = 'CalibrationLeakError'
    this.violations = violations
  }
}

/**
 * Runtime assertion: throws `CalibrationLeakError` if `payload` carries any
 * calibration-derived field, otherwise returns silently. Call it on any object
 * about to cross the serving boundary (an envelope, an SSE event body, a JSON
 * response). Cheap enough to run on every served response.
 */
export function assertNoCalibrationLeak(payload: unknown, context?: string): void {
  const violations = findCalibrationLeaks(payload)
  if (violations.length > 0) {
    throw new CalibrationLeakError(violations, context)
  }
}
