/**
 * Paripraśna safety — shared vocabulary and the injectable DB port (lane G1-A).
 *
 * PPR-12 / SAFETY_PRIVACY_TENANCY §2–§3. Nothing in this directory reaches for
 * `@/lib/db/client` directly: every persisting entry point takes a `SafetyDb`,
 * which production callers fill with `defaultSafetyDb()` and tests fill with an
 * in-memory double. That is what makes "the classifier is pure and the gate is
 * testable without a database" a checked claim rather than a promise.
 */

// ── Hard-stop classes (SAFETY_PRIVACY_TENANCY §2) ────────────────────────────

/**
 * The five detectable hard-stop classes. HS-5 (retraction) and HS-6 (predictive
 * sampling) are deliberately NOT here: they are not query classifications — HS-5
 * is a post-hoc governance act on an already-served reading (`retraction.ts`)
 * and HS-6 is an output-side sampling hook (`predictive_sampling.ts`).
 */
export type SafetyClass =
  | 'hs1_date_of_death'
  | 'hs2_suicide_adjacent'
  | 'hs3_health_crisis'
  | 'hs3_mental_health'
  | 'hs4_mortality_window'

export const SAFETY_CLASSES: readonly SafetyClass[] = [
  'hs1_date_of_death',
  'hs2_suicide_adjacent',
  'hs3_health_crisis',
  'hs3_mental_health',
  'hs4_mortality_window',
] as const

/**
 * Severity is a TOTAL ORDER, and the order is what makes "an LLM assist may only
 * RAISE severity" a checkable property rather than a style note (`llm_assist.ts`).
 */
export type SafetySeverity = 'none' | 'advisory' | 'review_required' | 'hard_stop'

export const SEVERITY_RANK: Record<SafetySeverity, number> = {
  none: 0,
  advisory: 1,
  review_required: 2,
  hard_stop: 3,
}

export function maxSeverity(a: SafetySeverity, b: SafetySeverity): SafetySeverity {
  return SEVERITY_RANK[a] >= SEVERITY_RANK[b] ? a : b
}

// ── Actions (SAFETY_PRIVACY_TENANCY §3's `action` field) ─────────────────────

/**
 * What the pipeline does with the decision.
 *
 *  · `proceed`               — nothing detected; the turn runs unchanged.
 *  · `reframe`               — the turn runs, but under HS-1/HS-4 capability
 *                              exclusion + prompt policy + the pre-wire scan,
 *                              and the reader is told what was withheld.
 *  · `interstitial`          — NCD-4: for a `native_self` subject, a deliberation
 *                              pause replaces the seal path for HS-3 classes
 *                              (health-crisis / mental-health) ONLY. The reading
 *                              then proceeds under the same reframe controls.
 *  · `seal_pending_signoff`  — HS-3 (non-native-self) and HS-4 (always): no
 *                              reading leaves this session. A review record is
 *                              opened; release requires two independent
 *                              adversarial passes AND a separate sign-off.
 *  · `hard_stop`             — HS-2: a fixed, non-generated response; NO plan is
 *                              built; audit row; cohort-native notification.
 *
 * The order below is the PRECEDENCE order used by `resolveAction`.
 */
export type SafetyAction =
  | 'proceed'
  | 'reframe'
  | 'interstitial'
  | 'seal_pending_signoff'
  | 'hard_stop'

export const ACTION_RANK: Record<SafetyAction, number> = {
  proceed: 0,
  reframe: 1,
  interstitial: 2,
  seal_pending_signoff: 3,
  hard_stop: 4,
}

export function maxAction(a: SafetyAction, b: SafetyAction): SafetyAction {
  return ACTION_RANK[a] >= ACTION_RANK[b] ? a : b
}

// ── Detections ───────────────────────────────────────────────────────────────

/**
 * One firing of one detector.
 *
 * NOTE what is deliberately absent: the matched TEXT. §5's safe-logging rule —
 * "audit logs reference content by hash/id, never duplicate C1 bodies" — and the
 * query is C1. `matched_span_hash` is a salted-by-nothing sha256 of the matched
 * substring: enough to correlate two firings of the same phrase across turns,
 * never enough to read the question back out of the audit table.
 */
export interface SafetyDetection {
  cls: SafetyClass
  severity: SafetySeverity
  /** Which detector fired — a stable id, never free text. */
  detector: string
  /** The rule id inside that detector (pattern name / combination-rule name). */
  rule: string
  /** sha256 of the matched substring. NEVER the substring itself. */
  matched_span_hash: string
  /** Where the detector looked: the question, the plan's domains, a capability. */
  surface: 'query' | 'domain' | 'capability' | 'llm_assist'
}

