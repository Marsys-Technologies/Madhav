/**
 * governed_generation_gate.ts — the ONE rule for whether a GOVERNED (5.x) Gochara generation may be served by a reader.
 *
 * Codex rounds 3 and 4 on PR 3110, steward SLICE-R4-CODEX follow-ups (a), (b), (c): the contact-ledger reader and the windows reader's shared
 * coverage path apply this same rule; neither carries a copy.
 *
 * A governed generation is served only when its manifest is PUBLISHED and SEALED, and is never a TEST SLICE. Anything else is a candidate under
 * construction (it may mix rebuild generations, e.g. between the manifest substep and the snapshot substep of a rebuild) or a generation whose
 * publication has ended (superseded / withdrawn): not a coverage statement.
 *
 * SEAL HISTORY IS DETERMINED INDEPENDENTLY OF PUBLICATION STATUS (follow-up (b)): a superseded or withdrawn generation that WAS sealed reports
 * `sealed: true`; the seal lookup is made whatever the manifest's status says. A failed lookup reports `sealed: null` (unknown) and never serves.
 *
 * The seal lookup is a plain `SELECT EXISTS (SELECT 1 FROM ka_gochara_generation_seal ...)`: it goes through the read-only SQL proxy
 * (`/api/mcp/db/query`), whose validator requires a FROM/JOIN clause (a presence probe with `to_regclass` and no FROM is rejected) and an
 * allowlisted table (`ka_gochara_generation_seal` is on the allowlist for exactly this read). A test runs this SQL through the route's real
 * validator.
 *
 * Legacy generations (3.x, 4.x) are unchanged: this gate serves them as it always did.
 */

/** The seal lookup, exactly as it goes through the proxy. */
export const SEAL_LOOKUP_SQL =
  'SELECT EXISTS (SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id = $1::uuid AND generation = $2) AS sealed'

export type GateQuery = (sql: string, params: unknown[]) => Promise<{ rows: Record<string, unknown>[] }>

/** What the gate needs to know about the generation's manifest row (null when there is none). */
export interface ManifestFacts {
  status: string | null
  stored_scope: string | null
  has_test_slice: boolean
}

export interface GateDecision {
  governed: boolean
  serve: boolean
  refusal?: 'test_slice_candidate' | 'candidate_not_served'
  manifest_status: string | null
  /** true / false when the seal lookup answered; null when it was not made (legacy, slice) or FAILED (unknown: never serves). */
  sealed: boolean | null
  seal_lookup_failed?: boolean
  /** Why the generation is not served (empty when it is). */
  reason: string
}

/** A governed generation: major version >= 5 (candidate_boundary.is_governed). */
export function isGovernedGeneration(generation: string): boolean {
  const major = Number.parseInt(String(generation).split('.', 1)[0] ?? '', 10)
  return Number.isFinite(major) && major >= 5
}

export async function governedGenerationGate(
  query: GateQuery,
  chartId: string,
  generation: string,
  facts: ManifestFacts | null
): Promise<GateDecision> {
  // A TEST SLICE (either marker is enough) is never served, governed or not, diagnostic or not.
  if (facts && (facts.stored_scope === 'test_slice' || facts.has_test_slice === true)) {
    return {
      governed: isGovernedGeneration(generation),
      serve: false,
      refusal: 'test_slice_candidate',
      manifest_status: facts.status,
      sealed: null,
      reason:
        `generation ${generation} is a TEST SLICE candidate (a small-test build over a narrowed set of classes and horizon): ` +
        'refused, never served as a coverage statement. Run the full build under a real manifest.',
    }
  }
  if (!isGovernedGeneration(generation)) {
    return { governed: false, serve: true, manifest_status: facts?.status ?? null, sealed: null, reason: '' }
  }
  // Seal history, independent of the manifest's status.
  let sealed: boolean | null = null
  let lookupFailed = false
  try {
    const { rows } = await query(SEAL_LOOKUP_SQL, [chartId, generation])
    sealed = rows[0]?.['sealed'] === true
  } catch {
    lookupFailed = true
  }
  const status = facts ? facts.status : null
  const published = status === 'published'
  if (published && sealed === true) {
    return { governed: true, serve: true, manifest_status: status, sealed: true, reason: '' }
  }
  const sealText = lookupFailed ? 'the seal lookup failed, so it is not known to be sealed' : sealed ? 'sealed' : 'not sealed'
  return {
    governed: true,
    serve: false,
    refusal: 'candidate_not_served',
    manifest_status: status,
    sealed,
    ...(lookupFailed ? { seal_lookup_failed: true } : {}),
    reason:
      `generation ${generation} is not published and sealed (manifest ${status ?? 'absent'}, ${sealText}): a governed generation ` +
      'under construction, or one whose publication has ended, is never served as a coverage statement.',
  }
}
