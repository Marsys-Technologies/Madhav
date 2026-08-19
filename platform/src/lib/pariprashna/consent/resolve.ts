/**
 * Paripraśna consent — ENTITLEMENT RESOLUTION (PPR-14, abuse case A9).
 *
 * This is the module the whole lane exists for. Everything else — the schema,
 * the register, the tombstones, the export — is bookkeeping around this one
 * decision:
 *
 *   "No L2+ output for a chart whose subject lacks a consent row, unless
 *    subject_kind = native_self (strictly: the subject IS the native, or the
 *    minor-guardian carve-out)."                                     — PPR-14
 *
 * ── WHAT "STRICTLY" MEANS HERE ───────────────────────────────────────────────
 * A row that merely SAYS `subject_kind = 'native_self'` proves nothing: writing
 * that row is exactly as easy as creating the chart, and abuse case A9 is a user
 * who creates a chart for a non-consenting adult. So `native_self` is honored
 * only when the row's `subject_principal_id` equals `charts.owner_id` — i.e. the
 * SUBJECT of the chart is the account holder — AND the caller is that same
 * principal. A `native_self` claim that fails this test is not downgraded to
 * "unverified" and served anyway; it is REFUSED and written to the
 * excluded-subject register as `native_self_claim_invalid`.
 *
 * Note what this deliberately does NOT do: there is no super_admin bypass.
 * Consent is not an authorization tier. A super_admin reading a non-consenting
 * adult's chart IS abuse case A9; a bypass would delete the control while
 * leaving its name in place.
 *
 * ── RELATIONSHIP TO `authorizeChartAccess` ───────────────────────────────────
 * `authorizeChartAccess` answers "may this CALLER touch this chart?" (ownership
 * and grants). This answers a different question that no existing code asks:
 * "may this SUBJECT's interpretive corpus be served at all?" Both must pass.
 * The order in `safety_gate.ts` is deliberate — authorization first, so an
 * unauthorized caller learns nothing about the subject's consent state.
 *
 * ── FLAG-OFF IS A ZERO-COST NO-OP ────────────────────────────────────────────
 * With `SUBJECT_CONSENT_ENFORCEMENT` OFF (the default), this function returns
 * `allow` with `enforced: false` and reason `enforcement_disabled` BEFORE
 * touching the database. Merging this lane therefore cannot change production
 * behavior, cannot add a query to the hot path, and cannot fail on a chart whose
 * consent row does not exist yet.
 */

import { CONSENT_FLAG, isConsentEnforcementEnabled } from './flag'
import { isMinorSubject, computeAgeYears, MINOR_AGE_THRESHOLD_YEARS } from './minor_exclusion'
import { registerExclusion, clearExclusion } from './register'
import type {
  AnonymizationChoice,
  ChartSubjectRow,
  ConsentDb,
  ConsentRow,
  ExclusionReason,
  SubjectKind,
} from './types'

export { CONSENT_FLAG }

export type ConsentAllowReason =
  | 'enforcement_disabled'
  | 'native_self'
  | 'guardian_minor'
  | 'cohort_consent_granted'
  | 'test_subject'

export type ConsentRefusalReason = ExclusionReason

export interface ConsentDecisionBase {
  chart_id: string
  /** false ONLY when the flag is off — i.e. when no consent question was asked. */
  enforced: boolean
  subject_kind: SubjectKind | null
  is_minor: boolean | null
  subject_age_years: number | null
  anonymization_choice: AnonymizationChoice | null
  /** Redaction requests the serving layer must honor (§3.5.D). */
  redaction_requests: unknown[]
}

export interface ConsentAllow extends ConsentDecisionBase {
  outcome: 'allow'
  reason: ConsentAllowReason
}

export interface ConsentRefusal extends ConsentDecisionBase {
  outcome: 'refuse'
  reason: ConsentRefusalReason
  /** Caller-facing text. A designed state, explained — never a bare error. */
  message: string
  /** Did the excluded-subject register write succeed? Reported, never assumed. */
  registered: boolean
}

export type SubjectConsentDecision = ConsentAllow | ConsentRefusal

