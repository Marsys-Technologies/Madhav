/**
 * F-175 — assess_* PACT promise gate (PARIŚEṢA-V4)
 * ================================================
 *
 * ## The defect
 *
 * `assess_marriage(482012f1-…)` served, verbatim, in its budget-immune `kernel.verdict`:
 *
 *   > "No contradictions are tagged to this domain specifically (3 exist chart-wide) —
 *   >  an honest domain-scoped absence, not a silent omission."
 *
 * while `pact_query(482012f1-…, domain:'relationship')` on the SAME server, in the SAME
 * minute, returned `pact_status: 'denied_at_promise'`, `composite_score: -3.5`, grounded in
 * 63 resolvable L1 `chart_facts.fact_id`s: *"the rāśi checklist does not promise this
 * matter."*
 *
 * This is strictly worse than F-110's omission on `kala_ahead_get`. F-110 failed to mention
 * a denial; this **affirmatively certifies its absence**. `contradictions.status =
 * 'no_contradictions_in_domain'` is a signal asserting "nothing in this chart argues against
 * this domain" whose only detector was a `domains_affected_array ∋ domain` filter over ONE
 * L2 table (`bodha_contradictions`) — a detector that structurally cannot see the promise
 * chain, and therefore cannot ever produce the value the claim needs to be earned (§N.8,
 * Earned-Signal Principle). `promise_spine.ts`'s INV-1 already declared this certification
 * illegal — "no caller may certify 'no contradictions' for a classically-denied domain" —
 * and named this exact breach as open residual F-110-b.
 *
 * ## The fix: disclosure, not suppression, not a fabricated downgrade (F-110 Option C)
 *
 * Both readings are TRUE at their own layer and both are served:
 *   - L2 `bodha_contradictions` genuinely tags 0 rows to this domain. That fact is NOT
 *     deleted, NOT re-derived, NOT downgraded (§N.5: this layer is not the authority over
 *     the L2 surface it reads).
 *   - PACT genuinely denies the domain at PROMISE. That fact is joined in verbatim through
 *     the SAME shared `interpretPactJoin` helper `kala_ahead_get` uses — no second chain
 *     implementation, no new astrological computation (B.10).
 *
 * What changes is that the L2 absence may no longer be *narrated as an all-clear* while the
 * denial is held silently on the same server. The certification sentence is qualified in
 * place, a dedicated `promise_chain` clause is inserted into the budget-immune verdict, and
 * `kernel.promise` — a field that has existed on `SaraKernel` since A-08 and was null on
 * every assess_* response ever served, because nothing populated it — is finally populated.
 *
 * ## Honest-null discipline (§N.7 item 6 / §N.8)
 *
 * When the chain cannot be consulted, the gate reports `state:'unreachable'` with a null
 * join and emits `promise_chain_unchecked`. **Unchecked is never smoothed into clean.**
 * Before this module, "checked and clear" and "never checked" were byte-identical to a
 * caller of assess_*; they are now distinguishable — the same F-110 A7 criterion.
 *
 * Full investigation and rejected alternatives:
 * `00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md` (§5.3
 * residual F-110-b is this finding).
 */

import { interpretPactJoin, type SaraPromiseJoin } from './promise_spine.js'
import { judgmentFlag, type JudgmentFlagEntry } from '../generated/envelope.js'

/** The L-PACT capability URI. Identical to the one `kala_ahead_get` gates on — one chain. */
export const PACT_CAPABILITY_URI = 'marsys://tool/L-PACT/pact_query'

export type AssessPromiseGateState = 'checked' | 'unreachable'

export interface AssessPromiseGate {
  state: AssessPromiseGateState
  /** The domain whose PACT chain was consulted. */
  domain: string
  /** `interpretPactJoin` output, verbatim. NEVER fabricated — null unless state==='checked'. */
  join: SaraPromiseJoin | null
  /** Raw `pact_status`, verbatim from the capability. null when unreachable. */
  pact_status: string | null
  /**
   * The field a caller reads to know this server independently denies the domain this
   * assessment is about. True ONLY when a real chain call returned a real `denied_at_*`.
   */
  contradicts_domain_assessment: boolean
  reason: string
}

/**
 * Interpret a raw `pact_query` capability result (or a failure) as an `AssessPromiseGate`.
 *
 * PURE — no I/O. `raw` is whatever `callRegistryCapability` returned; pass `null` (and
 * optionally `errorText`) when the call threw or the capability was unreachable.
 */
