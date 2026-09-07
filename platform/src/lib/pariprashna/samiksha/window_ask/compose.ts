/**
 * The window-opening ask — DETERMINISTIC composition (lane P4-G).
 *
 * ARCHITECTURE AUTHORITY: `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §6.6 / §14.7, item A-42
 * ("The window-opening ask"), which names this "the single highest-leverage unbuilt feature in
 * the architecture" and fixes its register with a worked example:
 *
 *     "Before I answer: in March I indicated X for April–June. What happened?"
 *
 * ── THE ONE CLAIM THIS MODULE MAKES ────────────────────────────────────────────────────────
 * Every character of the ask is ASSEMBLED FROM LEDGER FACTS by the pure function below. No
 * model composes any part of it. That is why the `window_ask` wire event carries
 * `composition: 'deterministic'` as a Zod LITERAL rather than an enum: a model-composed ask
 * cannot be represented on the wire at all. §N.8 says a claim needs a detector that could
 * report failure — here the detectors are (a) `__tests__/deterministic_by_construction.test.ts`,
 * which reads THIS FILE's source and fails if it ever imports a model/provider/synthesis path,
 * and (b) the wire schema itself, which rejects any other value.
 *
 * ── WHAT IS FACT AND WHAT IS FIXED PROSE (the voice panel will ask exactly this) ────────────
 * FROM THE LEDGER ROW, verbatim or by pure transform:
 *   · the claim              ← `claim_text`, markdown-de-chromed, never paraphrased, quoted
 *   · when it was said       ← `confirmed_at` (fallback `created_at`) → "in July" / "in July 2025"
 *   · when the window ended  ← `upper("window") - 1 day` → "31 December" / "31 December 2026"
 *   · what it was about      ← `domain`, mapped through a CLOSED set; omitted when unmapped
 * FIXED PROSE (identical in every ask, chosen once, reviewed as voice — never generated):
 *   · "Before I answer —"    the A-42 opener: the ask precedes the reading and does not gate it
 *   · "I said"               the instrument owns its own prior words in the first person
 *   · "That window ran to … and has closed."
 *   · "What happened?"
 *   · the honest-null offer  (see below)
 *
 * ── THE HONEST-NULL OFFER IS LOAD-BEARING, NOT POLITENESS ──────────────────────────────────
 * "If you cannot tell, say so — I would rather hold this open than write down a guess." reads
 * as courtesy and is not: it is CLAUDE.md §N.7 item 6 ("an honest null beats an invented
 * judgment") spoken to the reader in plain words. A reader who is not told that "I don't know"
 * is a real answer will supply a plausible one, and a plausible-but-invented outcome is worse
 * than no outcome — it silently poisons the calibration series this whole loop exists to
 * produce. The sentence is the difference between a calibration record and a folk memory.
 *
 * ── NO UNSOLICITED SEVERITY (a hard suppression, not a preference) ──────────────────────────
 * `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` line 2549: "An answer about career does not
 * volunteer a health finding because a signal fired." An unprompted ask is the purest form of
 * volunteering. Rows in a SEVERITY_SUPPRESSED_DOMAIN therefore never produce an ask — they
 * stay in the review tab, where the reader goes on purpose. See `SEVERITY_SUPPRESSED_DOMAINS`.
 *
 * ── LEAKAGE ────────────────────────────────────────────────────────────────────────────────
 * The ask never renders: a row id, a lifecycle token, a table name, a confidence band, a Brier
 * score, the word "calibration", or a raw `domain` token that is not in the closed map. The
 * `window_ask` event carries `ledger_row_id` for the client to echo back on answer, and that
 * field is machine-only — it is never part of `ask_text`.
 *
 * ISOMORPHIC on purpose (pure TypeScript, no `server-only`, no `pg`, no model client) so the
 * composition can be unit-tested with zero I/O and so a client could render the same text.
 */

import type { LedgerRow } from '../schema'

// ---------------------------------------------------------------------------
// Domains
// ---------------------------------------------------------------------------

