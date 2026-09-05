/**
 * engine_testimony.ts — N1 (Temporal Concordance Contract), a concrete step toward the
 * arbiter's serving attachment named in `L3_W1_ANALYSIS_BATCH_E.md` §1.5:
 * "`school_voices[]` becoming `engine_testimony[]`" beside `weakest_link` in
 * `kala_explain_get`, and the analogous `concordance` block in `kala_now_get`.
 *
 * THE DEFECT THIS CLOSES
 * -----------------------
 * Three independent modules already compute a school/engine's agreement with the operative
 * reading, and all three are field-for-field almost the same shape — but each invented its
 * own three-word vocabulary for the same concept:
 *
 *   - `kp_school_voice.ts`             — `KpAgreement`      = 'concurs' | 'dissents' | 'not_comparable'
 *   - `agnivasa_convention_b_voice.ts` — `AgnivasaAgreement` = 'agrees'  | 'diverges'  | 'not_comparable'
 *   - `explain.ts`'s `A5GocharaAgreement` (flag-guarded)     = 'concurs' | 'dissents'  | 'insufficient_data'
 *
 * The evidence base's own verdict: "Three implementations, one shape, three vocabularies —
 * unify." This module is that unification, done the safe way: NOT by renaming the existing
 * three types' own fields (an unaudited rename risks breaking a consumer somewhere that
 * pattern-matches the old string values), but by defining ONE canonical shape and pure,
 * total mapping functions from each of the three existing shapes onto it. Nothing in this
 * file changes any existing module's behaviour, output, or stored data.
 *
 * `A5GocharaAgreement` is the odd one out — it has no `school`/`school_label`/`state`/
 * `empty_reason`/`claim` fields at all, only `agreement` + three data fields. Its
 * `insufficient_data` value already plays the same role `not_comparable` + `honest_empty`
 * play together in the other two (§N.8: a flag with no real detector, or missing data,
 * reads null/honest_empty, never a fabricated comparison) — `a5AgreementToTestimony` below
 * synthesizes the missing fields rather than leaving them undefined.
 *
 * WHAT THIS PR DOES NOT DO (deliberately, a later N1 step)
 * ----------------------------------------------------------
 * Wire `EngineTestimony[]` into `kala_explain_get`'s `school_voices` array or `kala_now_get`'s
 * per-engine keys. That requires touching two large, already-tested serving files and
 * deciding the verdict-composition rule (`aligned | partially_aligned | disputed`) — a bigger,
 * riskier step this file intentionally stays upstream of.
 */

import type { KpSchoolVoice, KpAgreement } from './kp_school_voice.js'
import type { AgnivasaConventionBVoice, AgnivasaAgreement } from './agnivasa_convention_b_voice.js'

/** The one canonical agreement vocabulary every engine testimony is mapped onto.
 *  Chosen as `KpAgreement`'s own values — the first and most complete of the three,
 *  and the only one already carrying `not_comparable` (not a synonym for it). */
export type EngineAgreement = 'concurs' | 'dissents' | 'not_comparable'

/** One engine's testimony, in the shape every future `engine_testimony[]` array element
 *  will carry, regardless of which of the (currently three, eventually thirty-four)
 *  underlying engines produced it. */
export interface EngineTestimony {
  /** The engine/school tag a reader routes on (e.g. 'kp', 'muhurta_chintamani', 'gochara_v3'). */
  engine: string
  engine_label: string
  state: 'computed' | 'honest_empty'
  /** Populated iff `state === 'honest_empty'`; names the specific missing substrate/cause. */
  empty_reason: string | null
  agreement: EngineAgreement
  /** One deterministic sentence stating this engine's own verdict. */
  claim: string
}

const AGNIVASA_AGREEMENT_MAP: Record<AgnivasaAgreement, EngineAgreement> = {
  agrees: 'concurs',
  diverges: 'dissents',
  not_comparable: 'not_comparable',
}

/** A5's agreement type is inlined here (not exported from explain.ts to avoid a serving-tool
 *  import into a shared lib module) — kept in exact sync with `A5GocharaAgreement['agreement']`
 *  in `tools/kala_views/explain.ts`; a mismatch would be a compile error at that call site,
 *  not a silent drift, since TypeScript structurally checks the argument shape below. */
export type A5AgreementValue = 'concurs' | 'dissents' | 'insufficient_data'

const A5_AGREEMENT_MAP: Record<A5AgreementValue, EngineAgreement> = {
  concurs: 'concurs',
  dissents: 'dissents',
  insufficient_data: 'not_comparable',
}

export const A5_GOCHARA_ENGINE_LABEL = 'Gochara v3 (transit) agreement (SM-γ C4.2, flag-guarded)'

/** Maps `KpSchoolVoice` onto the canonical shape. Field-for-field identity on every field
 *  this shape shares with `EngineTestimony` — `KpAgreement`'s values already ARE the
 *  canonical vocabulary. */
export function kpVoiceToTestimony(voice: KpSchoolVoice): EngineTestimony {
  return {
    engine: voice.school,
    engine_label: voice.school_label,
    state: voice.state,
    empty_reason: voice.empty_reason,
    agreement: voice.agreement as KpAgreement,
    claim: voice.claim,
  }
}

/** Maps `AgnivasaConventionBVoice` onto the canonical shape, translating its
 *  agrees/diverges vocabulary to concurs/dissents. */
export function agnivasaVoiceToTestimony(voice: AgnivasaConventionBVoice): EngineTestimony {
  return {
    engine: voice.school,
    engine_label: voice.school_label,
    state: voice.state,
    empty_reason: voice.empty_reason,
    agreement: AGNIVASA_AGREEMENT_MAP[voice.agreement],
    claim: voice.claim,
  }
}

/** Maps the shape of `explain.ts`'s `A5GocharaAgreement` onto the canonical shape.
 *  Takes plain fields rather than the interface itself (which lives in a serving-tool
 *  file, not a shared lib) so this module has no import dependency on `explain.ts`.
 *  Synthesizes the fields A5 never had: `engine`/`engine_label` are fixed tags,
 *  `state`/`empty_reason` are derived from `insufficient_data` (A5's own stand-in for
 *  "no real comparison was possible" — §N.8: never report a comparison that wasn't made). */
export function a5AgreementToTestimony(a5: {
  agreement: A5AgreementValue
  note: string
}): EngineTestimony {
  const isEmpty = a5.agreement === 'insufficient_data'
  return {
    engine: 'gochara_v3',
    engine_label: A5_GOCHARA_ENGINE_LABEL,
    state: isEmpty ? 'honest_empty' : 'computed',
    empty_reason: isEmpty ? a5.note : null,
    agreement: A5_AGREEMENT_MAP[a5.agreement],
    claim: a5.note,
  }
}