export function buildAssessPromiseGate(
  domain: string,
  raw: unknown,
  errorText?: string,
): AssessPromiseGate {
  // §N.8: a null join is reported as null, never smoothed into a permissive default.
  const join = raw === null || raw === undefined ? null : interpretPactJoin(raw)
  if (!join) {
    return {
      state: 'unreachable',
      domain,
      join: null,
      pact_status: null,
      contradicts_domain_assessment: false,
      reason:
        `The PACT promise chain for '${domain}' could not be evaluated this call ` +
        `(${errorText ? `L-PACT capability error: ${errorText}` : 'the capability answered but returned no pact_status'}). ` +
        'Nothing below has therefore been checked against the classical promise chain — ' +
        'UNCHECKED, which is not the same as checked-and-clear. Re-run pact_query or ' +
        `kala_explain_get for domain='${domain}'.`,
    }
  }

  const inner = extractPactContent(raw)
  const pactStatus = (inner?.['pact_status'] as string | undefined) ?? null
  // INV-1 (promise_spine.ts): denied_at_* → stance 'contradicts', no override path.
  const contradicts = join.stance === 'contradicts'

  return {
    state: 'checked',
    domain,
    join,
    pact_status: pactStatus,
    contradicts_domain_assessment: contradicts,
    reason: contradicts
      ? `${join.promise_verdict} This server's own promise chain therefore DENIES '${domain}'. ` +
        'The L2 contradiction surface below is a separate, narrower instrument ' +
        '(bodha_contradictions, domain-tagged signal-pair tensions) — a domain-scoped ' +
        'absence there is not a clean bill of health and must not be read as one. Both ' +
        'readings are served; neither is dropped. Drill: pact_query / kala_explain_get.'
      : join.promise_verdict,
  }
}

function extractPactContent(raw: unknown): Record<string, unknown> | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const inner = r['content'] !== undefined && r['content'] !== null && typeof r['content'] === 'object'
    ? (r['content'] as Record<string, unknown>)
    : r
  return inner
}

/**
 * The kernel-layer judgment flags for a gate. Kernel flags are budget-protected; `grounding`
 * (where the structured `promise_gate` object lands) is dropped ALL-OR-NOTHING under budget
 * pressure — live-confirmed on assess_marriage at its own 40KB default — so the disclosure
 * must also exist at a seam a trim cannot delete.
 */
export function promiseGateFlags(gate: AssessPromiseGate | null | undefined): JudgmentFlagEntry[] {
  if (!gate) return []
  if (gate.state === 'unreachable') {
    return [judgmentFlag('promise_chain_unchecked', gate.reason, 'warning')]
  }
  if (gate.contradicts_domain_assessment) {
    return [judgmentFlag(
      'promise_chain_contradicts_domain',
      `pact_query returns ${gate.pact_status ?? 'a denial'} for '${gate.domain}' on this chart. ` +
      'Read every favourable statement in this assessment against that denial — in ' +
      'particular, any absence of domain-tagged L2 contradictions is NOT a corroboration ' +
      'of the promise. ' + gate.reason,
      'warning',
    )]
  }
  return []
}

/**
 * Annotate the L2 `contradictions` object with the promise-chain dispute, in place of nothing.
 *
 * The `status` value is deliberately NOT rewritten. `no_contradictions_in_domain` is a TRUE
 * statement about `bodha_contradictions` — 0 rows carry `domains_affected_array ∋ domain` —
 * and this layer is not the authority over the L2 surface it reads (§N.5). The defect was
 * never that the L2 count was wrong; it was that a narrow instrument's honest empty result
 * was serveable as a domain all-clear. So the fix is the adjacent field, not a rewrite:
 * `not_a_domain_all_clear: true` next to the status makes that reading unavailable to a
 * structured consumer without falsifying anything L2 computed.
 */
export function annotateContradictionsWithPromiseGate(
  contradictions: unknown,
  gate: AssessPromiseGate | null | undefined,
): unknown {
  if (!gate || !gate.contradicts_domain_assessment) return contradictions
  if (!contradictions || typeof contradictions !== 'object' || Array.isArray(contradictions)) {
    return contradictions
  }
  return {
    ...(contradictions as Record<string, unknown>),
    not_a_domain_all_clear: true,
    promise_chain: {
      pact_status: gate.pact_status,
      stance: gate.join?.stance ?? null,
      note:
        `This status describes the L2 bodha_contradictions surface ONLY. The classical promise ` +
        `chain (pact_query) independently returns ${gate.pact_status ?? 'a denial'} for ` +
        `'${gate.domain}' on this chart — do not read the L2 result as a domain all-clear.`,
      drill_uri: PACT_CAPABILITY_URI,
    },
  }
}

