/**
 * pariprashna/reader_text/entry_structure_gate.ts — lane P4-J review step, part 2.
 * (Was `citation_gate.ts` / `checkCitationGate` until 2026-08-23; renamed because
 * the old name promised something the code never did — see NAME HISTORY below.)
 *
 * WHAT THIS GATE CHECKS — the complete list, nothing implied beyond it:
 *   1. the entry's `signal_id` resolves to a real reader-facing catalog signal;
 *   2. `reader_text` is non-empty after trimming, and falls inside a coarse
 *      length band with at least one terminated sentence in it;
 *   3. `grounding_note` is non-empty;
 *   4. `grounding_note` contains at least one >=4-character fragment of the
 *      signal's own `classical_basis` string (a containment check, nothing more).
 *
 * WHAT THIS GATE DOES NOT CHECK, AND MUST NOT BE READ AS CHECKING:
 *   - It does not read the MEANING of `reader_text` at all. It cannot tell that
 *     a reading is about the wrong planet, that its degrees or rupas were
 *     invented, or that it flatly contradicts the signal's own falsifier. Nine
 *     independently-authored adversarial texts — including a reading about
 *     Jupiter attached to a Saturn signal, fabricated numeric values, a
 *     deterministic "certain to occur" prediction, and a mortality claim — all
 *     passed the pre-rename gate with zero flags. Check 2 above closes exactly
 *     one of those nine (the EMPTY `reader_text`, which passing was
 *     indefensible) and leaves the other eight open. There is no claim here
 *     that they are closed.
 *   - Check 4's discriminating power is WEAK, and measurably so. `sourceKeyTerms`
 *     splits `classical_basis` on `[;(),.]` and keeps >=4-character fragments,
 *     which reduces e.g. "BPHS Ch.26 Sl.19" to the fragment "bphs ch" — so a
 *     note naming ANY BPHS chapter matches ANY BPHS-sourced signal. Measured
 *     2026-08-23 over the 568-signal reader-facing catalog, by running each of
 *     the 25 authored `grounding_note`s against every OTHER signal's
 *     `classical_basis` — reproduce with
 *     `npx tsx --conditions=react-server
 *      src/lib/pariprashna/reader_text/scripts/measure_gate_discrimination.ts`:
 *         mean false-accept set  164.6 of 567 other signals (29.0%)
 *         worst  SIG.MSR.500  318 (56.1%)    best  SIG.MSR.302  4 (0.7%)
 *         12 of 25 entries cannot be distinguished from >50% of the catalog
 *     So check 4 catches a grounding note copied from a source-family the signal
 *     does not belong to at all. It does NOT establish that the note is the
 *     right signal's note. The pre-rename header claimed the note was "checked
 *     against THIS signal's real source, not merely present-and-plausible-
 *     sounding"; on those numbers that claim was not earned, and it is withdrawn.
 *
 * NAME HISTORY (§N.8 — a signal must measure the claim it asserts). The module
 * was called the "citation gate" and was cited by the lane as the thing standing
 * between a hallucinated reading and the frozen artifact. It never read
 * `reader_text`. A gate named for what it does not do is worse than no gate,
 * because a reviewer stops looking. It is now named for its two real subjects:
 * the STRUCTURE of an entry (both fields present, prose within sane bounds) and
 * the source-family containment of its grounding note.
 *
 * The two lints wrapped alongside this gate in `review.ts` (`voice/voice_lint.ts`,
 * `citations/register_leak_lint.ts`) are the real, pre-existing gates, reused
 * unchanged and never weakened (§9 hard-never).
 */
import type { MsrSignal, ReaderTextEntry, ReviewFlag } from './types'

export interface EntryStructureResult {
  readonly passed: boolean
  readonly flags: readonly ReviewFlag[]
}

/** Coarse sanity bounds on reader prose. Deliberately wide: this is a
 *  "is there a reading here at all" check, not a style rule. The authored 25
 *  span roughly 600-1000 characters; the bounds sit well outside that so a
 *  legitimate future entry is never squeezed by them. */