/**
 * Domains an unprompted ask NEVER fires on (the "no unsolicited severity" rule). These rows are
 * still resolvable — the review tab lists them exactly as before — but the instrument does not
 * raise them in conversation on its own initiative.
 */
export const SEVERITY_SUPPRESSED_DOMAINS: readonly string[] = [
  'health',
  'longevity',
  'mortality',
  'medical',
  'death',
] as const

/**
 * CLOSED map: stored `domain` token → the plain phrase the ask uses. A domain that is not a key
 * here contributes NOTHING to the ask (the phrase is omitted) rather than being passed through —
 * an unmapped token is internal vocabulary and must not reach the reader.
 */
export const DOMAIN_PHRASE: Readonly<Record<string, string>> = {
  career: 'your work',
  work: 'your work',
  profession: 'your work',
  wealth: 'your money',
  finance: 'your money',
  finances: 'your money',
  marriage: 'your marriage',
  relationship: 'your marriage',
  spouse: 'your marriage',
  education: 'your study',
  study: 'your study',
  family: 'your family',
  children: 'your family',
  property: 'your home',
  residence: 'your home',
  home: 'your home',
  travel: 'your travel',
} as const

// ---------------------------------------------------------------------------
// Answer options (machine-readable; the labels are reader-facing)
// ---------------------------------------------------------------------------

export const WINDOW_ASK_OPTION_KEYS = [
  'happened',
  'did_not_happen',
  'partial',
  'cant_tell',
  'dispute',
] as const
export type WindowAskOptionKey = (typeof WINDOW_ASK_OPTION_KEYS)[number]

export interface WindowAskOption {
  key: WindowAskOptionKey
  label: string
}

/**
 * The five offered answers. `cant_tell` and `dispute` are first-class OPTIONS, not fallbacks a
 * reader has to think of: an honest non-answer and a disagreement must each be as cheap to give
 * as a yes. `dispute` is deliberately about the ASK, not the outcome — a reader who thinks the
 * question is malformed must be able to say that without it being scored as a "no".
 */
export const WINDOW_ASK_OPTIONS: readonly WindowAskOption[] = [
  { key: 'happened', label: 'It happened' },
  { key: 'did_not_happen', label: 'It did not' },
  { key: 'partial', label: 'Partly' },
  { key: 'cant_tell', label: 'I cannot tell' },
  { key: 'dispute', label: 'You have framed this wrong' },
] as const

// ---------------------------------------------------------------------------
// Composed shape
// ---------------------------------------------------------------------------

export interface WindowAsk {
  /** The ledger row this ask resolves. MACHINE-ONLY — never appears in `text`. */
  ledgerRowId: string
  /** The ask, exactly as the reader sees it. */
  text: string
  options: readonly WindowAskOption[]
  /** Structural declaration: assembled from ledger facts, no model involved. */
  composition: 'deterministic'
  /** The facts this text was assembled from — the audit trail for a voice/§N.7 review. */
  derivedFrom: {
    claim_quoted: string
    said_when: string | null
    window_last_day: string | null
    domain_phrase: string | null
    claim_was_shortened: boolean
  }
}

/** Why an otherwise-closed window produced no ask. */
export const NO_COMPOSE_REASONS = [
  'severity_suppressed_domain',
  'claim_text_unusable',
  'window_missing_or_unparseable',
] as const
export type NoComposeReason = (typeof NO_COMPOSE_REASONS)[number]

export type ComposeResult =
  | { composed: true; ask: WindowAsk }
  | { composed: false; reason: NoComposeReason; detail: string }

// ---------------------------------------------------------------------------
// Pure helpers
// ---------------------------------------------------------------------------

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
] as const

/** Longest claim we quote back in full, in characters, before shortening at a sentence edge. */
export const CLAIM_QUOTE_MAX = 320

/**
 * De-chrome markdown from a stored claim WITHOUT de-contenting it.
 *
 * The rule, stated once so it can be argued with: a leading list bullet and a leading BOLDED
 * label (`**Prediction:**`) are authoring chrome the synthesis prompt produced — they are not
 * something the instrument said to this reader, and quoting them back is clumsy and slightly
 * dishonest about what the sentence was. Everything else — including an UNbolded leading label —
 * is content and survives. We remove emphasis MARKERS, never the words between them.
 */
