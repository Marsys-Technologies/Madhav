/** Shared publication gate for contact-ledger and windows coverage readers.
 * Governed generations require a published manifest and a known seal. A test
 * slice is never served, including diagnostics. Legacy reads need no seal.
 */
export const SEAL_LOOKUP_SQL =
  'SELECT EXISTS (SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id = $1::uuid AND generation = $2) AS sealed'

export type GateQuery = (sql: string, params: unknown[]) => Promise<{ rows: Record<string, unknown>[] }>

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
  sealed: boolean | null
  seal_lookup_failed?: boolean
  reason: string
}

/** Matches the sidecar candidate boundary: major version >= 5. */
export function isGovernedGeneration(generation: string): boolean {
  const major = Number.parseInt(generation.split('.', 1)[0] ?? '', 10)
  return Number.isFinite(major) && major >= 5
}

export async function governedGenerationGate(
  query: GateQuery,
  chartId: string,
  generation: string,
  facts: ManifestFacts | null
): Promise<GateDecision> {
  const governed = isGovernedGeneration(generation)
  const manifest_status = facts?.status ?? null
  if (facts?.stored_scope === 'test_slice' || facts?.has_test_slice === true) {
    return {
      governed, serve: false, refusal: 'test_slice_candidate', manifest_status, sealed: null,
      reason: `generation ${generation} is a TEST SLICE candidate (a small-test build over a narrowed set of classes and horizon): ` +
        'refused, never served as a coverage statement. Run the full build under a real manifest.',
    }
  }
  if (!governed) return { governed, serve: true, manifest_status, sealed: null, reason: '' }

  // Read seal history independently of publication status. Failed or malformed
  // responses establish neither presence nor absence of a seal (§N.8).
  let sealed: boolean | null = null
  let seal_lookup_failed = false
  try {
    const { rows } = await query(SEAL_LOOKUP_SQL, [chartId, generation])
    if (rows.length !== 1 || typeof rows[0]?.['sealed'] !== 'boolean') {
      seal_lookup_failed = true
    } else {
      sealed = rows[0]['sealed']
    }
  } catch {
    seal_lookup_failed = true
  }
  if (manifest_status === 'published' && sealed === true) {
    return { governed, serve: true, manifest_status, sealed, reason: '' }
  }
  const sealText = seal_lookup_failed
    ? 'the seal lookup failed, so it is not known to be sealed'
    : sealed ? 'sealed' : 'not sealed'
  return {
    governed, serve: false, refusal: 'candidate_not_served', manifest_status, sealed,
    ...(seal_lookup_failed ? { seal_lookup_failed: true } : {}),
    reason: `generation ${generation} is not published and sealed (manifest ${manifest_status ?? 'absent'}, ${sealText}): ` +
      'a governed generation under construction, or one whose publication has ended, is never served as a coverage statement.',
  }
}
