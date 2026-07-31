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
 * ── Production call sites (G5 — SAMĀPTI §8.1 / BRIEF_PB-3.1 G5) ───────────────
 * This guard previously had ZERO production call sites: it was exercised only by
 * the byte-identity harness and its own unit test, so "collect-only is enforced
 * at runtime" was a claim about a function nobody called. It is now wired at the
 * two real reading-serving boundaries:
 *
 *   1. `PariprashnaEmitter.write()` (protocol/emitter.ts) — EVERY event of the
 *      Paripraśna reading stream crosses this one method, so the whole served
 *      stream is covered by a single call site. The protocol's Zod event schemas
 *      are fully closed (no `z.record`/`z.unknown`/`.passthrough()`), so the set
 *      of keys that can appear is bounded by the schema and this guard cannot
 *      false-positive on a well-formed event.
 *   2. `/api/mcp/prashna_ask`'s `final` body — the MCP reading envelope.
 *
 * ── Why the raw evidence array is guarded SEPARATELY from the envelope ────────
 * `prashna_ask`'s final body carries `results`: the verbatim row payloads of the
 * tools the planner selected. Those rows are NOT an envelope annotation — they
 * are the tool's own disclosed output, explicitly requested. Two live tools
 * return rows whose COLUMN NAMES match this guard's key set for entirely
 * legitimate reasons: `query_calibration` (the declared calibration surface,
 * deliberately kept planner-selectable — see descriptor_defaults.ts's
 * CALIBRATION_CONTEXT_ONLY_URIS comment) returns a `brier_score` column, and
 * `query_projections` returns an `outcome_recorded` column. Guarding raw rows
 * with the envelope's key set would therefore fire on correct behaviour, and a
 * guard that cries wolf on correct behaviour gets deleted. The envelope — the
 * layer W-3 actually protects ("served phala/kala envelopes are byte-identical
 * whether or not calibration data exists") — is guarded; the evidence array is
 * excluded EXPLICITLY, named, and covered instead by NO-LEAKAGE arm 2 (the
 * `calibration_context_only` dispatch filter) and arm 1 (the static grep gate).
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
export const CALIBRATION_LEAK_KEYS: readonly RegExp[] = [
  /brier[_-]?score/i,
  /calibration[_-]?(annotation|badge|adjustment|weight|applied)/i,
  /priors[_-]?bumped/i,
  /outcome[_-]?recorded/i,
  /mimamsa_calibration/i,
  // G5: a BARE `calibration` key. Before this, the guard's suffixed patterns above
  // could not match the one real calibration payload in the estate —
  // `compute_spine_bundle.ts` names its section exactly `calibration`
  // ({ verdict_distribution, reliability, multipliers, qa_fail_count }), so a
  // guard wired to a serving envelope would have waved it straight through. ANCHORED
  // (^…$) on purpose: it matches the bare key and nothing else, so legitimate
  // neighbours such as `calibration_context_only` (a descriptor flag, not a result)
  // and free-prose keys containing the word are not swept up. A calibration RESULT
  // object on a served envelope is a leak whatever it is named; this closes the
  // most obvious name.
  /^calibration$/i,
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
