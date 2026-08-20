/**
 * pariprashna/citations/register_leak_lint.ts — PB-1 lane S-3.
 *
 * Register-leak backstop. Before ANY prose block commits to the wire, this lint
 * scans for internal identifiers that must never reach a reader and neutralizes
 * them. It is a STRUCTURED BACKSTOP CHANNEL, not a turn-killer: per the design
 * ruling, the primary defense is a clean evidence context feeding the model in
 * the first place. This lint therefore NEVER throws and NEVER aborts the turn —
 * on any internal error it degrades to "pass the text through + emit a telemetry
 * flag", because a mangled turn is worse than a logged near-miss.
 *
 * Verdicts per match:
 *   (a) REWRITE      — id-shaped AND a registry reader-label exists → substitute
 *                      the human label in place.
 *   (b) REDACT+FLAG  — strip the token from reader prose + emit a telemetry flag.
 *   (c) TELEMETRY    — log-only near-miss; text is left unchanged.
 *
 * ── LIST-COLLAPSE FIX (citation-leak-fix, 2026-08-20) ────────────────────────
 * Live-reproduced twice in production against the real native's chart
 * (482012f1-…): a closing sentence naming several internal registers in a list
 * — e.g. "...provided in the MSR, CGM, and CDLM artifacts." — came out the
 * OTHER side of this lint as "...provided in this, this, and this artifacts."
 * The subjectSafe substitution below was correct for a SINGLE register mention
 * ("The UCN concludes..." -> "This concludes...") but was applied
 * INDEPENDENTLY to each match in a `.replace()` pass, so N list items each
 * became their own demonstrative — a leak-free but nonsensical, user-visible
 * string that reads as a broken citation. `applySubjectSafeRun` below groups
 * consecutive subjectSafe matches joined ONLY by list connectives (",", "and",
 * "&", whitespace — nothing else) into one RUN and emits a single "this"/
 * "these" for the whole run, so a list of register mentions degrades to one
 * grammatical demonstrative instead of a repeated one per item. A lone match is
 * still a "run" of length 1 and behaves byte-for-byte as before.
 */

import type { CitationResolver, RegisterLeakFlag } from './types'

// ── Hard patterns (a match here MUST NOT reach the reader) ───────────────────
// Ordering matters: signal ids and asset-ids are "id-shaped" (REWRITE-eligible);
// register acronyms and table names are REDACT-only (no per-token label).

interface HardPattern {
  name: string
  re: RegExp
  /** id-shaped tokens are REWRITE-eligible; others go straight to REDACT. */
  idShaped: boolean
  /**
   * When true, a match preceded by a bare article ("The X", "the X", "a X",
   * "an X" — captured as part of the match itself, see the patterns below)
   * swaps the WHOLE article+token span for a neutral demonstrative
   * ("This"/"this") instead of deleting just the token. Deleting only the
   * token here leaves a subject-less sentence: "The UCN concludes..." ->
   * "The concludes...". Matches with no leading article (bare citation
   * markers like "(UCN §XX)") keep the original delete-only behavior, which
   * already reads fine as "( §XX)" — confirmed by the pre-existing S-3 tests.
   */
  subjectSafe?: boolean
}

// Internal DB table-name prefixes, harvested from platform/migrations/*.sql
// (bodha_*, mimamsa_*, kala_*, phala_*, ganita_*, brahma_*, chart_*, asset_*).
const TABLE_PREFIXES = [
  'bodha',
  'mimamsa',
  'kala',
  'phala',
  'ganita',
  'brahma',
  'chart',
  'asset',
]

// Applied FIRST, in this order — id-shaped tokens, REWRITE-eligible via a
// resolver, straight `.replace()` per pattern exactly as before the
// list-collapse fix (none of these are subjectSafe, so they are untouched by
// `applySubjectSafeRun` below).
const NON_SUBJECT_SAFE_BEFORE: HardPattern[] = [
  // SIG.MSR.001, SIG.CGM.42, SIG.<REG>.<n> — signal ids.
  { name: 'signal_id', re: /SIG\.\w+\.\d+/g, idShaped: true },
  // Internal asset-id prefixes: bo_/ga_/ka_/ph_/mi_/bg_ + snake tail.
  { name: 'asset_id', re: /\b(?:bo|ga|ka|ph|mi|bg)_[a-z][a-z_]*\b/g, idShaped: true },
  // Internal DB table names: <prefix>_<snake tail>.
  {
    name: 'table_name',
    re: new RegExp(`\\b(?:${TABLE_PREFIXES.join('|')})_[a-z][a-z_]*\\b`, 'g'),
    idShaped: false,
  },
]

