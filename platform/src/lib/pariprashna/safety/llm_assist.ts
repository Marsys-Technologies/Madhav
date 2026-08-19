/**
 * Paripraśna safety — THE RAISE-ONLY LLM ASSIST ENVELOPE (lane G1-A).
 *
 * SAFETY_PRIVACY_TENANCY §3, and the roadmap row, both state the constraint the
 * same way: "an LLM assist may RAISE severity, never lower it." This module is
 * that constraint expressed as a function whose TYPE cannot express the
 * forbidden operation, so the rule holds by construction rather than by review.
 *
 * ── HOW THE GUARANTEE HOLDS, STATED ACCURATELY ───────────────────────────────
 * `mergeLlmAssist` takes the deterministic result and an assist payload and
 * returns a merged result. The merge is a MONOTONE JOIN:
 *   · classes    — set UNION. An assist cannot remove a class.
 *   · severity   — per-detection `max`. An assist cannot lower one.
 *   · detections — the deterministic detections are carried through verbatim;
 *                  assist detections are APPENDED, never substituted.
 * `assist_never_lowers.test.ts` proves it by fuzzing adversarial payloads —
 * including ones that claim `severity: 'none'` and empty class lists — against
 * every deterministic result the suite produces.
 *
 * ── WHAT THIS FILE USED TO CLAIM, AND WHY IT NO LONGER DOES ──────────────────
 * The header used to open with "a function whose TYPE cannot express the
 * forbidden operation, so the rule holds by construction rather than by
 * review", and the interface below used to say "note what this interface CANNOT
 * express". A reviewer falsified both in the cheapest possible way: they added
 * an optional `downgrade_to?: SafetySeverity` field to `LlmAssistPayload` and a
 * branch that honored it. It compiled clean and the entire suite still passed.
 * Nothing was enforcing the shape — TypeScript's structural typing will accept
 * whatever the interface is edited to say, and the interface is the thing an
 * attacker (or a careless future author) edits.
 *
 * So the guarantee is now stated as what it actually is: the merge function's
 * BODY is monotone, and `LlmAssistPayload`'s field set is pinned by
 * `LLM_ASSIST_PAYLOAD_KEYS` plus the two compile-time assertions immediately
 * below it — IN THIS FILE, which is a `src/` path — so adding a field to the
 * interface is a `tsc` error the real CI pipeline sees and fails on. That is a
 * real detector on the real claim (§N.8) instead of a compile-time guarantee
 * the compiler was never actually providing. It is a weaker guarantee than the
 * old sentence described — and it is the one that is true.
 *
 * ── WHY THE DETECTOR LIVES HERE AND NOT IN A TEST (round 3, M-1/H-6) ─────────
 * The round-2 fix put the exhaustive-keys assertion in
 * `__tests__/coverage_hardening.test.ts` as a `Required<LlmAssistPayload>`
 * object literal, and called it "a test that fails the moment a field is added
 * to the interface". Re-verification falsified that sentence against THIS
 * REPO'S ACTUAL PIPELINE:
 *   · `vitest run` does not typecheck — 128/128 still passed with
 *     `downgrade_to?: SafetySeverity` added to the interface;
 *   · `tsc --noEmit` did produce exactly one error — but inside a `__tests__/`
 *     path, and `.github/workflows/ci.yml`'s typecheck job pipes tsc output
 *     through `grep "error TS" | grep -Ev "(tests/|__tests__/)"`, which deletes
 *     that error. CI went green with a live downgrade field on the payload.
 * A detector CI filters out is not a detector (§N.8). Both assertions are
 * therefore in this file, whose path contains no `tests/` segment and so
 * survives that grep verbatim.
 *
 * ── AND THE HONEST PART (§N.8) ───────────────────────────────────────────────
 * NO LLM DETECTOR IS WIRED. There is no model call in this file and none
 * anywhere in this lane. `SafetyDecision.llm_assist_ran` is therefore `false` on
 * every turn, and that `false` means "no assist ran" — it does NOT mean "an
 * assist ran and found nothing". Wiring a real assist is a later lane's work;
 * what ships here is the ENVELOPE, so that when a model is wired it cannot be
 * wired in a way that weakens the deterministic floor.
 */

import { SAFETY_CLASSES, maxSeverity, type SafetyClass, type SafetyDetection, type SafetySeverity } from './types'
import type { ClassificationResult } from './classifier'
import { spanHash } from './normalize'

/**
 * What an LLM assist is permitted to say. Every field is ADDITIVE: there is no
 * "clear", "downgrade", "override", or "confidence" field, and adding one is
 * the specific change `LLM_ASSIST_PAYLOAD_KEYS` exists to catch.
 */
export interface LlmAssistPayload {
  /** Classes the assist believes are present. Union'd in; never subtractive. */
  raised_classes: SafetyClass[]
  /** The severity the assist argues for. Applied as `max`, never as a set. */
  raised_severity: SafetySeverity
  /** Free-text rationale, kept for the audit trail as a HASH only. */
  rationale?: string
  /** Which model produced this. Recorded so a bad assist is attributable. */
  model_id: string
}

