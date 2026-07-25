/**
 * _absence_patterns.ts — shared "ontological-absence claim" phrase list, used by both
 * Task 4 (absence_phrasing_lint.ts — static source scan) and Task 5
 * (claim_checker_gate.ts — live response scan).
 *
 * An "ontological-absence claim" is a string that tells the caller a fact/record/thing
 * DOES NOT EXIST for this native/chart (as opposed to "was not returned on this page",
 * "was filtered out", or "this feature is not yet built") — e.g. "not in your data",
 * "doesn't exist", "no data found". The risk this class of phrase creates: if it is
 * emitted from a code path that never actually queried the authoritative store (a
 * generic catch-all error message, a stub, a default string), the caller is told a
 * confident negative the system never verified — the exact failure class CLAUDE.md
 * B.10 ("no fabricated computation") and the honesty-field discipline (C8 immune-field
 * set: `empty_reason`, `judgment_flags`) exist to prevent for numeric claims; this
 * lint/checker is the same discipline applied to prose.
 *
 * Deliberately heuristic (per task spec: "flag candidates for human/Verifier review
 * rather than trying to be a perfect static analyzer"). False positives are expected
 * and acceptable; false silence is not — the pattern list is intentionally broad.
 */

export type AbsencePattern = { id: string; re: RegExp; note: string }

// Each pattern is case-insensitive, matched against a single line (or a JSON string
// value) at a time. `re` sources are deliberately NOT global (`g`) here — callers
// that need repeated matches on the same string construct their own global copy.
export const ABSENCE_PATTERNS: AbsencePattern[] = [
  { id: 'not_in_your_data', re: /not (?:in|part of) your (?:chart|data)/i, note: '"not in your {chart,data}"' },
  { id: 'not_in_the_data', re: /not (?:in|part of) the (?:chart|data)/i, note: '"not in the {chart,data}"' },
  { id: 'doesnt_exist', re: /does(?:n'?t| not) exist/i, note: '"doesn\'t/does not exist"' },
  { id: 'no_data_found', re: /no data (?:found|available)/i, note: '"no data found/available"' },
  { id: 'not_found_for', re: /not found (?:in|for) (?:your|the|this) (?:chart|native|profile)/i, note: '"not found in/for your chart"' },
  { id: 'nothing_found', re: /nothing (?:found|available|to (?:show|report|display))/i, note: '"nothing found/available"' },
  { id: 'no_results_found', re: /no (?:results|records|matches|rows|entries) found/i, note: '"no {results,records,matches} found"' },
  { id: 'unable_to_find', re: /unable to (?:find|locate)/i, note: '"unable to find/locate"' },
  { id: 'could_not_find', re: /could not (?:find|locate)/i, note: '"could not find/locate"' },
  { id: 'is_absent', re: /\bis absent\b/i, note: '"is absent"' },
  { id: 'not_present_in', re: /not present in (?:your|the|this)/i, note: '"not present in your/the/this"' },
  { id: 'never_occurs', re: /never occurs? (?:in|for) (?:your|the|this) chart/i, note: '"never occurs in your chart"' },
  { id: 'has_no', re: /\b(?:you|this (?:native|chart)) has no\b/i, note: '"{you,this chart} has no"' },
  { id: 'lacks', re: /\bchart lacks\b/i, note: '"chart lacks"' },
  { id: 'without_any', re: /without any (?:record|data|trace) of/i, note: '"without any record/data/trace of"' },
]

/** Immune/grounding tokens that, if present ANYWHERE in the same response payload
 *  (structural check, Task 5) or nearby in the same source function (heuristic check,
 *  Task 4), indicate the absence claim traces back to an actual resolver-miss code
 *  path rather than a generic/stub message. Per C8 §4, `empty_reason` and
 *  `judgment_flags` are the frozen honesty-field vocabulary for exactly this purpose. */
export const GROUNDING_TOKENS = [
  'empty_reason',
  'judgment_flags',
  'catalog_only_note',
  'catalog_only_rows_in_page',
  'rows.length === 0',
  'rows.length == 0',
  '.length === 0',
  'result.rowCount === 0',
  'rowCount === 0',
  '?? null',
  'WHERE',
  'SELECT',
  'catch (',
  'catch(',
]

export function scanLineForAbsenceClaims(line: string): AbsencePattern[] {
  return ABSENCE_PATTERNS.filter((p) => p.re.test(line))
}