// Applied SECOND, as one combined run-aware pass (`applySubjectSafeRun`) — see
// the LIST-COLLAPSE FIX header comment. A list of these joined only by list
// connectives collapses to ONE demonstrative instead of one per item.
const SUBJECT_SAFE_PATTERNS: HardPattern[] = [
  // Register acronyms: MSR / UCN / CGM / CDLM / LEL / RM as standalone words.
  // The leading article is captured AS PART OF the match (group 1) so the
  // subjectSafe replacement below can swap the whole span at once — see
  // HardPattern.subjectSafe.
  {
    name: 'register_acronym',
    re: /\b(?:([Tt]he|[Aa]n?)\s+)?(?:MSR|UCN|CGM|CDLM|LEL|RM)\b/g,
    idShaped: false,
    subjectSafe: true,
  },
  // Spelled-out register names — the model sometimes narrates the full name
  // instead of (or alongside) the acronym; the acronym pattern above cannot
  // catch that. Longest-alternative-first so "Cross-Domain Linkage Matrix"
  // wins over the shorter "Cross-Domain Linkage" prefix. Both "Chart Graph
  // Model" (CLAUDE.md's canonical name) and "Causal Graph Model" (the name
  // actually used in b11_guard.ts's LAYER_MARKERS, which is what a model
  // reading that context would echo) are included.
  {
    name: 'register_full_name',
    re: /\b(?:([Tt]he|[Aa]n?)\s+)?(?:Master Signal Register|Cross-Domain Linkage Matrix|Cross-Domain Linkage|Unified Chart Narrative|Causal Graph Model|Chart Graph Model|Resonance Map|Life Event Log)\b/g,
    idShaped: false,
    subjectSafe: true,
  },
]

// Applied THIRD, straight `.replace()` exactly as before the list-collapse
// fix — not subjectSafe, so it runs after the run-aware pass, same relative
// order as the original single array.
const NON_SUBJECT_SAFE_AFTER: HardPattern[] = [
  // L1 chart_facts.fact_id / CGM node-id namespace codes: `namespace.SUBJECT`
  // or `namespace.SUBJECT.KEY` (ganita/types.ts's own doc comment: "namespace.
  // SUBJECT.KEY (e.g. PLN.SUN.LON_DEG)"), e.g. PLN.SUN, HSE.10, KRK.C8.AMATYA,
  // SEN.ARD.AL — confirmed leaking in production, always as a bare
  // parenthetical aside (often backtick-wrapped: "(`PLN.SUN`)"), never as a
  // sentence subject, so this pattern is NOT subjectSafe (plain delete, same
  // treatment as signal_id/table_name). No resolver exists for these today,
  // so REDACT rather than REWRITE (idShaped: false). `SIG.` is EXCLUDED here —
  // that namespace already has its own dedicated hard pattern (signal_id,
  // requires a numeric tail) and its own dedicated near-miss pattern
  // (partial_signal_id, telemetry-only for a truncated SIG ref with no
  // numeric tail); this generic pattern would otherwise hard-redact exactly
  // the truncated refs partial_signal_id is meant to leave untouched.
  {
    name: 'fact_id_namespace',
    re: /\b(?!SIG\.)[A-Z]{2,6}\.[A-Z0-9_]{1,40}(?:\.[A-Z0-9_]{1,40}){0,2}\b/g,
    idShaped: false,
  },
]

// Preserves the exact original array order for anything reading the FULL
// pattern set (REWRITE-label re-leak check, `LINT_PATTERN_NAMES`).
const HARD_PATTERNS: HardPattern[] = [
  ...NON_SUBJECT_SAFE_BEFORE,
  ...SUBJECT_SAFE_PATTERNS,
  ...NON_SUBJECT_SAFE_AFTER,
]

// ── Near-miss patterns (TELEMETRY only — never alter text) ───────────────────
// These "almost look internal" and are worth logging so we can tune the model
// prompt, but they are NOT confirmed leaks so we do not touch the prose.
const NEAR_MISS_PATTERNS: { name: string; re: RegExp }[] = [
  // `SIG.` + letters but NO numeric tail — a truncated / partial signal id.
  { name: 'partial_signal_id', re: /\bSIG\.[A-Za-z]+\b(?!\.\d)/g },
  // lowercase register words — case-variant of the acronym set.
  { name: 'lowercase_register', re: /\b(?:msr|ucn|cgm|cdlm|lel)\b/g },
]

export interface LintResult {
  /** The reader-safe text after REWRITE/REDACT verdicts applied. */
  clean: string
  /** Every verdict fired (audit channel). */
  flags: RegisterLeakFlag[]
  /** Convenience: count of hard matches (rewrite + redact). */
  leakCount: number
}

/**
 * Run the register-leak lint over a reader-prose fragment.
 * Guaranteed to return (never throws). The returned `clean` string is safe to
 * write to the wire.
 */