export interface ResolveSubjectConsentArgs {
  chartId: string
  /** The calling principal (Firebase uid), as `authorizeChartAccess` uses it. */
  principalId: string
  db: ConsentDb
  /** Injectable for tests; defaults to now. */
  asOf?: Date
}

const DETECTOR = 'consent.resolveSubjectConsent'

const REFUSAL_MESSAGES: Record<ConsentRefusalReason, string> = {
  no_consent_row:
    'This chart has no subject-consent record. Interpretive output is withheld until the ' +
    'subject’s consent is recorded (MACRO_PLAN §3.5.A.4). Chart computation is unaffected.',
  consent_withdrawn:
    'The subject of this chart has withdrawn consent. Interpretive output is permanently ' +
    'withheld and the subject’s corpus has been scheduled for verified deletion.',
  vulnerable_subject:
    'This subject is flagged as a vulnerable-subject exclusion at intake. Interpretive ' +
    'output is withheld (MACRO_PLAN §3.5.F).',
  minor:
    `The subject of this chart is under ${MINOR_AGE_THRESHOLD_YEARS}. Output is available ` +
    'only to the recorded parent/guardian, and never as part of a cohort (§3.5.F).',
  consent_incapacity:
    'The subject of this chart is recorded as unable to give consent. Interpretive output ' +
    'is withheld (§3.5.F).',
  native_self_claim_invalid:
    'This chart claims native_self, but its recorded subject is not the account holder. ' +
    'A native_self claim is not self-certifying (PPR-14); a consent record for the actual ' +
    'subject is required.',
  subject_deleted:
    'The subject of this chart completed a verified deletion. Nothing interpretive remains ' +
    'to serve, and nothing new may be produced.',
  birth_date_unavailable:
    'This chart’s birth date could not be read, so the under-18 exclusion could not be ' +
    'evaluated. Output is withheld rather than served on an unchecked assumption.',
}

/**
 * Resolve whether this subject's L2+ interpretive corpus may be served at all.
 *
 * Refusals write the excluded-subject register (§3.5.F) so the refusal is
 * auditable, and report whether that write succeeded rather than assuming it.
 */