export function dechromeClaim(raw: string): string {
  let s = raw.replace(/\r\n?/g, '\n').trim()

  // Leading list markers / headings, possibly nested ("* * item", "1. item", "- item").
  let before: string
  do {
    before = s
    s = s.replace(/^[\s>]*(?:[-*+•]|#{1,6}|\d{1,3}[.)])\s+/, '')
  } while (s !== before)

  // A leading BOLDED label — `**Prediction:**` / `**Trajectory to 2027**:` — is chrome.
  s = s.replace(/^\*\*[^*\n]{1,60}?:?\*\*\s*:?\s*/, '')

  // Emphasis MARKERS only. The words between them are content and stay.
  s = s.replace(/\*\*|__/g, '')
  s = s.replace(/(^|[\s(])[*_](\S)/g, '$1$2').replace(/(\S)[*_]($|[\s.,;:!?)])/g, '$1$2')

  // Inline-code and link chrome, keeping the visible text.
  s = s.replace(/`/g, '')
  s = s.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')

  return s.replace(/\s+/g, ' ').trim()
}

/**
 * Shorten a de-chromed claim to at most `CLAIM_QUOTE_MAX`, preferring a sentence boundary so
 * the quote is never cut mid-thought. Returns `shortened` so the caller can DISCLOSE that the
 * quote is partial rather than let a truncation pass as the whole claim.
 */
export function shortenClaim(claim: string, max = CLAIM_QUOTE_MAX): { text: string; shortened: boolean } {
  if (claim.length <= max) return { text: claim, shortened: false }

  const head = claim.slice(0, max)
  const lastSentence = Math.max(head.lastIndexOf('. '), head.lastIndexOf('? '), head.lastIndexOf('! '))
  if (lastSentence >= Math.floor(max * 0.4)) {
    return { text: head.slice(0, lastSentence + 1).trim(), shortened: true }
  }
  const lastSpace = head.lastIndexOf(' ')
  const cut = lastSpace >= Math.floor(max * 0.4) ? head.slice(0, lastSpace) : head
  return { text: `${cut.trim()}…`, shortened: true }
}

/** ISO-ish timestamp → `{ y, m, d }` in UTC, or null when unparseable. */
function partsOf(iso: string | null | undefined): { y: number; m: number; d: number } | null {
  if (!iso) return null
  const t = Date.parse(iso)
  if (Number.isNaN(t)) return null
  const dt = new Date(t)
  return { y: dt.getUTCFullYear(), m: dt.getUTCMonth(), d: dt.getUTCDate() }
}

/** `2026-07-31` → "July" when `nowYear` matches, else "July 2025". Month only — day is noise here. */
export function renderMonth(iso: string | null | undefined, nowYear: number): string | null {
  const p = partsOf(iso)
  if (!p) return null
  return p.y === nowYear ? MONTHS[p.m] : `${MONTHS[p.m]} ${p.y}`
}

/** `2026-12-31` → "31 December" when `nowYear` matches, else "31 December 2026". */
export function renderDay(iso: string | null | undefined, nowYear: number): string | null {
  const p = partsOf(iso)
  if (!p) return null
  const base = `${p.d} ${MONTHS[p.m]}`
  return p.y === nowYear ? base : `${base} ${p.y}`
}

/**
 * Postgres daterange literal → the INCLUSIVE last day of the window.
 *
 * Postgres canonicalises a daterange to `[lo,hi)`, so the upper bound is the first day the
 * window no longer covers. The reader-facing last day is therefore `upper − 1 day`. Getting
 * this wrong would tell the reader a window ended a day after it did; it is exactly the class
 * of small precision error §J does not forgive.
 */
export function windowLastDay(literal: string | null): string | null {
  if (!literal) return null
  const m = /^[[(]([^,]*),([^)\]]*)[)\]]$/.exec(literal.trim())
  if (!m) return null
  const rawUpper = m[2].trim().replace(/^"|"$/g, '')
  if (!/^\d{4}-\d{2}-\d{2}$/.test(rawUpper)) return null
  const upperExclusive = literal.trim().endsWith(')')
  const t = Date.parse(`${rawUpper}T00:00:00Z`)
  if (Number.isNaN(t)) return null
  const lastDay = new Date(t - (upperExclusive ? 86_400_000 : 0))
  return lastDay.toISOString().slice(0, 10)
}

// ---------------------------------------------------------------------------
// The composition
// ---------------------------------------------------------------------------

/**
 * Compose the ask for one `window_closed` ledger row. PURE: same row + same `asOf` → the same
 * string, byte for byte. That determinism is not an aesthetic preference — it is what lets the
 * capture path on a later turn REGENERATE the exact ask that was made, without storing it.
 *
 * @param row   the ledger row, read from the DB by `select.ts` (never constructed by a caller)
 * @param asOf  the run's notion of "now", ISO `yyyy-mm-dd`; only its YEAR is used, to decide
 *              whether a date needs its year spelled out
 */
export function composeWindowAsk(row: LedgerRow, asOf: string): ComposeResult {
  const domainKey = (row.domain ?? '').trim().toLowerCase()
  if (domainKey && SEVERITY_SUPPRESSED_DOMAINS.includes(domainKey)) {
    return {
      composed: false,
      reason: 'severity_suppressed_domain',
      detail:
        `domain "${domainKey}" is severity-suppressed: an unprompted ask never volunteers ` +
        `this class of finding (TARGET_ARCHITECTURE "no unsolicited severity"). The row stays ` +
        `resolvable in the review surface.`,
    }
  }

  const dechromed = dechromeClaim(row.claim_text ?? '')
  if (dechromed.length < 12) {
    return {
      composed: false,
      reason: 'claim_text_unusable',
      detail: `claim_text de-chromes to ${dechromed.length} characters; too little to quote honestly.`,
    }
  }

  const lastDayIso = windowLastDay(row.window)
  if (!lastDayIso) {
    return {
      composed: false,
      reason: 'window_missing_or_unparseable',
      detail: `window literal ${JSON.stringify(row.window)} has no parseable upper bound.`,
    }
  }

  const nowYear = Number(asOf.slice(0, 4))
  const { text: quoted, shortened } = shortenClaim(dechromed)
  const saidWhen = renderMonth(row.confirmed_at ?? row.created_at, nowYear)
  const lastDay = renderDay(lastDayIso, nowYear)
  const domainPhrase = domainKey ? (DOMAIN_PHRASE[domainKey] ?? null) : null

  // Terminal punctuation inside the quote: exactly one, and only when the quote was not
  // shortened with an ellipsis (an ellipsis is already a terminator and adding a stop after it
  // would misrepresent the cut).
  const quotedFinal = /[.?!…]$/.test(quoted) ? quoted : `${quoted}.`

  // ── the fixed prose. Every branch below is a FACT being present or absent, never a
  //    stylistic choice made at runtime. ──
  const lead =
    saidWhen && domainPhrase
      ? `Before I answer — in ${saidWhen} I said, of ${domainPhrase}:`
      : saidWhen
        ? `Before I answer — in ${saidWhen} I said:`
        : domainPhrase
          ? `Before I answer — I said, of ${domainPhrase}:`
          : 'Before I answer — I said:'

  const shortenedNote = shortened ? ' That reading ran on; this is how it opened.' : ''
  const closed = `That window ran to ${lastDay} and has closed.${shortenedNote} What happened?`
  const honestNull = 'If you cannot tell, say so — I would rather hold this open than write down a guess.'

  const text = `${lead}\n\n“${quotedFinal}”\n\n${closed} ${honestNull}`

  return {
    composed: true,
    ask: {
      ledgerRowId: row.id,
      text,
      options: WINDOW_ASK_OPTIONS,
      composition: 'deterministic',
      derivedFrom: {
        claim_quoted: quotedFinal,
        said_when: saidWhen,
        window_last_day: lastDayIso,
        domain_phrase: domainPhrase,
        claim_was_shortened: shortened,
      },
    },
  }
}