export function lintReaderProse(text: string, resolver?: CitationResolver): LintResult {
  try {
    return lintInner(text, resolver)
  } catch (err) {
    // Backstop's backstop: on internal failure, do NOT block the turn. Pass the
    // text through and log a telemetry flag so the failure is observable.
    return {
      clean: text,
      flags: [
        {
          type: 'flag',
          flag: 'register_leak',
          verdict: 'telemetry',
          pattern: 'lint_internal_error',
          original: String((err as Error)?.message ?? err),
        },
      ],
      leakCount: 0,
    }
  }
}

function lintInner(text: string, resolver?: CitationResolver): LintResult {
  const flags: RegisterLeakFlag[] = []
  let leakCount = 0
  let clean = text

  // Hard patterns (non-subjectSafe, BEFORE the run-aware pass): REWRITE or
  // REDACT by replacing each match in-place, exactly as before this fix.
  for (const pat of NON_SUBJECT_SAFE_BEFORE) {
    clean = applyHardPatternReplace(clean, pat, resolver, flags, (n) => (leakCount += n))
  }

  // subjectSafe patterns: ONE run-aware pass over BOTH register_acronym and
  // register_full_name matches together — see the LIST-COLLAPSE FIX header
  // comment. A run of 1 behaves byte-for-byte as the old per-pattern
  // `.replace()` did; a run of 2+ collapses to a single demonstrative.
  const subjectSafeResult = applySubjectSafeRun(clean, SUBJECT_SAFE_PATTERNS, flags)
  clean = subjectSafeResult.text
  leakCount += subjectSafeResult.leakCount

  // Hard patterns (non-subjectSafe, AFTER — same relative order as the
  // original single array, where fact_id_namespace ran last).
  for (const pat of NON_SUBJECT_SAFE_AFTER) {
    clean = applyHardPatternReplace(clean, pat, resolver, flags, (n) => (leakCount += n))
  }

  // Tidy whitespace left by redactions ("word  ." → "word.", doubled spaces).
  clean = tidyAfterRedaction(clean)

  // Near-miss patterns: TELEMETRY only, text untouched.
  for (const pat of NEAR_MISS_PATTERNS) {
    const re = new RegExp(pat.re.source, pat.re.flags)
    let m: RegExpExecArray | null
    while ((m = re.exec(clean)) !== null) {
      flags.push({
        type: 'flag',
        flag: 'register_leak',
        verdict: 'telemetry',
        pattern: pat.name,
        original: m[0],
      })
      if (m.index === re.lastIndex) re.lastIndex += 1 // zero-width guard
    }
  }

  return { clean, flags, leakCount }
}

/**
 * Apply ONE non-subjectSafe hard pattern with the original REWRITE/REDACT
 * verdict logic, unchanged from before the list-collapse fix. `bumpLeakCount`
 * is called with the number of matches this pattern fired (always 1 per
 * callback invocation) so the caller can accumulate a shared counter.
 */
function applyHardPatternReplace(
  text: string,
  pat: HardPattern,
  resolver: CitationResolver | undefined,
  flags: RegisterLeakFlag[],
  bumpLeakCount: (n: number) => void,
): string {
  return text.replace(new RegExp(pat.re.source, pat.re.flags), (match: string) => {
    bumpLeakCount(1)
    // (a) REWRITE — id-shaped + a reader label exists.
    if (pat.idShaped && resolver) {
      const label = safeReaderLabel(resolver, match)
      if (label && !wouldStillLeak(label)) {
        flags.push({
          type: 'flag',
          flag: 'register_leak',
          verdict: 'rewrite',
          pattern: pat.name,
          original: match,
          replacement: label,
        })
        return label
      }
    }
    // (b) REDACT+FLAG — strip from reader prose.
    flags.push({
      type: 'flag',
      flag: 'register_leak',
      verdict: 'redact',
      pattern: pat.name,
      original: match,
    })
    return ''
  })
}

/** One subjectSafe match, collected before grouping into runs. */
interface SubjectSafeMatch {
  patternName: string
  index: number
  length: number
  matchText: string
  article?: string
}

/**
 * Text strictly between two adjacent subjectSafe matches that is "just a list
 * separator" — commas, "and", "&", whitespace, in any combination, and
 * NOTHING else. Two register mentions separated by anything else (a verb, a
 * clause) are NOT part of the same list and must not be collapsed.
 */
function isListConnective(between: string): boolean {
  const stripped = between.replace(/,/g, ' ').replace(/&/g, ' ').trim().toLowerCase()
  return stripped === '' || stripped === 'and'
}

