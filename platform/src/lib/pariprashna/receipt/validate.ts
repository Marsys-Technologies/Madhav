/**
 * pariprashna/receipt/validate.ts — the §N.8 enforcement (lane G3-A, PPR-01).
 *
 * "Every receipt field MUST be earned by a detector or be null" — as actual
 * enforced code, not a comment. This module cannot re-run every upstream
 * detector at validation time (that would mean re-querying the DB a second
 * time for every field, which is not what a persistence-time guard is for);
 * what it CAN do, and does, is check the STRUCTURAL COHERENCE invariants a
 * genuinely-earned receipt always satisfies and a fabricated or tampered one
 * is likely to violate:
 *
 *   V1. `receipt_hash` equals the hash actually recomputed over the
 *       receipt's own content. Anything that changed a data field without
 *       recomputing the hash — including a hand-authored fake value with
 *       "no traceable source" — fails this check. This is the sharpest,
 *       least ambiguous check here: it directly enforces "this receipt's
 *       content is exactly what its own hash function says it is."
 *   V2. Every `status: 'measured' | 'unavailable'` field is INTERNALLY
 *       coherent: measured ⇒ its data subfields are non-null and
 *       `unavailable_reason` is null; unavailable ⇒ every data subfield is
 *       null and `unavailable_reason` is a non-empty string. A field that is
 *       "half populated" (claims measured but is missing data, or claims
 *       unavailable while still carrying data) has no honest state it could
 *       be in — this is exactly the class of bug §N.8 exists to catch.
 *   V3. `safety_decision` semantic coherence: `enforced: false` (no safety
 *       question was asked this turn) is incompatible with a populated
 *       `classes_detected` or any action other than `proceed` — a decision
 *       cannot claim "not enforced" while also claiming findings.
 *   V4. `coverage` arithmetic coherence: `served + empty + dark ===
 *       floor_item_total` when measured — a completeness receipt that does
 *       not add up did not come from the real `WebCompletenessReceipt`
 *       object, whose OWN emitter enforces the total-partition invariant.
 *   V5. `calibration_disclosure` coherence: `consulted` and
 *       `consulted_tool_names` cannot disagree about whether anything was
 *       found.
 *
 * `validateAcharyaReadingReceipt` NEVER throws; it returns a verdict.
 * `assertValidAcharyaReadingReceipt` is the FAILS-not-just-logs form the
 * persistence call site uses — throws on any violation.
 */

import type { AcharyaReadingReceipt } from './schema'
import { computeReceiptHash } from './hash'

export interface ReceiptValidationResult {
  ok: boolean
  violations: string[]
}

function checkStatusCoherence(
  label: string,
  status: 'measured' | 'unavailable',
  dataFields: Record<string, unknown>,
  unavailableReason: string | null,
  violations: string[],
): void {
  if (status === 'measured') {
    if (unavailableReason !== null) {
      violations.push(`${label}: status is 'measured' but unavailable_reason is non-null`)
    }
    for (const [key, value] of Object.entries(dataFields)) {
      if (value === null) violations.push(`${label}: status is 'measured' but ${key} is null`)
    }
  } else {
    if (!unavailableReason || unavailableReason.trim().length === 0) {
      violations.push(`${label}: status is 'unavailable' but unavailable_reason is empty`)
    }
    for (const [key, value] of Object.entries(dataFields)) {
      if (value !== null) violations.push(`${label}: status is 'unavailable' but ${key} is non-null`)
    }
  }
}

