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

const HARD_PATTERNS: HardPattern[] = [
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

  // Hard patterns: apply REWRITE or REDACT by replacing each match in-place.
  for (const pat of HARD_PATTERNS) {
    clean = clean.replace(
      new RegExp(pat.re.source, pat.re.flags),
      (match: string, article: string | undefined, offset: number, whole: string) => {
        leakCount += 1
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
        // (b1) subjectSafe: a bare citation marker like "(UCN §XX)" or
        // "Cross-Domain Linkage Matrix (CDLM)" reads fine with the token just
        // deleted (the existing S-3 behavior, preserved exactly) — detected
        // by the match sitting directly inside an open paren. Everywhere
        // else the token is standing in for a noun (subject, object of a
        // preposition, ...); deleting it alone leaves a dangling sentence
        // ("The UCN concludes..." -> "The concludes..."), so the whole
        // matched span (including any captured leading article) is swapped
        // for a neutral demonstrative instead.
        if (pat.subjectSafe) {
          const precedingTrimmed = whole.slice(0, offset).trimEnd()
          const isBareCitationMarker = precedingTrimmed.endsWith('(')
          if (!isBareCitationMarker) {
            const capitalize = article
              ? /^[A-Z]/.test(article)
              : precedingTrimmed === '' || /[.!?]['"”’]?$/.test(precedingTrimmed)
            const replacement = capitalize ? 'This' : 'this'
            flags.push({
              type: 'flag',
              flag: 'register_leak',
              verdict: 'redact',
              pattern: pat.name,
              original: match,
              replacement,
            })
            return replacement
          }
        }
        // (b2) REDACT+FLAG — strip from reader prose.
        flags.push({
          type: 'flag',
          flag: 'register_leak',
          verdict: 'redact',
          pattern: pat.name,
          original: match,
        })
        return ''
      },
    )
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