/**
 * The run-aware replacement for subjectSafe patterns (LIST-COLLAPSE FIX).
 * Collects every match from every pattern in `patterns` against `text`, sorts
 * by position, and groups adjacent matches into "runs" wherever the text
 * between them is nothing but a list connective (see `isListConnective`).
 * Each run collapses to ONE replacement:
 *   - a run inside a bare citation marker, e.g. "(UCN, CGM)" → deleted
 *     entirely, same "bare marker" carve-out the single-match path always had;
 *   - otherwise → a single "this"/"This" (run length 1, byte-for-byte the
 *     pre-fix behavior) or "these"/"These" (run length 2+, the fix: one
 *     demonstrative for the whole list instead of one per item).
 * Capitalization is decided from the FIRST match in the run, same rule as
 * before: its own captured article, else whether the text preceding it is
 * empty or ends a prior sentence.
 */
function applySubjectSafeRun(
  text: string,
  patterns: readonly HardPattern[],
  flags: RegisterLeakFlag[],
): { text: string; leakCount: number } {
  const rawMatches: SubjectSafeMatch[] = []
  for (const pat of patterns) {
    const re = new RegExp(pat.re.source, pat.re.flags)
    let m: RegExpExecArray | null
    while ((m = re.exec(text)) !== null) {
      rawMatches.push({
        patternName: pat.name,
        index: m.index,
        length: m[0].length,
        matchText: m[0],
        article: m[1],
      })
      if (m.index === re.lastIndex) re.lastIndex += 1 // zero-width guard
    }
  }
  if (rawMatches.length === 0) return { text, leakCount: 0 }
  rawMatches.sort((a, b) => a.index - b.index)

  const runs: SubjectSafeMatch[][] = []
  for (const m of rawMatches) {
    const lastRun = runs[runs.length - 1]
    const prev = lastRun?.[lastRun.length - 1]
    if (prev && isListConnective(text.slice(prev.index + prev.length, m.index))) {
      lastRun.push(m)
    } else {
      runs.push([m])
    }
  }

  let leakCount = 0
  let result = ''
  let cursor = 0
  for (const run of runs) {
    const first = run[0]
    const last = run[run.length - 1]
    result += text.slice(cursor, first.index)
    leakCount += run.length

    const precedingTrimmed = text.slice(0, first.index).trimEnd()
    const isBareCitationMarker = precedingTrimmed.endsWith('(')
    if (isBareCitationMarker) {
      // (b1) Bare citation marker, e.g. "(UCN §XX)" or "(UCN, CGM §XX)" — the
      // existing S-3 behavior for a single match, generalized to a run: the
      // whole span is just deleted, no demonstrative substitution.
      for (const m of run) {
        flags.push({
          type: 'flag',
          flag: 'register_leak',
          verdict: 'redact',
          pattern: m.patternName,
          original: m.matchText,
        })
      }
    } else {
      const capitalize = first.article
        ? /^[A-Z]/.test(first.article)
        : precedingTrimmed === '' || /[.!?]['"”’]?$/.test(precedingTrimmed)
      const plural = run.length > 1
      const replacement = capitalize ? (plural ? 'These' : 'This') : (plural ? 'these' : 'this')
      result += replacement
      for (const m of run) {
        flags.push({
          type: 'flag',
          flag: 'register_leak',
          verdict: 'redact',
          pattern: m.patternName,
          original: m.matchText,
          replacement,
        })
      }
    }
    cursor = last.index + last.length
  }
  result += text.slice(cursor)

  return { text: result, leakCount }
}

/** A reader label must itself be clean — guard against a label that re-leaks. */
function wouldStillLeak(label: string): boolean {
  return HARD_PATTERNS.some((p) => new RegExp(p.re.source).test(label))
}

function safeReaderLabel(resolver: CitationResolver, token: string): string | null {
  try {
    return resolver.readerLabel(token)
  } catch {
    return null
  }
}

/** Collapse artifacts left by removing a token from mid-sentence. */
function tidyAfterRedaction(s: string): string {
  return s
    .replace(/`\s*`/g, '') // emptied inline-code backticks (e.g. redacting the
    // id inside `PLN.SUN` leaves a bare `` pair) — runs before the emptied-
    // parens/brackets cleanup below since a backtick-wrapped id sitting
    // inside parens, e.g. "(`PLN.SUN`)", needs the backticks gone first
    // before "()" is recognizable as empty.
    .replace(/\(\s*\)/g, '') // emptied parens
    .replace(/\[\s*\]/g, '') // emptied brackets
    .replace(/\s+([,.;:!?])/g, '$1') // space before punctuation
    .replace(/ {2,}/g, ' ') // doubled spaces — LAST: removing emptied parens/
    // brackets above can itself introduce a fresh double space that an
    // earlier collapse pass would never see.
}

/** Exposed for tests / callers that want the pattern inventory. */
export const LINT_PATTERN_NAMES = [
  ...HARD_PATTERNS.map((p) => p.name),
  ...NEAR_MISS_PATTERNS.map((p) => p.name),
]