export const READER_TEXT_MIN_CHARS = 120
export const READER_TEXT_MAX_CHARS = 4000

function normalizeForContainment(s: string): string {
  return s.toLowerCase().replace(/\s+/g, ' ').trim()
}

/**
 * The >=4-character fragments of a `classical_basis` string that the grounding
 * note is tested for containment against. Exported so the gate's discriminating
 * power can be MEASURED rather than asserted — see the header's measurement and
 * `scripts/measure_gate_discrimination.ts`, which reproduces it.
 */
export function sourceKeyTerms(classicalBasis: string): string[] {
  return classicalBasis
    .split(/[;(),.]/)
    .map((t) => normalizeForContainment(t))
    .filter((t) => t.length >= 4)
}

/** True when `groundingNote` contains any key term of `classicalBasis`. */
export function groundingNoteMatchesSource(groundingNote: string, classicalBasis: string): boolean {
  const note = normalizeForContainment(groundingNote)
  return sourceKeyTerms(classicalBasis).some((term) => note.includes(term))
}

/**
 * Checks one entry's structure against its own catalog signal. `signal` is
 * `null` when no catalog entry matches the entry's `signal_id` — an entry
 * citing a signal that does not exist in the reader-facing catalog is an
 * automatic, unconditional fail (it cannot be grounded in something that
 * is not there).
 */
export function checkEntryStructure(entry: ReaderTextEntry, signal: MsrSignal | null): EntryStructureResult {
  const flags: ReviewFlag[] = []
  const fail = (code: string, detail: string): EntryStructureResult => {
    flags.push({ source: 'entry_structure', code, level: 'error', detail })
    return { passed: false, flags }
  }

  if (!signal) {
    return fail(
      'entry_structure_unknown_signal',
      `${entry.signal_id} does not match any reader-facing MSR catalog entry`,
    )
  }

  // An empty reader_text passing review was the sharpest single hole in the
  // pre-rename gate: it read only grounding_note, so an entry with no reading
  // in it at all froze clean. Presence and coarse shape are checkable, so they
  // are checked; nothing about the reading's CONTENT is claimed (header).
  const text = entry.reader_text.trim()
  if (text.length === 0) {
    return fail('entry_structure_empty_reader_text', `${entry.signal_id} has an empty reader_text`)
  }
  if (text.length < READER_TEXT_MIN_CHARS) {
    return fail(
      'entry_structure_reader_text_too_short',
      `${entry.signal_id}'s reader_text is ${text.length} characters, below the ${READER_TEXT_MIN_CHARS}-character floor — too short to be a reading`,
    )
  }
  if (text.length > READER_TEXT_MAX_CHARS) {
    return fail(
      'entry_structure_reader_text_too_long',
      `${entry.signal_id}'s reader_text is ${text.length} characters, above the ${READER_TEXT_MAX_CHARS}-character ceiling`,
    )
  }
  if (!/[.!?]/.test(text)) {
    return fail(
      'entry_structure_reader_text_unterminated',
      `${entry.signal_id}'s reader_text contains no terminated sentence — it is a fragment, not a reading`,
    )
  }

  if (entry.grounding_note.trim().length === 0) {
    return fail(
      'entry_structure_no_grounding_note',
      `${entry.signal_id} carries no grounding_note — an ungrounded entry cannot freeze`,
    )
  }

  const source = signal.classical_basis
  if (source) {
    // Containment only. This catches a grounding note copied from a source
    // FAMILY the signal does not belong to; it does not establish that the note
    // is this signal's note (see the header's measured false-accept figures).
    if (!groundingNoteMatchesSource(entry.grounding_note, source)) {
      return fail(
        'entry_structure_grounding_source_family_mismatch',
        `${entry.signal_id}'s grounding_note shares no key term with its catalog classical_basis ("${source}")`,
      )
    }
  } else {
    flags.push({
      source: 'entry_structure',
      code: 'entry_structure_no_classical_basis_in_catalog',
      level: 'info',
      detail: `${entry.signal_id}'s catalog entry carries no classical_basis to check against`,
    })
  }

  return { passed: true, flags }
}