// ── Verdict-prose correction ──────────────────────────────────────────────────

/** Structural shape of a `buildVerdictLayer` clause (register_d8_assess_domain.ts). */
interface VerdictClauseLike {
  text: string
  fact_ids?: string[]
  grounded?: boolean
  clause_id?: string
}

/**
 * The certification sentence, corrected. Note what this does NOT do: it does not delete the
 * L2 finding, does not restate the L2 row count as anything other than what L2 computed, and
 * does not invent a severity. It removes exactly one thing — the clause's standing as an
 * all-clear — and names the instrument that disputes it (§N.7 item 6: an honest disclosure,
 * never a plausible-sounding default in either direction).
 */
function qualifiedContradictionText(original: string, gate: AssessPromiseGate): string {
  const status = gate.pact_status ?? 'a promise-chain denial'
  return (
    `${original.replace(/\s*$/, '')} NOT A CLEAN BILL OF HEALTH: that absence is scoped to the ` +
    `L2 contradiction surface only — this server's classical promise chain independently ` +
    `returns ${status} for '${gate.domain}' (see the promise-chain clause above and ` +
    '`promise_gate`).'
  )
}

/** The dedicated clause inserted immediately after the overview when the chain contradicts. */
function promiseChainClause(gate: AssessPromiseGate): VerdictClauseLike {
  const status = gate.pact_status ?? 'a denial'
  return {
    // Kept deliberately tight: the Sāra kernel has a ~2KB irreducible ceiling and verdict is
    // immune to trimming, so every character here displaces a pointer or a flag, not prose.
    text:
      `PROMISE CHAIN CONTRADICTS THIS DOMAIN: pact_query returns ${status} for ` +
      `'${gate.domain}' on this chart — ${gate.join?.promise_verdict ?? ''} ` +
      'Read the statements below against that denial; drill pact_query / kala_explain_get.',
    // The denial's own L1 grounding, inherited (§N.5) — never re-derived here.
    fact_ids: gate.join?.shared_fact_ids ?? [],
    grounded: (gate.join?.shared_fact_ids?.length ?? 0) > 0,
    clause_id: 'promise_chain',
  }
}

/**
 * Apply the gate to a `VerdictLayer` (or a plain verdict string).
 *
 * Returns the value unchanged unless `gate.contradicts_domain_assessment` is true — a
 * `pending`/`consistent` stance, or an unreachable chain, leaves the prose byte-identical
 * (no over-correction into false positives; the `unreachable` case is disclosed through
 * `promiseGateFlags` instead, which is where an "I did not check" belongs).
 *
 * Clause targeting is by `clause_id`, never by matching the prose — see the
 * `VerdictClauseId` note in register_d8_assess_domain.ts.
 */
export function applyPromiseGateToVerdict(
  verdict: unknown,
  gate: AssessPromiseGate | null | undefined,
): unknown {
  if (!gate || !gate.contradicts_domain_assessment) return verdict

  // A plain-string verdict (legacy/hand-built shape): prepend the denial. A string carries no
  // clause structure to target, so the disclosure leads rather than being woven in.
  if (typeof verdict === 'string') {
    return `${promiseChainClause(gate).text} ${verdict}`
  }

  if (!verdict || typeof verdict !== 'object' || Array.isArray(verdict)) return verdict
  const layer = verdict as Record<string, unknown>
  if (!Array.isArray(layer['clauses'])) return verdict

  const clauses = (layer['clauses'] as unknown[]).filter(
    (c): c is VerdictClauseLike => Boolean(c) && typeof c === 'object' && !Array.isArray(c),
  )

  const corrected: VerdictClauseLike[] = clauses.map(clause =>
    clause.clause_id === 'contradictions' && typeof clause.text === 'string'
      ? { ...clause, text: qualifiedContradictionText(clause.text, gate) }
      : clause,
  )

  // Insert the promise clause right after the overview so it is read before any favourable
  // finding — and, when there is no overview to sit behind, at the very front.
  const overviewIdx = corrected.findIndex(c => c.clause_id === 'overview')
  const insertAt = overviewIdx >= 0 ? overviewIdx + 1 : 0
  corrected.splice(insertAt, 0, promiseChainClause(gate))

  const factIdsCited = Array.from(new Set(corrected.flatMap(c => c.fact_ids ?? [])))
  return {
    ...layer,
    clauses: corrected,
    sentence_count: corrected.length,
    fact_ids_cited: factIdsCited,
    promise_gate_applied: true,
  }
}