/** Evasion/displacement markers. These RAISE; nothing here can ever lower. */
export interface SafetyEvasionMarker {
  marker: string
  matched_span_hash: string
}

// ── The decision (the receipt's `safety_decision` field) ─────────────────────

/**
 * Written on EVERY turn — including turns where nothing fired. G3-A (receipt
 * emission) reads this field, and a receipt field must be earned by a detector
 * or be null (§N.8): `enforced: false` is how this object says "no safety
 * question was asked on this turn", which is a different statement from
 * "nothing was found".
 */
export interface SafetyDecision {
  decision_id: string
  turn_id: string
  chart_id: string
  /** false ONLY when the flag is OFF — i.e. when no classification ran. */
  enforced: boolean
  /** Empty when nothing fired. Order is `SAFETY_CLASSES` order, deduped. */
  classes_detected: SafetyClass[]
  severity: SafetySeverity
  action: SafetyAction
  /** The consent lane's subject_kind, or null when consent enforcement is OFF. */
  subject_kind: 'native_self' | 'cohort' | 'test' | null
  /** NCD-4 only applies to a PROVEN native_self subject; null is not proof. */
  ncd4_interstitial_applies: boolean
  detections: SafetyDetection[]
  evasion_markers: SafetyEvasionMarker[]
  /** Capability names the plan stage must not authorize (HS-1/HS-4 point (a)). */
  excluded_capabilities: string[]
  /**
   * Did an LLM assist run? `false` is the honest value today — no LLM detector
   * is wired (see `llm_assist.ts`). It is NOT "the assist ran and found nothing".
   */
  llm_assist_ran: boolean
  /** The review record opened for a seal/interstitial action, when one was. */
  review_id: string | null
  /** True once the audit row landed. Reported, never assumed (§N.8). */
  audit_written: boolean
  decided_at: string
}

// ── HS-3/HS-4 review lifecycle ───────────────────────────────────────────────

/**
 * The three-step path as a real state machine (SAFETY_PRIVACY_TENANCY §2 HS-3):
 * seal-pending → two INDEPENDENT adversarial passes → a SEPARATE sign-off.
 *
 * `interstitial_shown` is the NCD-4 branch: a terminal-for-this-turn state that
 * releases immediately, recorded distinctly so a query cannot ask "how many
 * sensitive readings went out under the relaxation" and get a guess.
 */
export type SafetyReviewState =
  | 'seal_pending'
  | 'adversarial_pass_1_recorded'
  | 'adversarial_passes_complete'
  | 'released'
  | 'withheld'
  | 'interstitial_shown'

export type AdversarialVerdict = 'refuted' | 'sustained' | 'sustained_with_reservations'

export interface AdversarialPass {
  pass_ordinal: 1 | 2
  /** Model id + context id. Two passes with the same pair are NOT independent. */
  reviewer_model_id: string
  reviewer_context_id: string
  verdict: AdversarialVerdict
  /** What the pass attacked: grounding, calibration language, framing. */
  findings: string[]
  recorded_at: string
}

export interface SafetyReviewRecord {
  review_id: string
  chart_id: string
  turn_id: string
  state: SafetyReviewState
  classes: SafetyClass[]
  subject_kind: 'native_self' | 'cohort' | 'test' | null
  passes: AdversarialPass[]
  signed_off_by: string | null
  signed_off_at: string | null
  withheld_reason: string | null
  opened_at: string
}

// ── DB port ──────────────────────────────────────────────────────────────────

export interface SafetyQueryable {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>
}

export interface SafetyDb extends SafetyQueryable {
  withTransaction<T>(fn: (tx: SafetyQueryable) => Promise<T>): Promise<T>
}

/** Raised when a safety entry point is called while the flag is OFF. */
export class SafetyFeatureDisabledError extends Error {
  readonly code = 'PARIPRASHNA_SAFETY_DISABLED'
  constructor(operation: string) {
    super(
      `PARIPRASHNA_SAFETY_DISABLED: ${operation} requires the ` +
        `PARIPRASHNA_SAFETY_GATE_ENABLED feature flag. It is OFF, so this ` +
        `operation does not exist for this deploy.`,
    )
    this.name = 'SafetyFeatureDisabledError'
  }
}