/**
 * The CANONICAL, EXHAUSTIVE field list of `LlmAssistPayload`.
 *
 * ── WHY A LIST GUARDS AN INTERFACE (hardening round, H-6) ────────────────────
 * A reviewer added `downgrade_to?: SafetySeverity` to the interface above plus
 * a branch that honored it, and the build and the full suite stayed green —
 * because an interface is not a constraint on itself. This list is the
 * constraint.
 *
 * The `satisfies` clause below is one direction of it: it makes the array's
 * element type exactly `keyof LlmAssistPayload`, so a key REMOVED from the
 * interface (or misspelled here) is a type error. TypeScript cannot make the
 * reverse assertion — that the array is exhaustive — from an array literal, so
 * the ADDED-field direction is `ASSERT_NO_UNLISTED_PAYLOAD_KEY` below.
 *
 * ADDING A FIELD HERE IS THE REVIEW GATE. A new field must be argued to be
 * additive-only in its diff, exactly as `SHORT_SQUASHED_ALLOWLIST` in the
 * classifier makes each of its exceptions a diff someone reads.
 */
export const LLM_ASSIST_PAYLOAD_KEYS = [
  'raised_classes',
  'raised_severity',
  'rationale',
  'model_id',
] as const satisfies readonly (keyof LlmAssistPayload)[]

/** Compile-time `never` assertion. A non-`never` argument is a type error. */
type AssertNever<T extends never> = T

/**
 * THE ADDED-FIELD DETECTOR, in a `src/` path (round 3, M-1/H-6).
 *
 * `Exclude<keyof LlmAssistPayload, listed keys>` is `never` exactly when the
 * interface has no field the list does not name. Add `downgrade_to?` to
 * `LlmAssistPayload` and this line becomes:
 *
 *   error TS2344: Type '"downgrade_to"' does not satisfy the constraint 'never'
 *
 * reported at `src/lib/pariprashna/safety/llm_assist.ts` — a path containing no
 * `tests/` segment, so `ci.yml`'s `grep -Ev "(tests/|__tests__/)"` cannot filter
 * it and the typecheck job fails. That is the difference between this and the
 * round-2 version of the same idea; see the module header.
 *
 * Exported rather than left as a bare local so no lint pass can "clean up" an
 * unused declaration and silently delete the guard.
 */
export type ASSERT_NO_UNLISTED_PAYLOAD_KEY = AssertNever<
  Exclude<keyof LlmAssistPayload, (typeof LLM_ASSIST_PAYLOAD_KEYS)[number]>
>

/**
 * The same assertion in VALUE form, so a reader who does not read types sees it
 * too, and so the failure mode is a second, differently-worded error.
 *
 * `Required<>` makes every optional field mandatory, so an added field —
 * optional or not — makes this object literal incomplete (TS2739/TS2741). A
 * field REMOVED from the interface makes the corresponding line here an excess
 * property (TS2353). Both directions, both in `src/`.
 *
 * The values are placeholders and are never read by anything; this is a type
 * probe, not a fixture. It is deliberately NOT a valid assist (`'none'`
 * severity, empty class list) so that nothing is tempted to import it as one.
 */
export const LLM_ASSIST_PAYLOAD_SHAPE_PROBE: Required<LlmAssistPayload> = {
  raised_classes: [],
  raised_severity: 'none',
  rationale: '',
  model_id: '',
}

/**
 * Merge an assist into a deterministic result under the monotone-join rule.
 *
 * Returns a result that is >= the input on BOTH axes (class set by inclusion,
 * severity by the total order). This is the entire safety contract of the LLM
 * half of the classifier.
 */
export function mergeLlmAssist(
  deterministic: ClassificationResult,
  assist: LlmAssistPayload,
): ClassificationResult {
  const assistDetections: SafetyDetection[] = assist.raised_classes
    // A class the assist names that is not in the vocabulary is DROPPED, not
    // trusted — an assist cannot invent a class the pipeline has no controls for.
    .filter((c) => (SAFETY_CLASSES as readonly string[]).includes(c))
    .map((cls) => ({
      cls,
      // `max` against the deterministic floor for that class: if the
      // deterministic pass already called it hard_stop, an assist saying
      // 'advisory' leaves it at hard_stop.
      severity: maxSeverity(
        assist.raised_severity,
        deterministic.detections
          .filter((d) => d.cls === cls)
          .reduce<SafetySeverity>((acc, d) => maxSeverity(acc, d.severity), 'none'),
      ),
      detector: 'llm_assist',
      rule: `assist:${assist.model_id}`,
      matched_span_hash: spanHash(assist.rationale ?? `assist:${assist.model_id}:${cls}`),
      surface: 'llm_assist' as const,
    }))

  // Deterministic detections FIRST and unmodified — the floor is carried, never
  // rewritten. Assist detections are strictly additional.
  const detections = [...deterministic.detections, ...assistDetections]
  const classes = SAFETY_CLASSES.filter((c) => detections.some((d) => d.cls === c))
  const severity = detections.reduce<SafetySeverity>((acc, d) => maxSeverity(acc, d.severity), 'none')

  return {
    detections,
    evasion_markers: deterministic.evasion_markers,
    classes,
    severity,
    normalized: deterministic.normalized,
  }
}

/**
 * Whether an LLM assist ran on this turn.
 *
 * Hard-coded `false`, and that is the point: there is no assist. A function
 * that reads a flag and returns "probably true" would be exactly the §N.8
 * defect this codebase has been burned by — a signal with no detector behind it.
 * When an assist is wired, this becomes a real read and the tests that assert
 * `llm_assist_ran === false` become the tests that catch a silent wiring.
 */
export function llmAssistRan(): boolean {
  return false
}
