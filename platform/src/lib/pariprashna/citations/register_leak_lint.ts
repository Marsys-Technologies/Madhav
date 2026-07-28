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
  // Register acronyms: MSR / UCN / CGM / CDLM / LEL as standalone words.
  { name: 'register_acronym', re: /\b(?:MSR|UCN|CGM|CDLM|LEL)\b/g, idShaped: false },
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
    clean = clean.replace(new RegExp(pat.re.source, pat.re.flags), (match) => {
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
    .replace(/ {2,}/g, ' ') // doubled spaces
    .replace(/\s+([,.;:!?])/g, '$1') // space before punctuation
    .replace(/\(\s*\)/g, '') // emptied parens
    .replace(/\[\s*\]/g, '') // emptied brackets
}

/** Exposed for tests / callers that want the pattern inventory. */
export const LINT_PATTERN_NAMES = [
  ...HARD_PATTERNS.map((p) => p.name),
  ...NEAR_MISS_PATTERNS.map((p) => p.name),
]
