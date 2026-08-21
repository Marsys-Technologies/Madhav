/**
 * A-08 One-Voice Spine — promise-join helper (EKAVAKYATĀ W1)
 *
 * Interprets a raw pact_query capability response as a SaraPromiseJoin —
 * the reconciliation object that the sāra composition kernel embeds as
 * `kernel.promise`. This is a PURE function: no network calls, no async,
 * no side effects. The caller fetches pact_query in parallel with the main
 * domain capability call and passes the raw result here.
 *
 * SaraPromiseJoin is declared here as the canonical definition; it matches
 * the structurally-identical type in response_budget.ts (added by A-09)
 * byte-for-byte so TypeScript structural typing keeps both assignable.
 * Once A-09 is merged to main a trivial import-consolidation PR can fold
 * the import source — no semantic change needed.
 *
 * INV-1 (One-Voice invariant): a domain that is denied at any PACT stage
 * MUST carry stance:'contradicts' — no caller may certify "no contradictions"
 * for a classically-denied domain. This invariant is asserted by the test
 * `no_contradictions certification impossible in a denied domain`.
 *
 * F-110/49/51-pair (EKV): the composition kernel's `promise` field was null
 * for every response because no helper existed to populate it. This module
 * closes that gap.
 *
 * PRODUCTION CALLERS (kept truthful — this list previously claimed a wiring
 * that had never been written, which is itself the §N.8 defect class this
 * module exists to close: `grep -rn interpretPactJoin` returned only this file
 * and its own test until 2026-08-21):
 *   - `tools/kala_views/ahead.ts` — `computePromiseGate`, the F-110 PACT gate on
 *     `kala_ahead_get`'s forward projections. See
 *     `00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md`.
 *   - `lib/assess_promise_gate.ts` — `buildAssessPromiseGate`, the F-175 PACT gate
 *     on all four `assess_marriage`/`assess_career`/`assess_health`/`assess_wealth`
 *     tools, wired in `tools/registry_bridge.ts` (`fetchAssessPromiseGate`). This
 *     CLOSES residual F-110-b. The paragraph that stood here previously said the
 *     assess_* handlers "still certify `contradictions.status=
 *     'no_contradictions_in_domain'` without consulting this helper — an open INV-1
 *     breach". As of 2026-08-21 they consult it, and a denial reaches the
 *     budget-immune kernel (verdict clause + `kernel.promise` + a hardFloored flag).
 *
 * Keep this list TRUE. It once claimed a wiring that had never been written — the
 * §N.8 defect class this module exists to close, committed inside the module itself.
 */

// ── SaraPromiseJoin (canonical definition — matches A-09 response_budget.ts) ─

/**
 * The reconciliation object the sāra composition kernel embeds as `promise`.
 * Represents the PACT chain verdict for the queried (chart, domain/bhava).
 */
export interface SaraPromiseJoin {
  /** Classical chain verdict: supported / contradicted / neutral / absent */
  projection: 'supported' | 'contradicted' | 'neutral' | 'absent'
  /** Human-readable summary of which PACT stage the chain reached or halted at */
  promise_verdict: string
  /** Lean slice of fact_id_refs from the PACT chain (capped at 25 for budget) */
  shared_fact_ids: string[]
  /**
   * INV-1 stance: consistent means the chain cleared all tested stages;
   * contradicts means a classical denial was issued; pending means the chain
   * is either still unresolved or blocked by infrastructure.
   */
  stance: 'consistent' | 'contradicts' | 'pending'
}

// ── PACT status values (from register_d10_pact.ts / design §26/§28.3) ─────────

type PactStatus =
  | 'denied_at_promise'
  | 'denied_at_confirmation'
  | 'denied_at_activation'
  | 'chain_pending_activation'
  | 'chain_incomplete_infra'
  | 'chain_complete'

function mapProjection(status: string | undefined): SaraPromiseJoin['projection'] {
  if (!status) return 'absent'
  if (status === 'chain_complete') return 'supported'
  if (status.startsWith('denied_at_')) return 'contradicted'
  if (status === 'chain_pending_activation' || status === 'chain_incomplete_infra') return 'neutral'
  return 'absent'
}

// INV-1 enforcement: denied_at_* → 'contradicts' (no override path).
function mapStance(status: string | undefined): SaraPromiseJoin['stance'] {
  if (!status) return 'pending'
  if (status === 'chain_complete') return 'consistent'
  if (status.startsWith('denied_at_')) return 'contradicts'
  return 'pending'
}

function buildVerdict(status: string | undefined, stagesCompleted: number): string {
  if (!status) return 'PACT chain not evaluated for this domain.'
  const s = status as PactStatus
  switch (s) {
    case 'chain_complete':
      return `PACT chain complete (${stagesCompleted}/4 stages): promise confirmed through trigger.`
    case 'denied_at_promise':
      return 'PACT chain denied at PROMISE stage: classical promise for this domain absent or denied in natal chart.'
    case 'denied_at_confirmation':
      return 'PACT chain denied at CONFIRMATION stage: promise-carrying graha lacks varga dignity to confirm the promise.'
    case 'denied_at_activation':
      return 'PACT chain denied at ACTIVATION stage: no Vimśottarī dasha activates the promise-carrying lord in the evaluated window.'
    case 'chain_pending_activation':
      return `PACT chain pending activation (${stagesCompleted}/4 stages): promise and confirmation hold; activation window not yet reached.`
    case 'chain_incomplete_infra':
      return `PACT chain reached infrastructure gap (${stagesCompleted}/4 stages): all classical stages attempted; TRIGGER could not be evaluated (ephemeris sidecar unreachable/empty) — infrastructure gap, not a classical denial.`
    default:
      return `PACT chain status: ${s}.`
  }
}

// ── Public API ─────────────────────────────────────────────────────────────────

/**
 * Interpret a raw pact_query capability response as a SaraPromiseJoin.
 *
 * Handles both the raw capability response shape (`{ pact_status, stages,
 * fact_id_refs }`) and the MCP content-wrapper shape (`{ content: { ... } }`).
 *
 * Returns null if:
 * - `raw` is null / not an object (network error or empty response)
 * - `pact_status` is absent (the response is not a PACT chain result)
 *
 * Callers MUST treat null as `kernel.promise = null` and must NOT fabricate
 * a SaraPromiseJoin — §N.8 (Earned-Signal Principle).
 */
export function interpretPactJoin(raw: unknown): SaraPromiseJoin | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>

  // Unwrap MCP content-wrapper envelope if present.
  const inner = (r['content'] !== undefined && r['content'] !== null && typeof r['content'] === 'object')
    ? (r['content'] as Record<string, unknown>)
    : r

  const pactStatus = inner['pact_status'] as string | undefined
  if (!pactStatus) return null // not a PACT response; §N.8 — don't invent a join

  const stages = Array.isArray(inner['stages'])
    ? (inner['stages'] as Record<string, unknown>[])
    : []
  const factIdRefs = Array.isArray(inner['fact_id_refs'])
    ? (inner['fact_id_refs'] as string[])
    : []

  return {
    projection: mapProjection(pactStatus),
    promise_verdict: buildVerdict(pactStatus, stages.length),
    // Lean slice: the full fact_id_refs set lives in the grounding envelope.
    shared_fact_ids: factIdRefs.slice(0, 25),
    stance: mapStance(pactStatus),
  }
}