export function validateAcharyaReadingReceipt(receipt: AcharyaReadingReceipt): ReceiptValidationResult {
  const violations: string[] = []

  // ── V1: receipt_hash must equal a fresh recompute over the receipt's own
  //    content (every field except receipt_hash itself). ────────────────────
  const { receipt_hash, ...content } = receipt
  const recomputed = computeReceiptHash(content)
  if (recomputed !== receipt_hash) {
    violations.push(`receipt_hash mismatch: stored=${receipt_hash} recomputed=${recomputed}`)
  }

  // ── V2: measured/unavailable coherence per complex field. ─────────────────
  checkStatusCoherence(
    'coverage',
    receipt.coverage.status,
    {
      served: receipt.coverage.served,
      empty: receipt.coverage.empty,
      dark: receipt.coverage.dark,
      floor_item_total: receipt.coverage.floor_item_total,
      channel: receipt.coverage.channel,
      channel_note: receipt.coverage.channel_note,
    },
    receipt.coverage.unavailable_reason,
    violations,
  )
  checkStatusCoherence(
    'cross_domain',
    receipt.cross_domain.status,
    { domains: receipt.cross_domain.domains },
    receipt.cross_domain.unavailable_reason,
    violations,
  )
  checkStatusCoherence(
    'evidence_grades',
    receipt.evidence_grades.status,
    {
      grade_counts: receipt.evidence_grades.grade_counts,
      hallucination_count: receipt.evidence_grades.hallucination_count,
    },
    receipt.evidence_grades.unavailable_reason,
    violations,
  )
  checkStatusCoherence(
    'honest_gaps',
    receipt.honest_gaps.status,
    { gaps: receipt.honest_gaps.gaps },
    receipt.honest_gaps.unavailable_reason,
    violations,
  )
  checkStatusCoherence(
    'safety_decision',
    receipt.safety_decision.status,
    {
      decision_id: receipt.safety_decision.decision_id,
      enforced: receipt.safety_decision.enforced,
      severity: receipt.safety_decision.severity,
      action: receipt.safety_decision.action,
      classes_detected: receipt.safety_decision.classes_detected,
      audit_written: receipt.safety_decision.audit_written,
      // review_id is legitimately null even when measured (most turns open
      // no review) — deliberately excluded from this coherence check.
    },
    receipt.safety_decision.unavailable_reason,
    violations,
  )

  // ── V3: safety_decision semantic coherence. ────────────────────────────────
  if (
    receipt.safety_decision.status === 'measured' &&
    receipt.safety_decision.enforced === false
  ) {
    if ((receipt.safety_decision.classes_detected?.length ?? 0) > 0) {
      violations.push('safety_decision: enforced=false but classes_detected is non-empty')
    }
    if (receipt.safety_decision.action !== null && receipt.safety_decision.action !== 'proceed') {
      violations.push(`safety_decision: enforced=false but action='${receipt.safety_decision.action}' (expected 'proceed')`)
    }
  }

  // ── V4: coverage arithmetic coherence. ─────────────────────────────────────
  if (receipt.coverage.status === 'measured') {
    const { served, empty, dark, floor_item_total } = receipt.coverage
    if (served !== null && empty !== null && dark !== null && floor_item_total !== null) {
      if (served + empty + dark !== floor_item_total) {
        violations.push(
          `coverage: served(${served}) + empty(${empty}) + dark(${dark}) !== floor_item_total(${floor_item_total})`,
        )
      }
    }
  }

  // ── V5: calibration_disclosure coherence. ──────────────────────────────────
  const calibrationHasNames = receipt.calibration_disclosure.consulted_tool_names.length > 0
  if (receipt.calibration_disclosure.consulted !== calibrationHasNames) {
    violations.push(
      `calibration_disclosure: consulted=${receipt.calibration_disclosure.consulted} but ` +
        `consulted_tool_names.length=${receipt.calibration_disclosure.consulted_tool_names.length}`,
    )
  }

  return { ok: violations.length === 0, violations }
}

/** FAILS (throws), never just logs — the "earned or null" contract as enforced code. */
export function assertValidAcharyaReadingReceipt(receipt: AcharyaReadingReceipt): void {
  const result = validateAcharyaReadingReceipt(receipt)
  if (!result.ok) {
    throw new Error(
      `AcharyaReadingReceipt validation FAILED (${result.violations.length} violation(s)): ` +
        result.violations.join('; '),
    )
  }
}
