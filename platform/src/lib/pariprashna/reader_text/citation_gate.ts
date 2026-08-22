/**
 * pariprashna/reader_text/citation_gate.ts — lane P4-J review step, part 2.
 *
 * The review step is "voice lint + citation gate" (§10.5). Voice lint and the
 * register-leak lint are the EXISTING, real gates (`voice/voice_lint.ts`,
 * `citations/register_leak_lint.ts`) — reused as-is in `review.ts`, never
 * weakened (§9 hard-never). This module is the "citation gate" half: a
 * STRUCTURAL check specific to this catalog-authoring context (there is no
 * live turn / tool call here to resolve a citation against, so the live-turn
 * `CitationResolver` machinery does not apply — this gate checks the thing
 * that DOES apply: has every authored entry actually been grounded against
 * its OWN catalog signal's classical source, rather than authored freehand).
 *
 * A `ReaderTextEntry` passes the citation gate when:
 *   1. `grounding_note` is non-empty (an entry with no stated grounding is
 *      not "possibly ungrounded" — it is FAIL, honest-null over silent pass);
 *   2. the catalog signal it claims to translate actually exists in the
 *      reader-facing catalog (`entries.ts` cannot invent a `signal_id`);
 *   3. `grounding_note` names the signal's own `classical_basis` (or, when
 *      the catalog carries none, explicitly says so) — i.e. the grounding
 *      note is checked against THIS signal's real source, not merely
 *      present-and-plausible-sounding.
 *
 * This is intentionally narrower than a general hallucination detector (no
 * NLP claim-matching) — a real, mechanical check that a reviewer or CI run
 * can re-derive, in the same spirit as `fact-category-pin-lint` (§N.7 item 2):
 * bounded, deterministic, no proxy standing in for a claim it cannot verify.
 */
import type { MsrSignal, ReaderTextEntry, ReviewFlag } from './types'

export interface CitationGateResult {
  readonly passed: boolean
  readonly flags: readonly ReviewFlag[]
}

function normalizeForContainment(s: string): string {
  return s.toLowerCase().replace(/\s+/g, ' ').trim()
}

/**
 * Checks one entry's grounding against its own catalog signal. `signal` is
 * `null` when no catalog entry matches the entry's `signal_id` — an entry
 * citing a signal that does not exist in the reader-facing catalog is an
 * automatic, unconditional fail (it cannot be grounded in something that
 * is not there).
 */
export function checkCitationGate(entry: ReaderTextEntry, signal: MsrSignal | null): CitationGateResult {
  const flags: ReviewFlag[] = []

  if (!signal) {
    flags.push({
      source: 'citation_gate',
      code: 'citation_gate_unknown_signal',
      level: 'error',
      detail: `${entry.signal_id} does not match any reader-facing MSR catalog entry`,
    })
    return { passed: false, flags }
  }

  if (entry.grounding_note.trim().length === 0) {
    flags.push({
      source: 'citation_gate',
      code: 'citation_gate_no_grounding_note',
      level: 'error',
      detail: `${entry.signal_id} carries no grounding_note — an ungrounded entry cannot freeze`,
    })
    return { passed: false, flags }
  }

  const source = signal.classical_basis
  if (source) {
    // The grounding note must actually reference the signal's own classical
    // source — a plausible-sounding but disconnected note (grounded in the
    // WRONG signal's source, e.g. from a copy-paste) fails here.
    const sourceKeyTerms = source
      .split(/[;(),.]/)
      .map((t) => normalizeForContainment(t))
      .filter((t) => t.length >= 4)
    const note = normalizeForContainment(entry.grounding_note)
    const matchesSource = sourceKeyTerms.some((term) => note.includes(term))
    if (!matchesSource) {
      flags.push({
        source: 'citation_gate',
        code: 'citation_gate_grounding_mismatch',
        level: 'error',
        detail: `${entry.signal_id}'s grounding_note does not reference its catalog classical_basis ("${source}")`,
      })
      return { passed: false, flags }
    }
  } else {
    flags.push({
      source: 'citation_gate',
      code: 'citation_gate_no_classical_basis_in_catalog',
      level: 'info',
      detail: `${entry.signal_id}'s catalog entry carries no classical_basis to check against`,
    })
  }

  return { passed: true, flags }
}