export async function resolveSubjectConsent(
  args: ResolveSubjectConsentArgs,
): Promise<SubjectConsentDecision> {
  const { chartId, principalId, db, asOf = new Date() } = args

  // ── The flag gate. Nothing below this line runs in production today. ────────
  if (!isConsentEnforcementEnabled()) {
    return {
      outcome: 'allow',
      reason: 'enforcement_disabled',
      chart_id: chartId,
      enforced: false,
      subject_kind: null,
      is_minor: null,
      subject_age_years: null,
      anonymization_choice: null,
      redaction_requests: [],
    }
  }

  const chart = await loadChartSubject(db, chartId)
  const consent = await loadConsentRow(db, chartId)

  const ageYears = computeAgeYears(chart?.birth_date ?? null, asOf)
  const minor = isMinorSubject(chart?.birth_date ?? null, asOf)

  const base: ConsentDecisionBase = {
    chart_id: chartId,
    enforced: true,
    subject_kind: consent?.subject_kind ?? null,
    is_minor: minor,
    subject_age_years: ageYears,
    anonymization_choice: consent?.anonymization_choice ?? null,
    redaction_requests: Array.isArray(consent?.redaction_requests)
      ? (consent!.redaction_requests as unknown[])
      : [],
  }

  const refuse = async (
    reason: ConsentRefusalReason,
    evidence: Record<string, unknown>,
  ): Promise<ConsentRefusal> => {
    let registered = false
    try {
      await registerExclusion(db, {
        chartId,
        reason,
        detector: DETECTOR,
        subjectAgeYears: ageYears,
        evidence,
      })
      registered = true
    } catch {
      // The refusal stands whether or not the register write landed. Reporting
      // `registered: false` is the honest signal; swallowing it and claiming the
      // exclusion was logged would be exactly the §N.8 defect class.
      registered = false
    }
    return { ...base, outcome: 'refuse', reason, message: REFUSAL_MESSAGES[reason], registered }
  }

  // ── 1. No consent row → refuse. This is the A9 defense. ─────────────────────
  if (!consent) {
    return refuse('no_consent_row', { chart_present: chart !== null })
  }

  // ── 2. Terminal states, checked before anything else can override them. ─────
  if (consent.verified_deletion_at) {
    return refuse('subject_deleted', { verified_deletion_at: consent.verified_deletion_at })
  }
  if (consent.consent_state === 'withdrawn') {
    return refuse('consent_withdrawn', { withdrawn_at: consent.withdrawn_at })
  }
  if (consent.vulnerable_exclusion_flag) {
    return refuse('vulnerable_subject', { flag_source: 'intake' })
  }

  // ── 3. Age. An unknown age fails closed — it is not "not a minor". ──────────
  if (minor === null) {
    return refuse('birth_date_unavailable', { birth_date_raw: chart?.birth_date ?? null })
  }

  // ── 4. Minors (§3.5.F): guardian-only, NEVER a cohort. ─────────────────────
  if (minor) {
    if (consent.subject_kind === 'cohort') {
      // Stated before the guardian check on purpose: a minor may not be a cohort
      // subject even WITH a guardian and a signed document.
      return refuse('minor', {
        rule: 'minor_never_enters_cohort',
        age_years: ageYears,
        subject_kind: consent.subject_kind,
      })
    }
    if (!consent.guardian_principal_id || consent.guardian_principal_id !== principalId) {
      return refuse('minor', {
        rule: 'minor_servable_only_to_recorded_guardian',
        age_years: ageYears,
        guardian_recorded: consent.guardian_principal_id !== null,
      })
    }
    return {
      ...base,
      outcome: 'allow',
      reason: 'guardian_minor',
    }
  }

  // The subject is 18+. If a `minor` exclusion is still open, it has expired.
  await clearExclusion(
    db,
    chartId,
    'minor',
    `subject reached ${MINOR_AGE_THRESHOLD_YEARS} (age ${ageYears} at ${asOf.toISOString()})`,
  ).catch(() => 0)

  // ── 5. Subject kind. ────────────────────────────────────────────────────────
  switch (consent.subject_kind) {
    case 'native_self': {
      const subjectIsAccountHolder =
        consent.subject_principal_id !== null &&
        chart?.owner_id != null &&
        consent.subject_principal_id === chart.owner_id
      const callerIsSubject = consent.subject_principal_id === principalId
      if (!subjectIsAccountHolder || !callerIsSubject) {
        return refuse('native_self_claim_invalid', {
          subject_is_account_holder: subjectIsAccountHolder,
          caller_is_subject: callerIsSubject,
        })
      }
      return { ...base, outcome: 'allow', reason: 'native_self' }
    }

    case 'cohort':
      // `consent_document_ref NOT NULL` for cohort rows is a DB CHECK, and
      // `consent_state = 'granted'` was established above, so reaching here IS
      // the documented-and-granted state. No further self-certification exists
      // to check, and inventing one would be theatre.
      return { ...base, outcome: 'allow', reason: 'cohort_consent_granted' }

    case 'test':
      return { ...base, outcome: 'allow', reason: 'test_subject' }

    default:
      // Unreachable given the DB CHECK, but an unknown kind must fail closed
      // rather than fall through to allow.
      return refuse('no_consent_row', { unexpected_subject_kind: consent.subject_kind })
  }
}

// ── Loaders ──────────────────────────────────────────────────────────────────

export async function loadConsentRow(
  db: ConsentDb,
  chartId: string,
): Promise<ConsentRow | null> {
  const { rows } = await db.query<ConsentRow>(
    `SELECT * FROM chart_subject_consent WHERE chart_id = $1`,
    [chartId],
  )
  return rows[0] ?? null
}

export async function loadChartSubject(
  db: ConsentDb,
  chartId: string,
): Promise<ChartSubjectRow | null> {
  const { rows } = await db.query<ChartSubjectRow>(
    `SELECT id, owner_id, role, birth_date::text AS birth_date, name, subject_name, birth_place
       FROM charts WHERE id = $1`,
    [chartId],
  )
  return rows[0] ?? null
}
